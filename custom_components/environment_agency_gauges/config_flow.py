"""Config flow for Environment Agency gauges."""

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import get_station
from .const import CONF_STATION_REFERENCE, DOMAIN


def _last_value(value: Any) -> Any:
    """Return the last value if the API gives a list."""
    if isinstance(value, list):
        return value[-1]
    return value


async def _validate_station(
    session: aiohttp.ClientSession, station_reference: str
) -> dict[str, Any]:
    """Fetch a station by reference and return its data."""
    return await get_station(session, station_reference)


class EnvironmentAgencyGaugesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an Environment Agency gauges config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        """Handle a flow start."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_reference = user_input[CONF_STATION_REFERENCE].strip()
            session = async_get_clientsession(hass=self.hass)

            try:
                station = await _validate_station(session, station_reference)
            except TimeoutError:
                errors["base"] = "timeout"
            except aiohttp.ClientResponseError as err:
                if err.status == 404:
                    errors[CONF_STATION_REFERENCE] = "station_not_found"
                else:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    station["stationReference"], raise_on_progress=False
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=(
                        f"{_last_value(station['label'])} - "
                        f"{station['stationReference']}"
                    ),
                    data={CONF_STATION_REFERENCE: station["stationReference"]},
                )

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {vol.Required(CONF_STATION_REFERENCE): str}
            ),
        )
