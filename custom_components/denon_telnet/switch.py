"""On/off settings."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .entity import DenonEntity, DenonSetting

SWITCHES = (
    ("PSDYNEQ ", "Dynamic EQ"),
    ("PSTONE CTRL ", "Tonkontroll"),
    ("PSCINEMA EQ.", "Cinema EQ"),
    ("PSSWR ", "Subwoofer"),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities(
        [DenonPower(entry, "PW", "Ström"), *(DenonSwitch(entry, *switch) for switch in SWITCHES)]
    )


class DenonSwitch(DenonSetting, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        return None if self.raw is None else self.raw == "ON"

    async def async_turn_on(self, **kwargs) -> None:
        await self._set("ON")

    async def async_turn_off(self, **kwargs) -> None:
        await self._set("OFF")


class DenonPower(DenonEntity, SwitchEntity):
    """Power for the receiver; the state follows what the receiver reports."""

    _attr_icon = "mdi:power"

    @property
    def is_on(self) -> bool | None:
        return None if self.raw is None else self.raw == "ON"

    async def async_turn_on(self, **kwargs) -> None:
        await self._client.send("PWON")

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.send("PWSTANDBY")
