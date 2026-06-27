# Investigation: Environment Agency rainfall gauges in HA `eafm`

## Finding

Home Assistant's `eafm` integration can already fetch and expose a rainfall station if the config entry contains that station reference. The missing piece is the config flow station picker.

The built-in integration depends on `aioeafm==0.1.2`.

`aioeafm.get_station(session, "E37151")` calls:

```text
http://environment.data.gov.uk/flood-monitoring/id/stations/E37151
```

That endpoint returns a valid station with a rainfall measure, `unitName: "mm"`, and a `latestReading`.

`aioeafm.get_stations(session)` calls:

```text
http://environment.data.gov.uk/flood-monitoring/id/stations?status=Active
```

That default `status=Active` filter excludes nearby rainfall-only stations such as `E37151`, because those station list records generally do not expose a `status` field.

Measured endpoint results on 2026-06-27:

| Query | Count | Includes `E37151` |
|---|---:|---|
| `/id/stations` | 5498 | yes |
| `/id/stations?parameter=rainfall` | 1042 | yes |
| `/id/stations?parameter=rainfall&status=Active` | 3 | no |

There is a second Home Assistant issue: `config_flow.py` assumes every station has `RLOIid`. Rainfall-only stations generally do not, so even if they are fetched they need to be labelled with `stationReference` instead.

## Prototype Patch

The mirrored integration in `upstream/homeassistant_eafm/config_flow.py` now:

- Fetches the broad station list with `get_stations(session, status=None)`.
- Excludes stations explicitly marked closed or suspended.
- Deduplicates by `stationReference`.
- Builds labels using `RLOIid` when present, otherwise `stationReference`.

This keeps the coordinator and sensor fetch path unchanged.

This broader approach includes the EA API measure parameters seen in the station
list: `level`, `flow`, `rainfall`, `wind`, `temperature`, `velocity`, and
`area`. The API returned no stations for `parameter=groundwater` during this
investigation.

## Where the fix belongs

The minimal product fix belongs in Home Assistant core's `eafm` config flow. `aioeafm` already supports passing `status=None` to omit the status filter.

A small `aioeafm` improvement would still be reasonable: document `status=None`, or add an explicit convenience for rainfall stations. But Home Assistant does not need a library release to prove the behavior.

## Follow-up for a core-quality patch

- Add config-flow tests for a station without `RLOIid`.
- Add config-flow tests proving no-status stations, including rainfall stations, are included.
- Add config-flow tests proving closed/suspended stations are excluded.
- Consider sensor metadata for rainfall:
  - device class: precipitation, if compatible with current HA sensor constants
  - unit: millimeters
  - extra state attributes for period/dateTime, if desired
