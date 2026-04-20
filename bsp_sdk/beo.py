"""
BEOClient — Create and manage Biological Entity Objects on Aptos.

Example::

    from bsp_sdk import BSPClient

    client = BSPClient(ieo_domain="fleury.bsp", private_key="...", environment="mainnet")

    # Check domain availability
    available = client.beo.is_available("andre.bsp")

    # Create BEO
    result = client.beo.create(
        domain    = "andre.bsp",
        guardians = [
            {"name": "Maria", "contact": "maria.bsp", "public_key": "...", "role": "primary"},
            {"name": "João",  "contact": "joao.bsp",  "public_key": "...", "role": "secondary"},
        ],
        threshold = 2,
    )
    # ⚠️  Store seed_phrase offline — never digitally

    # Destroy BEO (LGPD Art. 18 / GDPR Art. 17 — right to erasure)
    client.beo.destroy(
        beo_id = "42",        # wire format: decimal string (u64 on Move)
        reason = "user_requested_deletion",
    )
"""

from __future__ import annotations

import time
from typing import Optional, Union

from .crypto import CryptoUtils
from .http_client import BSPApiError, HttpClient
from .types import BEO, BSPConfig, RecoveryConfig


# BEO identifiers are `u64` on Move. In Python we accept either `int` or the
# wire-format decimal string. We always send the wire format to the API.
BeoId = Union[int, str]


def _serialize_beo_id(beo_id: BeoId) -> str:
    """Convert a BEO id into the canonical wire-format decimal string."""
    if isinstance(beo_id, int):
        if beo_id < 0:
            raise ValueError(f"beo_id must be non-negative, got {beo_id}")
        return str(beo_id)
    if isinstance(beo_id, str) and beo_id.isdigit():
        return beo_id
    raise TypeError(f"beo_id must be int or decimal string, got {beo_id!r}")


def _now_secs() -> int:
    """Unix seconds as integer — matches the API's `timestamp_secs` field."""
    return int(time.time())


class BEOClient:
    """Create and manage BEOs on Aptos. No approval required."""

    def __init__(self, config: BSPConfig, http: Optional[HttpClient] = None) -> None:
        self.config = config
        self.http = http or HttpClient(
            config.registry_url or HttpClient.default_base_url(config.environment),
            timeout_s=config.timeout_s,
        )

    def create(
        self,
        domain:    str,
        guardians: Optional[list[dict]] = None,
        threshold: int = 2,
    ) -> dict:
        """
        Create a new BEO. Keys returned ONCE — store immediately.

        Returns:
            beo, beo_id, domain, aptos_tx, private_key, seed_phrase, warning
        """
        if not domain.endswith(".bsp"):
            raise ValueError(f'domain must end with .bsp — got: "{domain}"')
        if not self.is_available(domain):
            raise ValueError(f'Domain "{domain}" is already registered')
        # Implementation: generate Ed25519 locally, relay to BEORegistry on Aptos via registry API
        raise NotImplementedError("Registry connection required")

    def resolve(self, domain: str) -> BEO:
        """Resolve a .bsp domain to its BEO object."""
        raise NotImplementedError("Registry connection required")

    def get(self, beo_id: BeoId) -> BEO:
        """Get a BEO by its on-chain u64 id."""
        raise NotImplementedError("Registry connection required")

    def is_available(self, domain: str) -> bool:
        """Check if a .bsp domain is available."""
        try:
            data = self.http.get(f"/v1/beo/resolve/{domain}")
            return not bool(data.get("exists", True)) if isinstance(data, dict) else False
        except BSPApiError as exc:
            if exc.status_code == 404:
                return True
            raise

    def lock(self, reason: Optional[str] = None) -> dict:
        """Lock a BEO — no reads/writes until unlocked."""
        raise NotImplementedError("Registry connection required")

    def unlock(self) -> dict:
        """Unlock a previously locked BEO."""
        raise NotImplementedError("Registry connection required")

    def update_recovery(self, config: RecoveryConfig) -> dict:
        """Update Social Recovery guardian configuration."""
        if config.threshold < 1 or config.threshold > len(config.guardians):
            raise ValueError(f"threshold must be between 1 and {len(config.guardians)}")
        raise NotImplementedError("Registry connection required")

    def list_beos(self, limit: int = 20, offset: int = 0) -> list:
        """List BEOs accessible to the configured IEO.

        Makes a GET request to ``/api/beo?limit=N&offset=N`` and returns the
        list of BEO objects from the response.

        :param limit:  Maximum number of BEOs to return (default: 20).
        :param offset: Number of records to skip for pagination (default: 0).
        :returns:      List of BEO dicts as returned by the registry API.
        :raises BSPApiError: Non-2xx response from the registry API.

        Example::

            client = BSPClient(ieo_domain="lab.bsp", private_key="...", environment="mainnet")
            beos = client.beo.list_beos(limit=50, offset=0)
            for beo in beos:
                print(beo["beo_id"], beo["domain"])
        """
        data = self.http.get(f"/api/beo?limit={limit}&offset={offset}")
        if isinstance(data, list):
            return data
        # Some registry responses wrap the list in a 'beos' or 'items' key
        if isinstance(data, dict):
            for key in ("beos", "items", "results", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    def destroy(
        self,
        beo_id: BeoId,
        reason: Optional[str] = None,
    ) -> dict:
        """Destroy a BEO permanently — LGPD Art. 18 / GDPR Art. 17 right to erasure.

        Reaches parity with the TypeScript SDK's ``BEOClient.destroy(beoId)``.

        Flow:
            1. Sign a canonical payload with the BEO's Ed25519 private key.
            2. POST ``/api/relayer/beo/destroy`` with ``timestamp_secs`` + hex nonce
               (v2 API alignment — see bsp-registry-api).
            3. The relayer invokes Move ``beo_registry::destroy_beo`` which
               nullifies the public key, revokes all ConsentTokens and releases
               the ``.bsp`` domain.

        :param beo_id: On-chain BEO id. Accepts ``int`` or decimal string.
                       Internally serialised to the canonical wire format (string).
        :param reason: Optional human-readable reason (audit-logged, not on-chain).
        :returns: ``{ "destroyed_at": str, "aptos_tx": str }``
        :raises BSPApiError: Non-2xx response from the registry API.

        .. warning::
           Irreversible. Once destroyed, the BEO cannot be recovered — even via
           Social Recovery. The ``.bsp`` domain becomes available for re-use by
           any other principal (typically the protocol enforces a cooldown).
        """
        wire_beo_id = _serialize_beo_id(beo_id)
        nonce = CryptoUtils.generate_nonce()
        timestamp_secs = _now_secs()

        payload_to_sign = {
            "function":       "destroyBEO",
            "beoId":          wire_beo_id,
            "nonce":          nonce,
            "timestamp_secs": timestamp_secs,
        }
        if not self.config.private_key:
            raise ValueError(
                "BSPConfig.private_key is required to sign destroy() — "
                "the relayer cannot forge this operation.",
            )
        signature = CryptoUtils.sign_payload(payload_to_sign, self.config.private_key)

        body = {
            "beoId":          wire_beo_id,
            "signature":      signature,
            "nonce":          nonce,
            "timestamp_secs": timestamp_secs,
        }
        if reason is not None:
            body["reason"] = reason

        result = self.http.post("/api/relayer/beo/destroy", body)
        if not isinstance(result, dict):
            raise BSPApiError(
                "Registry returned a non-object response for destroy",
                status_code=502,
                retryable=True,
            )
        return {
            "destroyed_at": result.get("destroyed_at"),
            "aptos_tx":     result.get("transactionHash") or result.get("transactionId"),
        }
