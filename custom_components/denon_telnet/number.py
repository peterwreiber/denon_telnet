"""Levels and delay."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant

from .client import db_to_level, level_to_db
from .entity import DenonSetting

CHANNELS = {
    "FL": "Nivå fram vänster",
    "FR": "Nivå fram höger",
    "C": "Nivå center",
    "SW": "Nivå subwoofer",
    "SL": "Nivå surround vänster",
    "SR": "Nivå surround höger",
    "SB": "Nivå surround bak",
    "SBL": "Nivå surround bak vänster",
    "SBR": "Nivå surround bak höger",
}


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    values = entry.runtime_data.values
    entities = [
        LevelNumber(entry, "PSBAS ", "Bas", -6, 6, 1),
        LevelNumber(entry, "PSTRE ", "Diskant", -6, 6, 1),
        LfeNumber(entry, "PSLFE ", "LFE"),
        DelayNumber(entry, "PSDELAY ", "Ljudfördröjning"),
        StepNumber(entry, "PSDIM ", "PLII Music Dimension", 0, 6),
        StepNumber(entry, "PSCEN ", "PLII Music Center Width", 0, 7),
    ]
    entities += [
        LevelNumber(entry, f"CV{channel} ", name, -12, 12, 0.5)
        for channel, name in CHANNELS.items()
        if f"CV{channel} " in values
    ]
    async_add_entities(entities)


class LevelNumber(DenonSetting, NumberEntity):
    """A level where 50 means 0 dB."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = "dB"

    def __init__(self, entry, key, name, low, high, step) -> None:
        super().__init__(entry, key, name)
        self._attr_native_min_value = low
        self._attr_native_max_value = high
        self._attr_native_step = step

    @property
    def native_value(self) -> float | None:
        return None if self.raw is None else level_to_db(self.raw)

    async def async_set_native_value(self, value: float) -> None:
        await self._set(db_to_level(value))


class LfeNumber(DenonSetting, NumberEntity):
    """LFE attenuation; the receiver stores 10 for -10 dB."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = "dB"
    _attr_native_min_value = -10
    _attr_native_max_value = 0
    _attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        return None if self.raw is None else -int(self.raw)

    async def async_set_native_value(self, value: float) -> None:
        await self._set(f"{-int(value):02d}")


class DelayNumber(DenonSetting, NumberEntity):
    """Audio delay."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
    _attr_native_min_value = 0
    _attr_native_max_value = 200
    _attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        return None if self.raw is None else int(self.raw)

    async def async_set_native_value(self, value: float) -> None:
        await self._set(f"{int(value):03d}")


class StepNumber(DenonSetting, NumberEntity):
    """A plain step value, sent with two digits."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, key, name, low, high) -> None:
        super().__init__(entry, key, name)
        self._attr_native_min_value = low
        self._attr_native_max_value = high
        self._attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        return None if self.raw is None else int(self.raw)

    async def async_set_native_value(self, value: float) -> None:
        await self._set(f"{int(value):02d}")
