"""Tests for BEOClient.destroy() — parity with the TypeScript SDK.

The destroy flow is a signed-payload POST. We:
    1. Assert the wire body shape (beoId as decimal string, timestamp_secs int,
       hex nonce, Ed25519 signature, optional reason).
    2. Verify the signature locally using CryptoUtils so we know the canonical
       payload matches what the API (and Move) will re-verify.
    3. Cover error paths: missing private key, invalid beo_id type, non-dict
       response.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import pytest

from bsp_sdk.beo import BEOClient, _serialize_beo_id
from bsp_sdk.crypto import CryptoUtils
from bsp_sdk.http_client import BSPApiError
from bsp_sdk.types import BSPConfig


# ── Fake HTTP client ──────────────────────────────────────────────────────────


class FakeHttp:
    """Records every request and returns pre-seeded responses."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses: dict[tuple[str, str], Any] = {}

    def seed(self, method: str, path: str, response: Any) -> None:
        self.responses[(method.upper(), path)] = response

    def _dispatch(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append({"method": method.upper(), "path": path, **kwargs})
        return self.responses.get((method.upper(), path), {})

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self._dispatch("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self._dispatch("POST", path, body=body)

    def delete(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self._dispatch("DELETE", path, body=body)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def keypair() -> dict[str, str]:
    return CryptoUtils.generate_key_pair()


@pytest.fixture
def client(keypair: dict[str, str]) -> tuple[BEOClient, FakeHttp]:
    http = FakeHttp()
    config = BSPConfig(
        ieo_domain="fleury.bsp",
        private_key=keypair["private_key"],
        environment="local",
    )
    return BEOClient(config, http=http), http


# ── _serialize_beo_id ─────────────────────────────────────────────────────────


class TestSerializeBeoId:
    def test_accepts_int(self) -> None:
        assert _serialize_beo_id(42) == "42"

    def test_accepts_decimal_string(self) -> None:
        assert _serialize_beo_id("999999999999999999") == "999999999999999999"

    def test_rejects_negative_int(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            _serialize_beo_id(-1)

    def test_rejects_non_decimal_string(self) -> None:
        with pytest.raises(TypeError):
            _serialize_beo_id("not-a-number")

    def test_rejects_hex_string(self) -> None:
        with pytest.raises(TypeError):
            _serialize_beo_id("0x2a")


# ── destroy() happy path ──────────────────────────────────────────────────────


class TestDestroy:
    def test_sends_canonical_wire_payload(
        self, client: tuple[BEOClient, FakeHttp], keypair: dict[str, str],
    ) -> None:
        beo, http = client
        http.seed(
            "POST",
            "/api/relayer/beo/destroy",
            {"destroyed_at": "2026-04-20T10:00:00Z", "transactionHash": "0xabc"},
        )

        result = beo.destroy(beo_id=42, reason="user_requested_deletion")

        assert result["destroyed_at"] == "2026-04-20T10:00:00Z"
        assert result["aptos_tx"] == "0xabc"
        assert len(http.calls) == 1
        call = http.calls[0]
        assert call["method"] == "POST"
        assert call["path"] == "/api/relayer/beo/destroy"

        body = call["body"]
        # Wire-format assertions
        assert body["beoId"] == "42"
        assert isinstance(body["beoId"], str)
        assert isinstance(body["timestamp_secs"], int)
        assert body["timestamp_secs"] > 0
        assert re.fullmatch(r"[0-9a-f]{32,}", body["nonce"]) is not None
        assert len(body["nonce"]) % 2 == 0
        assert body["reason"] == "user_requested_deletion"
        # Signature is base64 (44 chars for a 64-byte Ed25519 sig incl. padding)
        assert len(body["signature"]) > 0

        # Canonical signed payload re-verifies under the private key's public half
        payload = {
            "function": "destroyBEO",
            "beoId": body["beoId"],
            "nonce": body["nonce"],
            "timestamp_secs": body["timestamp_secs"],
        }
        assert CryptoUtils.verify_signature(payload, body["signature"], keypair["public_key"])

    def test_omits_reason_when_not_provided(
        self, client: tuple[BEOClient, FakeHttp],
    ) -> None:
        beo, http = client
        http.seed(
            "POST",
            "/api/relayer/beo/destroy",
            {"destroyed_at": "2026-04-20T10:00:00Z", "transactionHash": "0xabc"},
        )

        beo.destroy(beo_id=7)

        body = http.calls[0]["body"]
        assert "reason" not in body

    def test_accepts_decimal_string_beo_id(
        self, client: tuple[BEOClient, FakeHttp],
    ) -> None:
        beo, http = client
        http.seed(
            "POST",
            "/api/relayer/beo/destroy",
            {"destroyed_at": "2026-04-20T10:00:00Z", "transactionHash": "0xabc"},
        )

        beo.destroy(beo_id="18446744073709551615")  # u64 max

        assert http.calls[0]["body"]["beoId"] == "18446744073709551615"


# ── destroy() error paths ─────────────────────────────────────────────────────


class TestDestroyErrors:
    def test_requires_private_key(self, keypair: dict[str, str]) -> None:
        http = FakeHttp()
        config = BSPConfig(
            ieo_domain="fleury.bsp",
            private_key="",
            environment="local",
        )
        beo = BEOClient(config, http=http)
        with pytest.raises(ValueError, match="private_key is required"):
            beo.destroy(beo_id=42)

    def test_raises_on_non_dict_response(
        self, client: tuple[BEOClient, FakeHttp],
    ) -> None:
        beo, http = client
        http.seed("POST", "/api/relayer/beo/destroy", ["unexpected", "list"])
        with pytest.raises(BSPApiError):
            beo.destroy(beo_id=42)

    def test_rejects_unsupported_beo_id_type(
        self, client: tuple[BEOClient, FakeHttp],
    ) -> None:
        beo, _ = client
        with pytest.raises(TypeError):
            beo.destroy(beo_id=3.14)  # type: ignore[arg-type]
