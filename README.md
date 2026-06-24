# Warmtepomp Manager

## v1.7.2

- Dure stroom is nu opgesplitst in vandaag en morgen.
- Nieuwe sensoren: `sensor.warmtepomp_manager_dure_uren_vandaag` en `sensor.warmtepomp_manager_dure_uren_morgen`.
- Alias-sensoren toegevoegd: `sensor.warmtepomp_manager_dure_stroom_vandaag` en `sensor.warmtepomp_manager_dure_stroom_morgen`.
- Dashboard toont nu dure prijsblokken voor vandaag én morgen.
 v1.7.1

HACS-integratie voor boiler, energie, zonnescherm en vaatwasser.

## Speerpunten

- Boiler: 1x per dag volledig vat.
- Tot 31-12-2026: goedkoopste 2-uurs prijsblok leidend.
- Vanaf 01-01-2027: zonneblok/PV leidend, prijs wordt genegeerd.
- Negatieve tarieven overrulen het boilerschema en mogen ook bij een nog warme boiler laden naar 60 °C.
- Desinfectie/legionella combineren met de dagelijkse lading of met negatieve tarieven.
- Service `warmtepomp_manager.start_disinfection` voor handmatige tapwater-desinfectie.
- Vaatwasser: automatisch Eco 50°C plannen zodra de deur dicht is en remote start beschikbaar is.
- Vaatwasser: deur open reset de planning en stuurt een melding.
- Vaatwasser: deur dicht triggert een nieuwe berekening en stuurt een compacte planningmelding.
- Dagelijkse 18:30 melding voor vaatwasseradvies wanneer automatisch plannen uit staat.
- Melding bij dure stroom boven de ingestelde drempel, standaard €0,40/kWh.
- Melding voor stroomoverschot/auto laden.
- Zonnescherm: PV ≥ 3000 W gedurende 15 minuten, alleen juni t/m september.
- Notify-doelen per meldingstype instelbaar via de integratie-opties.

## Installatie

Plaats de map `custom_components/warmtepomp_manager` in Home Assistant onder `/config/custom_components/` of publiceer deze repository via HACS.

Na installatie Home Assistant herstarten en de integratie configureren via:

Instellingen → Apparaten & diensten → Warmtepomp Manager → Opties

## Belangrijke services

- `warmtepomp_manager.execute_advice`
- `warmtepomp_manager.refresh`
- `warmtepomp_manager.send_daily_report`
- `warmtepomp_manager.set_execution_mode`
- `warmtepomp_manager.set_awning_mode`
- `warmtepomp_manager.start_disinfection`

## Dashboard

Gebruik het YAML-dashboard in de map `dashboards/` als basis. Voor telefoon/tablet is de portrait-kaart het meest geschikt.


## v1.7.1

- Fix: toegevoegd `sensor.warmtepomp_manager_dure_uren_morgen`.
- Dashboard verwijst niet meer naar de niet-bestaande `sensor.warmtepomp_manager_dure_stroom_morgen`.
