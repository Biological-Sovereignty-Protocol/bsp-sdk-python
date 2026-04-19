"""
HttpClient — thin `requests` wrapper for BSP registry API calls.

Example::

    from bsp_sdk.http_client import HttpClient

    http = HttpClient(base_url="https://api.biologicalsovereigntyprotocol.com")
    data = http.get("/v1/beo/andre.bsp")
"""

from __future__ import annotations

from typing import Any, Literal, Optional

import requests


class BSPApiError(Exception):
    """Raised when the registry API returns a non-2xx status."""

    def __init__(self, message: str, status_code: int, retryable: bool = False) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


Environment = Literal["mainnet", "testnet", "local"]


class HttpClient:
    """Minimal HTTP client for BSP registry API calls."""

    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ── Verbs ─────────────────────────────────────────────────────────────────

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        res = self._session.get(
            self._url(path),
            params=params,
            timeout=self.timeout_s,
        )
        return self._parse(res)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        res = self._session.post(
            self._url(path),
            json=body,
            timeout=self.timeout_s,
        )
        return self._parse(res)

    def delete(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        res = self._session.delete(
            self._url(path),
            json=body,
            timeout=self.timeout_s,
        )
        return self._parse(res)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    @staticmethod
    def _parse(res: requests.Response) -> Any:
        try:
            data = res.json()
        except ValueError as exc:
            raise BSPApiError(
                f"Non-JSON response from registry (HTTP {res.status_code})",
                res.status_code,
            ) from exc

        if not res.ok:
            retryable = res.status_code == 429 or res.status_code >= 500
            message = (
                data.get("error") if isinstance(data, dict) else None
            ) or f"Request failed with status {res.status_code}"
            raise BSPApiError(message, res.status_code, retryable)

        return data

    @staticmethod
    def default_base_url(env: Environment) -> str:
        """Default registry API base URL for a given environment."""
        if env == "mainnet":
            return "https://api.biologicalsovereigntyprotocol.com"
        if env == "testnet":
            return "https://api-testnet.biologicalsovereigntyprotocol.com"
        if env == "local":
            return "http://localhost:3000"
        raise ValueError(f'Unknown environment: "{env}"')
