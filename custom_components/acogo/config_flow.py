from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AcogoApiError, AcogoClient
from .const import CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _async_validate_token(hass: HomeAssistant, token: str) -> dict:
    session = async_get_clientsession(hass)
    client = AcogoClient(session, token)
    devices = await client.async_get_devices()
    return {"devices": devices}


class AcogoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]

            try:
                data = await _async_validate_token(self.hass, token)
            except AcogoApiError:
                errors["base"] = "invalid_auth"
            else:
                devices = data["devices"]
                # Include the discovered device count in the entry title.
                title = f"acoGO! ({len(devices)} devices)"
                return self.async_create_entry(
                    title=title,
                    data={CONF_TOKEN: token, "devices": devices},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
