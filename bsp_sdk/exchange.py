"""
ExchangeClient — Submit and read biological data via the BSP Exchange Protocol.

Example (lab submitting)::

    result = client.submit_records(
        target_beo    = "patient.bsp",
        records       = [blood_test_record, hrv_record],
        consent_token = "tok_...",
    )
    print(result.aptos_txs)  # permanent tx hashes on Aptos

Example (physician reading)::

    from bsp_sdk.types import ReadFilters

    data = client.read_records(
        target_beo    = "patient.bsp",
        consent_token = "tok_...",
        filters       = ReadFilters(categories=["BSP-CV", "BSP-LA"], limit=50),
    )
    for record in data.records:
        print(record.biomarker, record.value, record.unit)
"""

from __future__ import annotations
from typing import Optional
from .types import BSPConfig, BioRecord, ReadResult, SubmitResult, ReadFilters


_BSP_ERRORS = {
    "TOKEN_NOT_FOUND":          "Token does not exist",
    "TOKEN_REVOKED":            "Token has been revoked",
    "TOKEN_EXPIRED":            "Token has expired",
    "INTENT_NOT_AUTHORIZED":    "Intent not in token scope",
    "CATEGORY_NOT_AUTHORIZED":  "Category not in token scope",
    "IEO_SIGNATURE_INVALID":    "IEO signature verification failed",
    "SCHEMA_VALIDATION_FAILED": "BioRecord schema validation failed",
    "BIOMARKER_CODE_INVALID":   "BSP biomarker code not found in taxonomy",
    "APTOS_TIMEOUT":            "Aptos transaction timed out — retryable",
    "RATE_LIMIT_EXCEEDED":      "Rate limit exceeded — retryable",
}


class ExchangeClient:
    """Submit and read biological data — all operations require ConsentToken."""

    def __init__(self, config: BSPConfig) -> None:
        self.config = config

    def submit_records(
        self,
        target_beo:    str,
        records:       list[BioRecord],
        consent_token: str,
    ) -> SubmitResult:
        """
        Submit BioRecords to a target BEO.

        Consent verification (enforced on-chain):
        ✓ token exists and belongs to this IEO + BEO pair
        ✓ token not revoked / not expired
        ✓ SUBMIT_RECORD intent in scope
        ✓ record category in token scope
        """
        if not records:
            raise ValueError("At least one BioRecord is required")
        if len(records) > 100:
            raise ValueError("Maximum 100 records per submission batch")
        # Implementation: sign with IEO private key, submit via registry API to Aptos
        raise NotImplementedError("Registry connection required")

    def read_records(
        self,
        target_beo:    str,
        consent_token: str,
        filters:       Optional[ReadFilters] = None,
    ) -> ReadResult:
        """
        Read BioRecords from an authorized BEO.
        Results paginated — use filters.offset for next page.
        """
        raise NotImplementedError("Registry connection required")

    def sovereign_export(
        self,
        target_beo:    str,
        consent_token: str,
        format:        str = "JSON",
    ) -> dict:
        """
        SOVEREIGN_EXPORT — Export all BioRecords.

        Any BSP-compliant system MUST support this.
        Blocking SOVEREIGN_EXPORT violates the BSP specification.
        """
        if format not in ("JSON", "CSV", "FHIR_R4"):
            raise ValueError(f'format must be JSON, CSV, or FHIR_R4 — got: "{format}"')
        raise NotImplementedError("Registry connection required")
