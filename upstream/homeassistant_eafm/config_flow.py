"""Config flow to configure flood monitoring gauges."""

from typing import Any, override

from aioeafm import get_stations
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN


def _last_value(value: Any) -> Any:
    """Return the last value if the API gives a list."""
    if isinstance(value, list):
        return value[-1]
    return value


def _station_label(station: dict[str, Any]) -> str:
    """Return a stable label for a station option."""
    label = _last_value(station["label"])
    station_reference = station["stationReference"]
    rlo_id = _last_value(station.get("RLOIid"))

    if rlo_id is None:
        return f"{label} - {station_reference}"

    return f"{label} - {rlo_id}"


def _station_is_configurable(station: dict[str, Any]) -> bool:
    """Return True if a station should be shown in the picker."""
    status = station.get("status")
    if status is None:
        return True

    statuses = status if isinstance(status, list) else [status]
    return not any(
        str(item).endswith(("statusClosed", "statusSuspended")) for item in statuses
    )


class UKFloodsFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a UK Environment Agency flood monitoring config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Handle a UK Floods config flow."""
        self.stations: dict[str, str] = {}

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow start."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_station = self.stations[user_input["station"]]
            await self.async_set_unique_id(selected_station, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input["station"],
                data={"station": selected_station},
            )

        session = async_get_clientsession(hass=self.hass)
        # Most non-level stations do not expose status/RLOIid, so aioeafm's
        # default status=Active filter excludes them from the picker.
        stations = await get_stations(session, status=None)

        self.stations = {}
        seen_station_references: set[str] = set()
        for station in stations:
            if not _station_is_configurable(station):
                continue

            station_reference = station["stationReference"]
            if station_reference in seen_station_references:
                continue

            self.stations[_station_label(station)] = station_reference
            seen_station_references.add(station_reference)

        if not self.stations:
            return self.async_abort(reason="no_stations")

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {vol.Required("station"): vol.In(sorted(self.stations))}
            ),
        )
