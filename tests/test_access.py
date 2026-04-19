"""Tests for AccessManager — verify, issue, and revoke ConsentTokens."""

from __future__ import annotations

import base64
import json
from typing import Any, Optional

import pytest

from bsp_sdk.access import AccessManager
from bsp_sdk.crypto import CryptoUtils
from bsp_sdk.http_client import BSPApiError
from bsp_sdk.types import BSPConfig


# ── Fake HTTP client ──────────────────────────────────────────────────────────

class FakeHttp:
    """Records every request and returns pre-seeded responses."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses: dict[tuple[str, str], Any] = {}
        self.errors: dict[tuple[str, str], BSPApiError] = {}

    def seed(self, method: str, path: str, response: Any) -> None:
        self.responses[(method.upper(), path)] = response

    def seed_error(self, method: str, path: str, err: BSPApiError) -> None:
        self.errors[(method.upper(), path)] = err

    def _dispatch(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append({"method": method.upper(), "path": path, **kwargs})
        key = (method.upper(), path)
        if key in self.errors:
            raise self.errors[key]
        if key in self.responses:
            return self.responses[key]
        return {}

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
def manager(keypair: dict[str, str]) -> tuple[AccessManager, FakeHttp]:
    config = BSPConfig(
        ieo_domain="fleury.bsp",
        private_key=keypair["private_key"],
        environment="local",
        registry_url="http://localhost:3000",
    )
    http = FakeHttp()
    return AccessManager(config, http=http), http  # type: ignore[arg-type]


def _token_payload(token_id: str = "tok_abc") -> dict[str, Any]:
    return {
        "token_id": token_id,
        "beo_id": "550e8400-e29b-41d4-a716-446655440000",
        "beo_domain": "patient.bsp",
        "ieo_id": "770e8400-e29b-41d4-a716-446655440001",
        "ieo_domain": "fleury.bsp",
        "granted_at": "2026-04-19T12:00:00.000Z",
        "scope": {
            "intents": ["READ_RECORDS"],
            "categories": ["BSP-HM"],
            "levels": [],
            "period": None,
            "max_records": None,
        },
        "revocable": True,
        "revoked": False,
        "owner_signature": "sig",
        "token_hash": "hash",
        "version": "2.0",
        "expires_at": None,
        "revoked_at": None,
        "aptos_tx": "0xdeadbeef",
    }


# ── verify_consent ────────────────────────────────────────────────────────────

class TestVerifyConsent:
    def test_valid_token(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed("GET", "/api/consent/tok_abc", {
            "valid": True,
            "reason": None,
            "token": _token_payload(),
        })

        result = mgr.verify_consent(
            beo_domain="patient.bsp",
            token_id="tok_abc",
            intent="READ_RECORDS",
            category="BSP-HM",
        )

        assert result["valid"] is True
        assert result["reason"] is None
        assert result["token"].token_id == "tok_abc"
        assert result["token"].scope.intents == ["READ_RECORDS"]

        call = http.calls[0]
        assert call["method"] == "GET"
        assert call["params"] == {"intent": "READ_RECORDS", "category": "BSP-HM"}

    def test_verify_without_category(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed("GET", "/api/consent/tok_x", {"valid": True, "reason": None, "token": _token_payload("tok_x")})

        mgr.verify_consent(
            beo_domain="patient.bsp",
            token_id="tok_x",
            intent="READ_RECORDS",
        )
        assert http.calls[0]["params"] == {"intent": "READ_RECORDS"}

    def test_token_not_found_returns_invalid(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed_error("GET", "/api/consent/tok_missing", BSPApiError("Not found", 404))

        result = mgr.verify_consent(
            beo_domain="patient.bsp",
            token_id="tok_missing",
            intent="READ_RECORDS",
        )
        assert result == {"valid": False, "reason": "TOKEN_NOT_FOUND", "token": None}

    def test_non_404_error_propagates(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed_error("GET", "/api/consent/tok_err", BSPApiError("Boom", 500, retryable=True))

        with pytest.raises(BSPApiError):
            mgr.verify_consent(
                beo_domain="patient.bsp",
                token_id="tok_err",
                intent="READ_RECORDS",
            )

    def test_invalid_token_response(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed("GET", "/api/consent/tok_revoked", {
            "valid": False,
            "reason": "TOKEN_REVOKED",
            "token": None,
        })
        result = mgr.verify_consent(
            beo_domain="patient.bsp",
            token_id="tok_revoked",
            intent="READ_RECORDS",
        )
        assert result["valid"] is False
        assert result["reason"] == "TOKEN_REVOKED"
        assert result["token"] is None


# ── issue_consent ─────────────────────────────────────────────────────────────

class TestIssueConsent:
    def test_signs_and_posts(
        self,
        manager: tuple[AccessManager, FakeHttp],
        keypair: dict[str, str],
    ) -> None:
        mgr, http = manager
        http.seed("POST", "/api/relayer/consent", {
            "token": _token_payload("tok_new"),
            "transactionId": "0xabc",
        })

        token = mgr.issue_consent(
            beo_id="550e8400-e29b-41d4-a716-446655440000",
            ieo_domain="dr-carlos.bsp",
            intents=["READ_RECORDS"],
            categories=["BSP-HM"],
            expires_in_days=90,
        )

        assert token.token_id == "tok_new"
        call = http.calls[0]
        body = call["body"]
        assert body["beoId"]        == "550e8400-e29b-41d4-a716-446655440000"
        assert body["ieoId"]        == "dr-carlos.bsp"
        assert body["expiresInDays"] == 90
        assert body["scope"]["intents"]    == ["READ_RECORDS"]
        assert body["scope"]["categories"] == ["BSP-HM"]

        payload_to_verify = {
            "function": "grantConsent",
            "beoId": body["beoId"],
            "ieoId": body["ieoId"],
            "scope": body["scope"],
            "expiresInDays": body["expiresInDays"],
            "nonce": body["nonce"],
            "timestamp": body["timestamp"],
        }
        assert CryptoUtils.verify_signature(
            payload_to_verify, body["signature"], keypair["public_key"]
        ) is True

    def test_raises_when_no_token_in_response(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed("POST", "/api/relayer/consent", {"transactionId": "0xabc"})
        with pytest.raises(BSPApiError):
            mgr.issue_consent(
                beo_id="550e8400-e29b-41d4-a716-446655440000",
                ieo_domain="dr-carlos.bsp",
                intents=["READ_RECORDS"],
                categories=["BSP-HM"],
            )


# ── revoke_consent ────────────────────────────────────────────────────────────

class TestRevokeConsent:
    def test_signs_and_deletes(
        self,
        manager: tuple[AccessManager, FakeHttp],
        keypair: dict[str, str],
    ) -> None:
        mgr, http = manager
        http.seed("DELETE", "/api/consent/tok_abc", {
            "token_id": "tok_abc",
            "revoked_at": "2026-04-19T13:00:00.000Z",
            "transactionId": "0xrevoke",
        })

        result = mgr.revoke_consent(
            beo_id="550e8400-e29b-41d4-a716-446655440000",
            token_id="tok_abc",
        )

        assert result == {
            "token_id": "tok_abc",
            "revoked_at": "2026-04-19T13:00:00.000Z",
            "aptos_tx": "0xrevoke",
        }

        body = http.calls[0]["body"]
        assert body["beoId"] == "550e8400-e29b-41d4-a716-446655440000"

        payload_to_verify = {
            "function": "revokeToken",
            "tokenId": "tok_abc",
            "nonce": body["nonce"],
            "timestamp": body["timestamp"],
        }
        assert CryptoUtils.verify_signature(
            payload_to_verify, body["signature"], keypair["public_key"]
        ) is True

    def test_revoke_all_from_ieo(
        self,
        manager: tuple[AccessManager, FakeHttp],
        keypair: dict[str, str],
    ) -> None:
        mgr, http = manager
        http.seed("DELETE", "/api/consent/ieo/dr-carlos.bsp", {"revoked_count": 3})

        result = mgr.revoke_all_from_ieo(
            beo_id="550e8400-e29b-41d4-a716-446655440000",
            ieo_domain="dr-carlos.bsp",
        )
        assert result == {"revoked_count": 3}

        body = http.calls[0]["body"]
        payload_to_verify = {
            "function": "revokeAllFromIEO",
            "beoId": "550e8400-e29b-41d4-a716-446655440000",
            "ieoId": "dr-carlos.bsp",
            "nonce": body["nonce"],
            "timestamp": body["timestamp"],
        }
        assert CryptoUtils.verify_signature(
            payload_to_verify, body["signature"], keypair["public_key"]
        ) is True

    def test_revoke_all_tokens(
        self,
        manager: tuple[AccessManager, FakeHttp],
        keypair: dict[str, str],
    ) -> None:
        mgr, http = manager
        http.seed("DELETE", "/api/consent/all", {"revoked_count": 12})

        result = mgr.revoke_all_tokens(beo_id="550e8400-e29b-41d4-a716-446655440000")
        assert result == {"revoked_count": 12}

        body = http.calls[0]["body"]
        payload_to_verify = {
            "function": "revokeAllTokens",
            "beoId": "550e8400-e29b-41d4-a716-446655440000",
            "nonce": body["nonce"],
            "timestamp": body["timestamp"],
        }
        assert CryptoUtils.verify_signature(
            payload_to_verify, body["signature"], keypair["public_key"]
        ) is True


# ── get_token_history ─────────────────────────────────────────────────────────

class TestTokenHistory:
    def test_returns_tokens(self, manager: tuple[AccessManager, FakeHttp]) -> None:
        mgr, http = manager
        http.seed("GET", "/api/consent/history/patient.bsp", {
            "tokens": [_token_payload("tok_1"), _token_payload("tok_2")],
        })

        history = mgr.get_token_history("patient.bsp")
        assert len(history) == 2
        assert history[0].token_id == "tok_1"
        assert history[1].token_id == "tok_2"


# ── Parity: signature canonicalization ────────────────────────────────────────

class TestSignatureCanonicalization:
    def test_signature_bytes_decode_to_64(self, keypair: dict[str, str]) -> None:
        payload = {
            "function": "revokeToken",
            "tokenId": "tok_abc",
            "nonce": "a" * 32,
            "timestamp": "2026-04-19T12:00:00.000Z",
        }
        sig_b64 = CryptoUtils.sign_payload(payload, keypair["private_key"])
        assert len(base64.b64decode(sig_b64)) == 64

    def test_canonical_json_sorts_keys(self) -> None:
        payload = {"z": 1, "a": {"y": 2, "b": 3}}
        canonical = CryptoUtils._stringify_deterministic(payload)
        assert canonical == json.dumps({"a": {"b": 3, "y": 2}, "z": 1}, separators=(",", ":"))
