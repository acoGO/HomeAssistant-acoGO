import logging

import aiohttp
import async_timeout

API_BASE = "https://api.aco.com.pl/public/v2"  # tu wstaw swój URL


class AcogoApiError(Exception):
    pass


class AcogoClient:
    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._token = token
        self._logger = logging.getLogger(__name__)

    async def _request(self, method: str, path: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        url = f"{API_BASE}{path}"

        self._logger.debug("acogo request start: %s %s", method, url)

        try:
            async with async_timeout.timeout(10):
                async with self._session.request(method, url, headers=headers, **kwargs) as resp:
                    self._logger.debug(
                        "acogo response status: %s %s -> %s", method, url, resp.status
                    )
                    if resp.status >= 400:
                        text = await resp.text()
                        self._logger.error(
                            "acogo request failed: %s %s -> %s %s", method, url, resp.status, text
                        )
                        raise AcogoApiError(f"{resp.status}: {text}")
                    if resp.content_type == "application/json":
                        self._logger.debug("acogo JSON response for %s %s", method, url)
                        return await resp.json()
                    self._logger.debug("acogo text response for %s %s", method, url)
                    return await resp.text()
        except Exception as err:
            self._logger.exception("acogo request error: %s %s", method, url)
            raise AcogoApiError(str(err)) from err

    async def async_get_devices(self):
        # GET /devices – przykładowy endpoint
        return await self._request("GET", "/devices")

    async def async_open_gate(self, dev_id: str):
        # przycisk "otwórz furtkę"
        path = f"/devices/{dev_id}/orders/ez-open"
        return await self._request("POST", path)
