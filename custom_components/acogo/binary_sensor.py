from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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

    entities: list[AcogoIoInputSensor] = []

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

        for in_number in range(1, 5):
            if not _port_defined(details, "in", in_number):
                continue

            in_name = details.get(f"in{in_number}Name") or f"Input {in_number}"
            entities.append(
                AcogoIoInputSensor(
                    io_coordinator, device, device_name, in_number, in_name
                )
            )

    async_add_entities(entities)


class AcogoIoInputSensor(CoordinatorEntity[AcogoIoCoordinator], BinarySensorEntity):
    _attr_icon = "mdi:binary-input"

    def __init__(
        self,
        coordinator: AcogoIoCoordinator,
        device: dict[str, Any],
        device_name: str,
        in_number: int,
        in_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._dev_id = device.get("devId")
        self._in_number = in_number

        self._attr_name = f"{device_name} - {in_name}"
        self._attr_unique_id = f"{self._dev_id}_in_{in_number}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)},
            name=device_name,
            manufacturer="ACO",
            model=device.get("model", "acoGO! I/O"),
            serial_number=self._dev_id,
        )

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        inputs = data.get("inputs") or {}
        return inputs.get(f"in{self._in_number}")

    @property
    def available(self) -> bool:
        return not self.coordinator.is_offline and super().available


def _port_defined(details: dict[str, Any], prefix: str, number: int) -> bool:
    if not details:
        return True
    name_key = f"{prefix}{number}Name"
    time_key = f"{prefix}{number}Time"
    return name_key in details or time_key in details


def _get_device_name(device: dict[str, Any], details: dict[str, Any]) -> str:
    return (
        device.get("name")
        or (details or {}).get("deviceName")
        or (details or {}).get("name")
        or device.get("devId", "")
    )
