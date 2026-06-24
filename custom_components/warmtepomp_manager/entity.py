from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, VERSION


class WarmtepompManagerEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "main")},
            name="Warmtepomp Manager",
            manufacturer="Sander Breedijk",
            model="PV/Prijs Warmtepomp Manager",
            sw_version=VERSION,
        )
