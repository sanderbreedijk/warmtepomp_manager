from __future__ import annotations

DOMAIN = "warmtepomp_manager"
VERSION = "1.7.0"

from homeassistant.const import Platform

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON, Platform.SELECT]

CONF_STRATEGY = "strategy"
CONF_SWITCH_DATE = "switch_date"
CONF_AUTO_EXECUTE = "auto_execute"
CONF_TARIFF_SENSOR = "tariff_sensor"
CONF_DHW_TEMP_SENSOR = "dhw_temp_sensor"
CONF_WATER_HEATER = "water_heater"
CONF_WATER_HEATER_COMFORT_MODE = "water_heater_comfort_mode"
CONF_DHW_ONETIME_SWITCH = "dhw_onetime_switch"
CONF_DHW_MAX_TEMP = "dhw_max_temp"
CONF_NET_SURPLUS_SENSOR = "net_surplus_sensor"
CONF_LOW_PRICE_THRESHOLD = "low_price_threshold"
CONF_PV_SURPLUS_THRESHOLD = "pv_surplus_threshold"
CONF_DHW_MIN_TEMP = "dhw_min_temp"
CONF_DHW_TARGET_TEMP = "dhw_target_temp"
CONF_COOLDOWN_HOURS = "cooldown_hours"
CONF_MAX_ONETIME_PER_DAY = "max_onetime_per_day"
CONF_EXECUTE_SET_MAX_TEMP = "execute_set_max_temp"
CONF_EXECUTE_WATER_HEATER_MODE = "execute_water_heater_mode"

# v1 planner / notifications / legionella
CONF_NOTIFY_SERVICE = "notify_service"
CONF_DHW_DISINFECT_DAY_SELECT = "dhw_disinfect_day_select"
CONF_DHW_DISINFECT_SWITCH = "dhw_disinfect_switch"
CONF_SHOWER_DAYS = "shower_days"
CONF_DHW_LOAD_ONCE_PER_DAY = "dhw_load_once_per_day"
CONF_DHW_PRICE_OPT_UNTIL = "dhw_price_opt_until"


# Dishwasher / phone notifications
CONF_NOTIFY_BOILER = "notify_boiler"
CONF_NOTIFY_AUTO = "notify_auto"
CONF_NOTIFY_DISHWASHER = "notify_dishwasher"
CONF_NOTIFY_PRICE = "notify_price"
CONF_DISHWASHER_ENABLE = "dishwasher_enable"
CONF_DISHWASHER_AUTO = "dishwasher_auto"
CONF_DISHWASHER_DOOR_SENSOR = "dishwasher_door_sensor"
CONF_DISHWASHER_REMOTE_START_SENSOR = "dishwasher_remote_start_sensor"
CONF_DISHWASHER_PROGRAM_SELECT = "dishwasher_program_select"
CONF_DISHWASHER_START_DELAY_SELECT = "dishwasher_start_delay_select"
CONF_DISHWASHER_START_BUTTON = "dishwasher_start_button"
CONF_DISHWASHER_ECO_OPTION = "dishwasher_eco_option"
CONF_DISHWASHER_KWH = "dishwasher_kwh"
CONF_DISHWASHER_NOTIFY_TIME = "dishwasher_notify_time"
CONF_HIGH_PRICE_THRESHOLD = "high_price_threshold"

# Electricity/net sensors
CONF_NET_PRODUCTION_SENSOR = "net_production_sensor"
CONF_NET_CONSUMPTION_L1_SENSOR = "net_consumption_l1_sensor"
CONF_NET_CONSUMPTION_L2_SENSOR = "net_consumption_l2_sensor"
CONF_NET_CONSUMPTION_L3_SENSOR = "net_consumption_l3_sensor"

# Performance sensors
CONF_TOTAL_ENERGY_SENSOR = "total_energy_sensor"
CONF_METER_TOTAL_SENSOR = "meter_total_sensor"
CONF_COMPRESSOR_RUNTIME_HOURS_SENSOR = "compressor_runtime_hours_sensor"
CONF_COMPRESSOR_STARTS_SENSOR = "compressor_starts_sensor"

