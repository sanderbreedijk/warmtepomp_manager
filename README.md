# Warmtepomp Manager v1.6.0

Opgeschoonde HACS-versie voor boiler, energie, zonnescherm en vaatwasser.

## Speerpunten

- Boiler: 1x per dag volledig vat.
- Tot 31-12-2026: goedkoopste 2-uurs prijsblok leidend.
- Vanaf 01-01-2027: zonneblok/PV leidend, prijs wordt genegeerd.
- Negatieve tarieven overrulen het boilerschema en mogen ook bij een nog warme boiler laden naar 60 °C.
- Desinfectie/legionella combineren met de dagelijkse lading of met negatieve tarieven.
- Vaatwasser: automatisch Eco 50°C plannen zodra de deur dicht is en remote start beschikbaar is.
- Vaatwasser: deur open reset de planning; daarna opnieuw berekenen.
- Dagelijkse 18:30 melding voor vaatwasseradvies.
- Melding bij dure stroom boven €0,40/kWh.
- Melding voor stroomoverschot/auto laden.
- Zonnescherm: PV ≥ 3000 W gedurende 15 minuten, alleen juni t/m september.
- Notify-doelen per meldingstype instelbaar via de integratie-opties.

## Installatie

Plaats de map `custom_components/warmtepomp_manager` in Home Assistant onder `/config/custom_components/` of publiceer deze repository via HACS.

Na installatie Home Assistant herstarten en de integratie configureren via Instellingen → Apparaten & diensten.

## Dashboard

Gebruik `dashboards/warmtepomp_manager_dashboard_v1_6_0_clean.yaml` als basisdashboard.
