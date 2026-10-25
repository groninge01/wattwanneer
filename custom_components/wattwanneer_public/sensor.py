"""Price sensors and the full public forecast."""

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, FEED_URL, NAME
from .forecast import daily_rows, select_hour

KINDS = {
    "current_price": "Current price",
    "next_hour_price": "Next hour price",
    "today_average": "Today average",
    "today_minimum": "Today minimum",
    "today_maximum": "Today maximum",
    "tomorrow_average": "Tomorrow average",
    "forecast": "Forecast average",
}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        WattWanneerSensor(entry.runtime_data, key, name) for key, name in KINDS.items()
    )


class WattWanneerSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_icon = "mdi:currency-eur"
    _attr_suggested_display_precision = 5
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name=NAME,
            manufacturer="WattWanneer",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_utc_time_change(self.hass, self._clock_tick, minute=0, second=0)
        )

    @callback
    def _clock_tick(self, now):
        self.async_write_ha_state()

    def _rows(self):
        rows = self.coordinator.data or []
        now = dt_util.utcnow()
        if self.key in ("current_price", "next_hour_price"):
            row = select_hour(rows, now, int(self.key == "next_hour_price"))
            return [row] if row else []
        if self.key == "forecast":
            return rows
        return daily_rows(rows, now, int(self.key == "tomorrow_average"))

    @property
    def available(self):
        return super().available and bool(self._rows())

    @property
    def native_value(self):
        prices = [row["price_eur_kwh"] for row in self._rows()]
        if not prices:
            return None
        if self.key in ("current_price", "next_hour_price"):
            return prices[0]
        if self.key.endswith("minimum"):
            return min(prices)
        if self.key.endswith("maximum"):
            return max(prices)
        return sum(prices) / len(prices)

    @property
    def extra_state_attributes(self):
        rows = self._rows()
        attrs = {
            "attribution": "Data provided by WattWanneer",
            "feed_url": FEED_URL,
            "timezone": "Europe/Amsterdam",
        }
        if rows:
            attrs["generated_at"] = rows[0].get("generated_at")
        if self.key in ("current_price", "next_hour_price") and rows:
            attrs.update({"datetime": rows[0]["datetime"], "source": rows[0].get("source")})
        if self.key == "forecast":
            attrs["forecast"] = self.coordinator.data
            attrs["hours"] = len(rows)
        return attrs
