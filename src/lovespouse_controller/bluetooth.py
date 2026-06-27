from __future__ import annotations

import asyncio
import logging
import time
from typing import Protocol

LOGGER = logging.getLogger(__name__)


class ToyDriver(Protocol):
    def send(self, strength: int, duration_seconds: float) -> None:
        ...


class BluetoothLeToyDriver:
    COMMANDS = (
        "F41D7C",
        "F7864E",
        "F60F5F",
        "F1B02B",
        "F0393A",
        "F3A208",
        "F22B19",
        "FDDCE1",
        "FC55F0",
        "C5175C",
    )

    def __init__(self) -> None:
        try:
            import winsdk.windows.devices.bluetooth.advertisement as advertisement
            import winsdk.windows.storage.streams as streams
            from winsdk.windows.devices.bluetooth.advertisement import (
                BluetoothLEAdvertisementPublisherStatus,
            )
        except ImportError as exc:
            raise RuntimeError(
                "winsdk is required for Bluetooth LE control. Install it or run with --dry-run."
            ) from exc

        self._advertisement = advertisement
        self._streams = streams
        self._started_status = BluetoothLEAdvertisementPublisherStatus.STARTED

    def send(self, strength: int, duration_seconds: float) -> None:
        command = self.COMMANDS[max(0, min(9, strength))]
        asyncio.run(self._send_command_async(command, duration_seconds))

    async def _send_command_async(self, command: str, duration_seconds: float) -> None:
        advertisement = self._advertisement
        publisher = advertisement.BluetoothLEAdvertisementPublisher()
        manufacturer_data = advertisement.BluetoothLEManufacturerData()
        manufacturer_data.company_id = 0xFF

        writer = self._streams.DataWriter()
        writer.write_bytes(bytearray.fromhex("0000006db643ce97fe427c" + command))
        manufacturer_data.data = writer.detach_buffer()
        publisher.advertisement.manufacturer_data.append(manufacturer_data)

        publisher.start()
        while publisher.status != self._started_status:
            time.sleep(0.01)

        time.sleep(duration_seconds)
        publisher.stop()


class DryRunToyDriver:
    def send(self, strength: int, duration_seconds: float) -> None:
        LOGGER.info("dry-run command strength=%s duration=%.3fs", strength, duration_seconds)
        time.sleep(duration_seconds)
