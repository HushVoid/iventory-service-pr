import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone




PORT = int(os.environ.get("PORT", "8005"))
MESSAGE = os.environ.get("MESSAGE", "Inventory online")
APP_VERSION = os.environ.get("APP_VERSION", "1.0")
HOSTNAME = socket.gethostname()

DATA_DIR = "/data"
STATE_FILE = os.path.join(DATA_DIR, "state.json")

REQUIRED_FIELDS = ("id", "name", "serial", "type")



def validate_device(device: dict) -> None:

    if not isinstance(device, dict):
        raise ValueError("Device must be a dict")
    for field in REQUIRED_FIELDS:
        if field not in device:
            raise ValueError(f"Missing required field: {field}")
        if device[field] in ("", None):
            raise ValueError(f"Field '{field}' must not be empty")


def serial_exists(devices: list, serial: str) -> bool:
    return any(d.get("serial") == serial for d in devices)


def add_device(devices: list, device: dict) -> list:

#    validate_device(device)
#    if serial_exists(devices, device["serial"]):
 #       raise ValueError(f"Serial number '{device['serial']}' is not unique")
    devices.append(device)
    return devices


def find_device(devices: list, serial: str):
    for d in devices:
        if d.get("serial") == serial:
            return d
    return None


def remove_device(devices: list, serial: str) -> list:
    if not serial_exists(devices, serial):
        raise ValueError(f"Device with serial '{serial}' not found")
    return [d for d in devices if d.get("serial") != serial]


def filter_by_type(devices: list, device_type: str) -> list:
    return [d for d in devices if d.get("type") == device_type]


def count_by_status(devices: list, status: str) -> int:
    return sum(1 for d in devices if d.get("status") == status)


def load_devices(path: str) -> list:

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of devices in {path}")
    return data


def save_devices(path: str, devices: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)


def load_counter() -> int:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("requests", 0))
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return 0


def save_counter(value: int) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"requests": value}, f)



INITIAL_DEVICES = [
    {"id": 1, "name": "Router R1", "serial": "SN-001", "type": "router", "status": "active"},
    {"id": 2, "name": "Switch S1", "serial": "SN-002", "type": "switch", "status": "active"},
    {"id": 3, "name": "Server A1", "serial": "SN-003", "type": "server", "status": "maintenance"},
]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-App-Name", "inventory-service")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        counter = load_counter() + 1
        save_counter(counter)

        if self.path == "/health":
            self._send(200, {"status": "ok", "hostname": HOSTNAME})
        elif self.path == "/inventory":
            self._send(200, {
                "message": MESSAGE,
                "version": APP_VERSION,
                "hostname": HOSTNAME,
                "requests": counter,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "devices": INITIAL_DEVICES,
            })
        else:
            self._send(404, {"error": "not found", "path": self.path})


if __name__ == "__main__":
    print(f"Starting inventory-service on 0.0.0.0:{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()