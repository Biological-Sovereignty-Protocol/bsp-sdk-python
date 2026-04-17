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
"""

from __future__ import annotations
from typing import Optional
from .types import BEO, BSPConfig, RecoveryConfig


class BEOClient:
    """Create and manage BEOs on Aptos. No approval required."""

    def __init__(self, config: BSPConfig) -> None:
        self.config = config

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

    def get(self, beo_id: str) -> BEO:
        """Get a BEO by its UUID."""
        raise NotImplementedError("Registry connection required")

    def is_available(self, domain: str) -> bool:
        """Check if a .bsp domain is available."""
        raise NotImplementedError("Registry connection required")

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
