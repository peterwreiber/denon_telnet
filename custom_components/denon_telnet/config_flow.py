"""Config flow for Denon Telnet."""
from __future__ import annotations

import asyncio

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST

from .client import PORT
from .const import DOMAIN


class DenonTelnetConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(user_input[CONF_HOST], PORT), 5
                )
                writer.close()
                await writer.wait_closed()
            except (OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                await asyncio.sleep(1)
                return self.async_create_entry(title="Denon Telnet", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST, default="192.168.10.101"): str}),
            errors=errors,
        )
