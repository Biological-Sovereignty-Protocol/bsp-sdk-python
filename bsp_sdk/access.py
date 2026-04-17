"""
AccessManager — Manage ConsentTokens for BSP data access.

Example (BEO holder issuing consent to a physician)::

    token = client.access.issue_consent(
        ieo_domain      = "dr-carlos.bsp",
        intents         = ["READ_RECORDS"],
        categories      = ["BSP-LA", "BSP-CV"],
        expires_in_days = 90,
        reason          = "Quarterly health review",
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
from typing import Optional
from .types import BSPConfig, ConsentToken, BSPIntent


class AccessManager:
    """Manage ConsentTokens — issue, verify, revoke."""

    def __init__(self, config: BSPConfig) -> None:
        self.config = config

    def verify_consent(
        self,
        beo_domain: str,
        token_id:   str,
        intent:     BSPIntent,
        category:   Optional[str] = None,
    ) -> dict:
        """
        Verify token is valid for a specific intent.
        Returns {"valid": bool, "reason": str | None, "token": ConsentToken | None}.
        """
        raise NotImplementedError("Registry connection required")

    def issue_consent(
        self,
        ieo_domain:      str,
        intents:         list[BSPIntent],
        categories:      list[str],
        expires_in_days: Optional[int] = None,
        reason:          Optional[str] = None,
    ) -> ConsentToken:
        """Issue a ConsentToken (BEO holder operation). Signed locally, written to Aptos."""
        raise NotImplementedError("Registry connection required")

    def revoke_consent(self, token_id: str) -> dict:
        """Revoke a token immediately — on-chain effect. Returns {"token_id", "revoked_at", "aptos_tx"}."""
        raise NotImplementedError("Registry connection required")

    def revoke_all_from_ieo(self, ieo_domain: str) -> dict:
        """Revoke ALL active tokens from a specific IEO. Returns {"revoked_count": int}."""
        raise NotImplementedError("Registry connection required")

    def revoke_all_tokens(self) -> dict:
        """Emergency: revoke ALL active consent tokens from the BEO."""
        raise NotImplementedError("Registry connection required")

    def get_token_history(self, beo_domain: str) -> list[ConsentToken]:
        """Get full audit log of tokens for a BEO."""
        raise NotImplementedError("Registry connection required")
