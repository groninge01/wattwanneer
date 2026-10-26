"""WattWanneer public forecast integration."""

from homeassistant.const import Platform
from homeassistant.helpers.event import async_track_time_change

from .api import ForecastHistoryView
from .coordinator import WattWanneerCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass, config):
    """Register the archive API once, independently of feed refreshes."""
    hass.http.register_view(ForecastHistoryView(hass))
    return True


async def async_setup_entry(hass, entry):
    coordinator = WattWanneerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async def async_scheduled_refresh(now):
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_track_time_change(
            hass, async_scheduled_refresh, hour=[6, 18], minute=0, second=0
        )
    )
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
