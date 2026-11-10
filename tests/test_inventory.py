import json
import os
import sys
import tempfile
import unittest

# Чтобы импорт работал при `python -m unittest discover -s tests -v`
# из корня проекта: добавляем корень в sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory import (
    INITIAL_DEVICES,
    add_device,
    count_by_status,
    filter_by_type,
    find_device,
    load_devices,
    remove_device,
    save_devices,
    serial_exists,
    validate_device,
)


class TestValidateDevice(unittest.TestCase):

    def test_valid_device_passes(self):
        device = {"id": 1, "name": "Router", "serial": "SN-100", "type": "router"}
        # не должно бросать исключение
        validate_device(device)

    def test_missing_field_raises(self):
        device = {"id": 1, "name": "Router", "serial": "SN-100"}  # нет type
        with self.assertRaises(ValueError):
            validate_device(device)

    def test_empty_field_raises(self):
        device = {"id": 1, "name": "", "serial": "SN-100", "type": "router"}
        with self.assertRaises(ValueError):
            validate_device(device)

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError):
            validate_device("not a dict")  # type: ignore[arg-type]


class TestSerialExists(unittest.TestCase):

    def test_serial_exists_true(self):
        devices = [{"id": 1, "name": "R1", "serial": "SN-001", "type": "router"}]
        self.assertTrue(serial_exists(devices, "SN-001"))

    def test_serial_exists_false(self):
        devices = [{"id": 1, "name": "R1", "serial": "SN-001", "type": "router"}]
        self.assertFalse(serial_exists(devices, "SN-999"))


class TestAddDevice(unittest.TestCase):

    def test_add_device_success(self):
        devices = []
        device = {"id": 1, "name": "R1", "serial": "SN-001", "type": "router"}
        result = add_device(devices, device)
        self.assertIs(result, devices)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["serial"], "SN-001")

    def test_serial_number_is_unique(self):
        devices = [{"id": 1, "name": "R1", "serial": "SN-001", "type": "router"}]
        duplicate = {"id": 2, "name": "R2", "serial": "SN-001", "type": "router"}
        with self.assertRaises(ValueError):
            add_device(devices, duplicate)
        self.assertEqual(len(devices), 1)

    def test_add_device_invalid_payload_raises(self):
        devices = []
        bad = {"id": 2, "name": "R2"}  # нет serial и type
        with self.assertRaises(ValueError):
            add_device(devices, bad)
        self.assertEqual(devices, [])


class TestFindAndRemove(unittest.TestCase):

    def test_find_device_found(self):
        devices = [
            {"id": 1, "name": "R1", "serial": "SN-001", "type": "router"},
            {"id": 2, "name": "S1", "serial": "SN-002", "type": "switch"},
        ]
        found = find_device(devices, "SN-002")
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "S1")

    def test_find_device_not_found(self):
        devices = [{"id": 1, "name": "R1", "serial": "SN-001", "type": "router"}]
        self.assertIsNone(find_device(devices, "SN-999"))

    def test_remove_device_success(self):
        devices = [
            {"id": 1, "name": "R1", "serial": "SN-001", "type": "router"},
            {"id": 2, "name": "S1", "serial": "SN-002", "type": "switch"},
        ]
        remaining = remove_device(devices, "SN-001")
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["serial"], "SN-002")
        # исходный список не изменён (функция возвращает новый)
        self.assertEqual(len(devices), 2)

    def test_remove_device_missing_raises(self):
        devices = [{"id": 1, "name": "R1", "serial": "SN-001", "type": "router"}]
        with self.assertRaises(ValueError):
            remove_device(devices, "SN-999")


class TestFiltersAndCounters(unittest.TestCase):

    def test_filter_by_type(self):
        devices = [
            {"id": 1, "name": "R1", "serial": "SN-001", "type": "router"},
            {"id": 2, "name": "S1", "serial": "SN-002", "type": "switch"},
            {"id": 3, "name": "R2", "serial": "SN-003", "type": "router"},
        ]
        routers = filter_by_type(devices, "router")
        self.assertEqual(len(routers), 2)
        self.assertTrue(all(d["type"] == "router" for d in routers))

    def test_count_by_status(self):
        devices = [
            {"id": 1, "name": "R1", "serial": "SN-001", "type": "router", "status": "active"},
            {"id": 2, "name": "S1", "serial": "SN-002", "type": "switch", "status": "active"},
            {"id": 3, "name": "A1", "serial": "SN-003", "type": "server", "status": "maintenance"},
        ]
        self.assertEqual(count_by_status(devices, "active"), 2)
        self.assertEqual(count_by_status(devices, "maintenance"), 1)
        self.assertEqual(count_by_status(devices, "retired"), 0)


class TestFileIO(unittest.TestCase):

    def test_load_devices_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing.json")
            self.assertEqual(load_devices(path), [])

    def test_load_devices_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "broken.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not a json")
            with self.assertRaises(ValueError):
                load_devices(path)

    def test_load_devices_not_a_list_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "obj.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"devices": []}, f)
            with self.assertRaises(ValueError):
                load_devices(path)

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devices.json")
            save_devices(path, INITIAL_DEVICES)
            loaded = load_devices(path)
            self.assertEqual(loaded, INITIAL_DEVICES)


if __name__ == "__main__":
    unittest.main()