# Status machine sensors
CONF_HP_POWER_SENSOR = "hp_power_sensor"
CONF_DHW_ACTIVE_SENSOR = "dhw_active_sensor"
CONF_HEATING_ACTIVE_SENSOR = "heating_active_sensor"
CONF_COOLING_ACTIVE_SENSOR = "cooling_active_sensor"
CONF_HP_OPERATING_STATE_SENSOR = "hp_operating_state_sensor"
CONF_STANDBY_POWER_W = "standby_power_w"
CONF_ACTIVE_POWER_W = "active_power_w"

CONF_PV_LIMIT_CONTROL_MODE_SELECT = "pv_limit_control_mode_select"

# Awning / solar shading
CONF_AWNING_MODE = "awning_mode"
CONF_AWNING_COVER = "awning_cover"
CONF_AWNING_PV_POWER_SENSOR = "awning_pv_power_sensor"
CONF_AWNING_PV_CLOSE_W = "awning_pv_close_w"
CONF_AWNING_PV_TIMEOUT_MIN = "awning_pv_timeout_min"
CONF_AWNING_ACTIVE_MONTHS = "awning_active_months"
CONF_UV_SENSOR = "uv_sensor"
CONF_WIND_SPEED_SENSOR = "wind_speed_sensor"
CONF_RAIN_SENSOR = "rain_sensor"
CONF_AWNING_UV_CLOSE = "awning_uv_close"
CONF_AWNING_UV_OPEN = "awning_uv_open"
CONF_AWNING_MAX_WIND = "awning_max_wind"
CONF_AWNING_MIN_INDOOR_TEMP = "awning_min_indoor_temp"
CONF_AWNING_START_HOUR = "awning_start_hour"
CONF_AWNING_END_HOUR = "awning_end_hour"

AWNING_MODE_OFF = "off"
AWNING_MODE_ADVICE = "advice"
AWNING_MODE_AUTO = "auto"
AWNING_MODE_LABELS = {
    AWNING_MODE_OFF: "Uit",
    AWNING_MODE_ADVICE: "Alleen advies",
    AWNING_MODE_AUTO: "Automatisch",
}

# Forecast / comfort
CONF_FORECAST_SOLAR_TODAY_SENSOR = "forecast_solar_today_sensor"
CONF_FORECAST_SOLAR_TOMORROW_SENSOR = "forecast_solar_tomorrow_sensor"
CONF_SOLAR_PEAK_TOMORROW_SENSOR = "solar_peak_tomorrow_sensor"
CONF_SOLAR_NEXT_12H_SENSOR = "solar_next_12h_sensor"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_INDOOR_TEMP_SENSOR = "indoor_temp_sensor"
CONF_COMFORT_TEMP = "comfort_temp"
CONF_NEGATIVE_PRICE_STRATEGY = "negative_price_strategy"

STRATEGY_PRICE = "price"
STRATEGY_PV = "pv"
STRATEGY_AUTO = "auto"

ACTION_NONE = "none"
ACTION_WAIT = "wait"
ACTION_DHW_ONETIME = "dhw_onetime"
ACTION_FLOOR_HEAT_BUFFER = "floor_heat_buffer"
ACTION_FLOOR_COOL_BUFFER = "floor_cool_buffer"

NEGATIVE_PRICE_OFF = "off"
NEGATIVE_PRICE_DHW_ONLY = "dhw_only"
NEGATIVE_PRICE_DHW_FLOOR_CAREFUL = "dhw_floor_careful"

