"""ExchangeClient — Submit and read biological data via the BSP Exchange Protocol."""

from typing import Optional
from .types import BioRecord, ConsentToken


class ExchangeClient:
    """
    Submit and read biological data using BSP Exchange Protocol.

    All operations require a valid ConsentToken signed by the BEO holder.

    Example:
        client = ExchangeClient(ieo_id="my-lab.bsp")
        result = client.submit(record, token=consent_token)
    """

    def __init__(self, ieo_id: str):
        self.ieo_id = ieo_id

    def submit(self, record: BioRecord, token: ConsentToken) -> dict:
        """Submit a BioRecord to a BEO."""
        if not token.is_valid():
            raise PermissionError("BSP-E-001: Invalid or missing consent token")
        if token.is_expired():
            raise PermissionError("BSP-E-002: Token expired")
        if token.revoked:
            raise PermissionError("BSP-E-003: Token revoked")
        if "SUBMIT_BIORECORD" not in token.intents:
            raise PermissionError("BSP-E-004: Intent not authorized by token")
        raise NotImplementedError("Install bsp-sdk from PyPI when published")

    def read_records(
        self,
        beo_id: str,
        token: ConsentToken,
        categories: Optional[list[str]] = None,
        biomarkers: Optional[list[str]] = None,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Read BioRecords from a BEO."""
        raise NotImplementedError("Install bsp-sdk from PyPI when published")
