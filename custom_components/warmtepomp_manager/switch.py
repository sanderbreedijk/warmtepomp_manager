from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_AUTO_EXECUTE
from .entity import WarmtepompManagerEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WarmtepompManagerAutoExecuteSwitch(coordinator, entry)])


class WarmtepompManagerAutoExecuteSwitch(WarmtepompManagerEntity, SwitchEntity):
    _attr_translation_key = "automatisch_uitvoeren"
    _attr_icon = "mdi:robot"
    _attr_unique_id = None

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_name = "Automatisch uitvoeren"
        self._attr_unique_id = f"{entry.entry_id}_automatisch_uitvoeren"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.cfg.get(CONF_AUTO_EXECUTE, False))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_execute(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_auto_execute(False)
