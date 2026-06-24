from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfPower
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import WarmtepompManagerEntity


@dataclass(frozen=True, kw_only=True)
class WpSensorDescription(SensorEntityDescription):
    """Description for Warmtepomp Manager sensors."""

    name: str
    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: list[WpSensorDescription] = [
    WpSensorDescription(key="strategie", name="Strategie", translation_key="strategie", icon="mdi:strategy", value_fn=lambda d: d.get("strategy_label") or d.get("strategy")),
    WpSensorDescription(key="advies", name="Advies", translation_key="advies", icon="mdi:lightbulb-on-outline", value_fn=lambda d: d.get("advice")),
    WpSensorDescription(key="actie", name="Actie", translation_key="actie", icon="mdi:lightning-bolt", value_fn=lambda d: d.get("action")),
    WpSensorDescription(key="reden", name="Reden", translation_key="reden", icon="mdi:comment-question-outline", value_fn=lambda d: d.get("reason")),
    WpSensorDescription(key="volgende_kans", name="Volgende kans", translation_key="volgende_kans", icon="mdi:clock-star-four-points-outline", value_fn=lambda d: d.get("next_opportunity")),
    WpSensorDescription(key="status", name="Status", translation_key="status", icon="mdi:information-outline", value_fn=lambda d: "Automatisch" if d.get("auto_execute") else "Alleen advies"),
    WpSensorDescription(key="auto_status", name="Automatische uitvoering", translation_key="auto_status", icon="mdi:robot", value_fn=lambda d: d.get("auto_status")),
    WpSensorDescription(key="omschakeldatum", name="Omschakeldatum", translation_key="omschakeldatum", icon="mdi:calendar", value_fn=lambda d: d.get("switch_date_display")),
    WpSensorDescription(key="live_cop", name="Live COP", translation_key="live_cop", icon="mdi:speedometer", value_fn=lambda d: d.get("live_cop")),
    WpSensorDescription(key="scop", name="SCOP", translation_key="scop", icon="mdi:chart-line", value_fn=lambda d: d.get("scop")),
    WpSensorDescription(key="cyclustijd", name="Cyclustijd", translation_key="cyclustijd", native_unit_of_measurement="h", icon="mdi:timer-outline", value_fn=lambda d: d.get("cycle_hours")),
    WpSensorDescription(key="starts_per_dag", name="Starts per dag", translation_key="starts_per_dag", icon="mdi:counter", value_fn=lambda d: d.get("starts_per_day")),
    WpSensorDescription(key="laatste_beslissing", name="Laatste beslissing", translation_key="laatste_beslissing", icon="mdi:history", value_fn=lambda d: d.get("last_decision")),
    WpSensorDescription(key="tarief", name="Stroomprijs", translation_key="tarief", native_unit_of_measurement="€/kWh", icon="mdi:currency-eur", value_fn=lambda d: d.get("tariff")),
    WpSensorDescription(key="tariefgroep", name="Tariefgroep", translation_key="tariefgroep", icon="mdi:shape-outline", value_fn=lambda d: d.get("tariff_group")),
    WpSensorDescription(key="tapwater", name="Tapwater", translation_key="tapwater", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, icon="mdi:water-boiler", value_fn=lambda d: d.get("dhw_temp")),
    WpSensorDescription(key="netto_overschot", name="Netto overschot", translation_key="netto_overschot", device_class=SensorDeviceClass.POWER, native_unit_of_measurement="kW", icon="mdi:solar-power-variant", value_fn=lambda d: d.get("net_surplus")),
    WpSensorDescription(key="wp_status", name="Warmtepomp status", translation_key="wp_status", icon="mdi:heat-pump", value_fn=lambda d: d.get("wp_status")),
    WpSensorDescription(key="wp_vermogen", name="Warmtepomp vermogen", translation_key="wp_vermogen", device_class=SensorDeviceClass.POWER, native_unit_of_measurement=UnitOfPower.WATT, icon="mdi:flash", value_fn=lambda d: d.get("wp_power")),
    WpSensorDescription(key="dhw_max_display", name="Tapwater max", translation_key="dhw_max_display", icon="mdi:thermometer", value_fn=lambda d: d.get("dhw_max_display")),
    WpSensorDescription(key="forecast_solar_today", name="Zonneverwachting vandaag", translation_key="forecast_solar_today", native_unit_of_measurement="kWh", icon="mdi:solar-power", value_fn=lambda d: d.get("forecast_solar_today")),
    WpSensorDescription(key="forecast_solar_tomorrow", name="Zonneverwachting morgen", translation_key="forecast_solar_tomorrow", native_unit_of_measurement="kWh", icon="mdi:solar-power", value_fn=lambda d: d.get("forecast_solar_tomorrow")),
    WpSensorDescription(key="zonnepiek_morgen", name="Zonnepiek morgen", translation_key="zonnepiek_morgen", icon="mdi:weather-sunny-alert", value_fn=lambda d: d.get("solar_peak_tomorrow")),
    WpSensorDescription(key="zonnevermogen_12u", name="Zonnevermogen over 12 uur", translation_key="zonnevermogen_12u", native_unit_of_measurement="W", icon="mdi:solar-power", value_fn=lambda d: d.get("solar_next_12h")),
    WpSensorDescription(key="binnentemperatuur", name="Binnentemperatuur", translation_key="binnentemperatuur", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, icon="mdi:home-thermometer", value_fn=lambda d: d.get("indoor_temp")),
    WpSensorDescription(key="uitvoeringen_vandaag", name="Uitvoeringen vandaag", translation_key="uitvoeringen_vandaag", icon="mdi:counter", value_fn=lambda d: d.get("executions_today")),
    WpSensorDescription(key="stroomprijs", name="Stroomprijs", translation_key="stroomprijs", native_unit_of_measurement="€/kWh", icon="mdi:currency-eur", value_fn=lambda d: d.get("tariff")),
    WpSensorDescription(key="gemiddelde_prijs_vandaag", name="Gemiddelde prijs vandaag", translation_key="gemiddelde_prijs_vandaag", native_unit_of_measurement="€/kWh", icon="mdi:chart-bell-curve", value_fn=lambda d: d.get("avg_price_today")),
    WpSensorDescription(key="gemiddelde_prijs_morgen", name="Gemiddelde prijs morgen", translation_key="gemiddelde_prijs_morgen", native_unit_of_measurement="€/kWh", icon="mdi:chart-bell-curve", value_fn=lambda d: d.get("avg_price_tomorrow")),
    WpSensorDescription(key="negatieve_prijzen_actief", name="Negatieve prijzen actief", translation_key="negatieve_prijzen_actief", icon="mdi:cash-minus", value_fn=lambda d: d.get("negative_prices_active")),
    WpSensorDescription(key="negatieve_prijzen_morgen", name="Negatieve prijzen morgen", translation_key="negatieve_prijzen_morgen", icon="mdi:calendar-alert", value_fn=lambda d: d.get("negative_prices_tomorrow")),
    WpSensorDescription(key="negatieve_uren_morgen", name="Negatieve uren morgen", translation_key="negatieve_uren_morgen", icon="mdi:clock-alert-outline", value_fn=lambda d: d.get("negative_hours_tomorrow")),
    WpSensorDescription(key="laagste_prijs_morgen", name="Laagste prijs morgen", translation_key="laagste_prijs_morgen", native_unit_of_measurement="€/kWh", icon="mdi:cash-clock", value_fn=lambda d: d.get("lowest_price_tomorrow")),
    WpSensorDescription(key="goedkoopste_2u_blok", name="Goedkoopste 2-uursblok", translation_key="goedkoopste_2u_blok", icon="mdi:clock-check-outline", value_fn=lambda d: d.get("cheapest_2h_block_tomorrow")),
    WpSensorDescription(key="goedkoopste_2u_blokprijs", name="Goedkoopste 2-uursblokprijs", translation_key="goedkoopste_2u_blokprijs", native_unit_of_measurement="€/kWh", icon="mdi:cash-clock", value_fn=lambda d: d.get("cheapest_2h_price_tomorrow")),
    WpSensorDescription(key="pv_mode", name="PV modus", translation_key="pv_mode", icon="mdi:solar-power-variant", value_fn=lambda d: d.get("pv_mode")),
    WpSensorDescription(key="planningstrategie", name="Planningstrategie", translation_key="planningstrategie", icon="mdi:strategy", value_fn=lambda d: d.get("ai_strategy")),
    WpSensorDescription(key="planning_status", name="Planningstatus", translation_key="planning_status", icon="mdi:calendar-clock", value_fn=lambda d: d.get("planning_status")),
    WpSensorDescription(key="dagplanning", name="Dagplanning", translation_key="dagplanning", icon="mdi:clipboard-text-clock", value_fn=lambda d: d.get("ai_day_plan")),
    WpSensorDescription(key="geplande_actie", name="Geplande actie", translation_key="geplande_actie", icon="mdi:calendar-check", value_fn=lambda d: d.get("planned_action")),
    WpSensorDescription(key="verwachte_besparing", name="Verwachte besparing", translation_key="verwachte_besparing", native_unit_of_measurement="€", icon="mdi:cash-plus", value_fn=lambda d: d.get("expected_savings")),
    WpSensorDescription(key="goedkoopste_2u_blok_morgen", name="Goedkoopste 2-uursblok morgen", translation_key="goedkoopste_2u_blok_morgen", icon="mdi:clock-check-outline", value_fn=lambda d: d.get("cheapest_2h_block_tomorrow")),
    WpSensorDescription(key="goedkoopste_4u_blok_morgen", name="Goedkoopste 4-uursblok morgen", translation_key="goedkoopste_4u_blok_morgen", icon="mdi:clock-check-outline", value_fn=lambda d: d.get("cheapest_4h_block_tomorrow")),
    WpSensorDescription(key="tapwater_laadstrategie", name="Tapwater laadstrategie", translation_key="tapwater_laadstrategie", icon="mdi:water-boiler-auto", value_fn=lambda d: d.get("dhw_load_strategy")),
    WpSensorDescription(key="legionella_dag", name="Legionella dag", translation_key="legionella_dag", icon="mdi:bacteria-outline", value_fn=lambda d: d.get("legionella_day")),
    WpSensorDescription(key="legionella_advies", name="Legionella advies", translation_key="legionella_advies", icon="mdi:shield-check-outline", value_fn=lambda d: d.get("legionella_advice")),
    WpSensorDescription(key="dagrapport_status", name="Dagrapport status", translation_key="dagrapport_status", icon="mdi:cellphone-message", value_fn=lambda d: d.get("daily_report_status")),
    WpSensorDescription(key="systeemgezondheid", name="Systeemgezondheid", translation_key="systeemgezondheid", icon="mdi:shield-check", value_fn=lambda d: d.get("system_health")),
    WpSensorDescription(key="ontbrekende_entiteiten", name="Ontbrekende entiteiten", translation_key="ontbrekende_entiteiten", icon="mdi:alert-circle-outline", value_fn=lambda d: len(d.get("missing_entities") or [])),
    WpSensorDescription(key="vandaag_vs_gisteren", name="Vandaag vs gisteren", translation_key="vandaag_vs_gisteren", icon="mdi:compare-horizontal", value_fn=lambda d: d.get("today_vs_yesterday")),
    WpSensorDescription(key="zonnescherm_status", name="Zonnescherm status", translation_key="zonnescherm_status", icon="mdi:awning-outline", value_fn=lambda d: d.get("awning_status")),
    WpSensorDescription(key="zonnescherm_advies", name="Zonnescherm advies", translation_key="zonnescherm_advies", icon="mdi:weather-sunny-alert", value_fn=lambda d: d.get("awning_desired")),
    WpSensorDescription(key="zonnescherm_reden", name="Zonnescherm reden", translation_key="zonnescherm_reden", icon="mdi:comment-question-outline", value_fn=lambda d: d.get("awning_reason")),
    WpSensorDescription(key="zonnescherm_pv_vermogen", name="Zonnescherm PV vermogen", translation_key="zonnescherm_pv_vermogen", native_unit_of_measurement="W", icon="mdi:solar-power", value_fn=lambda d: d.get("awning_pv_power_w")),
    WpSensorDescription(key="vaatwasser_status", name="Vaatwasser status", translation_key="vaatwasser_status", icon="mdi:dishwasher", value_fn=lambda d: d.get("dishwasher_status")),
    WpSensorDescription(key="vaatwasser_advies", name="Vaatwasser advies", translation_key="vaatwasser_advies", icon="mdi:dishwasher-alert", value_fn=lambda d: d.get("dishwasher_message")),
    WpSensorDescription(key="vaatwasser_beste_blok", name="Vaatwasser beste blok", translation_key="vaatwasser_beste_blok", icon="mdi:clock-check-outline", value_fn=lambda d: d.get("dishwasher_best_block")),
    WpSensorDescription(key="vaatwasser_besparing", name="Vaatwasser besparing", translation_key="vaatwasser_besparing", native_unit_of_measurement="€", icon="mdi:cash-plus", value_fn=lambda d: d.get("dishwasher_savings")),
    WpSensorDescription(key="dure_stroom", name="Dure stroom", translation_key="dure_stroom", icon="mdi:transmission-tower-alert", value_fn=lambda d: d.get("high_price_status")),
    WpSensorDescription(key="dure_stroom_blokken", name="Dure stroom blokken", translation_key="dure_stroom_blokken", icon="mdi:clock-alert-outline", value_fn=lambda d: d.get("high_price_blocks") or "Geen"),
    WpSensorDescription(key="dure_uren_vandaag", name="Dure uren vandaag", translation_key="dure_uren_vandaag", icon="mdi:clock-alert-outline", value_fn=lambda d: d.get("high_price_blocks_today") or "Geen"),
    WpSensorDescription(key="dure_uren_morgen", name="Dure uren morgen", translation_key="dure_uren_morgen", icon="mdi:clock-alert-outline", value_fn=lambda d: d.get("high_price_blocks_tomorrow") or "Geen"),
    WpSensorDescription(key="dure_stroom_vandaag", name="Dure stroom vandaag", translation_key="dure_stroom_vandaag", icon="mdi:transmission-tower-alert", value_fn=lambda d: d.get("high_price_blocks_today") or "Geen"),
    WpSensorDescription(key="dure_stroom_morgen", name="Dure stroom morgen", translation_key="dure_stroom_morgen", icon="mdi:transmission-tower-alert", value_fn=lambda d: d.get("high_price_blocks_tomorrow") or "Geen"),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Warmtepomp Manager sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WarmtepompManagerSensor(coordinator, entry, desc) for desc in SENSORS])


