from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SUPPORTED_GATE_MODELS
from .api import AcogoClient
from . import AcogoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: AcogoCoordinator = data["coordinator"]
    client: AcogoClient = data["client"]

    entities: list[AcogoOpenGateButton] = []

    # Na start: zrób po jednym przycisku dla każdego urządzenia typu "gate"
    for dev in coordinator.devices:
        model = dev.get("model")
        if model in SUPPORTED_GATE_MODELS:
            entities.append(AcogoOpenGateButton(coordinator, client, dev))

    async_add_entities(entities)


class AcogoOpenGateButton(CoordinatorEntity[AcogoCoordinator], ButtonEntity):
    _attr_translation_key = "open_gate"  # możesz potem dodać tłumaczenia

    def __init__(self, coordinator: AcogoCoordinator, client: AcogoClient, device: dict) -> None:
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._dev_id = device.get("devId")

        self._attr_name = f"{device.get('name', 'acoGO gate')} – otwórz"
        self._attr_unique_id = f"{self._dev_id}_ez_open"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)},
            name=device.get("name", self._dev_id),
            manufacturer="ACO",
            model=device.get("model", "acoGO!"),
        )

    async def async_press(self) -> None:
        await self._client.async_open_gate(self._dev_id)
