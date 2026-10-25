"""Fetch the public feed for all entities."""

import asyncio
import logging

from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import FEED_URL, NAME
from .forecast import parse_forecast

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

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(30):
                async with self.session.get(FEED_URL) as response:
                    response.raise_for_status()
                    payload = await response.json()
            return parse_forecast(payload)
        except (ClientError, TimeoutError, ValueError, TypeError) as err:
            raise UpdateFailed(f"Unable to read WattWanneer forecast: {err}") from err
