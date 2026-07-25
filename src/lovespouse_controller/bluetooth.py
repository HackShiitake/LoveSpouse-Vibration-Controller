from __future__ import annotations

import asyncio
import logging
import time
from typing import Protocol

LOGGER = logging.getLogger(__name__)

# Maximum time to wait for the advertisement publisher to reach STARTED before
# giving up. Without a bound a failed publisher would hang the worker forever.
_START_TIMEOUT_SECONDS = 3.0


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
            import winsdk.windows.devices.radios as radios
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
        self._radios = radios
        self._started_status = BluetoothLEAdvertisementPublisherStatus.STARTED
        self._aborted_status = BluetoothLEAdvertisementPublisherStatus.ABORTED

        # Turning the radio on up front means the very first pulse works and the
        # user gets an actionable message immediately instead of silent failure.
        self._ensure_radio_on()

    def send(self, strength: int, duration_seconds: float) -> None:
        command = self.COMMANDS[max(0, min(9, strength))]
        asyncio.run(self._send_command_async(command, duration_seconds))

    def _ensure_radio_on(self) -> None:
        try:
            asyncio.run(self._ensure_radio_on_async())
        except Exception:
            LOGGER.warning(
                "Could not verify the Bluetooth radio state; make sure Bluetooth is turned on.",
                exc_info=True,
            )

    async def _ensure_radio_on_async(self) -> None:
        radios = self._radios
        try:
            await radios.Radio.request_access_async()
        except Exception:
            LOGGER.debug("Bluetooth radio access request failed.", exc_info=True)

        bluetooth = await self._get_bluetooth_radio()
        if bluetooth is None:
            LOGGER.warning("No Bluetooth radio was detected on this system.")
            return

        if bluetooth.state == radios.RadioState.ON:
            LOGGER.info("Bluetooth radio is on.")
            return

        LOGGER.warning(
            "Bluetooth radio is %s; attempting to turn it on...", bluetooth.state.name
        )
        try:
            await bluetooth.set_state_async(radios.RadioState.ON)
        except Exception:
            LOGGER.warning(
                "Could not turn Bluetooth on automatically. "
                "Please enable Bluetooth in Windows settings.",
                exc_info=True,
            )
            return

        bluetooth = await self._get_bluetooth_radio()
        if bluetooth is not None and bluetooth.state == radios.RadioState.ON:
            LOGGER.info("Bluetooth radio turned on.")
        else:
            LOGGER.warning(
                "Bluetooth is still off. Please enable Bluetooth in Windows settings."
            )

    async def _get_bluetooth_radio(self):
        radios = self._radios
        all_radios = await radios.Radio.get_radios_async()
        for radio in all_radios:
            if radio.kind == radios.RadioKind.BLUETOOTH:
                return radio
        return None

    async def _send_command_async(self, command: str, duration_seconds: float) -> None:
        advertisement = self._advertisement
        publisher = advertisement.BluetoothLEAdvertisementPublisher()
        manufacturer_data = advertisement.BluetoothLEManufacturerData()
        manufacturer_data.company_id = 0xFF

        writer = self._streams.DataWriter()
        writer.write_bytes(bytearray.fromhex("0000006db643ce97fe427c" + command))
        manufacturer_data.data = writer.detach_buffer()
        publisher.advertisement.manufacturer_data.append(manufacturer_data)

        loop = asyncio.get_running_loop()
        started: asyncio.Future = loop.create_future()

        def on_status_changed(_sender, args) -> None:
            if started.done():
                return
            if args.status == self._started_status:
                loop.call_soon_threadsafe(started.set_result, None)
            elif args.status == self._aborted_status:
                message = self._describe_abort(args.error)
                loop.call_soon_threadsafe(
                    started.set_exception, RuntimeError(message)
                )

        token = publisher.add_status_changed(on_status_changed)
        try:
            publisher.start()
            try:
                await asyncio.wait_for(started, timeout=_START_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                raise RuntimeError(
                    "Bluetooth advertisement did not start within "
                    f"{_START_TIMEOUT_SECONDS:.0f}s (status={publisher.status})."
                )
            await asyncio.sleep(duration_seconds)
        finally:
            try:
                publisher.stop()
            except Exception:
                LOGGER.debug("Failed to stop advertisement.", exc_info=True)
            publisher.remove_status_changed(token)

    @staticmethod
    def _describe_abort(error) -> str:
        name = getattr(error, "name", str(error))
        if name == "RADIO_NOT_AVAILABLE":
            return (
                "Bluetooth advertisement was aborted: the Bluetooth radio is not "
                "available. Turn Bluetooth on in Windows settings."
            )
        return f"Bluetooth advertisement was aborted ({name})."


class DryRunToyDriver:
    def send(self, strength: int, duration_seconds: float) -> None:
        LOGGER.info("dry-run command strength=%s duration=%.3fs", strength, duration_seconds)
        time.sleep(duration_seconds)
