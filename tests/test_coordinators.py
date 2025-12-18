from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.acogo.api import AcogoApiError
from custom_components.acogo.const import DOMAIN
from custom_components.acogo.gate import (
    AcogoGateCoordinator,
    async_get_or_create_gate_coordinator,
)
from custom_components.acogo.io import (
    AcogoIoCoordinator,
    async_get_or_create_io_coordinator,
)


class DummyClient:
    def __init__(
        self,
        *,
        gate_payload=None,
        io_state=None,
        io_details=None,
        gate_error=None,
        io_error=None,
    ):
        self.gate_payload = gate_payload or {}
        self.io_state = io_state or {}
        self.io_details = io_details or {}
        self.gate_error = gate_error
        self.io_error = io_error
        self.calls = []

    async def async_get_gate_details(self, device_id: str):
        self.calls.append(("gate_details", device_id))
        if self.gate_error:
            raise self.gate_error
        return self.gate_payload

    async def async_get_io_state(self, device_id: str):
        self.calls.append(("io_state", device_id))
        if self.io_error:
            raise self.io_error
        return self.io_state

    async def async_get_io_details(self, device_id: str):
        self.calls.append(("io_details", device_id))
        if self.io_error:
            raise self.io_error
        return self.io_details


@pytest.mark.asyncio
async def test_gate_coordinator_marks_offline_on_timeout(hass):
    client = DummyClient(gate_error=AcogoApiError("offline", status=408))
    coordinator = AcogoGateCoordinator(hass, client, "gate-1")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.is_offline


@pytest.mark.asyncio
async def test_gate_coordinator_returns_payload(hass):
    payload = {"status": "ok"}
    client = DummyClient(gate_payload=payload)
    coordinator = AcogoGateCoordinator(hass, client, "gate-1")

    result = await coordinator._async_update_data()

    assert result == payload
    assert not coordinator.is_offline


@pytest.mark.asyncio
async def test_async_get_or_create_gate_coordinator_reuses_instance(
    hass, monkeypatch
):
    hass.data.setdefault(DOMAIN, {})["entry"] = {}
    client = DummyClient()

    async def fake_first_refresh(self):
        self.async_set_updated_data({})

    monkeypatch.setattr(
        AcogoGateCoordinator, "async_config_entry_first_refresh", fake_first_refresh
    )

    first = await async_get_or_create_gate_coordinator(
        hass, "entry", client, "gate-1"
    )
    second = await async_get_or_create_gate_coordinator(
        hass, "entry", client, "gate-1"
    )

    assert first is second
    assert hass.data[DOMAIN]["entry"]["gate_coordinators"]["gate-1"] is first


@pytest.mark.asyncio
async def test_async_get_or_create_gate_coordinator_sets_offline_on_failure(
    hass, monkeypatch
):
    hass.data.setdefault(DOMAIN, {})["entry"] = {}
    client = DummyClient()

    async def failing_refresh(self):
        raise UpdateFailed("boom")

    monkeypatch.setattr(
        AcogoGateCoordinator, "async_config_entry_first_refresh", failing_refresh
    )

    coordinator = await async_get_or_create_gate_coordinator(
        hass, "entry", client, "gate-1"
    )

    assert coordinator.is_offline
    assert coordinator.data == {}


@pytest.mark.asyncio
async def test_io_coordinator_formats_state(hass):
    state = {"message": {"inputs": {"in1": True}, "outputs": {"out1": False}}}
    client = DummyClient(io_state=state)
    coordinator = AcogoIoCoordinator(hass, client, "io-1")

    result = await coordinator._async_update_data()

    assert result["inputs"]["in1"] is True
    assert result["outputs"]["out1"] is False
    assert not coordinator.is_offline


@pytest.mark.asyncio
async def test_io_coordinator_handles_offline(hass):
    client = DummyClient(io_error=AcogoApiError("offline", status=408))
    coordinator = AcogoIoCoordinator(hass, client, "io-1")

    result = await coordinator._async_update_data()

    assert result["_offline"]
    assert coordinator.is_offline


@pytest.mark.asyncio
async def test_io_coordinator_refresh_state_updates_data(hass):
    client = DummyClient(
        io_state={"inputs": {"in2": True}, "outputs": {"out3": True}}
    )
    coordinator = AcogoIoCoordinator(hass, client, "io-1")

    await coordinator.async_refresh_state()

    assert coordinator.data["inputs"]["in2"] is True
    assert coordinator.data["outputs"]["out3"] is True
    assert not coordinator.is_offline


@pytest.mark.asyncio
async def test_io_coordinator_async_get_details_caches(hass):
    client = DummyClient(io_details={"deviceName": "Custom IO"})
    coordinator = AcogoIoCoordinator(hass, client, "io-1")

    result = await coordinator.async_get_details()
    cached = await coordinator.async_get_details()

    assert result == {"deviceName": "Custom IO"}
    assert cached is result
    assert client.calls.count(("io_details", "io-1")) == 1


@pytest.mark.asyncio
async def test_async_get_or_create_io_coordinator_sets_offline_on_refresh_error(
    hass, monkeypatch
):
    hass.data.setdefault(DOMAIN, {})["entry"] = {}
    client = DummyClient()

    async def fake_get_details(self):
        return {}

    async def failing_refresh(self):
        raise UpdateFailed("fail")

    monkeypatch.setattr(AcogoIoCoordinator, "async_get_details", fake_get_details)
    monkeypatch.setattr(
        AcogoIoCoordinator, "async_config_entry_first_refresh", failing_refresh
    )

    coordinator = await async_get_or_create_io_coordinator(
        hass, "entry", client, "io-1"
    )

    assert coordinator.is_offline
    assert coordinator.data["_offline"]


@pytest.mark.asyncio
async def test_async_get_or_create_io_coordinator_propagates_missing_entry(hass):
    with pytest.raises(UpdateFailed):
        await async_get_or_create_io_coordinator(
            hass, "missing", DummyClient(), "io-1"
        )
