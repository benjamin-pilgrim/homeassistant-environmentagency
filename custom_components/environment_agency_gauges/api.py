"""Client helpers for the Environment Agency flood-monitoring API."""

from typing import Any
from urllib.parse import quote

import aiohttp

BASE_URL = "https://environment.data.gov.uk/flood-monitoring"


async def get_station(
    session: aiohttp.ClientSession, station_reference: str
) -> dict[str, Any]:
    """Return all data for a station reference."""
    encoded_station_reference = quote(station_reference, safe="")
    response = await session.get(
        f"{BASE_URL}/id/stations/{encoded_station_reference}",
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=30),
    )
    results = await response.json()

    return results["items"]
