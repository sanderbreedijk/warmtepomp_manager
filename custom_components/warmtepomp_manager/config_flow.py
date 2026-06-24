from __future__ import annotations

from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import *


def normalize_switch_date(value: Any) -> str:
    """Return a valid DD-MM-YYYY date string. Falls back to 01-01-2027."""
    text = str(value or "").strip()
    if text in LEGACY_WRONG_SWITCH_DATES:
        return DEFAULTS[CONF_SWITCH_DATE]
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return DEFAULTS[CONF_SWITCH_DATE]


def merged_config(data: dict[str, Any] | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(DEFAULTS)
    cfg.update(data or {})
    cfg.update(options or {})
    cfg[CONF_SWITCH_DATE] = normalize_switch_date(cfg.get(CONF_SWITCH_DATE))
    return cfg


def _schema(current: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Optional(CONF_STRATEGY, default=current[CONF_STRATEGY]): vol.In(STRATEGIES),
        vol.Optional(CONF_SWITCH_DATE, default=current[CONF_SWITCH_DATE]): str,
        vol.Optional(CONF_AUTO_EXECUTE, default=current[CONF_AUTO_EXECUTE]): bool,
        vol.Optional(CONF_TARIFF_SENSOR, default=current[CONF_TARIFF_SENSOR]): str,
        vol.Optional(CONF_DHW_TEMP_SENSOR, default=current[CONF_DHW_TEMP_SENSOR]): str,
        vol.Optional(CONF_WATER_HEATER, default=current[CONF_WATER_HEATER]): str,
        vol.Optional(CONF_WATER_HEATER_COMFORT_MODE, default=current[CONF_WATER_HEATER_COMFORT_MODE]): str,
        vol.Optional(CONF_DHW_ONETIME_SWITCH, default=current[CONF_DHW_ONETIME_SWITCH]): str,
        vol.Optional(CONF_DHW_MAX_TEMP, default=current[CONF_DHW_MAX_TEMP]): str,
        vol.Optional(CONF_NET_SURPLUS_SENSOR, default=current[CONF_NET_SURPLUS_SENSOR]): str,
        vol.Optional(CONF_NET_PRODUCTION_SENSOR, default=current[CONF_NET_PRODUCTION_SENSOR]): str,
        vol.Optional(CONF_NET_CONSUMPTION_L1_SENSOR, default=current[CONF_NET_CONSUMPTION_L1_SENSOR]): str,
        vol.Optional(CONF_NET_CONSUMPTION_L2_SENSOR, default=current[CONF_NET_CONSUMPTION_L2_SENSOR]): str,
        vol.Optional(CONF_NET_CONSUMPTION_L3_SENSOR, default=current[CONF_NET_CONSUMPTION_L3_SENSOR]): str,
        vol.Optional(CONF_TOTAL_ENERGY_SENSOR, default=current[CONF_TOTAL_ENERGY_SENSOR]): str,
        vol.Optional(CONF_METER_TOTAL_SENSOR, default=current[CONF_METER_TOTAL_SENSOR]): str,
        vol.Optional(CONF_COMPRESSOR_RUNTIME_HOURS_SENSOR, default=current[CONF_COMPRESSOR_RUNTIME_HOURS_SENSOR]): str,
        vol.Optional(CONF_COMPRESSOR_STARTS_SENSOR, default=current[CONF_COMPRESSOR_STARTS_SENSOR]): str,
        vol.Optional(CONF_HP_POWER_SENSOR, default=current[CONF_HP_POWER_SENSOR]): str,
        vol.Optional(CONF_DHW_ACTIVE_SENSOR, default=current[CONF_DHW_ACTIVE_SENSOR]): str,
        vol.Optional(CONF_HEATING_ACTIVE_SENSOR, default=current[CONF_HEATING_ACTIVE_SENSOR]): str,
        vol.Optional(CONF_COOLING_ACTIVE_SENSOR, default=current[CONF_COOLING_ACTIVE_SENSOR]): str,
        vol.Optional(CONF_HP_OPERATING_STATE_SENSOR, default=current[CONF_HP_OPERATING_STATE_SENSOR]): str,
        vol.Optional(CONF_STANDBY_POWER_W, default=current[CONF_STANDBY_POWER_W]): vol.Coerce(float),
        vol.Optional(CONF_ACTIVE_POWER_W, default=current[CONF_ACTIVE_POWER_W]): vol.Coerce(float),
        vol.Optional(CONF_FORECAST_SOLAR_TODAY_SENSOR, default=current[CONF_FORECAST_SOLAR_TODAY_SENSOR]): str,
        vol.Optional(CONF_FORECAST_SOLAR_TOMORROW_SENSOR, default=current[CONF_FORECAST_SOLAR_TOMORROW_SENSOR]): str,
        vol.Optional(CONF_SOLAR_PEAK_TOMORROW_SENSOR, default=current[CONF_SOLAR_PEAK_TOMORROW_SENSOR]): str,
        vol.Optional(CONF_SOLAR_NEXT_12H_SENSOR, default=current[CONF_SOLAR_NEXT_12H_SENSOR]): str,
        vol.Optional(CONF_WEATHER_ENTITY, default=current[CONF_WEATHER_ENTITY]): str,
        vol.Optional(CONF_INDOOR_TEMP_SENSOR, default=current[CONF_INDOOR_TEMP_SENSOR]): str,
        vol.Optional(CONF_COMFORT_TEMP, default=current[CONF_COMFORT_TEMP]): vol.Coerce(float),
        vol.Optional(CONF_NEGATIVE_PRICE_STRATEGY, default=current[CONF_NEGATIVE_PRICE_STRATEGY]): vol.In(NEGATIVE_PRICE_STRATEGIES),
        vol.Optional(CONF_PV_LIMIT_CONTROL_MODE_SELECT, default=current[CONF_PV_LIMIT_CONTROL_MODE_SELECT]): str,
        vol.Optional(CONF_AWNING_MODE, default=current[CONF_AWNING_MODE]): vol.In(AWNING_MODE_LABELS),
        vol.Optional(CONF_AWNING_COVER, default=current[CONF_AWNING_COVER]): str,
        vol.Optional(CONF_AWNING_PV_POWER_SENSOR, default=current[CONF_AWNING_PV_POWER_SENSOR]): str,
        vol.Optional(CONF_AWNING_PV_CLOSE_W, default=current[CONF_AWNING_PV_CLOSE_W]): vol.Coerce(float),
        vol.Optional(CONF_AWNING_PV_TIMEOUT_MIN, default=current[CONF_AWNING_PV_TIMEOUT_MIN]): vol.Coerce(int),
        vol.Optional(CONF_AWNING_ACTIVE_MONTHS, default=current[CONF_AWNING_ACTIVE_MONTHS]): str,
        vol.Optional(CONF_UV_SENSOR, default=current[CONF_UV_SENSOR]): str,
        vol.Optional(CONF_WIND_SPEED_SENSOR, default=current[CONF_WIND_SPEED_SENSOR]): str,
        vol.Optional(CONF_RAIN_SENSOR, default=current[CONF_RAIN_SENSOR]): str,
        vol.Optional(CONF_AWNING_UV_CLOSE, default=current[CONF_AWNING_UV_CLOSE]): vol.Coerce(float),
        vol.Optional(CONF_AWNING_UV_OPEN, default=current[CONF_AWNING_UV_OPEN]): vol.Coerce(float),
        vol.Optional(CONF_AWNING_MAX_WIND, default=current[CONF_AWNING_MAX_WIND]): vol.Coerce(float),
        vol.Optional(CONF_AWNING_MIN_INDOOR_TEMP, default=current[CONF_AWNING_MIN_INDOOR_TEMP]): vol.Coerce(float),
        vol.Optional(CONF_AWNING_START_HOUR, default=current[CONF_AWNING_START_HOUR]): vol.Coerce(int),
        vol.Optional(CONF_AWNING_END_HOUR, default=current[CONF_AWNING_END_HOUR]): vol.Coerce(int),
        vol.Optional(CONF_LOW_PRICE_THRESHOLD, default=current[CONF_LOW_PRICE_THRESHOLD]): vol.Coerce(float),
        vol.Optional(CONF_PV_SURPLUS_THRESHOLD, default=current[CONF_PV_SURPLUS_THRESHOLD]): vol.Coerce(float),
        vol.Optional(CONF_DHW_MIN_TEMP, default=current[CONF_DHW_MIN_TEMP]): vol.Coerce(float),
        vol.Optional(CONF_DHW_TARGET_TEMP, default=current[CONF_DHW_TARGET_TEMP]): vol.Coerce(float),
        vol.Optional(CONF_COOLDOWN_HOURS, default=current[CONF_COOLDOWN_HOURS]): vol.Coerce(float),
        vol.Optional(CONF_MAX_ONETIME_PER_DAY, default=current[CONF_MAX_ONETIME_PER_DAY]): vol.Coerce(int),
        vol.Optional(CONF_EXECUTE_SET_MAX_TEMP, default=current[CONF_EXECUTE_SET_MAX_TEMP]): bool,
        vol.Optional(CONF_EXECUTE_WATER_HEATER_MODE, default=current[CONF_EXECUTE_WATER_HEATER_MODE]): bool,
        vol.Optional(CONF_NOTIFY_SERVICE, default=current[CONF_NOTIFY_SERVICE]): str,
        vol.Optional(CONF_NOTIFY_BOILER, default=current[CONF_NOTIFY_BOILER]): str,
        vol.Optional(CONF_NOTIFY_AUTO, default=current[CONF_NOTIFY_AUTO]): str,
        vol.Optional(CONF_NOTIFY_DISHWASHER, default=current[CONF_NOTIFY_DISHWASHER]): str,
        vol.Optional(CONF_NOTIFY_PRICE, default=current[CONF_NOTIFY_PRICE]): str,
        vol.Optional(CONF_HIGH_PRICE_THRESHOLD, default=current[CONF_HIGH_PRICE_THRESHOLD]): vol.Coerce(float),
        vol.Optional(CONF_DISHWASHER_ENABLE, default=current[CONF_DISHWASHER_ENABLE]): bool,
        vol.Optional(CONF_DISHWASHER_AUTO, default=current[CONF_DISHWASHER_AUTO]): bool,
        vol.Optional(CONF_DISHWASHER_DOOR_SENSOR, default=current[CONF_DISHWASHER_DOOR_SENSOR]): str,
        vol.Optional(CONF_DISHWASHER_REMOTE_START_SENSOR, default=current[CONF_DISHWASHER_REMOTE_START_SENSOR]): str,
        vol.Optional(CONF_DISHWASHER_PROGRAM_SELECT, default=current[CONF_DISHWASHER_PROGRAM_SELECT]): str,
        vol.Optional(CONF_DISHWASHER_START_DELAY_SELECT, default=current[CONF_DISHWASHER_START_DELAY_SELECT]): str,
        vol.Optional(CONF_DISHWASHER_START_BUTTON, default=current[CONF_DISHWASHER_START_BUTTON]): str,
        vol.Optional(CONF_DISHWASHER_ECO_OPTION, default=current[CONF_DISHWASHER_ECO_OPTION]): str,
        vol.Optional(CONF_DISHWASHER_KWH, default=current[CONF_DISHWASHER_KWH]): vol.Coerce(float),
        vol.Optional(CONF_DISHWASHER_NOTIFY_TIME, default=current[CONF_DISHWASHER_NOTIFY_TIME]): str,
        vol.Optional(CONF_DHW_DISINFECT_DAY_SELECT, default=current[CONF_DHW_DISINFECT_DAY_SELECT]): str,
        vol.Optional(CONF_DHW_DISINFECT_SWITCH, default=current[CONF_DHW_DISINFECT_SWITCH]): str,
        vol.Optional(CONF_SHOWER_DAYS, default=current[CONF_SHOWER_DAYS]): str,
        vol.Optional(CONF_DHW_LOAD_ONCE_PER_DAY, default=current[CONF_DHW_LOAD_ONCE_PER_DAY]): bool,
        vol.Optional(CONF_DHW_PRICE_OPT_UNTIL, default=current[CONF_DHW_PRICE_OPT_UNTIL]): str,
    })


class WarmtepompManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 12

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_SWITCH_DATE] = normalize_switch_date(user_input.get(CONF_SWITCH_DATE))
            await self.async_set_unique_id("warmtepomp_manager_main")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Warmtepomp Manager", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(merged_config()), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WarmtepompManagerOptionsFlow(config_entry)


class WarmtepompManagerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_SWITCH_DATE] = normalize_switch_date(user_input.get(CONF_SWITCH_DATE))
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=_schema(merged_config(self.config_entry.data, self.config_entry.options)))
