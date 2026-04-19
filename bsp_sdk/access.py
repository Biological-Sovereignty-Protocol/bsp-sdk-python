"""
AccessManager — Manage ConsentTokens for BSP data access.

Example (BEO holder issuing consent to a physician)::

    token = client.access.issue_consent(
        beo_id          = "550e8400-e29b-41d4-a716-446655440000",
        ieo_domain      = "dr-carlos.bsp",
        intents         = ["READ_RECORDS"],
        categories      = ["BSP-LA", "BSP-CV"],
        expires_in_days = 90,
    )

Example (lab verifying consent before submitting)::

    check = client.access.verify_consent(
        beo_domain  = "patient.bsp",
        token_id    = "tok_...",
        intent      = "SUBMIT_RECORD",
        category    = "BSP-HM",
    )
    if not check["valid"]:
        raise PermissionError(check["reason"])
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .crypto import CryptoUtils
from .http_client import BSPApiError, HttpClient
from .types import BSPConfig, BSPIntent, ConsentToken, TokenScope


class AccessManager:
    """Manage ConsentTokens — issue, verify, revoke."""

    def __init__(self, config: BSPConfig, http: Optional[HttpClient] = None) -> None:
        self.config = config
        self.http = http or HttpClient(
            config.registry_url or HttpClient.default_base_url(config.environment),
            timeout_s=config.timeout_s,
        )

    # ── Verify ────────────────────────────────────────────────────────────────

    def verify_consent(
        self,
        beo_domain: str,
        token_id:   str,
        intent:     BSPIntent,
        category:   Optional[str] = None,
    ) -> dict:
        """
        Verify token is valid for a specific intent.

        Checks enforced by the AccessControl contract:
        - token exists and belongs to this IEO + BEO pair
        - token not revoked
        - token not expired
        - intent is in token scope
        - category (if specified) is in token scope

        Returns ``{"valid": bool, "reason": str | None, "token": ConsentToken | None}``.

        ``beo_domain`` is kept in the signature for API symmetry with the TS SDK
        and future audit-log extensions; the registry resolves the BEO from the token.
        """
        _ = beo_domain
        params: dict[str, Any] = {"intent": intent}
        if category is not None:
            params["category"] = category

        try:
            result = self.http.get(f"/api/consent/{token_id}", params=params)
        except BSPApiError as err:
            if err.status_code == 404:
                return {"valid": False, "reason": "TOKEN_NOT_FOUND", "token": None}
            raise

        token_data = result.get("token") if isinstance(result, dict) else None
        return {
            "valid": bool(result.get("valid")) if isinstance(result, dict) else False,
            "reason": result.get("reason") if isinstance(result, dict) else None,
            "token": _token_from_dict(token_data) if token_data else None,
        }

    # ── Issue ─────────────────────────────────────────────────────────────────

    def issue_consent(
        self,
        beo_id:          str,
        ieo_domain:      str,
        intents:         list[BSPIntent],
        categories:      list[str],
        period:          Optional[dict] = None,
        max_records:     Optional[int] = None,
        expires_in_days: Optional[int] = None,
    ) -> ConsentToken:
        """Issue a ConsentToken (BEO holder operation). Signed locally, written to Aptos."""
        nonce = CryptoUtils.generate_nonce()
        timestamp = _now_iso()

        scope = {
            "intents": list(intents),
            "categories": list(categories),
            "period": period,
            "max_records": max_records,
        }

        payload_to_sign = {
            "function": "grantConsent",
            "beoId": beo_id,
            "ieoId": ieo_domain,
            "scope": scope,
            "expiresInDays": expires_in_days,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        signature = CryptoUtils.sign_payload(payload_to_sign, self.config.private_key)

        result = self.http.post(
            "/api/relayer/consent",
            {
                "beoId": beo_id,
                "ieoId": ieo_domain,
                "scope": scope,
                "expiresInDays": expires_in_days,
                "signature": signature,
                "nonce": nonce,
                "timestamp": timestamp,
            },
        )

        token_data = result.get("token") if isinstance(result, dict) else None
        if not token_data:
            raise BSPApiError("Registry did not return a token", 500)
        return _token_from_dict(token_data)

    # ── Revoke one ────────────────────────────────────────────────────────────

    def revoke_consent(self, beo_id: str, token_id: str) -> dict:
        """Revoke a token immediately — on-chain effect. Returns ``{"token_id", "revoked_at", "aptos_tx"}``."""
        nonce = CryptoUtils.generate_nonce()
        timestamp = _now_iso()

        payload_to_sign = {
            "function": "revokeToken",
            "tokenId": token_id,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        signature = CryptoUtils.sign_payload(payload_to_sign, self.config.private_key)

        result = self.http.delete(
            f"/api/consent/{token_id}",
            {
                "beoId": beo_id,
                "signature": signature,
                "nonce": nonce,
                "timestamp": timestamp,
            },
        )

        return {
            "token_id": result.get("token_id"),
            "revoked_at": result.get("revoked_at"),
            "aptos_tx": result.get("transactionId"),
        }

    # ── Revoke many ───────────────────────────────────────────────────────────

    def revoke_all_from_ieo(self, beo_id: str, ieo_domain: str) -> dict:
        """Revoke ALL active tokens from a specific IEO. Returns ``{"revoked_count": int}``."""
        nonce = CryptoUtils.generate_nonce()
        timestamp = _now_iso()

        payload_to_sign = {
            "function": "revokeAllFromIEO",
            "beoId": beo_id,
            "ieoId": ieo_domain,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        signature = CryptoUtils.sign_payload(payload_to_sign, self.config.private_key)

        result = self.http.delete(
            f"/api/consent/ieo/{ieo_domain}",
            {
                "beoId": beo_id,
                "signature": signature,
                "nonce": nonce,
                "timestamp": timestamp,
            },
        )
        return {"revoked_count": int(result.get("revoked_count", 0))}

    def revoke_all_tokens(self, beo_id: str) -> dict:
        """Emergency: revoke ALL active consent tokens from the BEO."""
        nonce = CryptoUtils.generate_nonce()
        timestamp = _now_iso()

        payload_to_sign = {
            "function": "revokeAllTokens",
            "beoId": beo_id,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        signature = CryptoUtils.sign_payload(payload_to_sign, self.config.private_key)

        result = self.http.delete(
            "/api/consent/all",
            {
                "beoId": beo_id,
                "signature": signature,
                "nonce": nonce,
                "timestamp": timestamp,
            },
        )
        return {"revoked_count": int(result.get("revoked_count", 0))}

    # ── History ───────────────────────────────────────────────────────────────

    def get_token_history(self, beo_domain: str) -> list[ConsentToken]:
        """Get full audit log of tokens for a BEO."""
        result = self.http.get(f"/api/consent/history/{beo_domain}")
        tokens = result.get("tokens", []) if isinstance(result, dict) else []
        return [_token_from_dict(t) for t in tokens]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """UTC timestamp in ISO 8601 with trailing ``Z`` (matches ``new Date().toISOString()``)."""
    now = datetime.now(tz=timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _token_from_dict(data: dict) -> ConsentToken:
    """Rehydrate a ConsentToken dataclass from the registry JSON payload."""
    scope_data = data.get("scope", {}) or {}
    scope = TokenScope(
        intents=list(scope_data.get("intents", [])),
        categories=list(scope_data.get("categories", [])),
        levels=list(scope_data.get("levels", [])),
        period=scope_data.get("period"),
        max_records=scope_data.get("max_records"),
    )
    return ConsentToken(
        token_id=data["token_id"],
        beo_id=data["beo_id"],
        beo_domain=data["beo_domain"],
        ieo_id=data["ieo_id"],
        ieo_domain=data["ieo_domain"],
        granted_at=data["granted_at"],
        scope=scope,
        revocable=bool(data.get("revocable", True)),
        revoked=bool(data.get("revoked", False)),
        owner_signature=data.get("owner_signature", ""),
        token_hash=data.get("token_hash", ""),
        version=data.get("version", "2.0"),
        expires_at=data.get("expires_at"),
        revoked_at=data.get("revoked_at"),
        aptos_tx=data.get("aptos_tx"),
    )
