"""
BSPClient — Main entry point for the BSP Python SDK.

Example::

    import os
    from bsp_sdk import BSPClient

    client = BSPClient(
        ieo_domain  = "fleury.bsp",
        private_key = os.environ["BSP_IEO_PRIVATE_KEY"],
        environment = "mainnet",
    )

    # Build and submit a BioRecord
    record = (
        client.record("patient.bsp")
        .set_biomarker("BSP-HM-001")
        .set_value(13.8)
        .set_unit("g/dL")
        .set_collection_time("2026-02-26T08:00:00Z")
        .build()
    )

    result = client.submit_records(
        target_beo    = "patient.bsp",
        records       = [record],
        consent_token = "tok_...",
    )
    print(result.aptos_txs)
"""

from __future__ import annotations
from typing import Optional
from .types import BSPConfig, BioRecord, ReadResult, SubmitResult, ReadFilters, BSPIntent, ConsentToken
from .beo import BEOClient
from .ieo import IEOBuilder
from .biorecord import BioRecordBuilder
from .taxonomy import TaxonomyResolver
from .access import AccessManager
from .exchange import ExchangeClient


class BSPClient:
    """Main BSP client — wraps all SDK modules."""

    def __init__(
        self,
        ieo_domain:       str,
        private_key:      str,
        environment:      str = "mainnet",
        registry_url:     Optional[str] = None,
        contract_address: Optional[str] = None,
        aptos_network:    Optional[str] = None,
        aptos_node_url:   Optional[str] = None,
        timeout_s:        float = 30.0,
    ) -> None:
        if not ieo_domain.endswith(".bsp"):
            raise ValueError(f'ieo_domain must end with .bsp — got: "{ieo_domain}"')
        if not private_key:
            raise ValueError("private_key is required")
        if environment not in ("mainnet", "testnet", "local"):
            raise ValueError('environment must be "mainnet", "testnet", or "local"')

        self.config = BSPConfig(
            ieo_domain=ieo_domain,
            private_key=private_key,
            environment=environment,
            registry_url=registry_url,
            contract_address=contract_address,
            aptos_network=aptos_network,
            aptos_node_url=aptos_node_url,
            timeout_s=timeout_s,
        )
        self.beo      = BEOClient(self.config)
        self.access   = AccessManager(self.config)
        self._exchange = ExchangeClient(self.config)

    def record(self, beo_domain: str) -> BioRecordBuilder:
        """Create a BioRecordBuilder pre-filled with this IEO's domain."""
        builder = BioRecordBuilder(ieo_domain=self.config.ieo_domain)
        # Caller will set_beo_id from beo_domain after resolving
        return builder

    def submit_records(
        self,
        target_beo:    str,
        records:       list[BioRecord],
        consent_token: str,
    ) -> SubmitResult:
        """Submit BioRecords to a target BEO with ConsentToken."""
        return self._exchange.submit_records(target_beo, records, consent_token)

    def read_records(
        self,
        target_beo:    str,
        consent_token: str,
        filters:       Optional[ReadFilters] = None,
    ) -> ReadResult:
        """Read BioRecords from an authorized BEO."""
        return self._exchange.read_records(target_beo, consent_token, filters)

    @property
    def taxonomy(self) -> TaxonomyResolver:
        return TaxonomyResolver()

    @staticmethod
    def create_ieo(
        domain:       str,
        name:         str,
        ieo_type:     str,
        jurisdiction: str,
        legal_id:     str,
        contact:      str,
    ) -> IEOBuilder:
        """Create an IEOBuilder for registering a new institution."""
        return IEOBuilder(
            domain=domain, name=name, ieo_type=ieo_type,
            jurisdiction=jurisdiction, legal_id=legal_id, contact=contact,
        )