DEFAULTS = {
    CONF_STRATEGY: STRATEGY_AUTO,
    CONF_SWITCH_DATE: "01-01-2027",
    CONF_AUTO_EXECUTE: False,
    CONF_TARIFF_SENSOR: "sensor.zonneplan_current_electricity_tariff",
    CONF_DHW_TEMP_SENSOR: "sensor.boiler_hptw1",
    CONF_WATER_HEATER: "water_heater.warmtepomp_waterheater",
    CONF_WATER_HEATER_COMFORT_MODE: "Comfort+",
    CONF_DHW_ONETIME_SWITCH: "switch.boiler_dhw_onetime",
    CONF_DHW_MAX_TEMP: "number.boiler_dhw_maxtemp",
    CONF_NET_SURPLUS_SENSOR: "sensor.netto_energie_overschot",
    CONF_NET_PRODUCTION_SENSOR: "sensor.electricity_meter_energieproductie",
    CONF_NET_CONSUMPTION_L1_SENSOR: "sensor.electricity_meter_energieverbruik_fase_l1",
    CONF_NET_CONSUMPTION_L2_SENSOR: "sensor.electricity_meter_energieverbruik_fase_l2",
    CONF_NET_CONSUMPTION_L3_SENSOR: "sensor.electricity_meter_energieverbruik_fase_l3",
    CONF_TOTAL_ENERGY_SENSOR: "sensor.boiler_total_energy",
    CONF_METER_TOTAL_SENSOR: "sensor.boiler_meter_total",
    CONF_COMPRESSOR_RUNTIME_HOURS_SENSOR: "sensor.boiler_compressor_runtime_hours",
    CONF_COMPRESSOR_STARTS_SENSOR: "sensor.boiler_compressor_starts",
    CONF_HP_POWER_SENSOR: "sensor.boiler_hpcurrpower",
    CONF_DHW_ACTIVE_SENSOR: "binary_sensor.boiler_tapwateractive",
    CONF_HEATING_ACTIVE_SENSOR: "binary_sensor.boiler_heatingactive",
    CONF_COOLING_ACTIVE_SENSOR: "binary_sensor.thermostat_hc1_coolingon",
    CONF_HP_OPERATING_STATE_SENSOR: "sensor.thermostat_hc1_hpoperatingstate",
    CONF_STANDBY_POWER_W: 50.0,
    CONF_ACTIVE_POWER_W: 200.0,
    CONF_FORECAST_SOLAR_TODAY_SENSOR: "",
    CONF_FORECAST_SOLAR_TOMORROW_SENSOR: "sensor.energy_production_tomorrow",
    CONF_SOLAR_PEAK_TOMORROW_SENSOR: "sensor.power_highest_peak_time_tomorrow",
    CONF_SOLAR_NEXT_12H_SENSOR: "sensor.power_production_next_12hours",
    CONF_WEATHER_ENTITY: "weather.buienradar",
    CONF_INDOOR_TEMP_SENSOR: "sensor.thermostat_hc1_currtemp",
    CONF_COMFORT_TEMP: 22.0,
    CONF_NEGATIVE_PRICE_STRATEGY: NEGATIVE_PRICE_DHW_FLOOR_CAREFUL,
    CONF_PV_LIMIT_CONTROL_MODE_SELECT: "select.buiten_zonnepanelen_limit_control_mode",
    CONF_AWNING_MODE: AWNING_MODE_ADVICE,
    CONF_AWNING_COVER: "cover.shellyswitch25_3494546b7c09",
    CONF_AWNING_PV_POWER_SENSOR: "sensor.electricity_meter_energieproductie",
    CONF_AWNING_PV_CLOSE_W: 3000.0,
    CONF_AWNING_PV_TIMEOUT_MIN: 15,
    CONF_AWNING_ACTIVE_MONTHS: "6,7,8,9",
    CONF_UV_SENSOR: "",
    CONF_WIND_SPEED_SENSOR: "",
    CONF_RAIN_SENSOR: "",
    CONF_AWNING_UV_CLOSE: 4.0,
    CONF_AWNING_UV_OPEN: 2.0,
    CONF_AWNING_MAX_WIND: 25.0,
    CONF_AWNING_MIN_INDOOR_TEMP: 22.0,
    CONF_AWNING_START_HOUR: 10,
    CONF_AWNING_END_HOUR: 19,
    CONF_LOW_PRICE_THRESHOLD: 0.25,
    CONF_PV_SURPLUS_THRESHOLD: 2500.0,
    CONF_DHW_MIN_TEMP: 54.0,
    CONF_DHW_TARGET_TEMP: 60.0,
    CONF_COOLDOWN_HOURS: 4.0,
    CONF_MAX_ONETIME_PER_DAY: 1,
    CONF_EXECUTE_SET_MAX_TEMP: True,
    CONF_EXECUTE_WATER_HEATER_MODE: False,
    CONF_NOTIFY_SERVICE: "notify.mobile_app_iphonie",
    CONF_NOTIFY_BOILER: "notify.mobile_app_iphonie",
    CONF_NOTIFY_AUTO: "notify.mobile_app_iphonie",
    CONF_NOTIFY_DISHWASHER: "notify.mobile_app_iphonie",
    CONF_NOTIFY_PRICE: "notify.mobile_app_iphonie",
    CONF_DISHWASHER_ENABLE: True,
    CONF_DISHWASHER_AUTO: True,
    CONF_DISHWASHER_DOOR_SENSOR: "binary_sensor.siemens_012080386530019255_bsh_common_status_doorstate",
    CONF_DISHWASHER_REMOTE_START_SENSOR: "binary_sensor.siemens_012080386530019255_bsh_common_status_remotecontrolstartallowed",
    CONF_DISHWASHER_PROGRAM_SELECT: "select.siemens_012080386530019255_programs",
    CONF_DISHWASHER_START_DELAY_SELECT: "select.siemens_012080386530019255_bsh_common_option_startinrelative",
    CONF_DISHWASHER_START_BUTTON: "button.siemens_012080386530019255_start_pause",
    CONF_DISHWASHER_ECO_OPTION: "Dishcare.Dishwasher.Program.Eco50",
    CONF_DISHWASHER_KWH: 0.75,
    CONF_DISHWASHER_NOTIFY_TIME: "18:30",
    CONF_HIGH_PRICE_THRESHOLD: 0.40,
    CONF_DHW_DISINFECT_DAY_SELECT: "select.thermostat_dhw_disinfectday",
    CONF_DHW_DISINFECT_SWITCH: "switch.thermostat_dhw_disinfecting",
    CONF_SHOWER_DAYS: "Wo,Zo",
    CONF_DHW_LOAD_ONCE_PER_DAY: True,
    CONF_DHW_PRICE_OPT_UNTIL: "31-12-2026",
}

