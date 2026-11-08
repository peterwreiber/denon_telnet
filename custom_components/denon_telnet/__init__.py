"""Denon Telnet: settings and signal values that denonavr does not expose."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .client import DenonClient

PLATFORMS = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = DenonClient(entry.data[CONF_HOST])
    task = entry.async_create_background_task(hass, client.run(), "denon_telnet session")
    try:
        await client.wait_ready(20)
    except TimeoutError as err:
        task.cancel()
        raise ConfigEntryNotReady(f"No reply from {client.host} on telnet") from err
    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
