from pydantic import BaseModel
from typing import List, Optional


class DeviceRegisterRequest(BaseModel):
    mac_address: str
    chip_model: str
    firmware_version: str
    device_name: str
    ip_address: str
    capabilities: List[str]


class DeviceRegisterResponse(BaseModel):
    status: str
    device_id: str
    registered: bool
    websocket_url: str


class RelayState(BaseModel):
    id: int
    state: bool


class DeviceInfo(BaseModel):
    mac_address: str
    chip_model: str
    firmware_version: str
    device_name: str
    ip_address: str
    capabilities: List[str]
    connected: bool
    relays: List[RelayState] = []
    rssi: Optional[int] = None
    uptime: Optional[int] = None
    last_seen: Optional[str] = None


class RelayCommand(BaseModel):
    action: str = "SET_RELAY"
    relay_id: int
    state: bool


class StateUpdate(BaseModel):
    event: str
    mac_address: str
    relays: List[RelayState]
    rssi: Optional[int] = None
    uptime: Optional[int] = None
