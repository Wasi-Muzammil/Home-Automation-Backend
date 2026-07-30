from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from ..models import (
    DeviceRegisterRequest, DeviceRegisterResponse,
    DeviceInfo, RelayCommand, StateUpdate, RelayState,
)
from ..ws_manager import manager
import json
from datetime import datetime, timezone

router = APIRouter()


@router.post(
    "/api/v1/devices/register",
    response_model=DeviceRegisterResponse,
    summary="Register a new device",
    description="Called by ESP32 on boot to register itself with the central server.",
)
async def register_device(body: DeviceRegisterRequest):
    mac = body.mac_address
    device_id = f"node-{mac.replace(':', '').lower()}"

    info = DeviceInfo(
        mac_address=mac,
        chip_model=body.chip_model,
        firmware_version=body.firmware_version,
        device_name=body.device_name,
        ip_address=body.ip_address,
        capabilities=body.capabilities,
        connected=False,
    )

    existing = manager.get_device(mac)
    if existing:
        info.relays = existing.relays

    manager._device_states[mac] = info

    ws_url = f"ws://{body.ip_address}:8000/ws/device/{mac}"

    return DeviceRegisterResponse(
        status="success",
        device_id=device_id,
        registered=True,
        websocket_url=ws_url,
    )


@router.get(
    "/api/v1/devices",
    response_model=list[DeviceInfo],
    summary="List all registered devices",
)
async def list_devices():
    return list(manager.list_devices().values())


@router.get(
    "/api/v1/devices/{mac_address}",
    response_model=DeviceInfo,
    summary="Get a single device by MAC address",
)
async def get_device(mac_address: str):
    dev = manager.get_device(mac_address)
    if dev is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return dev


@router.post(
    "/api/v1/devices/{mac_address}/command",
    summary="Send a relay command to a device via WebSocket",
    description="Sends a SET_RELAY command to the device if it is connected via WebSocket.",
)
async def send_command(mac_address: str, cmd: RelayCommand):
    if not manager.is_connected(mac_address):
        raise HTTPException(status_code=503, detail="Device not connected")

    payload = cmd.model_dump()
    ok = await manager.send_json(mac_address, payload)
    if not ok:
        raise HTTPException(status_code=503, detail="Failed to send command")
    return {"status": "sent", "device": mac_address, "command": payload}


@router.websocket("/ws/device/{mac_address}")
async def device_websocket(websocket: WebSocket, mac_address: str):
    info = manager.get_device(mac_address)
    if info is None:
        info = DeviceInfo(
            mac_address=mac_address,
            chip_model="unknown",
            firmware_version="unknown",
            device_name=mac_address,
            ip_address=websocket.client.host if websocket.client else "unknown",
            capabilities=[],
            connected=False,
        )

    await manager.connect(mac_address, websocket, info)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event = data.get("event")
            if event == "STATE_UPDATE":
                relays_raw = data.get("relays", [])
                relays = [RelayState(id=r["id"], state=r["state"]) for r in relays_raw]
                rssi = data.get("rssi")
                uptime = data.get("uptime")
                manager.update_state(mac_address, relays, rssi, uptime)

                dev = manager.get_device(mac_address)
                if dev:
                    dev.last_seen = datetime.now(timezone.utc).isoformat()

    except WebSocketDisconnect:
        manager.disconnect(mac_address)
