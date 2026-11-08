"""Read-only values."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .entity import DenonEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities(
        [
            DenonSensor(entry, "SD", "Ingångsläge"),
            DenonSensor(entry, "SSINFAISFSV ", "Samplingsfrekvens"),
            DenonSensor(entry, "SSINFAISSIG ", "Insignal (kod)"),
            DenonSensor(entry, "PSMODE:", "Pro Logic-läge"),
            DenonSensor(entry, "PSLOM ", "Loudness Management"),
            DenonSensor(entry, "PSDCO ", "Dolby-kompression"),
            TunerSensor(entry, "TFAN", "Radiofrekvens"),
        ]
    )


class DenonSensor(DenonEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        return self.raw


class TunerSensor(DenonEntity, SensorEntity):
    """FM frequency, sent as 010670 for 106.70 MHz."""

    _attr_native_unit_of_measurement = "MHz"

    @property
    def native_value(self) -> float | None:
        return None if self.raw is None else int(self.raw) / 100
