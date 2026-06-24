from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN
from .config_flow import merged_config

TO_REDACT = {
    "notify_service",
    "tariff_sensor",
    "dhw_temp_sensor",
    "water_heater",
    "dhw_onetime_switch",
    "dhw_max_temp",
    "net_surplus_sensor",
    "net_production_sensor",
    "net_consumption_l1_sensor",
    "net_consumption_l2_sensor",
    "net_consumption_l3_sensor",
    "weather_entity",
}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return safe diagnostics for Home Assistant's diagnostics download."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    cfg = merged_config(entry.data, entry.options)
    data = dict(getattr(coordinator, "data", {}) or {})
    safe_data = {
        key: value
        for key, value in data.items()
        if key not in {"missing_entities"}
    }
    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": getattr(entry, "minor_version", None),
        },
        "config": async_redact_data(cfg, TO_REDACT),
        "runtime": async_redact_data(safe_data, TO_REDACT),
    }
