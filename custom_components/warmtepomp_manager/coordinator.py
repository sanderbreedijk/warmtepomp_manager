from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import *
from .config_flow import merged_config, normalize_switch_date

_LOGGER = logging.getLogger(__name__)


def _float_state(hass: HomeAssistant, entity_id: str | None, default: float | None = None) -> float | None:
    if not entity_id:
        return default
    st = hass.states.get(entity_id)
    if st is None or st.state in ("unknown", "unavailable", ""):
        return default
    try:
        return float(str(st.state).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _state(hass: HomeAssistant, entity_id: str | None, default: str = "") -> str:
    if not entity_id:
        return default
    st = hass.states.get(entity_id)
    if st is None or st.state in ("unknown", "unavailable", ""):
        return default
    return str(st.state)


def _is_on(hass: HomeAssistant, entity_id: str | None) -> bool:
    return _state(hass, entity_id).lower() in ("on", "aan", "true", "1", "active", "actief")


def _entity_available(hass: HomeAssistant, entity_id: str | None) -> bool:
    if not entity_id:
        return True
    st = hass.states.get(entity_id)
    return st is not None and st.state not in ("unknown", "unavailable", "")





def _float_state_in_watts(hass: HomeAssistant, entity_id: str | None, default: float | None = None) -> float | None:
    """Read a power sensor and normalize kW to W when the unit says kW."""
    if not entity_id:
        return default
    st = hass.states.get(entity_id)
    if st is None or st.state in ("unknown", "unavailable", ""):
        return default
    try:
        value = float(str(st.state).replace(",", "."))
    except (TypeError, ValueError):
        return default
    unit = str(st.attributes.get("unit_of_measurement", "")).lower().strip()
    if unit == "kw" or unit.endswith(" kw"):
        return value * 1000.0
    return value


def _parse_months(value: Any) -> set[int]:
    """Parse comma/space separated month numbers. Defaults to June-September."""
    months: set[int] = set()
    for part in re.split(r"[^0-9]+", str(value or "")):
        if not part:
            continue
        try:
            month = int(part)
        except ValueError:
            continue
        if 1 <= month <= 12:
            months.add(month)
    return months or {6, 7, 8, 9}

def _is_rainy(hass: HomeAssistant, weather_entity: str | None, rain_sensor: str | None) -> bool:
    """Best-effort rain detection from an optional rain sensor and weather state."""
    if rain_sensor:
        raw = _state(hass, rain_sensor).lower()
        if raw in ("on", "aan", "true", "1", "rain", "regen", "raining", "wet"):
            return True
        val = _float_state(hass, rain_sensor)
        if val is not None and val > 0:
            return True
    weather = _state(hass, weather_entity).lower()
    return weather in ("rainy", "pouring", "lightning-rainy", "snowy-rainy", "regen", "buien")


def _cover_is_down(hass: HomeAssistant, cover_entity: str | None) -> bool:
    """Return True when the awning is already down/closed.

    Home Assistant covers use state 'closed' for down. Some covers also expose
    current_position where 0 is fully closed/down and 100 is open/up.
    """
    if not cover_entity:
        return False
    st = hass.states.get(cover_entity)
    if st is None:
        return False
    if str(st.state).lower() == "closed":
        return True
    pos = st.attributes.get("current_position")
    try:
        return float(pos) <= 5
    except (TypeError, ValueError):
        return False


def _cover_is_up(hass: HomeAssistant, cover_entity: str | None) -> bool:
    """Return True when the awning is already up/open."""
    if not cover_entity:
        return False
    st = hass.states.get(cover_entity)
    if st is None:
        return False
    if str(st.state).lower() == "open":
        return True
    pos = st.attributes.get("current_position")
    try:
        return float(pos) >= 95
    except (TypeError, ValueError):
        return False

def _availability_report(hass: HomeAssistant, cfg: dict[str, Any]) -> tuple[int, list[str]]:
    """Return availability without flagging optional fallback sensors as errors.

    In eerdere versies werd sensor.netto_energie_overschot als ontbrekend gemeld,
    ook wanneer het netto overschot correct uit productie + faseverbruik werd
    berekend. Dat maakte Systeemgezondheid onnodig "Controle nodig".
    """
    important = [
        CONF_TARIFF_SENSOR,
        CONF_DHW_TEMP_SENSOR,
        CONF_DHW_ONETIME_SWITCH,
        CONF_FORECAST_SOLAR_TOMORROW_SENSOR,
        CONF_INDOOR_TEMP_SENSOR,
    ]
    missing: list[str] = []
    configured = 0
    available = 0
    for key in important:
        entity_id = str(cfg.get(key) or "").strip()
        if not entity_id:
            continue
        configured += 1
        if _entity_available(hass, entity_id):
            available += 1
        else:
            missing.append(entity_id)

    # Net-overschot mag direct óf berekend beschikbaar zijn.
    direct_net = str(cfg.get(CONF_NET_SURPLUS_SENSOR) or "").strip()
    fallback_entities = [
        str(cfg.get(CONF_NET_PRODUCTION_SENSOR) or "").strip(),
        str(cfg.get(CONF_NET_CONSUMPTION_L1_SENSOR) or "").strip(),
        str(cfg.get(CONF_NET_CONSUMPTION_L2_SENSOR) or "").strip(),
        str(cfg.get(CONF_NET_CONSUMPTION_L3_SENSOR) or "").strip(),
    ]
    has_direct_net = bool(direct_net and _entity_available(hass, direct_net))
    has_fallback_net = bool(fallback_entities[0] and _entity_available(hass, fallback_entities[0]))
    configured += 1
    if has_direct_net or has_fallback_net:
        available += 1
    elif direct_net:
        missing.append(direct_net)
    else:
        missing.append("netto overschot: geen productie/netto sensor ingesteld")

    if configured == 0:
        return 0, missing
    return round((available / configured) * 100), missing


def _zonneplan_tariff_group(hass: HomeAssistant, tariff_entity_id: str | None, tariff: float | None, low_price_threshold: float) -> str:
    st = hass.states.get(tariff_entity_id) if tariff_entity_id else None
    if st is not None:
        for key in (
            "tariff_group", "tariffGroup", "current_tariff_group", "currentTariffGroup",
            "electricity_tariff_group", "tariff_group_name", "price_level", "current_price_level", "group",
        ):
            value = st.attributes.get(key)
            if value not in (None, "", "unknown", "unavailable"):
                return str(value).strip().lower()
    if tariff is None:
        return "onbekend"
    if tariff < 0:
        return "negatief"
    if tariff <= low_price_threshold * 0.75:
        return "zeer_laag"
    if tariff <= low_price_threshold:
        return "laag"
    if tariff <= low_price_threshold * 1.35:
        return "normaal"
    if tariff <= low_price_threshold * 1.75:
        return "hoog"
    return "zeer_hoog"



def _zonneplan_forecast_prices(hass: HomeAssistant, tariff_entity_id: str | None) -> list[tuple[datetime | None, float]]:
    """Return forecast prices as (datetime, eur_per_kwh). Supports Zonneplan attributes and hour sensors."""
    result: list[tuple[datetime | None, float]] = []
    st = hass.states.get(tariff_entity_id) if tariff_entity_id else None
    if st is not None:
        forecast = st.attributes.get("forecast") or st.attributes.get("forecasts") or []
        if isinstance(forecast, list):
            for item in forecast:
                if not isinstance(item, dict):
                    continue
                raw_price = item.get("electricity_price", item.get("price", item.get("tariff")))
                if raw_price in (None, "", "unknown", "unavailable"):
                    continue
                try:
                    price = float(str(raw_price).replace(",", "."))
                except (TypeError, ValueError):
                    continue
                # Zonneplan forecast sometimes exposes integer micro-cents; convert when implausibly large.
                if abs(price) > 10:
                    price = price / 10000000
                dt_value = item.get("datetime") or item.get("date_time") or item.get("from") or item.get("time")
                parsed_dt: datetime | None = None
                if dt_value:
                    try:
                        parsed_dt = dt_util.parse_datetime(str(dt_value))
                    except Exception:
                        parsed_dt = None
                result.append((parsed_dt, round(price, 4)))

    # Fallback: common Zonneplan hourly forecast entities.
    if not result:
        for i in range(1, 25):
            eid = f"sensor.zonneplan_forecast_tariff_hour_{i}"
            price = _float_state(hass, eid)
            if price is not None:
                result.append((None, round(price, 4)))
    return result



def _average_price_for_date(hass: HomeAssistant, tariff_entity_id: str | None, target_date: date) -> float | None:
    """Return average electricity price for a local calendar day from tariff forecast.

    This is deliberately separate from the cheapest-block price. The dashboard row
    "Gemiddelde prijs" must show the whole-day average, not the average of the
    cheapest 2/3/4-hour block. Falls back to the current tariff for today when no
    forecast is available.
    """
    prices = _zonneplan_forecast_prices(hass, tariff_entity_id)
    day_prices: list[float] = []
    for dt_value, price in prices:
        if dt_value is None:
            continue
        local_dt = dt_util.as_local(dt_value) if dt_value.tzinfo is not None else dt_value
        if local_dt.date() == target_date:
            day_prices.append(float(price))
    if day_prices:
        return round(sum(day_prices) / len(day_prices), 3)

    if target_date == dt_util.now().date():
        current = _float_state(hass, tariff_entity_id)
        return round(current, 3) if current is not None else None
    return None

def _average_price_today_tomorrow(hass: HomeAssistant, tariff_entity_id: str | None) -> tuple[float | None, float | None]:
    today = dt_util.now().date()
    tomorrow = today + timedelta(days=1)
    return (
        _average_price_for_date(hass, tariff_entity_id, today),
        _average_price_for_date(hass, tariff_entity_id, tomorrow),
    )

def _negative_price_forecast(hass: HomeAssistant, tariff_entity_id: str | None) -> tuple[str, str, float | None]:
    """Return (Ja/Nee/Onbekend, negative-hour-label, lowest-price-tomorrow).

    Zonneplan timestamps are UTC; use local time before deciding whether an
    hour belongs to tomorrow. Prices are already normalized to EUR/kWh by
    _zonneplan_forecast_prices().
    """
    prices = _zonneplan_forecast_prices(hass, tariff_entity_id)
    if not prices:
        return "Onbekend", "—", None

    tomorrow = dt_util.now().date() + timedelta(days=1)
    tomorrow_prices: list[tuple[datetime | None, float]] = []
    for dt_value, price in prices:
        if dt_value is None:
            continue
        local_dt = dt_util.as_local(dt_value) if dt_value.tzinfo is not None else dt_value
        if local_dt.date() == tomorrow:
            tomorrow_prices.append((local_dt, price))

    if not tomorrow_prices:
        return "Onbekend", "—", None

    lowest = min((p for _dt, p in tomorrow_prices), default=None)
    neg_items = [(dt_value, price) for dt_value, price in tomorrow_prices if price < 0]
    if not neg_items:
        return "Nee", "geen", round(lowest, 3) if lowest is not None else None

    labels = [dt_value.strftime("%H:%M") for dt_value, _price in neg_items if dt_value is not None]
    return "Ja", ", ".join(labels) if labels else "negatief", round(lowest, 3) if lowest is not None else None



def _pv_mode_display(raw_mode: str) -> str:
    """Human-friendly display for inverter limit control mode.

    Disabled means normal PV behaviour. Production Control is used as the safe
    limitation mode during negative prices and should be shown as disabled/limited.
    """
    mode = (raw_mode or "").strip()
    low = mode.lower()
    if low == "disabled":
        return "Normaal"
    if low == "production control":
        return "Uitgeschakeld"
    if not mode or low in ("unknown", "unavailable"):
        return "Onbekend"
    return mode


def _cheapest_3h_block_tomorrow(hass: HomeAssistant, tariff_entity_id: str | None) -> tuple[str, float | None]:
    """Return cheapest consecutive 3-hour block tomorrow as ('HH:MM-HH:MM', avg_price)."""
    prices = _zonneplan_forecast_prices(hass, tariff_entity_id)
    if not prices:
        return "—", None

    tomorrow = dt_util.now().date() + timedelta(days=1)
    items: list[tuple[datetime, float]] = []
    for dt_value, price in prices:
        if dt_value is None:
            continue
        local_dt = dt_util.as_local(dt_value) if dt_value.tzinfo is not None else dt_value
        if local_dt.date() == tomorrow:
            items.append((local_dt.replace(minute=0, second=0, microsecond=0), price))

    if len(items) < 3:
        return "—", None

    items.sort(key=lambda x: x[0])
    best_start: datetime | None = None
    best_avg: float | None = None

    for i in range(len(items) - 2):
        block = items[i:i+3]
        # Require truly consecutive hours.
        if block[1][0] - block[0][0] != timedelta(hours=1):
            continue
        if block[2][0] - block[1][0] != timedelta(hours=1):
            continue
        avg = sum(p for _dt, p in block) / 3
        if best_avg is None or avg < best_avg:
            best_avg = avg
            best_start = block[0][0]

    if best_start is None or best_avg is None:
        return "—", None

    end = best_start + timedelta(hours=3)
    return f"{best_start.strftime('%H:%M')}-{end.strftime('%H:%M')}", round(best_avg, 3)



def _fmt_price(price: float | None) -> str:
    if price is None:
        return "—"
    return f"€{price:.3f}/kWh"


def _fmt_kw(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f} kW"




def _parse_block_hours(block: str) -> tuple[int | None, int | None]:
    try:
        start, end = str(block).split('-', 1)
        return int(start.split(':')[0]), int(end.split(':')[0])
    except Exception:
        return None, None


def _now_in_hour_block(block: str) -> bool:
    start, end = _parse_block_hours(block)
    if start is None or end is None:
        return False
    hour = dt_util.now().hour
    if end > start:
        return start <= hour < end
    return hour >= start or hour < end


def _near_time_label(time_label: str, margin_hours: int = 1) -> bool:
    if not time_label or time_label == '—':
        return False
    try:
        target = int(str(time_label).split(':')[0])
    except Exception:
        return False
    hour = dt_util.now().hour
    return abs(hour - target) <= margin_hours


def _select_legionella_day(shower_days: str, negative_tomorrow: str, solar_tomorrow: float | None) -> str:
    # Default follows natural hot-water demand. Prefer Wednesday, then Sunday.
    days = [d.strip() for d in str(shower_days or 'Wo,Zo').split(',') if d.strip()]
    if not days:
        days = ['Wo', 'Zo']
    # Only shift to Sunday when solar is very strong or negative prices are expected; otherwise keep Wednesday.
    if str(negative_tomorrow).lower() == 'ja' and 'Zo' in days:
        return 'Zo'
    if solar_tomorrow is not None and solar_tomorrow >= 35 and 'Zo' in days:
        return 'Zo'
    return days[0]

def _timestamp_time(hass: HomeAssistant, entity_id: str | None) -> str:
    text = _state(hass, entity_id, "")
    if not text:
        return "—"
    try:
        dt_value = dt_util.parse_datetime(text)
        if dt_value is None:
            return "—"
        local_dt = dt_util.as_local(dt_value) if dt_value.tzinfo is not None else dt_value
        return local_dt.strftime("%H:%M")
    except Exception:
        return "—"


def _professional_wait_reason(
    *,
    base_reason: str,
    cheapest_block: str,
    cheapest_price: float | None,
    lowest_price: float | None,
    current_price: float | None,
    solar_tomorrow: float | None,
    solar_peak_tomorrow: str | None,
    dhw_temp: float | None,
) -> str:
    """Return a concise *current* reason for the advice card.

    The advice card describes the situation now. Tomorrow data belongs only in
    the morning/planning card. Also avoid repeating values that the dashboard
    already shows as separate rows, such as tapwater temperature and current
    price.
    """
    reason = (base_reason or "").strip().rstrip(".")

    # Remove duplicate leading measurements from older reason strings.
    reason = re.sub(r"^Tapwater\s+[0-9]+(?:[\.,][0-9]+)?\s*°C,?\s*", "", reason, flags=re.I)
    reason = re.sub(r"^Prijs\s+[0-9]+(?:[\.,][0-9]+)?\s*€/kWh,?\s*", "", reason, flags=re.I)

    replacements = {
        "prijs niet laag genoeg": "Prijs nu niet gunstig genoeg",
        "dagelijks laadmoment nog niet bereikt": "Dagelijks laadmoment nog niet bereikt",
        "zonnemoment nog niet bereikt": "Zonnemoment nog niet bereikt",
    }
    lower = reason.lower()
    for needle, value in replacements.items():
        if needle in lower:
            return value

    return reason or "Wachten op het geplande laadmoment"


def _tomorrow_price_items(hass: HomeAssistant, tariff_entity_id: str | None) -> list[tuple[datetime, float]]:
    """Return local tomorrow prices as sorted hourly items."""
    tomorrow = dt_util.now().date() + timedelta(days=1)
    items: list[tuple[datetime, float]] = []
    for dt_value, price in _zonneplan_forecast_prices(hass, tariff_entity_id):
        if dt_value is None:
            continue
        local_dt = dt_util.as_local(dt_value) if dt_value.tzinfo is not None else dt_value
        if local_dt.date() == tomorrow:
            items.append((local_dt.replace(minute=0, second=0, microsecond=0), price))
    items.sort(key=lambda x: x[0])
    return items


def _best_consecutive_block(items: list[tuple[datetime, float]], hours: int) -> tuple[str, float | None]:
    """Find cheapest consecutive block from already sorted hourly items."""
    if len(items) < hours:
        return "—", None
    best_start: datetime | None = None
    best_avg: float | None = None
    for i in range(len(items) - hours + 1):
        block = items[i:i + hours]
        if any(block[j][0] - block[j - 1][0] != timedelta(hours=1) for j in range(1, len(block))):
            continue
        avg = sum(p for _dt, p in block) / hours
        if best_avg is None or avg < best_avg:
            best_avg = avg
            best_start = block[0][0]
    if best_start is None or best_avg is None:
        return "—", None
    return f"{best_start.strftime('%H:%M')}-{(best_start + timedelta(hours=hours)).strftime('%H:%M')}", round(best_avg, 3)


def _best_blocks_tomorrow(hass: HomeAssistant, tariff_entity_id: str | None) -> dict[str, Any]:
    items = _tomorrow_price_items(hass, tariff_entity_id)
    block2, price2 = _best_consecutive_block(items, 2)
    block3, price3 = _best_consecutive_block(items, 3)
    block4, price4 = _best_consecutive_block(items, 4)
    return {
        "items": items,
        "block_2h": block2,
        "price_2h": price2,
        "block_3h": block3,
        "price_3h": price3,
        "block_4h": block4,
        "price_4h": price4,
    }


def _build_ai_day_plan(
    *,
    strategy_mode: str,
    current_price: float | None,
    dhw_temp: float | None,
    dhw_min: float,
    cheapest_block: str,
    cheapest_price: float | None,
    cheapest_2h_block: str,
    cheapest_4h_block: str,
    negative_hours: str,
    negative_tomorrow: str,
    solar_tomorrow: float | None,
    solar_peak_tomorrow: str,
    solar_next_12h: float | None,
    indoor_temp: float | None,
    comfort_temp: float,
) -> dict[str, Any]:
    """Deterministic day plan without AI/score wording."""
    has_neg = str(negative_tomorrow).lower() == "ja"
    price_known = cheapest_2h_block not in ("", "—") and cheapest_price is not None
    solar_known = solar_peak_tomorrow not in ("", "—", None)

    if has_neg:
        status = "Negatieve prijs overrulet schema"
        strategy = "Negatieve prijs"
        action = f"Boiler laden tijdens {negative_hours}" if negative_hours else "Boiler extra laden"
        plan_lines = [
            "Negatieve tarieven beschikbaar",
            f"Uren: {negative_hours or 'onbekend'}",
            "Boiler naar 60 °C; desinfectie combineren indien nodig",
        ]
    elif strategy_mode == STRATEGY_PV:
        status = "Zonplanning" if solar_known else "Wachten op zondata"
        strategy = "Zon vanaf 01-01-2027"
        action = f"Boiler laden rond zonpiek {solar_peak_tomorrow}" if solar_known else "Geen zonneblok bekend"
        plan_lines = [
            "1x per dag volledig vat",
            f"Zonpiek: {solar_peak_tomorrow or '—'}",
            f"Zonneverwachting: {solar_tomorrow:.1f} kWh" if solar_tomorrow is not None else "Zonneverwachting: —",
            "Prijs wordt genegeerd vanaf 01-01-2027",
        ]
    else:
        status = "Prijsplanning" if price_known else "Wachten op prijsdata"
        strategy = "Prijs tot 31-12-2026"
        action = f"Boiler laden in goedkoopste 2-uursblok {cheapest_2h_block}" if price_known else "Wachten op Zonneplan-prijzen"
        plan_lines = [
            "1x per dag volledig vat",
            f"Goedkoopste 2-uursblok: {cheapest_2h_block or '—'}",
            f"Blokprijs: {_fmt_price(cheapest_price)}",
            "Desinfectie combineren met deze lading indien nodig",
        ]

    expected_savings = None
    if current_price is not None and cheapest_price is not None and current_price > cheapest_price:
        expected_savings = round((current_price - cheapest_price) * 4, 2)

    return {
        "ai_strategy": strategy,
        "planning_status": status,
        "planned_action": action,
        "ai_day_plan": " · ".join(plan_lines),
        "ai_day_plan_lines": plan_lines,
        "energy_opportunity_score": None,
        "expected_savings": expected_savings,
        "cheapest_2h_block_tomorrow": cheapest_2h_block,
        "cheapest_4h_block_tomorrow": "—",
    }

def _calculate_net_surplus(hass: HomeAssistant, cfg: dict[str, Any]) -> tuple[float | None, str]:
    direct = _float_state(hass, cfg.get(CONF_NET_SURPLUS_SENSOR))
    if direct is not None:
        return direct, str(cfg.get(CONF_NET_SURPLUS_SENSOR))
    production = _float_state(hass, cfg.get(CONF_NET_PRODUCTION_SENSOR))
    l1 = _float_state(hass, cfg.get(CONF_NET_CONSUMPTION_L1_SENSOR), 0.0)
    l2 = _float_state(hass, cfg.get(CONF_NET_CONSUMPTION_L2_SENSOR), 0.0)
    l3 = _float_state(hass, cfg.get(CONF_NET_CONSUMPTION_L3_SENSOR), 0.0)
    if production is None:
        return None, "geen productie- of netto-overschot sensor beschikbaar"
    return round(production - ((l1 or 0.0) + (l2 or 0.0) + (l3 or 0.0)), 1), "berekend uit productiesensor en faseverbruik"


def _calculate_scop(hass: HomeAssistant, cfg: dict[str, Any]) -> float | None:
    produced = _float_state(hass, cfg.get(CONF_TOTAL_ENERGY_SENSOR))
    consumed = _float_state(hass, cfg.get(CONF_METER_TOTAL_SENSOR))
    if produced is None or consumed is None or consumed <= 0:
        return None
    return round(produced / consumed, 2)


def _calculate_cycle_hours(hass: HomeAssistant, cfg: dict[str, Any]) -> float | None:
    runtime = _float_state(hass, cfg.get(CONF_COMPRESSOR_RUNTIME_HOURS_SENSOR))
    starts = _float_state(hass, cfg.get(CONF_COMPRESSOR_STARTS_SENSOR))
    if runtime is None or starts is None or starts <= 0:
        return None
    return round(runtime / starts, 2)


def _calculate_starts_per_day(hass: HomeAssistant, cfg: dict[str, Any]) -> float | None:
    return None


def _calculate_live_cop() -> float | None:
    return None


def _parse_date(value: Any, fallback: date = date(2027, 1, 1)) -> date:
    text = normalize_switch_date(value)
    try:
        return datetime.strptime(text, "%d-%m-%Y").date()
    except ValueError:
        return fallback


def _as_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _as_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _wp_status(hass: HomeAssistant, cfg: dict[str, Any]) -> tuple[str, str, float | None]:
    power = _float_state(hass, cfg.get(CONF_HP_POWER_SENSOR))
    standby = _as_float(cfg.get(CONF_STANDBY_POWER_W), 50.0)
    active = _as_float(cfg.get(CONF_ACTIVE_POWER_W), 200.0)
    op_state = _state(hass, cfg.get(CONF_HP_OPERATING_STATE_SENSOR), "").lower()

    if _is_on(hass, cfg.get(CONF_DHW_ACTIVE_SENSOR)):
        return "Tapwater laden", "orange", power
    if _is_on(hass, cfg.get(CONF_COOLING_ACTIVE_SENSOR)) or "koel" in op_state or "cool" in op_state:
        return "Koelen", "cyan", power
    if _is_on(hass, cfg.get(CONF_HEATING_ACTIVE_SENSOR)) or "verwarm" in op_state or "heat" in op_state:
        return "Verwarmen", "green", power
    if power is not None:
        if power > active:
            return "Warmtepomp actief", "green", power
        if power > standby:
            return "Opstarten", "blue", power
        return "Stand-by", "grey", power
    if op_state and op_state not in ("uit", "off"):
        return op_state.capitalize(), "blue", power
    return "Rust", "grey", power


def _dhw_max_display(hass: HomeAssistant, cfg: dict[str, Any]) -> str:
    value = _float_state(hass, cfg.get(CONF_DHW_MAX_TEMP))
    if value is None or value <= 0:
        return "schema"
    return f"{value:.0f} °C"


def _future_price_items(hass: HomeAssistant, tariff_entity_id: str | None, hours: int = 30) -> list[tuple[datetime, float]]:
    """Return future hourly prices from now, local time."""
    now = dt_util.now().replace(minute=0, second=0, microsecond=0)
    end = now + timedelta(hours=hours)
    items: list[tuple[datetime, float]] = []
    for dt_value, price in _zonneplan_forecast_prices(hass, tariff_entity_id):
        if dt_value is None:
            continue
        local_dt = dt_util.as_local(dt_value).replace(minute=0, second=0, microsecond=0)
        if now <= local_dt <= end:
            items.append((local_dt, float(price)))
    return sorted(set(items), key=lambda x: x[0])


def _weighted_dishwasher_cost(prices: list[float], kwh: float) -> float:
    """Eco dishwasher cost for a 3-hour window; second hour uses the least energy."""
    weights = (0.35, 0.20, 0.45)
    return round(sum(p * w * kwh for p, w in zip(prices, weights)), 2)


def _format_delay_for_select(start: datetime) -> str:
    """Return Home Connect start delay option like H:MM, rounded to nearest 30 minutes."""
    now = dt_util.now()
    minutes = max(0, int((start - now).total_seconds() // 60))
    minutes = int(round(minutes / 30) * 30)
    minutes = max(0, min(24 * 60, minutes))
    return f"{minutes // 60}:{minutes % 60:02d}"


def _best_dishwasher_plan(hass: HomeAssistant, cfg: dict[str, Any]) -> dict[str, Any]:
    """Find the best future 3-hour dishwasher window."""
    kwh = max(0.1, _as_float(cfg.get(CONF_DISHWASHER_KWH), 0.75))
    items = _future_price_items(hass, cfg.get(CONF_TARIFF_SENSOR), hours=30)
    if len(items) < 3:
        return {"status": "Geen prijsdata", "message": "🍽️ Eco: prijsdata ontbreekt", "best_start": None}
    best: tuple[float, datetime, list[float]] | None = None
    for i in range(len(items) - 2):
        t0, p0 = items[i]
        t1, p1 = items[i+1]
        t2, p2 = items[i+2]
        if t1 - t0 != timedelta(hours=1) or t2 - t1 != timedelta(hours=1):
            continue
        cost = _weighted_dishwasher_cost([p0, p1, p2], kwh)
        if best is None or cost < best[0]:
            best = (cost, t0, [p0, p1, p2])
    if best is None:
        return {"status": "Geen aaneengesloten blok", "message": "🍽️ Eco: geen blok", "best_start": None}
    best_cost, best_start, best_prices = best
    current_prices = [p for _t, p in items[:3]]
    now_cost = _weighted_dishwasher_cost(current_prices, kwh) if len(current_prices) >= 3 else None
    savings = round(max(0.0, (now_cost or best_cost) - best_cost), 2) if now_cost is not None else None
    if now_cost is not None and savings is not None:
        msg = f"🍽️ Eco: nu €{now_cost:.2f}; {best_start.strftime('%H:%M')} €{best_cost:.2f}; bespaar €{savings:.2f}"
    else:
        msg = f"🍽️ Eco: start {best_start.strftime('%H:%M')} · €{best_cost:.2f}"
    return {
        "status": "Plan beschikbaar",
        "best_start": best_start,
        "best_block": f"{best_start.strftime('%H:%M')}-{(best_start + timedelta(hours=3)).strftime('%H:%M')}",
        "best_cost": best_cost,
        "now_cost": now_cost,
        "savings": savings,
        "delay_option": _format_delay_for_select(best_start),
        "message": msg,
        "prices": best_prices,
    }


def _high_price_blocks(hass: HomeAssistant, cfg: dict[str, Any]) -> dict[str, Any]:
    threshold = _as_float(cfg.get(CONF_HIGH_PRICE_THRESHOLD), 0.40)
    items = _future_price_items(hass, cfg.get(CONF_TARIFF_SENSOR), hours=30)
    high = [(dt, price) for dt, price in items if price >= threshold]
    if not high:
        return {"status": "Nee", "blocks": "—", "message": ""}
    blocks: list[str] = []
    start = prev = high[0][0]
    prices = [high[0][1]]
    for dt, price in high[1:]:
        if dt - prev == timedelta(hours=1):
            prev = dt
            prices.append(price)
        else:
            if len(prices) >= 1:
                blocks.append(f"{start.strftime('%H:%M')}-{(prev+timedelta(hours=1)).strftime('%H:%M')} €{min(prices):.2f}-€{max(prices):.2f}")
            start = prev = dt
            prices = [price]
    blocks.append(f"{start.strftime('%H:%M')}-{(prev+timedelta(hours=1)).strftime('%H:%M')} €{min(prices):.2f}-€{max(prices):.2f}")
    short = "; ".join(blocks[:3])
    return {"status": "Ja", "blocks": short, "message": f"⚠️ Dure stroom: {short}"}


class WarmtepompManagerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=1))
        self.entry = entry
        self.last_decision = "Nog geen beslissing"
        self.last_action_key = ACTION_NONE
        self.last_reason = ""
        self.last_executed: datetime | None = None
        self.executions_today = 0
        self.execution_date: date | None = None
        self._first_update_done = False
        self.last_report_date: date | None = None
        self._tracking_date: date | None = None
        self._today_snapshot: dict[str, Any] = {}
        self._yesterday_snapshot: dict[str, Any] | None = None
        self.last_awning_action: str | None = None
        self.last_awning_action_time: datetime | None = None
        self._auto_execute_override: bool | None = None
        self._awning_mode_override: str | None = None
        self._awning_pv_high_since: datetime | None = None
        self._awning_pv_low_since: datetime | None = None
        self._dishwasher_last_door_open: bool | None = None
        self._dishwasher_plan_key: str | None = None
        self._dishwasher_last_notify_key: str | None = None
        self._price_alert_sent_key: str | None = None

    @property
    def cfg(self) -> dict[str, Any]:
        cfg = merged_config(self.entry.data, self.entry.options)
        if self._auto_execute_override is not None:
            cfg[CONF_AUTO_EXECUTE] = self._auto_execute_override
        if self._awning_mode_override is not None:
            cfg[CONF_AWNING_MODE] = self._awning_mode_override
        return cfg

    def _reset_daily_counter_if_needed(self) -> None:
        today = dt_util.now().date()
        if self.execution_date != today:
            self.execution_date = today
            self.executions_today = 0

    def current_strategy(self) -> str:
        cfg = self.cfg
        strategy = str(cfg.get(CONF_STRATEGY) or STRATEGY_AUTO)
        if strategy in (STRATEGY_PRICE, STRATEGY_PV):
            return strategy
        return STRATEGY_PV if dt_util.now().date() >= _parse_date(cfg.get(CONF_SWITCH_DATE)) else STRATEGY_PRICE

    def _can_auto_execute(self) -> tuple[bool, str]:
        self._reset_daily_counter_if_needed()
        cfg = self.cfg
        max_daily = max(0, _as_int(cfg.get(CONF_MAX_ONETIME_PER_DAY), 1))
        if max_daily == 0:
            return False, "daglimiet staat op 0"
        if self.executions_today >= max_daily:
            return False, "daglimiet bereikt"
        cooldown = max(0.0, _as_float(cfg.get(CONF_COOLDOWN_HOURS), 4.0))
        if self.last_executed is not None and dt_util.now() - self.last_executed < timedelta(hours=cooldown):
            return False, "cooldown actief"
        return True, "toegestaan"

    async def async_set_auto_execute(self, enabled: bool) -> None:
        """Switch between advice-only and automatic execution mode."""
        self._auto_execute_override = bool(enabled)
        options = dict(self.entry.options or {})
        options[CONF_AUTO_EXECUTE] = bool(enabled)
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        data = dict(self.data or {})
        data[CONF_AUTO_EXECUTE] = bool(enabled)
        data["auto_execute"] = bool(enabled)
        data["execution_mode"] = EXECUTION_MODE_AUTO if enabled else EXECUTION_MODE_ADVICE
        data["auto_status"] = "aan · modus handmatig gewijzigd" if enabled else "uit"
        self.async_set_updated_data(data)
        await self.async_request_refresh()

    async def async_set_awning_mode(self, mode: str) -> None:
        """Set awning mode: off, advice or auto."""
        normalized = str(mode or "").lower().strip()
        label_map = {v.lower(): k for k, v in AWNING_MODE_LABELS.items()}
        normalized = label_map.get(normalized, normalized)
        if normalized not in AWNING_MODE_LABELS:
            normalized = AWNING_MODE_ADVICE
        self._awning_mode_override = normalized
        options = dict(self.entry.options or {})
        options[CONF_AWNING_MODE] = normalized
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        data = dict(self.data or {})
        data["awning_mode"] = normalized
        data["awning_mode_label"] = AWNING_MODE_LABELS.get(normalized, normalized)
        self.async_set_updated_data(data)
        await self.async_request_refresh()

    async def _send_notify(self, notify_service: str | None, title: str, message: str) -> str:
        """Send a compact notification to a configurable notify service."""
        target = str(notify_service or "").strip()
        if not target:
            return "Geen notify-service ingesteld"
        try:
            domain, service = target.split('.', 1) if '.' in target else ('notify', target)
            await self.hass.services.async_call(domain, service, {"title": title, "message": message}, blocking=True)
            return f"Verstuurd naar {target}"
        except Exception as err:
            _LOGGER.exception("Warmtepomp Manager notification failed")
            return f"Melding mislukt: {err}"

    async def _evaluate_price_alerts(self) -> dict[str, Any]:
        """Notify once when known upcoming prices exceed the configured high-price threshold."""
        cfg = self.cfg
        info = _high_price_blocks(self.hass, cfg)
        now = dt_util.now()
        key = f"{now.date().isoformat()}|{info.get('blocks')}"
        notify_status = "Niet verstuurd"
        if info.get("status") == "Ja" and key != self._price_alert_sent_key:
            notify_status = await self._send_notify(cfg.get(CONF_NOTIFY_PRICE) or cfg.get(CONF_NOTIFY_SERVICE), "Dure stroom", info.get("message") or "Dure stroom verwacht")
            self._price_alert_sent_key = key
        return {
            "high_price_status": info.get("status"),
            "high_price_blocks": info.get("blocks"),
            "high_price_threshold": _as_float(cfg.get(CONF_HIGH_PRICE_THRESHOLD), 0.40),
            "high_price_notify_status": notify_status,
        }

    async def _evaluate_dishwasher(self) -> dict[str, Any]:
        """Eco dishwasher planner.

        Door closed: set Eco, set calculated delay and press start when automatic mode is enabled.
        Door opened: reset internal plan so a new calculation is made next time it closes.
        """
        cfg = self.cfg
        enabled = bool(cfg.get(CONF_DISHWASHER_ENABLE, True))
        automatic = bool(cfg.get(CONF_DISHWASHER_AUTO, True))
        door_entity = str(cfg.get(CONF_DISHWASHER_DOOR_SENSOR) or "").strip()
        remote_entity = str(cfg.get(CONF_DISHWASHER_REMOTE_START_SENSOR) or "").strip()
        program_select = str(cfg.get(CONF_DISHWASHER_PROGRAM_SELECT) or "").strip()
        delay_select = str(cfg.get(CONF_DISHWASHER_START_DELAY_SELECT) or "").strip()
        start_button = str(cfg.get(CONF_DISHWASHER_START_BUTTON) or "").strip()
        eco_option = str(cfg.get(CONF_DISHWASHER_ECO_OPTION) or "Dishcare.Dishwasher.Program.Eco50").strip()
        now = dt_util.now()
        door_open = _is_on(self.hass, door_entity) if door_entity else False
        remote_ok = _is_on(self.hass, remote_entity) if remote_entity else True

        if not enabled:
            return {"dishwasher_status": "Uit", "dishwasher_message": "", "dishwasher_last_notify": None}

        if door_open:
            self._dishwasher_last_door_open = True
            self._dishwasher_plan_key = None
            return {
                "dishwasher_status": "Wachten op gesloten deur",
                "dishwasher_door": "open",
                "dishwasher_remote_start": remote_ok,
                "dishwasher_message": "Deur open; planning gereset",
                "dishwasher_last_notify": self._dishwasher_last_notify_key,
            }

        plan = _best_dishwasher_plan(self.hass, cfg)
        plan_key = f"{now.date().isoformat()}|{plan.get('best_block')}|{plan.get('best_cost')}|{automatic}"
        status = str(plan.get("status") or "Onbekend")
        action_status = "Geen actie"

        should_plan = bool(automatic and remote_ok and plan.get("best_start") is not None and plan_key != self._dishwasher_plan_key)
        if should_plan:
            try:
                # Always force Eco 50°C first.
                if program_select and eco_option:
                    await self.hass.services.async_call("select", "select_option", {"entity_id": program_select, "option": eco_option}, blocking=True)
                if delay_select and plan.get("delay_option"):
                    await self.hass.services.async_call("select", "select_option", {"entity_id": delay_select, "option": plan.get("delay_option")}, blocking=True)
                if start_button:
                    await self.hass.services.async_call("button", "press", {"entity_id": start_button}, blocking=True)
                self._dishwasher_plan_key = plan_key
                msg = f"🍽️ Eco ingepland: {plan.get('best_start').strftime('%H:%M')} · bespaar €{(plan.get('savings') or 0):.2f}"
                action_status = await self._send_notify(cfg.get(CONF_NOTIFY_DISHWASHER) or cfg.get(CONF_NOTIFY_SERVICE), "Vaatwasser", msg)
                self._dishwasher_last_notify_key = plan_key
            except Exception as err:
                _LOGGER.exception("Dishwasher planning failed")
                action_status = f"Instellen mislukt: {err}"
        elif not remote_ok:
            action_status = "Remote start niet toegestaan"
        elif not automatic:
            # Daily 18:30 advice-only message.
            hhmm = str(cfg.get(CONF_DISHWASHER_NOTIFY_TIME) or "18:30")
            try:
                hour, minute = [int(x) for x in hhmm.split(":", 1)]
            except Exception:
                hour, minute = 18, 30
            notify_key = f"{now.date().isoformat()}|18:30|{plan.get('best_block')}|{plan.get('best_cost')}"
            if now.hour == hour and now.minute == minute and notify_key != self._dishwasher_last_notify_key:
                action_status = await self._send_notify(cfg.get(CONF_NOTIFY_DISHWASHER) or cfg.get(CONF_NOTIFY_SERVICE), "Vaatwasser", plan.get("message") or "🍽️ Vaatwasseradvies niet beschikbaar")
                self._dishwasher_last_notify_key = notify_key
        else:
            action_status = "Al ingepland of geen prijsdata"

        return {
            "dishwasher_status": status,
            "dishwasher_door": "dicht",
            "dishwasher_remote_start": remote_ok,
            "dishwasher_auto": automatic,
            "dishwasher_program": "Eco 50°C",
            "dishwasher_best_block": plan.get("best_block"),
            "dishwasher_best_start": plan.get("best_start").isoformat() if plan.get("best_start") else None,
            "dishwasher_delay_option": plan.get("delay_option"),
            "dishwasher_cost_now": plan.get("now_cost"),
            "dishwasher_cost_best": plan.get("best_cost"),
            "dishwasher_savings": plan.get("savings"),
            "dishwasher_message": plan.get("message"),
            "dishwasher_action_status": action_status,
            "dishwasher_last_notify": self._dishwasher_last_notify_key,
        }

    async def _evaluate_awning(self, *, indoor_temp: float | None) -> dict[str, Any]:
        """Evaluate and optionally control awning.

        v1.4.5: PV power is the primary sun-strength source. The awning only
        goes down after sustained PV production above the configured threshold,
        and only in the configured summer months. This prevents duplicate and
        jittery commands.
        """
        cfg = self.cfg
        cover = str(cfg.get(CONF_AWNING_COVER) or "").strip()
        mode = str(cfg.get(CONF_AWNING_MODE) or AWNING_MODE_ADVICE).lower().strip()
        if mode not in AWNING_MODE_LABELS:
            mode = AWNING_MODE_ADVICE

        now = dt_util.now()
        pv_sensor = str(cfg.get(CONF_AWNING_PV_POWER_SENSOR) or "").strip()
        pv_power_w = _float_state_in_watts(self.hass, pv_sensor)
        pv_close_w = max(0.0, _as_float(cfg.get(CONF_AWNING_PV_CLOSE_W), 3000.0))
        timeout_min = max(1, _as_int(cfg.get(CONF_AWNING_PV_TIMEOUT_MIN), 15))
        active_months = _parse_months(cfg.get(CONF_AWNING_ACTIVE_MONTHS))
        in_active_month = now.month in active_months

        uv = _float_state(self.hass, cfg.get(CONF_UV_SENSOR))
        wind = _float_state(self.hass, cfg.get(CONF_WIND_SPEED_SENSOR))
        rainy = _is_rainy(self.hass, cfg.get(CONF_WEATHER_ENTITY), cfg.get(CONF_RAIN_SENSOR))
        start_hour = max(0, min(23, _as_int(cfg.get(CONF_AWNING_START_HOUR), 10)))
        end_hour = max(0, min(23, _as_int(cfg.get(CONF_AWNING_END_HOUR), 19)))
        in_time = start_hour <= now.hour < end_hour if start_hour < end_hour else (now.hour >= start_hour or now.hour < end_hour)
        max_wind = _as_float(cfg.get(CONF_AWNING_MAX_WIND), 25.0)
        min_indoor = _as_float(cfg.get(CONF_AWNING_MIN_INDOOR_TEMP), 22.0)
        wind_safe = wind is None or wind <= max_wind
        indoor_ok = indoor_temp is None or indoor_temp >= min_indoor
        is_down = _cover_is_down(self.hass, cover)
        is_up = _cover_is_up(self.hass, cover)
        current = "omlaag" if is_down else ("omhoog" if is_up else _state(self.hass, cover, "onbekend"))

        pv_high_now = bool(pv_power_w is not None and pv_power_w >= pv_close_w)
        pv_low_now = bool(pv_power_w is not None and pv_power_w < pv_close_w)
        if pv_high_now and in_active_month and in_time and wind_safe and not rainy and indoor_ok:
            if self._awning_pv_high_since is None:
                self._awning_pv_high_since = now
        else:
            self._awning_pv_high_since = None

        if pv_low_now or not in_active_month or not in_time or not wind_safe or rainy:
            if self._awning_pv_low_since is None:
                self._awning_pv_low_since = now
        else:
            self._awning_pv_low_since = None

        high_for_min = (now - self._awning_pv_high_since).total_seconds() / 60 if self._awning_pv_high_since else 0.0
        low_for_min = (now - self._awning_pv_low_since).total_seconds() / 60 if self._awning_pv_low_since else 0.0
        pv_high_stable = high_for_min >= timeout_min
        pv_low_stable = low_for_min >= timeout_min

        desired = "geen actie"
        reason = "Zonneschermregeling staat uit" if mode == AWNING_MODE_OFF else "Onvoldoende gegevens"
        should_down = bool(cover and mode != AWNING_MODE_OFF and pv_high_stable and in_active_month and in_time and wind_safe and not rainy and indoor_ok)
        should_up = bool(cover and mode != AWNING_MODE_OFF and (rainy or not wind_safe or not in_active_month or not in_time or pv_low_stable))

        if should_down:
            desired = "omlaag"
            reason = f"PV {pv_power_w:.0f} W ≥ {pv_close_w:.0f} W gedurende {high_for_min:.0f} min; zomermaand; wind veilig; geen regen"
            if indoor_temp is not None:
                reason += f"; binnen {indoor_temp:.1f} °C"
        elif should_up:
            desired = "omhoog"
            parts = []
            if rainy:
                parts.append("regen")
            if not wind_safe:
                parts.append(f"wind {wind:.1f} > {max_wind:.1f}")
            if not in_active_month:
                parts.append("buiten zomermaanden")
            if not in_time:
                parts.append("buiten tijdvenster")
            if pv_low_stable and pv_power_w is not None:
                parts.append(f"PV {pv_power_w:.0f} W < {pv_close_w:.0f} W gedurende {low_for_min:.0f} min")
            reason = "; ".join(parts) or "PV laag"
        elif mode != AWNING_MODE_OFF:
            desired = "geen actie"
            parts = []
            if pv_power_w is None:
                parts.append("geen PV-vermogenssensor ingesteld/beschikbaar")
            else:
                parts.append(f"PV {pv_power_w:.0f} W")
                if pv_high_now and not pv_high_stable:
                    parts.append(f"wacht {max(0, timeout_min - high_for_min):.0f} min")
            if not in_active_month:
                parts.append("buiten zomermaanden")
            if rainy:
                parts.append("regen actief")
            if not wind_safe:
                parts.append(f"wind te hoog ({wind:.1f})")
            if not in_time:
                parts.append("buiten tijdvenster")
            if not indoor_ok and indoor_temp is not None:
                parts.append(f"binnen {indoor_temp:.1f} °C < {min_indoor:.1f} °C")
            reason = "; ".join(parts) or "geen zonneschermactie nodig"

        service_called = ""
        if mode == AWNING_MODE_AUTO and cover:
            if desired == "omlaag" and not is_down:
                await self.hass.services.async_call("cover", "close_cover", {"entity_id": cover}, blocking=True)
                self.last_awning_action = "omlaag"
                self.last_awning_action_time = now
                service_called = "close_cover"
            elif desired == "omhoog" and not is_up:
                await self.hass.services.async_call("cover", "open_cover", {"entity_id": cover}, blocking=True)
                self.last_awning_action = "omhoog"
                self.last_awning_action_time = now
                service_called = "open_cover"

        status = AWNING_MODE_LABELS.get(mode, mode)
        if desired == "omlaag" and is_down:
            status += " · al omlaag"
        elif desired == "omhoog" and is_up:
            status += " · al omhoog"
        elif service_called:
            status += f" · uitgevoerd {desired}"
        elif desired != "geen actie":
            status += f" · advies {desired}"
        else:
            status += " · geen actie"

        return {
            "awning_mode": mode,
            "awning_mode_label": AWNING_MODE_LABELS.get(mode, mode),
            "awning_cover": cover,
            "awning_current": current,
            "awning_desired": desired,
            "awning_status": status,
            "awning_reason": reason,
            "awning_uv": uv,
            "awning_pv_power_w": round(pv_power_w, 0) if pv_power_w is not None else None,
            "awning_pv_threshold_w": pv_close_w,
            "awning_pv_high_for_min": round(high_for_min, 1),
            "awning_pv_low_for_min": round(low_for_min, 1),
            "awning_active_months": ",".join(str(m) for m in sorted(active_months)),
            "awning_in_active_month": in_active_month,
            "awning_wind": wind,
            "awning_rain": "Ja" if rainy else "Nee",
            "awning_last_action": self.last_awning_action,
            "awning_last_action_time": self.last_awning_action_time.isoformat() if self.last_awning_action_time else None,
        }

    def _update_today_vs_yesterday(self, *, tariff, forecast_today, action, action_key, auto_execute) -> tuple[str, dict[str, Any]]:
        """Track a small in-memory day comparison without depending on Recorder."""
        today = dt_util.now().date()
        if self._tracking_date != today:
            if self._today_snapshot:
                self._yesterday_snapshot = dict(self._today_snapshot)
            self._today_snapshot = {"date": today.isoformat(), "price_samples": [], "min_price": None, "max_price": None, "executions": 0, "last_action": "Geen actie"}
            self._tracking_date = today

        snap = self._today_snapshot
        if tariff is not None:
            samples = snap.setdefault("price_samples", [])
            samples.append(float(tariff))
            # Keep memory bounded: one sample per minute for ~36 hours is more than enough.
            del samples[:-2160]
            snap["avg_price"] = round(sum(samples) / len(samples), 4)
            snap["min_price"] = tariff if snap.get("min_price") is None else min(float(snap["min_price"]), float(tariff))
            snap["max_price"] = tariff if snap.get("max_price") is None else max(float(snap["max_price"]), float(tariff))
        if forecast_today is not None:
            snap["solar_forecast"] = float(forecast_today)
        snap["executions"] = self.executions_today
        snap["last_action"] = action or "Geen actie"
        snap["mode"] = EXECUTION_MODE_LABELS[EXECUTION_MODE_AUTO if auto_execute else EXECUTION_MODE_ADVICE]

        yesterday = self._yesterday_snapshot
        attrs = {"vandaag": dict(snap), "gisteren": dict(yesterday or {})}
        if not yesterday:
            return "Nog geen vergelijk met gisteren", attrs

        parts: list[str] = []
        if snap.get("avg_price") is not None and yesterday.get("avg_price") is not None:
            diff = float(snap["avg_price"]) - float(yesterday["avg_price"])
            if abs(diff) < 0.005:
                parts.append("stroomprijs vrijwel gelijk")
            elif diff < 0:
                parts.append(f"gemiddelde prijs {abs(diff):.3f} €/kWh lager")
            else:
                parts.append(f"gemiddelde prijs {diff:.3f} €/kWh hoger")
        if snap.get("solar_forecast") is not None and yesterday.get("solar_forecast") is not None:
            sdiff = float(snap["solar_forecast"]) - float(yesterday["solar_forecast"])
            if abs(sdiff) >= 0.5:
                parts.append(f"zonverwachting {abs(sdiff):.1f} kWh {'hoger' if sdiff > 0 else 'lager'}")
        if int(snap.get("executions") or 0) != int(yesterday.get("executions") or 0):
            parts.append(f"uitvoeringen {snap.get('executions', 0)} vs {yesterday.get('executions', 0)}")
        if not parts:
            parts.append("geen belangrijk verschil")
        return "Vandaag vs gisteren: " + "; ".join(parts), attrs

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._build_data()
        except Exception as err:
            _LOGGER.exception("Warmtepomp Manager update failed")
            return self._error_data(err)

    def _base_data(self) -> dict[str, Any]:
        cfg = self.cfg
        return {
            "strategy": STRATEGY_PRICE,
            "strategy_label": STRATEGIES[STRATEGY_PRICE],
            "switch_date_display": normalize_switch_date(cfg.get(CONF_SWITCH_DATE)),
            "auto_execute": False,
            "auto_status": "uit",
            "advice": "Configuratie controleren",
            "action": "Geen actie",
            "action_key": ACTION_NONE,
            "reason": "",
            "last_decision": self.last_decision,
            "tariff": None,
            "tariff_group": "onbekend",
            "dhw_temp": None,
            "dhw_max_display": "schema",
            "net_surplus": None,
            "net_surplus_source": "onbekend",
            "live_cop": None,
            "scop": None,
            "cycle_hours": None,
            "starts_per_day": None,
            "executions_today": self.executions_today,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "wp_status": "Rust",
            "wp_status_color": "grey",
            "wp_power": None,
            "forecast_solar_today": None,
            "forecast_solar_tomorrow": None,
            "indoor_temp": None,
            "negative_prices_active": "Nee",
            "negative_prices_tomorrow": "Onbekend",
            "negative_hours_tomorrow": "—",
            "lowest_price_tomorrow": None,
            "pv_mode": "Onbekend",
            "pv_mode_raw": "Onbekend",
            "cheapest_3h_block_tomorrow": "—",
            "cheapest_3h_price_tomorrow": None,
            "next_opportunity": "—",
            "solar_peak_tomorrow": "—",
            "solar_next_12h": None,
            "ai_strategy": "AI-monitoring",
            "planning_status": "Observeren",
            "planned_action": "Geen planning beschikbaar",
            "ai_day_plan": "Nog onvoldoende gegevens voor een betrouwbaar plan",
            "ai_day_plan_lines": [],
            "expected_savings": None,
            "cheapest_2h_block_tomorrow": "—",
            "cheapest_4h_block_tomorrow": "—",
            "dhw_load_strategy": "1x per dag volledig vat",
            "legionella_day": "Wo",
            "legionella_advice": "Combineren met doucheavond",
            "daily_report_status": "Niet verstuurd",
            "system_health": "Onbekend",
            "missing_entities": [],
            "last_report": None,
            "execution_mode": EXECUTION_MODE_ADVICE,
            "today_vs_yesterday": "Nog geen vergelijk met gisteren",
            "today_vs_yesterday_attrs": {},
            "awning_mode": AWNING_MODE_ADVICE,
            "awning_mode_label": AWNING_MODE_LABELS[AWNING_MODE_ADVICE],
            "awning_cover": "",
            "awning_current": "onbekend",
            "awning_desired": "geen actie",
            "awning_status": "Alleen advies · geen actie",
            "awning_reason": "Nog niet bijgewerkt",
            "awning_uv": None,
            "awning_pv_power_w": None,
            "awning_pv_threshold_w": 3000.0,
            "awning_pv_high_for_min": 0.0,
            "awning_pv_low_for_min": 0.0,
            "awning_active_months": "6,7,8,9",
            "awning_in_active_month": False,
            "awning_wind": None,
            "awning_rain": "Nee",
            "awning_last_action": None,
            "awning_last_action_time": None,
        }

    def _error_data(self, err: Exception) -> dict[str, Any]:
        data = self._base_data()
        data.update({"auto_status": "fout bij bijwerken", "reason": str(err), "last_decision": f"Fout bij bijwerken: {err}"})
        return data

    async def _build_data(self) -> dict[str, Any]:
        cfg = self.cfg
        availability_score, missing_entities = _availability_report(self.hass, cfg)
        strategy = self.current_strategy()
        tariff = _float_state(self.hass, cfg.get(CONF_TARIFF_SENSOR))
        dhw_temp_raw = _float_state(self.hass, cfg.get(CONF_DHW_TEMP_SENSOR))
        # Eén centrale tapwaterwaarde voor alle sensoren, attributen en dashboardweergave.
        # Hierdoor kan dezelfde temperatuur niet als 56,7 en 56,8 op twee plekken verschijnen.
        dhw_temp = round(dhw_temp_raw, 1) if dhw_temp_raw is not None else None
        dhw_max_display = _dhw_max_display(self.hass, cfg)
        net_surplus, net_surplus_source = _calculate_net_surplus(self.hass, cfg)
        scop = _calculate_scop(self.hass, cfg)
        cycle_hours = _calculate_cycle_hours(self.hass, cfg)
        starts_per_day = _calculate_starts_per_day(self.hass, cfg)
        live_cop = _calculate_live_cop()
        wp_status, wp_color, wp_power = _wp_status(self.hass, cfg)
        forecast_today = _float_state(self.hass, cfg.get(CONF_FORECAST_SOLAR_TODAY_SENSOR))
        forecast_tomorrow = _float_state(self.hass, cfg.get(CONF_FORECAST_SOLAR_TOMORROW_SENSOR))
        solar_peak_tomorrow = _timestamp_time(self.hass, cfg.get(CONF_SOLAR_PEAK_TOMORROW_SENSOR))
        solar_next_12h = _float_state(self.hass, cfg.get(CONF_SOLAR_NEXT_12H_SENSOR))
        indoor_temp = _float_state(self.hass, cfg.get(CONF_INDOOR_TEMP_SENSOR))
        comfort_temp = _as_float(cfg.get(CONF_COMFORT_TEMP), 22.0)

        low_price_threshold = _as_float(cfg.get(CONF_LOW_PRICE_THRESHOLD), 0.25)
        tariff_group = _zonneplan_tariff_group(self.hass, cfg.get(CONF_TARIFF_SENSOR), tariff, low_price_threshold)
        pv_threshold = _as_float(cfg.get(CONF_PV_SURPLUS_THRESHOLD), 2500.0)
        # UI historically used watts, while net_surplus is displayed/handled in kW.
        # Convert large threshold values automatically to keep existing configs sane.
        if pv_threshold > 100:
            pv_threshold = pv_threshold / 1000
        dhw_min = _as_float(cfg.get(CONF_DHW_MIN_TEMP), 54.0)
        dhw_low = dhw_temp is not None and dhw_temp < dhw_min
        tariff_low = tariff is not None and tariff <= low_price_threshold
        tariff_negative = tariff is not None and tariff < 0
        group_low = tariff_group.lower() in ("negatief", "zeer_laag", "laag", "low", "cheap", "goedkoop", "low_price")
        pv_ok = net_surplus is not None and net_surplus >= pv_threshold

        avg_price_today, avg_price_tomorrow = _average_price_today_tomorrow(self.hass, cfg.get(CONF_TARIFF_SENSOR))
        negative_tomorrow, negative_hours_tomorrow, lowest_price_tomorrow = _negative_price_forecast(self.hass, cfg.get(CONF_TARIFF_SENSOR))
        best_blocks = _best_blocks_tomorrow(self.hass, cfg.get(CONF_TARIFF_SENSOR))
        cheapest_3h_block_tomorrow = best_blocks.get("block_2h") or "—"
        cheapest_3h_price_tomorrow = best_blocks.get("price_2h")
        pv_mode_raw = _state(self.hass, cfg.get(CONF_PV_LIMIT_CONTROL_MODE_SELECT), "Onbekend")
        pv_mode = _pv_mode_display(pv_mode_raw)
        legionella_day = _select_legionella_day(str(cfg.get(CONF_SHOWER_DAYS)), negative_tomorrow, forecast_tomorrow)
        negative_active = "Aan" if tariff_negative else "Nee"
        next_opportunity = (
            f"Morgen {cheapest_3h_block_tomorrow} ({_fmt_price(cheapest_3h_price_tomorrow)})"
            if cheapest_3h_block_tomorrow and cheapest_3h_block_tomorrow != "—" and cheapest_3h_price_tomorrow is not None
            else "Nog geen goedkoop blok bekend"
        )
        ai_plan = _build_ai_day_plan(
            strategy_mode=strategy,
            current_price=tariff,
            dhw_temp=dhw_temp,
            dhw_min=dhw_min,
            cheapest_block=cheapest_3h_block_tomorrow,
            cheapest_price=cheapest_3h_price_tomorrow,
            cheapest_2h_block=best_blocks.get("block_2h") or "—",
            cheapest_4h_block=best_blocks.get("block_4h") or "—",
            negative_hours=negative_hours_tomorrow,
            negative_tomorrow=negative_tomorrow,
            solar_tomorrow=forecast_tomorrow,
            solar_peak_tomorrow=solar_peak_tomorrow,
            solar_next_12h=solar_next_12h,
            indoor_temp=indoor_temp,
            comfort_temp=comfort_temp,
        )

        advice = "Geen actie nodig"
        action = "Geen actie"
        action_key = ACTION_NONE
        reason = "Systeem binnen ingestelde grenzen"

        if tariff_negative and str(cfg.get(CONF_NEGATIVE_PRICE_STRATEGY)) != NEGATIVE_PRICE_OFF:
            advice = "Negatieve prijs · boilerschema overruled"
            action = "Boiler extra laden"
            action_key = ACTION_DHW_ONETIME
            reason = f"Negatief tarief {_fmt_price(tariff)} · laden naar 60 °C, ook bij voldoende warm tapwater"
        elif strategy == STRATEGY_PRICE:
            in_best_price_block = _now_in_hour_block(cheapest_3h_block_tomorrow)
            if dhw_low and in_best_price_block:
                advice = "Dagelijks laadmoment · goedkoopste blok actief"
                action = "Boiler eenmalig laden"
                action_key = ACTION_DHW_ONETIME
                reason = f"1x vol vat vandaag · prijsblok {cheapest_3h_block_tomorrow} · tapwater {dhw_temp:.1f} °C"
            elif dhw_low:
                advice = "Tapwater lager dan doel · wachten op goedkoopste dagmoment"
                action = "Wachten"
                action_key = ACTION_WAIT
                reason = f"Tapwater {dhw_temp:.1f} °C, dagelijks laadmoment nog niet bereikt"
            else:
                advice = "Tapwater voldoende warm" if dhw_temp is not None else "Geen tapwaterdata"
                reason = f"1x laden per dag · tapwater {dhw_temp:.1f} °C" if dhw_temp is not None else "Controleer tapwater-entiteit"
        else:
            near_solar_peak = _near_time_label(solar_peak_tomorrow, 1)
            if dhw_low and (pv_ok or near_solar_peak):
                advice = "Dagelijks laadmoment · zonmoment actief"
                action = "Boiler eenmalig laden"
                action_key = ACTION_DHW_ONETIME
                reason = f"1x vol vat vandaag · zonpiek {solar_peak_tomorrow} · tapwater {dhw_temp:.1f} °C"
            elif dhw_low:
                advice = "Tapwater lager dan doel · wachten op beste zonnemoment"
                action = "Wachten"
                action_key = ACTION_WAIT
                reason = f"Tapwater {dhw_temp:.1f} °C, zonnemoment nog niet bereikt"
            else:
                advice = "Tapwater voldoende warm" if dhw_temp is not None else "Geen tapwaterdata"
                reason = f"1x laden per dag · tapwater {dhw_temp:.1f} °C" if dhw_temp is not None else "Controleer tapwater-entiteit"

        if action_key == ACTION_WAIT:
            reason = _professional_wait_reason(
                base_reason=reason,
                cheapest_block=cheapest_3h_block_tomorrow,
                cheapest_price=cheapest_3h_price_tomorrow,
                lowest_price=lowest_price_tomorrow,
                current_price=tariff,
                solar_tomorrow=forecast_tomorrow,
                solar_peak_tomorrow=solar_peak_tomorrow,
                dhw_temp=dhw_temp,
            )

        auto_execute = bool(cfg.get(CONF_AUTO_EXECUTE))
        auto_status = "uit"
        if auto_execute and not self._first_update_done:
            auto_status = "aan · startup beveiliging actief"
        elif auto_execute and action_key == ACTION_DHW_ONETIME:
            allowed, why = self._can_auto_execute()
            if allowed:
                result = await self.async_execute_advice(manual=False, refresh_after=False)
                auto_status = f"uitgevoerd: {result}"
            else:
                auto_status = f"niet uitgevoerd: {why}"
        elif auto_execute:
            auto_status = "aan · geen uitvoerbare actie"

        self.last_action_key = action_key
        self.last_reason = reason
        if not auto_status.startswith("uitgevoerd"):
            self.last_decision = f"{advice} · {action} · {reason}"
        self._first_update_done = True

        daily_report_status = "Niet verstuurd"
        now = dt_util.now()
        today_vs_yesterday, today_vs_yesterday_attrs = self._update_today_vs_yesterday(
            tariff=tariff,
            forecast_today=forecast_today,
            action=action,
            action_key=action_key,
            auto_execute=auto_execute,
        )
        awning_data = await self._evaluate_awning(indoor_temp=indoor_temp)
        dishwasher_data = await self._evaluate_dishwasher()
        price_alert_data = await self._evaluate_price_alerts()

        if str(cfg.get(CONF_NOTIFY_SERVICE) or "").strip() and now.hour == 23 and self.last_report_date != now.date():
            daily_report_status = await self.async_send_daily_report(data_override={
                "ai_strategy": ai_plan.get("ai_strategy"),
                "planned_action": ai_plan.get("planned_action"),
                "dhw_temp": dhw_temp,
                "cheapest_3h_block_tomorrow": cheapest_3h_block_tomorrow,
                "cheapest_3h_price_tomorrow": cheapest_3h_price_tomorrow,
                "cheapest_2h_block_tomorrow": best_blocks.get("block_2h") or "—",
                "cheapest_2h_price_tomorrow": best_blocks.get("price_2h"),
                "solar_peak_tomorrow": solar_peak_tomorrow,
                "forecast_solar_tomorrow": forecast_tomorrow,
                "legionella_day": legionella_day,
                "missing_entities": missing_entities,
                "today_vs_yesterday": today_vs_yesterday,
            })

        return {
            "strategy": strategy,
            "strategy_label": STRATEGIES.get(strategy, strategy),
            "switch_date_display": normalize_switch_date(cfg.get(CONF_SWITCH_DATE)),
            "auto_execute": auto_execute,
            "auto_status": auto_status,
            "advice": advice,
            "action": action,
            "action_key": action_key,
            "reason": reason,
            "last_decision": self.last_decision,
            "tariff": tariff,
            "tariff_group": tariff_group,
            "avg_price_today": avg_price_today,
            "avg_price_tomorrow": avg_price_tomorrow,
            "dhw_temp": dhw_temp,
            "dhw_max_display": dhw_max_display,
            "net_surplus": net_surplus,
            "net_surplus_source": net_surplus_source,
            "live_cop": live_cop,
            "scop": scop,
            "cycle_hours": cycle_hours,
            "starts_per_day": starts_per_day,
            "executions_today": self.executions_today,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "wp_status": wp_status,
            "wp_status_color": wp_color,
            "wp_power": wp_power,
            "forecast_solar_today": forecast_today,
            "forecast_solar_tomorrow": forecast_tomorrow,
            "solar_peak_tomorrow": solar_peak_tomorrow,
            "solar_next_12h": solar_next_12h,
            "indoor_temp": indoor_temp,
            "negative_prices_active": negative_active,
            "negative_prices_tomorrow": negative_tomorrow,
            "negative_hours_tomorrow": negative_hours_tomorrow,
            "lowest_price_tomorrow": lowest_price_tomorrow,
            "cheapest_3h_block_tomorrow": cheapest_3h_block_tomorrow,
            "cheapest_3h_price_tomorrow": cheapest_3h_price_tomorrow,
            "next_opportunity": next_opportunity,
            "pv_mode": pv_mode,
            "pv_mode_raw": pv_mode_raw,
            "ai_strategy": ai_plan.get("ai_strategy"),
            "planning_status": ai_plan.get("planning_status"),
            "planned_action": ai_plan.get("planned_action"),
            "ai_day_plan": ai_plan.get("ai_day_plan"),
            "ai_day_plan_lines": ai_plan.get("ai_day_plan_lines"),
            "expected_savings": ai_plan.get("expected_savings"),
            "cheapest_2h_block_tomorrow": ai_plan.get("cheapest_2h_block_tomorrow"),
            "cheapest_2h_price_tomorrow": best_blocks.get("price_2h"),
            "cheapest_4h_block_tomorrow": ai_plan.get("cheapest_4h_block_tomorrow"),
            "dhw_load_strategy": "1x/dag volledig vat · tot 31-12-2026 goedkoopste 2u · vanaf 01-01-2027 zonblok · negatieve prijs overrulet",
            "legionella_day": legionella_day,
            "legionella_advice": f"Voorkeur {legionella_day}: combineren met doucheavond (woensdag/zondag)",
            "daily_report_status": daily_report_status,
            "system_health": "Goed" if not missing_entities else "Controle nodig",
            "missing_entities": missing_entities,
            "execution_mode": EXECUTION_MODE_AUTO if auto_execute else EXECUTION_MODE_ADVICE,
            "today_vs_yesterday": today_vs_yesterday,
            "today_vs_yesterday_attrs": today_vs_yesterday_attrs,
            **awning_data,
            **dishwasher_data,
            **price_alert_data,
            "last_report": self.last_report_date.isoformat() if self.last_report_date else None,
        }

    def _build_report_message(self, data: dict[str, Any]) -> str:
        lines = [
            "🧠 Warmtepomp Manager",
            "",
            f"Strategie: {data.get('ai_strategy') or data.get('strategy_label') or 'Onbekend'}",
            f"Actie: {data.get('planned_action') or 'Geen actie'}",
        ]
        dhw_temp = data.get("dhw_temp")
        if dhw_temp is not None:
            lines.append(f"Tapwater: {dhw_temp:.1f} °C")
        block = data.get("cheapest_3h_block_tomorrow") or "—"
        block_price = data.get("cheapest_3h_price_tomorrow")
        lines.append(f"Goedkoopste blok: {block} ({_fmt_price(block_price)})")
        lines.append(f"Zonpiek morgen: {data.get('solar_peak_tomorrow') or '—'}")
        solar = data.get("forecast_solar_tomorrow")
        if solar is not None:
            lines.append(f"Zon morgen: {solar:.1f} kWh")
        lines.append(f"Legionella voorkeur: {data.get('legionella_day') or 'Wo'} · combineren met doucheavond")
        lines.append("Tapwaterstrategie: 1x per dag volledig vat")
        comparison = data.get("today_vs_yesterday")
        if comparison:
            lines.append(comparison)
        missing = data.get("missing_entities") or []
        if missing:
            lines.append("Let op: ontbrekend/onbeschikbaar: " + ", ".join(missing[:3]))
        return "\n".join(lines)

    async def async_send_daily_report(self, data_override: dict[str, Any] | None = None) -> str:
        cfg = self.cfg
        notify_service = str(cfg.get(CONF_NOTIFY_SERVICE) or "").strip()
        if not notify_service:
            return "Geen notify-service ingesteld"
        data = dict(self.data or {})
        if data_override:
            data.update(data_override)
        try:
            domain, service = notify_service.split('.', 1) if '.' in notify_service else ('notify', notify_service)
            await self.hass.services.async_call(
                domain,
                service,
                {"title": "Warmtepomp Manager", "message": self._build_report_message(data)},
                blocking=True,
            )
            self.last_report_date = dt_util.now().date()
            return f"Verstuurd naar {notify_service}"
        except Exception as err:
            _LOGGER.exception("Warmtepomp Manager report failed")
            return f"Melding mislukt: {err}"

    async def async_execute_advice(self, manual: bool = True, refresh_after: bool = True) -> str:
        if refresh_after:
            await self.async_request_refresh()
        data = self.data or {}
        action_key = data.get("action_key", self.last_action_key)
        cfg = self.cfg

        if action_key not in (ACTION_DHW_ONETIME,):
            self.last_decision = "Geen uitvoerbare actie beschikbaar"
            if refresh_after:
                await self.async_request_refresh()
            return self.last_decision

        target_temp = _as_float(cfg.get(CONF_DHW_TARGET_TEMP), 60.0)
        if bool(cfg.get(CONF_EXECUTE_SET_MAX_TEMP, True)):
            max_temp_entity = cfg.get(CONF_DHW_MAX_TEMP) or ""
            if max_temp_entity:
                await self.hass.services.async_call("number", "set_value", {"entity_id": max_temp_entity, "value": target_temp}, blocking=True)

        if bool(cfg.get(CONF_EXECUTE_WATER_HEATER_MODE, False)):
            heater = cfg.get(CONF_WATER_HEATER) or ""
            mode = cfg.get(CONF_WATER_HEATER_COMFORT_MODE) or "Comfort+"
            if heater:
                await self.hass.services.async_call("water_heater", "set_operation_mode", {"entity_id": heater, "operation_mode": mode}, blocking=True)

        onetime_entity = cfg.get(CONF_DHW_ONETIME_SWITCH) or ""
        if not onetime_entity:
            self.last_decision = "Geen eenmalig-laden switch ingesteld"
            return self.last_decision

        await self.hass.services.async_call("switch", "turn_on", {"entity_id": onetime_entity}, blocking=True)
        self._reset_daily_counter_if_needed()
        self.executions_today += 1
        self.last_executed = dt_util.now()
        mode_label = "Handmatig" if manual else "Automatisch"
        self.last_decision = f"{mode_label} uitgevoerd: boiler eenmalig laden naar {target_temp:.0f} °C"
        if refresh_after:
            await self.async_request_refresh()
        return self.last_decision
