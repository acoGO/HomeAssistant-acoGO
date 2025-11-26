from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_TOKEN, DEFAULT_POLL_INTERVAL
from .api import AcogoClient, AcogoApiError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["button"]  # na start tylko przyciski


class AcogoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: AcogoClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="acogo",
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
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

    await coordinator.async_config_entry_first_refresh()

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