"""BSP Core Types — v2.0 (Aptos)
Full type definitions for the Biological Sovereignty Protocol Python SDK.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Literal
from datetime import datetime, timezone

# ─── Literals ─────────────────────────────────────────────────────────────────

BEOStatus    = Literal["ACTIVE", "LOCKED", "RECOVERY_PENDING"]
BioLevel     = Literal["CORE", "STANDARD", "EXTENDED", "DEVICE"]
RecordStatus = Literal["ACTIVE", "SUPERSEDED", "PENDING"]
IEOStatus    = Literal["ACTIVE", "SUSPENDED", "REVOKED", "PENDING"]
CertLevel    = Literal["UNCERTIFIED", "BASIC", "ADVANCED", "FULL", "DEVICE", "RESEARCH"]
IEOType      = Literal["LABORATORY", "HOSPITAL", "WEARABLE", "PHYSICIAN", "INSURER", "RESEARCH", "PLATFORM"]
ExportFormat = Literal["JSON", "CSV", "FHIR_R4"]
BSPIntent    = Literal[
    "SUBMIT_RECORD",
    "READ_RECORDS",
    "ANALYZE_VITALITY",
    "REQUEST_SCORE",
    "SOVEREIGN_EXPORT",
    "SYNC_PROTOCOL",
]

# ─── BEO ──────────────────────────────────────────────────────────────────────

@dataclass
class Guardian:
    name:       str
    contact:    str
    public_key: str
    role:       Literal["primary", "secondary", "tertiary"]
    accepted:   bool
    added_at:   str


@dataclass
class RecoveryConfig:
    enabled:   bool
    threshold: int
    guardians: list[Guardian]


@dataclass
class BEO:
    beo_id:     str
    domain:     str
    public_key: str
    created_at: str
    version:    str
    recovery:   RecoveryConfig
    status:     BEOStatus
    locked_at:  Optional[str] = None
    aptos_tx: Optional[str] = None


# ─── IEO ──────────────────────────────────────────────────────────────────────

@dataclass
class IEOCertification:
    level:      CertLevel
    granted_at: Optional[str]
    expires_at: Optional[str]
    categories: list[str]
    intents:    list[BSPIntent]


@dataclass
class IEO:
    ieo_id:        str
    domain:        str
    display_name:  str
    ieo_type:      IEOType
    country:       str
    jurisdiction:  str
    legal_id:      str
    public_key:    str
    created_at:    str
    version:       str
    certification: IEOCertification
    status:        IEOStatus
    aptos_tx:    Optional[str] = None


# ─── BioRecord ────────────────────────────────────────────────────────────────

@dataclass
class RangeObject:
    optimal:    str
    functional: str
    unit:       str
    deficiency: Optional[str] = None
    toxicity:   Optional[str] = None
    population: Optional[str] = None


@dataclass
class SourceMeta:
    ieo_id:     str
    ieo_domain: str
    method:     str
    signature:  str
    equipment:  Optional[str] = None
    operator:   Optional[str] = None
    firmware:   Optional[str] = None


@dataclass
class BioRecord:
    record_id:    str
    beo_id:       str
    ieo_id:       str
    version:      str
    biomarker:    str
    category:     str
    level:        BioLevel
    value:        Union[float, str, dict]
    unit:         str
    ref_range:    RangeObject
    collected_at: str
    submitted_at: str
    source:       SourceMeta
    status:       RecordStatus
    supersedes:   Optional[str] = None
    confidence:   Optional[float] = None
    aptos_tx:   Optional[str] = None
    data_hash:    Optional[str] = None


# ─── ConsentToken ─────────────────────────────────────────────────────────────

@dataclass
class TokenScope:
    intents:     list[BSPIntent]
    categories:  list[str]
    levels:      list[BioLevel]
    period:      Optional[dict] = None   # {"from": ISO8601 | null, "to": ISO8601 | null}
    max_records: Optional[int] = None


@dataclass
class ConsentToken:
    token_id:        str
    beo_id:          str
    beo_domain:      str
    ieo_id:          str
    ieo_domain:      str
    granted_at:      str
    scope:           TokenScope
    revocable:       bool
    revoked:         bool
    owner_signature: str
    token_hash:      str
    version:         str
    expires_at:      Optional[str] = None
    revoked_at:      Optional[str] = None
    aptos_tx:      Optional[str] = None

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        return exp < datetime.now(tz=timezone.utc)

    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired()


# ─── Exchange ─────────────────────────────────────────────────────────────────

BSPStatus = Literal["SUCCESS", "ERROR", "PARTIAL", "PENDING"]

@dataclass
class BSPError:
    code:      str
    message:   str
    retryable: bool
    field:     Optional[str] = None


@dataclass
class SubmitResult:
    request_id:  str
    status:      BSPStatus
    record_ids:  list[str]
    aptos_txs: list[str]
    timestamp:   str
    error:       Optional[BSPError] = None


@dataclass
class ReadResult:
    request_id: str
    beo_id:     str
    records:    list[BioRecord]
    total:      int
    has_more:   bool
    error:      Optional[BSPError] = None


@dataclass
class ReadFilters:
    categories: Optional[list[str]] = None
    biomarkers: Optional[list[str]] = None
    levels:     Optional[list[BioLevel]] = None
    from_date:  Optional[str] = None
    to_date:    Optional[str] = None
    limit:      int = 100
    offset:     int = 0
    status:     RecordStatus = "ACTIVE"


# ─── SDK Config ───────────────────────────────────────────────────────────────

AptosNetwork = Literal["mainnet", "testnet", "devnet", "local"]


@dataclass
class BSPConfig:
    ieo_domain:       str
    private_key:      str
    environment:      Literal["mainnet", "testnet", "local"] = "mainnet"
    registry_url:     Optional[str] = None
    contract_address: Optional[str] = None
    aptos_network:    Optional[AptosNetwork] = None
    aptos_node_url:   Optional[str] = None
    timeout_s:        float = 30.0
