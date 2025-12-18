import logging

import aiohttp
import async_timeout

API_BASE = "https://api.aco.com.pl/public/v2"


class AcogoApiError(Exception):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


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
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as resp:
                    self._logger.debug(
                        "acogo response status: %s %s -> %s", method, url, resp.status
                    )
                    if resp.status >= 400:
                        text = await resp.text()
                        if resp.status == 408:
                            self._logger.debug(
                                "acogo device offline: %s %s -> %s %s",
                                method,
                                url,
                                resp.status,
                                text,
                            )
                            raise AcogoApiError(
                                "Device offline (408)", status=resp.status
                            )
                        self._logger.error(
                            "acogo request failed: %s %s -> %s %s",
                            method,
                            url,
                            resp.status,
                            text,
                        )
                        raise AcogoApiError(
                            f"{resp.status}: {text}", status=resp.status
                        )
                    if resp.content_type == "application/json":
                        self._logger.debug("acogo JSON response for %s %s", method, url)
                        return await resp.json()
                    self._logger.debug("acogo text response for %s %s", method, url)
                    return await resp.text()
        except AcogoApiError:
            # Allow upstream handlers to decide how to
            # treat known API errors (e.g. offline).
            raise
        except Exception as err:
            self._logger.exception("acogo request error: %s %s", method, url)
            raise AcogoApiError(str(err)) from err

    async def async_get_devices(self):
        # Example endpoint: GET /devices.
        return await self._request("GET", "/devices")

    async def async_open_gate(self, dev_id: str):
        # Trigger the "open gate" action.
        path = f"/devices/{dev_id}/orders/ez-open"
        return await self._request("POST", path)

    async def async_get_io_details(self, device_id: str):
        # Fetch details for an acoGO! I/O device.
        return await self._request("GET", f"/devices/io/{device_id}")

    async def async_get_io_state(self, device_id: str):
        # Fetch I/O input and output states.
        return await self._request("GET", f"/io/{device_id}/state")

    async def async_set_io_output(self, device_id: str, out_number: int, state: bool):
        # Set the state of an I/O output.
        payload = {"state": state}
        return await self._request(
            "POST", f"/io/{device_id}/out/{out_number}", json=payload
        )

    async def async_get_gate_details(self, device_id: str):
        # Fetch details or status for a gate device.
        return await self._request("GET", f"/devices/gates/{device_id}")
