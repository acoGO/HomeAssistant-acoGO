from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AcogoApiError, AcogoClient
from .const import CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["button", "cover", "binary_sensor"]


class AcogoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: AcogoClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="acogo",
        )
        self.client = client
        self.devices = []

    async def _async_update_data(self):
        try:
            self.devices = await self.client.async_get_devices()
            return self.devices
        except AcogoApiError as err:
            raise UpdateFailed(str(err)) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    token = entry.data[CONF_TOKEN]

    client = AcogoClient(session, token)
    coordinator = AcogoCoordinator(hass, client)

    # Nie wykonujemy automatycznych odświeżeń; korzystamy z listy urządzeń
    # zapisanej podczas rejestracji.
    coordinator.devices = entry.data.get("devices", [])
    coordinator.async_set_updated_data(coordinator.devices)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
