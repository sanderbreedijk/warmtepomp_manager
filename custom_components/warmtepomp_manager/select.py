from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, CONF_AUTO_EXECUTE, CONF_AWNING_MODE,
    EXECUTION_MODE_ADVICE, EXECUTION_MODE_AUTO, EXECUTION_MODE_LABELS,
    AWNING_MODE_LABELS,
)
from .entity import WarmtepompManagerEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        WarmtepompManagerExecutionModeSelect(coordinator, entry),
        WarmtepompManagerAwningModeSelect(coordinator, entry),
    ])


class WarmtepompManagerExecutionModeSelect(WarmtepompManagerEntity, SelectEntity):
    _attr_translation_key = "uitvoeringsmodus"
    _attr_icon = "mdi:toggle-switch-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_name = "Uitvoeringsmodus"
        self._attr_unique_id = f"{entry.entry_id}_uitvoeringsmodus"
        self._attr_options = [EXECUTION_MODE_LABELS[EXECUTION_MODE_ADVICE], EXECUTION_MODE_LABELS[EXECUTION_MODE_AUTO]]

    @property
    def current_option(self) -> str:
        enabled = bool(self.coordinator.cfg.get(CONF_AUTO_EXECUTE, False))
        return EXECUTION_MODE_LABELS[EXECUTION_MODE_AUTO if enabled else EXECUTION_MODE_ADVICE]

    async def async_select_option(self, option: str) -> None:
        if option == EXECUTION_MODE_LABELS[EXECUTION_MODE_AUTO]:
            await self.coordinator.async_set_auto_execute(True)
        elif option == EXECUTION_MODE_LABELS[EXECUTION_MODE_ADVICE]:
            await self.coordinator.async_set_auto_execute(False)
        self.async_write_ha_state()


class WarmtepompManagerAwningModeSelect(WarmtepompManagerEntity, SelectEntity):
    _attr_translation_key = "zonnescherm_modus"
    _attr_icon = "mdi:awning-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_name = "Zonnescherm modus"
        self._attr_unique_id = f"{entry.entry_id}_zonnescherm_modus"
        self._attr_options = list(AWNING_MODE_LABELS.values())

    @property
    def current_option(self) -> str:
        mode = str(self.coordinator.cfg.get(CONF_AWNING_MODE) or "advice")
        return AWNING_MODE_LABELS.get(mode, AWNING_MODE_LABELS["advice"])

    async def async_select_option(self, option: str) -> None:
        reverse = {v: k for k, v in AWNING_MODE_LABELS.items()}
        await self.coordinator.async_set_awning_mode(reverse.get(option, "advice"))
        self.async_write_ha_state()
