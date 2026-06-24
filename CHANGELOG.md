
## v1.7.2

- Fix: `sensor.warmtepomp_manager_dure_stroom_morgen` bestaat nu als alias.
- Nieuw: `sensor.warmtepomp_manager_dure_uren_vandaag`.
- Dure-prijsblokken worden nu gescheiden voor vandaag en morgen.
- Dashboard bijgewerkt zodat bij stroom zowel vandaag als morgen wordt vermeld.

# Changelog

## 1.7.1

- Fix: `sensor.warmtepomp_manager_dure_uren_morgen` toegevoegd.
- Dashboardreferenties naar `dure_stroom_morgen` opgeschoond.

## 1.7.0

- Vaatwasser: melding naar mobiel zodra de deur opengaat en de planning wordt gereset.
- Vaatwasser: melding naar mobiel zodra de deur weer dichtgaat en de planning/berekening klaar is.
- Vaatwasser: bij gesloten deur wordt Eco 50°C gepland, startvertraging ingesteld en de startknop gebruikt wanneer automatisch plannen mogelijk is.
- Vaatwasser: als automatisch starten niet mogelijk is, wordt alsnog een compacte berekeningsmelding verstuurd.
- Nieuwe service `warmtepomp_manager.start_disinfection` toegevoegd; deze zet de ingestelde tapwater-desinfectieschakelaar aan.
- Dure-stroommelding boven de ingestelde drempel blijft beschikbaar.
- Python compile-check uitgevoerd.

## 1.6.0

- Repository opgeschoond: geen root-level duplicaten en geen `__pycache__`/`.pyc` bestanden.
- Dashboard vernieuwd voor de vereenvoudigde strategie.
- Boilerlogica gericht op 1x per dag laden.
- Goedkoopste 2-uursblok is leidend tot en met 31-12-2026.
- Vanaf 01-01-2027 is zon/PV leidend, ongeacht stroomprijs.
- Negatieve tarieven overrulen het boilerschema.
- Vaatwasserlogica: Eco 50°C, deur dicht plannen, deur open resetten.
- Notify-doelen per meldingstype configureerbaar.
- Dure-stroommelding boven €0,40/kWh.
- Zonneschermregeling op PV ≥ 3000 W gedurende 15 minuten in juni t/m september.
