from fastapi import WebSocket
from typing import Dict, Optional
from models import DeviceInfo, RelayState


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._device_states: Dict[str, DeviceInfo] = {}

    async def connect(self, mac: str, ws: WebSocket, info: DeviceInfo):
        await ws.accept()
        self._connections[mac] = ws
        info.connected = True
        self._device_states[mac] = info

    def disconnect(self, mac: str):
        self._connections.pop(mac, None)
        if mac in self._device_states:
            self._device_states[mac].connected = False

    async def send_json(self, mac: str, data: dict) -> bool:
        ws = self._connections.get(mac)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception:
            self.disconnect(mac)
            return False

    def update_state(self, mac: str, relays: list, rssi: Optional[int], uptime: Optional[int]):
        info = self._device_states.get(mac)
        if info:
            info.relays = [RelayState(**r) if isinstance(r, dict) else r for r in relays]
            info.rssi = rssi
            info.uptime = uptime

    def get_device(self, mac: str) -> Optional[DeviceInfo]:
        return self._device_states.get(mac)

    def list_devices(self) -> Dict[str, DeviceInfo]:
        return dict(self._device_states)

    def is_connected(self, mac: str) -> bool:
        return mac in self._connections


manager = ConnectionManager()
