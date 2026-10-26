"""Authenticated access to the persisted forecast archive."""

from http import HTTPStatus

from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.storage import Store

from .const import DOMAIN


class ForecastHistoryView(HomeAssistantView):
    """Read saved generations without fetching a new forecast."""

    url = f"/api/{DOMAIN}/forecast_history"
    name = f"api:{DOMAIN}:forecast_history"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    async def get(self, request):
        """Return the archive directly from Home Assistant storage."""
        # A fresh Store reads the saved file rather than a cached feed snapshot.
        store = Store(self.hass, 1, f"{DOMAIN}.forecast_history")
        try:
            snapshots = await store.async_load()
        except (OSError, ValueError):
            return self.json_message(
                "Unable to read stored forecast history.",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        return self.json({"data": snapshots if snapshots is not None else {}})
