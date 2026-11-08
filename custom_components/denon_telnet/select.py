"""Audyssey and related modes."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .entity import DenonSetting

SELECTS = (
    ("PSMULTEQ:", "Audyssey MultEQ", ["AUDYSSEY", "BYP.LR", "FLAT", "MANUAL", "OFF"]),
    ("PSDYNVOL ", "Dynamic Volume", ["OFF", "LIT", "MED", "HEV"]),
    ("PSREFLEV ", "Reference Level Offset", ["0", "5", "10", "15"]),
    ("PSDRC ", "Dynamikkompression", ["AUTO", "LOW", "MID", "HI", "OFF"]),
    ("PSRSTR ", "Restorer", ["OFF", "MODE1", "MODE2", "MODE3"]),
)


SOUND_MODES = [
    "MOVIE",
    "MUSIC",
    "GAME",
    "STEREO",
    "MCH STEREO",
    "DIRECT",
    "PURE DIRECT",
    "DOLBY DIGITAL",
    "DTS SURROUND",
]
# Movie, music and game are reported as the decoder in use, e.g. DOLBY PL2 MUSIC.
DECODERS = ("DOLBY", "DTS", "PLII", "AAC", "M CH IN")
DECODER_MODES = (
    ("MUSIC", ("MUSIC", " M", " MS")),
    ("MOVIE", ("MOVIE", "CINEMA", " C", " MV")),
    ("GAME", ("GAME", " G", " GM")),
)


def sound_mode(raw: str | None) -> str | None:
    """Map the mode the receiver reports to the option that selects it."""
    if raw is None or raw in SOUND_MODES:
        return raw
    if raw.startswith(DECODERS):
        for mode, endings in DECODER_MODES:
            if raw.endswith(endings):
                return mode
    return None


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    async_add_entities(
        [*(DenonSelect(entry, *select) for select in SELECTS), DenonSoundMode(entry)]
    )


class DenonSelect(DenonSetting, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, key, name, options) -> None:
        super().__init__(entry, key, name)
        self._attr_options = options

    @property
    def current_option(self) -> str | None:
        return self.raw if self.raw in self.options else None

    async def async_select_option(self, option: str) -> None:
        await self._set(option)


class DenonSoundMode(DenonSetting, SelectEntity):
    """Surround mode. The receiver takes a second or two to switch."""

    _attr_options = SOUND_MODES

    def __init__(self, entry) -> None:
        super().__init__(entry, "MS", "Ljudläge")

    @property
    def current_option(self) -> str | None:
        return sound_mode(self.raw)

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {"rapporterat": self.raw}

    async def async_select_option(self, option: str) -> None:
        # MUSIC recalls the last music mode, which may be plain STEREO.
        accepted = {option, "STEREO"} if option == "MUSIC" else {option}
        await self._set(option, lambda raw: sound_mode(raw) in accepted, timeout=5)
