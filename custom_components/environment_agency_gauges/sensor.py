"""Support for Environment Agency gauge sensors."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength

try:
    from homeassistant.const import UnitOfPrecipitation
except ImportError:
    UnitOfPrecipitation = None
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EafmConfigEntry, EafmCoordinator

UNIT_MAPPING = {
    "http://qudt.org/1.1/vocab/unit#Millimeter": (
        UnitOfPrecipitation.MILLIMETERS if UnitOfPrecipitation is not None else "mm"
    ),
    "http://qudt.org/1.1/vocab/unit#Meter": UnitOfLength.METERS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EafmConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Environment Agency sensors."""
    coordinator = config_entry.runtime_data
    created_entities: set[str] = set()

    @callback
    def _async_create_new_entities():
        """Create new entities."""
        if not coordinator.last_update_success:
            return
        measures: dict[str, dict[str, Any]] = coordinator.data["measures"]
        entities: list[Measurement] = []
        # Look to see if payload contains new measures
        for key, data in measures.items():
            if key in created_entities:
                continue

            if "latestReading" not in data:
                # Don't create a sensor entity for a gauge that isn't available
                continue

            entities.append(Measurement(coordinator, key))
            created_entities.add(key)

        async_add_entities(entities)

    _async_create_new_entities()

    # Subscribe to the coordinator to create new entities
    # when the coordinator updates
    config_entry.async_on_unload(
        coordinator.async_add_listener(_async_create_new_entities)
    )


class Measurement(CoordinatorEntity, SensorEntity):
    """A gauge at an Environment Agency station."""

    _attr_attribution = (
        "This uses Environment Agency flood-monitoring data "
        "from the real-time data API"
    )
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator: EafmCoordinator, key: str) -> None:
        """Initialise the gauge with a data instance and station."""
        super().__init__(coordinator)
        self.key = key
        self._attr_unique_id = key
        self._attr_name = f"{self.parameter_name} {self.qualifier}"

    @property
    def measure(self):
        """Return the measure data for this entity."""
        return self.coordinator.data["measures"][self.key]

    @property
    def station_name(self):
        """Return the station name for the measure."""
        return self.coordinator.data["label"]

    @property
    def station_id(self):
        """Return the station id for the measure."""
        return self.measure["stationReference"]

    @property
    def qualifier(self):
        """Return the qualifier for the station."""
        return self.measure["qualifier"]

    @property
    def parameter_name(self):
        """Return the parameter name for the station."""
        return self.measure["parameterName"]

    @property
    def device_class(self):
        """Return the sensor device class."""
        if self.measure.get("parameter") == "rainfall":
            return SensorDeviceClass.PRECIPITATION
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self.station_id)},
            manufacturer="https://environment.data.gov.uk/",
            model=self.parameter_name,
            name=f"{self.station_name} - {self.station_id}",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        # If sensor goes offline it will no longer contain a reading
        if "latestReading" not in self.measure:
            return False

        # Sometimes lastestReading key is present but actually
        # a URL rather than a piece of data.
        # This is usually because the sensor has been archived
        if not isinstance(self.measure["latestReading"], dict):
            return False

        return True

    @property
    def native_unit_of_measurement(self):
        """Return units for the sensor."""
        measure = self.measure
        if "unit" not in measure:
            return None
        return UNIT_MAPPING.get(measure["unit"], measure["unitName"])

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.measure["latestReading"]["value"]

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        latest_reading = self.measure["latestReading"]
        if not isinstance(latest_reading, dict):
            latest_reading = {}

        return {
            "station_reference": self.station_id,
            "station_label": self.station_name,
            "measure_id": self.measure.get("@id"),
            "notation": self.measure.get("notation"),
            "parameter": self.measure.get("parameter"),
            "parameter_name": self.parameter_name,
            "qualifier": self.qualifier,
            "period_seconds": self.measure.get("period"),
            "latest_reading_id": latest_reading.get("@id"),
            "latest_reading_date": latest_reading.get("date"),
            "latest_reading_datetime": latest_reading.get("dateTime"),
        }
