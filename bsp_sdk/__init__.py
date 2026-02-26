"""
BSP SDK — Biological Sovereignty Protocol Python SDK
Version 0.2.0

Official Python SDK for building BSP-compliant applications.
"""

from .beo import BEOClient
from .biorecord import BioRecordBuilder, TaxonomyResolver
from .exchange import ExchangeClient
from .access import AccessManager
from .types import (
    BEO, BioRecord, ConsentToken, IEOType, BioLevel,
    RecordStatus, BSPIntent, RangeObject, SourceMeta
)

__version__ = "0.2.0"
__all__ = [
    "BEOClient",
    "BioRecordBuilder",
    "TaxonomyResolver",
    "ExchangeClient",
    "AccessManager",
    "BEO",
    "BioRecord",
    "ConsentToken",
    "IEOType",
    "BioLevel",
    "RecordStatus",
    "BSPIntent",
    "RangeObject",
    "SourceMeta",
]
