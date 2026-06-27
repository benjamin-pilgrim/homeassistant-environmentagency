"""Environment Agency gauges integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import EafmConfigEntry, EafmCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: EafmConfigEntry) -> bool:
    """Set up Environment Agency sensors for this config entry."""
    coordinator = EafmCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EafmConfigEntry) -> bool:
    """Unload Environment Agency sensors."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
