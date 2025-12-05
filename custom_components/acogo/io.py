from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AcogoApiError, AcogoClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

IO_UPDATE_INTERVAL = timedelta(seconds=5)


class AcogoIoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: AcogoClient, device_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"acogo_io_{device_id}",
            update_interval=IO_UPDATE_INTERVAL,
        )
        self._client = client
        self.device_id = device_id
        self.details: dict[str, Any] | None = None
        self._offline = False

    async def async_get_details(self) -> dict[str, Any]:
        if self.details is None:
            try:
                self.details = await self._client.async_get_io_details(self.device_id)
            except AcogoApiError as err:
                _LOGGER.warning("Could not fetch IO details for %s: %s", self.device_id, err)
                self.details = {}
        return self.details

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            state = await self._client.async_get_io_state(self.device_id)
        except AcogoApiError as err:
            if err.status == 408:
                self._offline = True
                _LOGGER.debug("acoGO! I/O %s offline (408)", self.device_id)
                return self._offline_payload()
            raise UpdateFailed(str(err)) from err

        self._offline = False
        return self._format_state(state)

    def _format_state(self, state: dict[str, Any], offline: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if isinstance(state, dict):
            payload = state.get("message") or state

        return {
            "inputs": payload.get("inputs") or {},
            "outputs": payload.get("outputs") or {},
            "_offline": offline,
        }

    def _offline_payload(self) -> dict[str, Any]:
        return self._format_state({}, offline=True)

    async def async_refresh_state(self) -> None:
        try:
            state = await self._client.async_get_io_state(self.device_id)
        except AcogoApiError as err:
            if err.status == 408:
                self._offline = True
                _LOGGER.debug("acoGO! I/O %s offline (408)", self.device_id)
                self.async_set_updated_data(self._offline_payload())
                return
            raise

        self._offline = False
        self.async_set_updated_data(self._format_state(state))

    @property
    def is_offline(self) -> bool:
        return self._offline


async def async_get_or_create_io_coordinator(
    hass: HomeAssistant, entry_id: str, client: AcogoClient, device_id: str
) -> AcogoIoCoordinator:
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if entry_data is None:
        raise UpdateFailed(f"Missing entry data for {entry_id}")

    coordinators: dict[str, AcogoIoCoordinator] = entry_data.setdefault(
        "io_coordinators", {}
    )
    coordinator = coordinators.get(device_id)
    if coordinator is None:
        coordinator = AcogoIoCoordinator(hass, client, device_id)
        coordinators[device_id] = coordinator
        try:
            try:
                await coordinator.async_get_details()
            except AcogoApiError as err:
                _LOGGER.warning("Initial IO details fetch failed for %s: %s", device_id, err)
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.warning("Initial IO refresh failed for %s: %s", device_id, err)
            coordinator._offline = True
            coordinator.async_set_updated_data({"inputs": {}, "outputs": {}, "_offline": True})

    return coordinator
