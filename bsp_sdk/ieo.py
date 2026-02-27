"""
IEOBuilder — Create and register Institutional Entity Objects.

Example::

    from bsp_sdk import IEOBuilder

    result = (
        IEOBuilder(
            domain       = "fleury.bsp",
            name         = "Fleury Laboratórios",
            ieo_type     = "LABORATORY",
            jurisdiction = "BR",
            legal_id     = "60.840.055/0001-31",
            contact      = "bsp@fleury.com.br",
        )
        .register()
    )
    # Store result["private_key"] in .env as BSP_IEO_PRIVATE_KEY
    # Store result["seed_phrase"] offline — never digitally
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class IEOBuilder:
    """Build and register an IEO on Arweave. No approval required."""

    domain:       str
    name:         str
    ieo_type:     str
    jurisdiction: str
    legal_id:     str
    contact:      str
    country:      Optional[str] = None
    website:      Optional[str] = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        valid_types = [
            "LABORATORY", "HOSPITAL", "WEARABLE",
            "PHYSICIAN", "INSURER", "RESEARCH", "PLATFORM",
        ]
        if not self.domain.endswith(".bsp"):
            raise ValueError(f'domain must end with .bsp — got: "{self.domain}"')
        if len(self.name.strip()) < 2:
            raise ValueError("name must be at least 2 characters")
        if len(self.legal_id.strip()) < 5:
            raise ValueError("legal_id required (CNPJ, EIN, VAT, etc.)")
        if self.ieo_type not in valid_types:
            raise ValueError(f'Invalid ieo_type: "{self.ieo_type}". Must be one of: {valid_types}')

    def register(self) -> dict:
        """
        Register the IEO on Arweave. Returns keys — store them securely.

        Returns dict with:
            ieo_id, domain, arweave_tx, private_key, seed_phrase, status, warning

        CRITICAL: private_key and seed_phrase returned ONCE.
        """
        # Implementation: generate Ed25519 key pair, post to IEORegistry on Arweave
        raise NotImplementedError("Registry connection required — bsp-registry not yet deployed")

    def preview(self) -> dict:
        """Dry run — shows what the IEO would look like without registering."""
        return {
            "domain":        self.domain,
            "display_name":  self.name,
            "ieo_type":      self.ieo_type,
            "jurisdiction":  self.jurisdiction,
            "legal_id":      self.legal_id,
            "certification": {"level": "UNCERTIFIED"},
            "status":        "ACTIVE",
            "warning":       "PREVIEW — not registered on-chain",
        }
