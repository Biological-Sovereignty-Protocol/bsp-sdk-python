"""
BSP SDK — Biological Sovereignty Protocol Python SDK
Version 1.0.0 | Ambrósio Institute

Install::

    pip install bsp-sdk

Quick start::

    from bsp_sdk import BSPClient
    import os

    client = BSPClient(
        ieo_domain  = "fleury.bsp",
        private_key = os.environ["BSP_IEO_PRIVATE_KEY"],
        environment = "mainnet",
    )
"""

from .client import BSPClient
from .beo import BEOClient
from .ieo import IEOBuilder
from .biorecord import BioRecordBuilder
from .taxonomy import TaxonomyResolver
from .access import AccessManager
from .exchange import ExchangeClient
from .types import (
    # Config
    BSPConfig,
    # BEO
    BEO, Guardian, RecoveryConfig, BEOStatus,
    # IEO
    IEO, IEOCertification, IEOType, IEOStatus, CertLevel,
    # BioRecord
    BioRecord, RangeObject, SourceMeta, BioLevel, RecordStatus,
    # ConsentToken
    ConsentToken, TokenScope, BSPIntent,
    # Exchange
    SubmitResult, ReadResult, ReadFilters, BSPStatus, BSPError,
)

__version__ = "2.0.0"

__all__ = [
    # Clients
    "BSPClient", "BEOClient", "IEOBuilder",
    "BioRecordBuilder", "TaxonomyResolver",
    "AccessManager", "ExchangeClient",
    # Config
    "BSPConfig",
    # BEO types
    "BEO", "Guardian", "RecoveryConfig", "BEOStatus",
    # IEO types
    "IEO", "IEOCertification", "IEOType", "IEOStatus", "CertLevel",
    # BioRecord types
    "BioRecord", "RangeObject", "SourceMeta", "BioLevel", "RecordStatus",
    # Consent types
    "ConsentToken", "TokenScope", "BSPIntent",
    # Exchange types
    "SubmitResult", "ReadResult", "ReadFilters", "BSPStatus", "BSPError",
]
