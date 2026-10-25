"""Fetch the public feed for all entities."""

import asyncio
import logging

from aiohttp import ClientError
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, FEED_URL, NAME
from .forecast import parse_forecast
from .history import ForecastHistory

_LOGGER = logging.getLogger(__name__)


class WattWanneerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry=None):
        super().__init__(
            hass,
            _LOGGER,
            name=NAME,
            config_entry=entry,
        )
        self.session = async_get_clientsession(hass)
        self.history = (
            ForecastHistory(Store(hass, 1, f"{DOMAIN}.forecast_history", atomic_writes=True))
            if entry is not None
            else None
        )

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(30):
                async with self.session.get(FEED_URL) as response:
                    response.raise_for_status()
                    payload = await response.json()
            rows = parse_forecast(payload)
            if self.history is not None:
                await self.history.async_archive(rows)
            return rows
        except (ClientError, TimeoutError, ValueError, TypeError, OSError, HomeAssistantError) as err:
            raise UpdateFailed(f"Unable to read or archive WattWanneer forecast: {err}") from err
