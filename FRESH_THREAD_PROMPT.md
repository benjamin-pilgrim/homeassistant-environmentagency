# Fresh Codex Thread Prompt

Continue this investigation in `/home/ben/src/personal/homeassistant-environmentagency`.

Goal:

Investigate Home Assistant's built-in `eafm` integration and why it exposes Environment Agency river/sea-level gauges but not rainfall gauges. Work out whether the fix belongs in Home Assistant core, the `aioeafm` library, or a separate custom integration/rest sensor package.

Context:

- User wants nearby Environment Agency rainfall gauges in Home Assistant.
- Built-in HA integration: `homeassistant/components/eafm`
- Manifest dependency: `aioeafm==0.1.2`
- Upstream HA source is mirrored in `upstream/homeassistant_eafm/`.
- GOV.UK exposes separate UI groups:
  - River/sea: `https://check-for-flooding.service.gov.uk/river-and-sea-levels/colchester-essex?group=river`
  - Rainfall: `https://check-for-flooding.service.gov.uk/river-and-sea-levels/colchester-essex?group=rainfall`
- The Environment Agency API definitely has rainfall measures near Highwoods / Colchester.

Nearby rainfall gauges found:

```text
E37151  ~3.6 km  rainfall, 15 min tipping bucket
E22683  ~6.8 km  rainfall
E24930  ~12.3 km rainfall
E24874  ~12.8 km rainfall
E44121  ~13.1 km rainfall
E24901  ~13.7 km rainfall
E24913  ~14.0 km rainfall
E24863  ~15.0 km rainfall
```

Example measure:

```text
https://environment.data.gov.uk/flood-monitoring/id/measures/E37151-rainfall-tipping_bucket_raingauge-t-15_min-mm
```

Example latest reading:

```text
https://environment.data.gov.uk/flood-monitoring/id/measures/E37151-rainfall-tipping_bucket_raingauge-t-15_min-mm/readings?latest
```

First tasks:

1. Inspect/download `aioeafm==0.1.2`.
2. Identify what endpoints `get_stations()` and `get_station()` use.
3. Test rainfall station `E37151` against `aioeafm.get_station`.
4. Determine why rainfall gauges do not appear in HA config flow.
5. Propose or implement a minimal patch/prototype.

Important likely clue:

`upstream/homeassistant_eafm/config_flow.py` assumes each station from `get_stations()` has `label`, `RLOIid`, and `stationReference`. Rainfall stations may not have `RLOIid`, or may be excluded from the library's station list. `sensor.py` itself appears generic enough to expose rainfall if the station data includes a measure with `latestReading`.

