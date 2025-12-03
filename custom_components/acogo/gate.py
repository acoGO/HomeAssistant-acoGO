from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AcogoApiError, AcogoClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

GATE_UPDATE_INTERVAL = timedelta(seconds=30)


class AcogoGateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: AcogoClient, device_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"acogo_gate_{device_id}",
            update_interval=GATE_UPDATE_INTERVAL,
        )
        self._client = client
        self.device_id = device_id
        self._offline = False

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            details = await self._client.async_get_gate_details(self.device_id)
        except AcogoApiError as err:
            if err.status == 408:
                self._offline = True
                raise UpdateFailed("acoGO! gate is offline (408)") from err
            raise UpdateFailed(str(err)) from err

        self._offline = False
        return details or {}

    @property
    def is_offline(self) -> bool:
        return self._offline


async def async_get_or_create_gate_coordinator(
    hass: HomeAssistant, entry_id: str, client: AcogoClient, device_id: str
) -> AcogoGateCoordinator:
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if entry_data is None:
        raise UpdateFailed(f"Missing entry data for {entry_id}")

    coordinators: dict[str, AcogoGateCoordinator] = entry_data.setdefault(
        "gate_coordinators", {}
    )
    coordinator = coordinators.get(device_id)
    if coordinator is None:
        coordinator = AcogoGateCoordinator(hass, client, device_id)
        coordinators[device_id] = coordinator
        try:
            await coordinator.async_config_entry_first_refresh()
        except (UpdateFailed, ConfigEntryNotReady) as err:
            _LOGGER.warning("Initial gate refresh failed for %s: %s", device_id, err)
            coordinator._offline = True
            coordinator.async_set_updated_data({})

    return coordinator
