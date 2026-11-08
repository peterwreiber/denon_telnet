"""Base entity for Denon Telnet."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .client import DenonClient
from .const import DOMAIN


class DenonEntity(Entity):
    """An entity for one tracked value."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _needs_power = False

    def __init__(self, entry: ConfigEntry, key: str, name: str) -> None:
        self._client: DenonClient = entry.runtime_data
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key.strip()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Denon Telnet",
            manufacturer="Denon",
        )

    @property
    def available(self) -> bool:
        if self._needs_power and self._client.values.get("PW") != "ON":
            return False
        return self._client.connected and self._key in self._client.values

    @property
    def raw(self) -> str | None:
        return self._client.values.get(self._key)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._client.add_listener(self.async_write_ha_state))

    async def _set(self, value: str, confirmed=None, timeout: float = 1) -> None:
        if not await self._client.set(self._key, value, confirmed, timeout):
            raise HomeAssistantError(
                f"Stärkaren nekade ändringen av {self.name}. Den gäller inte i nuvarande läge "
                "eller är låst, till exempel utan Audyssey-kalibrering. "
                "Bas och diskant kräver att tonkontrollen är på."
            )


class DenonSetting(DenonEntity):
    """A setting the receiver only accepts while it is on."""

    _needs_power = True
