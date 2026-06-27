# Environment Agency Gauges

Home Assistant custom integration for Environment Agency flood-monitoring gauges.

This integration is intentionally station-reference based. Add a station such as
`E37151`, and Home Assistant will create sensors for every measure returned by
that station, including rainfall, level, flow, wind, temperature, velocity, and
area measures when the Environment Agency API provides a latest reading.

## Installation

### HACS custom repository

1. In HACS, add this repository as a custom repository.
2. Select category `Integration`.
3. Install `Environment Agency Gauges`.
4. Restart Home Assistant.
5. Add the integration from **Settings > Devices & services**.

### Manual

Copy `custom_components/environment_agency_gauges` into your Home Assistant
`custom_components` directory, then restart Home Assistant.

## Configuration

Add a station by Environment Agency station reference.

Example rainfall station:

```text
E37151
```

The integration validates the reference using:

```text
https://environment.data.gov.uk/flood-monitoring/id/stations/{station_reference}
```

The integration uses a small local client for the Environment Agency API and
does not depend on `aioeafm`.

## Sensors

The integration creates one sensor per station measure that has a latest reading.

Rainfall sensors use Home Assistant's `precipitation` device class and report in
millimeters when the Environment Agency measure uses `mm`.

Each sensor exposes these attributes:

| Attribute | Description |
|---|---|
| `station_reference` | Environment Agency station reference, for example `E37151`. |
| `station_label` | Station label returned by the API. |
| `measure_id` | Full Environment Agency measure URL. |
| `notation` | Environment Agency measure notation. |
| `parameter` | Machine-readable parameter, for example `rainfall` or `level`. |
| `parameter_name` | Human-readable parameter, for example `Rainfall`. |
| `qualifier` | Measure qualifier, for example `Tipping Bucket Raingauge`. |
| `period_seconds` | Measurement period in seconds, for example `900`. |
| `latest_reading_id` | Full Environment Agency latest reading URL. |
| `latest_reading_date` | Latest reading date. |
| `latest_reading_datetime` | Latest reading timestamp. |

## Notes

- The integration does not use `RLOIid`.
- The config flow stores only the Environment Agency `stationReference`.
- Sensors are created only for measures that include `latestReading`.
- Data is polled every 15 minutes.

See `INVESTIGATION.md` for the original analysis of why Home Assistant's built-in
`eafm` integration misses many rainfall gauges.
