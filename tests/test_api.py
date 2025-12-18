import pytest

from custom_components.acogo.api import API_BASE, AcogoApiError, AcogoClient


class MockResponse:
    def __init__(
        self,
        status: int,
        json_data=None,
        text_data=None,
        content_type="application/json",
    ):
        self.status = status
        self._json_data = json_data
        self._text_data = text_data or ""
        self.content_type = content_type

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class MockSession:
    def __init__(self, response_or_factory):
        self._response_or_factory = response_or_factory
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method, url, headers=None, **kwargs):
        self.calls.append((method, url, headers or {}))
        if callable(self._response_or_factory):
            return self._response_or_factory(method, url, headers or {}, **kwargs)
        return self._response_or_factory


@pytest.mark.asyncio
async def test_request_returns_json_and_adds_auth_header():
    response = MockResponse(200, json_data={"ok": True})
    session = MockSession(response)
    client = AcogoClient(session, "secret-token")

    result = await client._request("GET", "/devices")

    assert result == {"ok": True}
    assert session.calls[0][0] == "GET"
    assert session.calls[0][1] == f"{API_BASE}/devices"
    assert session.calls[0][2]["Authorization"] == "Bearer secret-token"


@pytest.mark.asyncio
async def test_request_handles_text_response():
    response = MockResponse(200, text_data="plain", content_type="text/plain")
    session = MockSession(response)
    client = AcogoClient(session, "token")

    result = await client._request("POST", "/echo")

    assert result == "plain"


@pytest.mark.asyncio
async def test_request_raises_on_http_error():
    response = MockResponse(500, text_data="failure", content_type="text/plain")
    session = MockSession(response)
    client = AcogoClient(session, "token")

    with pytest.raises(AcogoApiError) as err:
        await client._request("GET", "/fail")

    assert "500" in str(err.value)
    assert err.value.status == 500


@pytest.mark.asyncio
async def test_request_marks_offline_on_timeout_status():
    response = MockResponse(408, text_data="offline", content_type="text/plain")
    session = MockSession(response)
    client = AcogoClient(session, "token")

    with pytest.raises(AcogoApiError) as err:
        await client._request("GET", "/offline")

    assert err.value.status == 408


@pytest.mark.asyncio
async def test_request_wraps_unexpected_exception():
    def raise_error(method, url, headers=None, **kwargs):
        raise RuntimeError("boom")

    session = MockSession(raise_error)
    client = AcogoClient(session, "token")

    with pytest.raises(AcogoApiError) as err:
        await client._request("GET", "/explode")

    assert "boom" in str(err.value)


@pytest.mark.asyncio
async def test_async_get_devices_calls_request(monkeypatch):
    called = {}

    async def fake_request(method, path, **kwargs):
        called["method"] = method
        called["path"] = path
        return {"devices": []}

    session = MockSession(MockResponse(200, json_data={}))
    client = AcogoClient(session, "token")
    monkeypatch.setattr(client, "_request", fake_request)

    result = await client.async_get_devices()

    assert called == {"method": "GET", "path": "/devices"}
    assert result == {"devices": []}