STRATEGIES = {
    STRATEGY_PRICE: "Prijsoptimalisatie",
    STRATEGY_PV: "PV-optimalisatie",
    STRATEGY_AUTO: "Automatisch op datum",
}

NEGATIVE_PRICE_STRATEGIES = {
    NEGATIVE_PRICE_OFF: "Uit",
    NEGATIVE_PRICE_DHW_ONLY: "Alleen tapwater",
    NEGATIVE_PRICE_DHW_FLOOR_CAREFUL: "Tapwater + vloer voorzichtig",
}


# Runtime / reporting
SERVICE_EXECUTE_ADVICE = "execute_advice"
SERVICE_SEND_DAILY_REPORT = "send_daily_report"
SERVICE_REFRESH = "refresh"
SERVICE_SET_EXECUTION_MODE = "set_execution_mode"
SERVICE_SET_AWNING_MODE = "set_awning_mode"
SERVICE_START_DISINFECTION = "start_disinfection"

EXECUTION_MODE_ADVICE = "advice"
EXECUTION_MODE_AUTO = "auto"
EXECUTION_MODE_LABELS = {
    EXECUTION_MODE_ADVICE: "Alleen advies",
    EXECUTION_MODE_AUTO: "Automatisch uitvoeren",
}
ATTR_TARGET = "target"
ATTR_MESSAGE = "message"
ATTR_TITLE = "title"

LEGACY_WRONG_SWITCH_DATES = {"13-08-2027", "2027-08-13", "01-01-2026", "2026-01-01"}
