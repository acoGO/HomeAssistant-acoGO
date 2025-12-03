from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AcogoCoordinator
from .api import AcogoClient
from .const import DOMAIN
from .io import AcogoIoCoordinator, async_get_or_create_io_coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: AcogoCoordinator = data["coordinator"]
    client: AcogoClient = data["client"]

    entities: list[AcogoIoOutputCover] = []

    for device in coordinator.devices:
        if device.get("model") != "acoGO! I/O":
            continue

        try:
            io_coordinator = await async_get_or_create_io_coordinator(
                hass, entry.entry_id, client, device["devId"]
            )
        except Exception:
            continue

        details = await io_coordinator.async_get_details()
        device_name = _get_device_name(device, details)

        for out_number in range(1, 5):
            if not _port_defined(details, "out", out_number):
                continue

            out_name = details.get(f"out{out_number}Name") or f"Wyjście {out_number}"
            entities.append(
                AcogoIoOutputCover(
                    io_coordinator, client, device, device_name, out_number, out_name
                )
            )

    async_add_entities(entities)


class AcogoIoOutputCover(CoordinatorEntity[AcogoIoCoordinator], CoverEntity):
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
    _attr_device_class = CoverDeviceClass.GARAGE

    def __init__(
        self,
        coordinator: AcogoIoCoordinator,
        client: AcogoClient,
        device: dict[str, Any],
        device_name: str,
        out_number: int,
        out_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._dev_id = device.get("devId")
        self._out_number = out_number

        self._attr_name = f"{device_name} - {out_name}"
        self._attr_unique_id = f"{self._dev_id}_out{out_number}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)},
            name=device_name,
            manufacturer="ACO",
            model=device.get("model", "acoGO! I/O"),
        )

    @property
    def is_closed(self) -> bool | None:
        state = self._current_state
        if state is None:
            return None
        return not state

    @property
    def available(self) -> bool:
        return not self.coordinator.is_offline and super().available

    @property
    def _current_state(self) -> bool | None:
        data = self.coordinator.data or {}
        outputs = data.get("outputs") or {}
        return outputs.get(f"out{self._out_number}")

    async def async_open_cover(self, **kwargs) -> None:
        if self.coordinator.is_offline:
            raise HomeAssistantError("acoGO! I/O device is offline.")
        await self._client.async_set_io_output(self._dev_id, self._out_number, True)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs) -> None:
        if self.coordinator.is_offline:
            raise HomeAssistantError("acoGO! I/O device is offline.")
        await self._client.async_set_io_output(self._dev_id, self._out_number, False)
        await self.coordinator.async_request_refresh()


def _port_defined(details: dict[str, Any], prefix: str, number: int) -> bool:
    if not details:
        return True
    name_key = f"{prefix}{number}Name"
    time_key = f"{prefix}{number}Time"
    return name_key in details or time_key in details


def _get_device_name(device: dict[str, Any], details: dict[str, Any]) -> str:
    return (
        device.get("name")
    )
