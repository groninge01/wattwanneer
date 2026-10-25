"""UI setup for the public feed; no API key required."""

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, NAME
from .coordinator import WattWanneerCoordinator


class WattWanneerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            coordinator = WattWanneerCoordinator(self.hass)
            await coordinator.async_refresh()
            if coordinator.last_update_success:
                return self.async_create_entry(title=NAME, data={})
            errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}), errors=errors)
