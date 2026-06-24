from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN, PLATFORMS, CONF_SWITCH_DATE, DEFAULTS, LEGACY_WRONG_SWITCH_DATES,
    SERVICE_EXECUTE_ADVICE, SERVICE_SEND_DAILY_REPORT, SERVICE_REFRESH, SERVICE_SET_EXECUTION_MODE, SERVICE_SET_AWNING_MODE,
    EXECUTION_MODE_AUTO,
)
from .config_flow import normalize_switch_date
from .coordinator import WarmtepompManagerCoordinator


def _normalize_legacy_date(value):
    if value in LEGACY_WRONG_SWITCH_DATES:
        return DEFAULTS[CONF_SWITCH_DATE]
    return normalize_switch_date(value)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries safely."""
    data = dict(entry.data or {})
    options = dict(entry.options or {})
    changed = False

    for container in (data, options):
        if CONF_SWITCH_DATE in container:
            new = _normalize_legacy_date(container[CONF_SWITCH_DATE])
            if new != container[CONF_SWITCH_DATE]:
                container[CONF_SWITCH_DATE] = new
                changed = True
        if "tariff_group_sensor" in container:
            container.pop("tariff_group_sensor", None)
            changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=data, options=options)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Warmtepomp Manager from a config entry."""
    coordinator = WarmtepompManagerCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def execute_advice_service(call: ServiceCall) -> None:
        await coordinator.async_execute_advice(manual=True, refresh_after=True)

    async def send_daily_report_service(call: ServiceCall) -> None:
        await coordinator.async_send_daily_report()
        await coordinator.async_request_refresh()

    async def refresh_service(call: ServiceCall) -> None:
        await coordinator.async_request_refresh()

    async def set_execution_mode_service(call: ServiceCall) -> None:
        mode = str(call.data.get("mode", "")).lower().strip()
        await coordinator.async_set_auto_execute(mode in (EXECUTION_MODE_AUTO, "automatisch", "automatic", "auto"))

    async def set_awning_mode_service(call: ServiceCall) -> None:
        mode = str(call.data.get("mode", "")).lower().strip()
        await coordinator.async_set_awning_mode(mode)

    if not hass.services.has_service(DOMAIN, SERVICE_EXECUTE_ADVICE):
        hass.services.async_register(DOMAIN, SERVICE_EXECUTE_ADVICE, execute_advice_service)
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_DAILY_REPORT):
        hass.services.async_register(DOMAIN, SERVICE_SEND_DAILY_REPORT, send_daily_report_service)
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, refresh_service)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_EXECUTION_MODE):
        hass.services.async_register(DOMAIN, SERVICE_SET_EXECUTION_MODE, set_execution_mode_service)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_AWNING_MODE):
        hass.services.async_register(DOMAIN, SERVICE_SET_AWNING_MODE, set_awning_mode_service)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN):
            hass.services.async_remove(DOMAIN, SERVICE_EXECUTE_ADVICE)
            hass.services.async_remove(DOMAIN, SERVICE_SEND_DAILY_REPORT)
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
            hass.services.async_remove(DOMAIN, SERVICE_SET_EXECUTION_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_AWNING_MODE)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
