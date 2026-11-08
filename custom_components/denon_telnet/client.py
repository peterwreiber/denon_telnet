"""Telnet client for Denon receivers. The receiver allows one session at a time."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
import re

_LOGGER = logging.getLogger(__name__)

PORT = 23
RETRY_SECONDS = 10
POLL_SECONDS = 30
FULL_POLL_EVERY = 10
READ_TIMEOUT = 90
SEND_GAP = 0.15

# Reply prefix + value is also the command that sets that value.
PREFIXES = (
    "SSINFAISFSV ",
    "SSINFAISSIG ",
    "PSMULTEQ:",
    "PSDYNEQ ",
    "PSDYNVOL ",
    "PSREFLEV ",
    "PSTONE CTRL ",
    "PSCINEMA EQ.",
    "PSBAS ",
    "PSTRE ",
    "PSLFE ",
    "PSDRC ",
    "PSDELAY ",
    "PSRSTR ",
    "PSSWR ",
    "PSDIM ",
    "PSCEN ",
    "PSMODE:",
    "PSLOM ",
    "PSDCO ",
    "TFAN",
    "PW",
    "SLP",
    "SD",
    "MS",
)
STATUS_QUERIES = ("PW?", "SSINFAISFSV ?", "SSINFAISSIG ?")
FULL_QUERIES = (
    "PSMULTEQ: ?",
    "PSDYNEQ ?",
    "PSDYNVOL ?",
    "PSREFLEV ?",
    "PSTONE CTRL ?",
    "PSCINEMA EQ. ?",
    "PSBAS ?",
    "PSTRE ?",
    "PSLFE ?",
    "PSDRC ?",
    "PSDELAY ?",
    "PSRSTR ?",
    "PSSWR ?",
    "PSDIM ?",
    "PSCEN ?",
    "PSMODE: ?",
    "PSLOM ?",
    "PSDCO ?",
    "TFAN?",
    "SLP?",
    "SD?",
    "MS?",
    "CV?",
    *STATUS_QUERIES,
)
CHANNEL = re.compile(r"^(CV[A-Z0-9]+ )(\d{2,3})$")


def parse(line: str) -> tuple[str, str] | None:
    """Return (key, value) for a line from the receiver, or None if it is not tracked."""
    if line.startswith("MSQUICK"):
        return None
    if channel := CHANNEL.match(line):
        return channel[1], channel[2]
    for prefix in PREFIXES:
        if line.startswith(prefix):
            return prefix, line[len(prefix) :].strip()
    return None


def level_to_db(value: str) -> float:
    """Convert a level around 50 to dB: 50 is 0, 48 is -2 and 485 is -1.5."""
    return int(value) / (10 if len(value) == 3 else 1) - 50


def db_to_level(db: float) -> str:
    """Convert dB to the receiver's level format."""
    level = round((db + 50) * 10)
    return str(level // 10) if level % 10 == 0 else str(level)


class DenonClient:
    """Keeps a telnet session open and mirrors the tracked values."""

    def __init__(self, host: str, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.values: dict[str, str] = {}
        self.connected = False
        self._ready = asyncio.Event()
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._listeners: list[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Call listener on every change; returns a function that removes it."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    async def wait_ready(self, timeout: float) -> None:
        """Wait for the first full reading."""
        await asyncio.wait_for(self._ready.wait(), timeout)

    async def send(self, command: str) -> None:
        """Send one command, spaced so that the receiver keeps up."""
        async with self._lock:
            if self._writer is None:
                raise ConnectionError("Not connected to the receiver")
            self._writer.write(f"{command}\r".encode("latin-1"))
            await self._writer.drain()
            await asyncio.sleep(SEND_GAP)

    async def set(
        self,
        key: str,
        value: str,
        confirmed: Callable[[str | None], bool] | None = None,
        timeout: float = 1,
    ) -> bool:
        """Set a value and report whether the receiver confirmed it."""
        if confirmed is None:
            confirmed = value.__eq__
        await self.send(f"{key}{value}")
        for _ in range(round(timeout * 10)):
            if confirmed(self.values.get(key)):
                return True
            await asyncio.sleep(0.1)
        return False

    async def run(self) -> None:
        """Hold the session until cancelled, reconnecting when it drops."""
        while True:
            try:
                reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), 10
                )
                self._set_connected(True)
                poller = asyncio.create_task(self._poll())
                try:
                    await self._read(reader)
                finally:
                    poller.cancel()
            except (OSError, EOFError, TimeoutError) as err:
                _LOGGER.debug("Telnet session to %s ended: %r", self.host, err)
            finally:
                self._close()
                self._set_connected(False)
            await asyncio.sleep(RETRY_SECONDS)

    async def _read(self, reader: asyncio.StreamReader) -> None:
        while True:
            data = await asyncio.wait_for(reader.readuntil(b"\r"), READ_TIMEOUT)
            self._handle(data.decode("latin-1").strip())

    async def _poll(self) -> None:
        polls = 0
        try:
            while True:
                full = polls % FULL_POLL_EVERY == 0
                for command in FULL_QUERIES if full else STATUS_QUERIES:
                    await self.send(command)
                await asyncio.sleep(0.5)
                self._ready.set()
                polls += 1
                await asyncio.sleep(POLL_SECONDS)
        except (OSError, ConnectionError) as err:
            _LOGGER.debug("Telnet send to %s failed: %r", self.host, err)
            self._close()

    def _handle(self, line: str) -> None:
        parsed = parse(line)
        if parsed is None or self.values.get(parsed[0]) == parsed[1]:
            return
        self.values[parsed[0]] = parsed[1]
        self._notify()

    def _set_connected(self, connected: bool) -> None:
        if self.connected != connected:
            self.connected = connected
            self._notify()

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    def _close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
