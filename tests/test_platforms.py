from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.acogo import binary_sensor, button, cover
from custom_components.acogo.binary_sensor import AcogoIoInputSensor
from custom_components.acogo.button import AcogoOpenGateButton
from custom_components.acogo.const import DOMAIN
from custom_components.acogo.cover import AcogoIoOutputCover


class DummyCoordinator:
    def __init__(self, data=None, offline=False):
        self.data = data or {}
        self.is_offline = offline
        self.last_update_success = True
        self.refreshed = 0

    def async_add_listener(self, update_callback):
        return lambda: None

    async def async_request_refresh(self):
        return None

    async def async_refresh_state(self):
        self.refreshed += 1


class DummyClient:
    def __init__(self):
        self.calls = []

    async def async_open_gate(self, dev_id):
        self.calls.append(("open_gate", dev_id))

    async def async_set_io_output(self, dev_id, out_number, state):
        self.calls.append(("set_output", dev_id, out_number, state))


@pytest.mark.asyncio
async def test_button_setup_creates_gate_entity(hass, config_entry, monkeypatch):
    client = DummyClient()
    coordinator = SimpleNamespace(
        devices=[{"devId": "gate-1", "model": "acoGO! P", "name": "Gate"}]
    )
    hass.data[DOMAIN] = {
        config_entry.entry_id: {"coordinator": coordinator, "client": client}
    }

    gate_coordinator = DummyCoordinator({})

    async def fake_get_or_create_gate_coordinator(*args, **kwargs):
        return gate_coordinator

    monkeypatch.setattr(
        button,
        "async_get_or_create_gate_coordinator",
        fake_get_or_create_gate_coordinator,
    )

    entities = []
    await button.async_setup_entry(
        hass, config_entry, lambda ents: entities.extend(ents)
    )

    assert len(entities) == 1
    entity: AcogoOpenGateButton = entities[0]
    assert entity.available

    await entity.async_press()
    assert client.calls == [("open_gate", "gate-1")]


@pytest.mark.asyncio
async def test_gate_button_unavailable_when_offline():
    coordinator = DummyCoordinator({}, offline=True)
    client = DummyClient()
    entity = AcogoOpenGateButton(
        coordinator, client, {"devId": "gate-1", "name": "Gate"}
    )

    assert not entity.available
    with pytest.raises(HomeAssistantError):
        await entity.async_press()


@pytest.mark.asyncio
async def test_cover_entity_open_and_close(hass):
    coordinator = DummyCoordinator({"outputs": {"out1": False}})
    client = DummyClient()
    device = {"devId": "io-1", "name": "Garage", "model": "acoGO! I/O"}
    entity = AcogoIoOutputCover(
        coordinator, client, device, "Garage", 1, "Output 1", 0
    )

    assert entity.is_closed

    await entity.async_open_cover()
    await entity.async_close_cover()

    assert client.calls == [
        ("set_output", "io-1", 1, True),
        ("set_output", "io-1", 1, False),
    ]
    assert coordinator.refreshed == 2


@pytest.mark.asyncio
async def test_cover_entity_with_timed_output_rejects_close():
    coordinator = DummyCoordinator({"outputs": {"out1": True}})
    client = DummyClient()
    device = {"devId": "io-1", "name": "Garage", "model": "acoGO! I/O"}
    entity = AcogoIoOutputCover(
        coordinator, client, device, "Garage", 1, "Timed", 5
    )

    assert entity.available
    assert entity.is_closed is False
    await entity.async_open_cover()
    with pytest.raises(HomeAssistantError):
        await entity.async_close_cover()


@pytest.mark.asyncio
async def test_cover_setup_creates_entities(hass, config_entry, monkeypatch):
    client = DummyClient()
    coordinator = SimpleNamespace(
        devices=[{"devId": "io-1", "model": "acoGO! I/O", "name": "IO Device"}]
    )
    hass.data[DOMAIN] = {
        config_entry.entry_id: {"coordinator": coordinator, "client": client}
    }

    io_details = {"out1Name": "Relay 1", "out2Time": 5}
    io_coordinator = DummyCoordinator({"outputs": {"out1": True, "out2": False}})

    async def fake_get_details():
        return io_details

    io_coordinator.async_get_details = fake_get_details

    async def fake_get_or_create_io_coordinator(*args, **kwargs):
        return io_coordinator

    monkeypatch.setattr(
        cover,
        "async_get_or_create_io_coordinator",
        fake_get_or_create_io_coordinator,
    )

    entities = []
    await cover.async_setup_entry(
        hass, config_entry, lambda ents: entities.extend(ents)
    )

    assert len(entities) == 2
    names = sorted(e.name for e in entities)
    assert names == sorted(["Relay 1", "Output 2"])


@pytest.mark.asyncio
async def test_binary_sensor_setup_creates_entities(hass, config_entry, monkeypatch):
    client = DummyClient()
    coordinator = SimpleNamespace(
        devices=[{"devId": "io-1", "model": "acoGO! I/O", "name": "IO Device"}]
    )
    hass.data[DOMAIN] = {
        config_entry.entry_id: {"coordinator": coordinator, "client": client}
    }

    io_details = {"in1Name": "Sensor 1"}
    io_coordinator = DummyCoordinator({"inputs": {"in1": True}})

    async def fake_get_details():
        return io_details

    io_coordinator.async_get_details = fake_get_details

    async def fake_get_or_create_io_coordinator(*args, **kwargs):
        return io_coordinator

    monkeypatch.setattr(
        binary_sensor,
        "async_get_or_create_io_coordinator",
        fake_get_or_create_io_coordinator,
    )

    entities = []
    await binary_sensor.async_setup_entry(
        hass, config_entry, lambda ents: entities.extend(ents)
    )

    assert len(entities) == 1
    entity: AcogoIoInputSensor = entities[0]
    assert entity.is_on is True
    assert entity.available


def test_input_sensor_unavailable_when_offline():
    coordinator = DummyCoordinator({"inputs": {"in1": False}}, offline=True)
    entity = AcogoIoInputSensor(
        coordinator, {"devId": "io-1"}, "IO", 1, "Input 1"
    )

    assert not entity.available
    assert entity.is_on is False
