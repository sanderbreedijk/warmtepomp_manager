from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import WarmtepompManagerEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WarmtepompManagerExecuteButton(coordinator, entry)])


class WarmtepompManagerExecuteButton(WarmtepompManagerEntity, ButtonEntity):
    _attr_translation_key = "actie_nu"
    _attr_icon = "mdi:play-circle"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Voer advies nu uit"
        self._attr_unique_id = f"{entry.entry_id}_actie_nu"

    async def async_press(self) -> None:
        await self.coordinator.async_execute_advice(manual=True, refresh_after=True)