class WarmtepompManagerSensor(WarmtepompManagerEntity, SensorEntity):
    """Warmtepomp Manager sensor entity."""

    entity_description: WpSensorDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: WpSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_translation_key = description.translation_key
        self._attr_name = description.name
        self._attr_unique_id = f"warmtepomp_manager_{entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = f"warmtepomp_manager_{description.key}"
        legacy_disabled = {
            "live_cop", "scop", "cyclustijd", "starts_per_dag",
            "goedkoopste_4u_blok_morgen", "verwachte_besparing",
            "pv_mode", "tariefgroep", "dhw_max_display",
            "vandaag_vs_gisteren",
        }
        if description.key in legacy_disabled:
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "strategie": data.get("strategy"),
            "strategie_label": data.get("strategy_label"),
            "omschakeldatum": data.get("switch_date_display"),
            "automatisch_uitvoeren": data.get("auto_execute"),
            "auto_status": data.get("auto_status"),
            "voorgestelde_actie": data.get("action"),
            "actie_code": data.get("action_key"),
            "reden": data.get("reason"),
            "tarief": data.get("tariff"),
            "tariefgroep": data.get("tariff_group"),
            "tapwater_temperatuur": data.get("dhw_temp"),
            "tapwater_max_weergave": data.get("dhw_max_display"),
            "warmtepomp_status": data.get("wp_status"),
            "warmtepomp_vermogen": data.get("wp_power"),
            "warmtepomp_status_kleur": data.get("wp_status_color"),
            "zonneverwachting_vandaag": data.get("forecast_solar_today"),
            "zonneverwachting_morgen": data.get("forecast_solar_tomorrow"),
            "binnentemperatuur": data.get("indoor_temp"),
            "netto_overschot": data.get("net_surplus"),
            "netto_overschot_bron": data.get("net_surplus_source"),
            "live_cop": data.get("live_cop"),
            "scop": data.get("scop"),
            "cyclustijd_uren": data.get("cycle_hours"),
            "starts_per_dag": data.get("starts_per_day"),
            "uitvoeringen_vandaag": data.get("executions_today"),
            "laagste_prijs_morgen": data.get("lowest_price_tomorrow"),
            "goedkoopste_blok_morgen": data.get("cheapest_3h_block_tomorrow"),
            "goedkoopste_blok_prijs_morgen": data.get("cheapest_3h_price_tomorrow"),
            "volgende_kans": data.get("next_opportunity"),
            "zonnepiek_morgen": data.get("solar_peak_tomorrow"),
            "zonnevermogen_12u": data.get("solar_next_12h"),
            "pv_mode_raw": data.get("pv_mode_raw"),
            "ai_strategie": data.get("ai_strategy"),
            "planning_status": data.get("planning_status"),
            "geplande_actie": data.get("planned_action"),
            "dagplanning_regels": data.get("ai_day_plan_lines"),
            "verwachte_besparing": data.get("expected_savings"),
            "goedkoopste_2u_blok_morgen": data.get("cheapest_2h_block_tomorrow"),
            "goedkoopste_4u_blok_morgen": data.get("cheapest_4h_block_tomorrow"),
            "tapwater_laadstrategie": data.get("dhw_load_strategy"),
            "legionella_dag": data.get("legionella_day"),
            "legionella_advies": data.get("legionella_advice"),
            "dagrapport_status": data.get("daily_report_status"),
            "systeemgezondheid": data.get("system_health"),
            "ontbrekende_entiteiten": data.get("missing_entities"),
            "uitvoeringsmodus": data.get("execution_mode"),
            "vandaag_vs_gisteren_details": data.get("today_vs_yesterday_attrs"),
            "laatste_rapport": data.get("last_report"),
            "laatst_uitgevoerd": data.get("last_executed"),
            "zonnescherm_modus": data.get("awning_mode_label"),
            "zonnescherm_huidige_stand": data.get("awning_current"),
            "zonnescherm_gewenste_stand": data.get("awning_desired"),
            "zonnescherm_reden": data.get("awning_reason"),
            "zonkracht": data.get("awning_uv"),
            "zonnescherm_pv_vermogen": data.get("awning_pv_power_w"),
            "zonnescherm_pv_drempel": data.get("awning_pv_threshold_w"),
            "zonnescherm_pv_hoog_minuten": data.get("awning_pv_high_for_min"),
            "zonnescherm_pv_laag_minuten": data.get("awning_pv_low_for_min"),
            "zonnescherm_actieve_maanden": data.get("awning_active_months"),
            "zonnescherm_in_actieve_maand": data.get("awning_in_active_month"),
            "wind": data.get("awning_wind"),
            "regen": data.get("awning_rain"),
            "zonnescherm_laatste_actie": data.get("awning_last_action"),
            "zonnescherm_laatste_actie_tijd": data.get("awning_last_action_time"),
            "vaatwasser_deur": data.get("dishwasher_door"),
            "vaatwasser_remote_start": data.get("dishwasher_remote_start"),
            "vaatwasser_auto": data.get("dishwasher_auto"),
            "vaatwasser_programma": data.get("dishwasher_program"),
            "vaatwasser_beste_blok": data.get("dishwasher_best_block"),
            "vaatwasser_start": data.get("dishwasher_best_start"),
            "vaatwasser_startvertraging": data.get("dishwasher_delay_option"),
            "vaatwasser_kosten_nu": data.get("dishwasher_cost_now"),
            "vaatwasser_kosten_beste": data.get("dishwasher_cost_best"),
            "vaatwasser_besparing": data.get("dishwasher_savings"),
            "vaatwasser_melding": data.get("dishwasher_message"),
            "vaatwasser_actie_status": data.get("dishwasher_action_status"),
            "dure_stroom_drempel": data.get("high_price_threshold"),
            "dure_stroom_blokken": data.get("high_price_blocks"),
            "dure_uren_vandaag": data.get("high_price_blocks_today"),
            "dure_uren_morgen": data.get("high_price_blocks_tomorrow"),
            "dure_stroom_vandaag": data.get("high_price_blocks_today"),
            "dure_stroom_morgen": data.get("high_price_blocks_tomorrow"),
            "dure_stroom_melding_status": data.get("high_price_notify_status"),
        }
