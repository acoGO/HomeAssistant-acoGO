from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, SUPPORTED_GATE_MODELS
from .api import AcogoClient
from .gate import AcogoGateCoordinator, async_get_or_create_gate_coordinator
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
            try:
                gate_coordinator = await async_get_or_create_gate_coordinator(
                    hass, entry.entry_id, client, dev["devId"]
                )
            except Exception:
                continue
            entities.append(AcogoOpenGateButton(gate_coordinator, client, dev))

    async_add_entities(entities)


class AcogoOpenGateButton(CoordinatorEntity[AcogoGateCoordinator], ButtonEntity):
    _attr_translation_key = "open_gate"  # możesz potem dodać tłumaczenia

    def __init__(
        self,
        coordinator: AcogoGateCoordinator,
        client: AcogoClient,
        device: dict,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._dev_id = device.get("devId")

        device_name = device.get("name")
        self._attr_name = f"{device_name} – otwórz"
        self._attr_unique_id = f"{self._dev_id}_ez_open"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)},
            name=device_name,
            manufacturer="ACO",
            model=device.get("model", "acoGO!"),
            serial_number=self._dev_id,
        )
        object_id = slugify(f"{self._dev_id}_ez_open")
        self._attr_entity_id = f"button.{object_id}"

    @property
    def available(self) -> bool:
        return not self.coordinator.is_offline and super().available

    async def async_press(self) -> None:
        if self.coordinator.is_offline:
            raise HomeAssistantError("acoGO! gate is offline.")
        await self._client.async_open_gate(self._dev_id)
