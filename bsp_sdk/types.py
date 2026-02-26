"""BSP Core Types — v0.2"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime

BioLevel = Literal["CORE", "STANDARD", "EXTENDED", "DEVICE"]
RecordStatus = Literal["ACTIVE", "SUPERSEDED", "PENDING"]
IEOStatus = Literal["ACTIVE", "SUSPENDED", "REVOKED", "PENDING"]
CertLevel = Literal["BASIC", "ADVANCED", "FULL", "RESEARCH"]
IEOType = Literal["LABORATORY", "HOSPITAL", "WEARABLE", "PHYSICIAN", "INSURER", "RESEARCH", "PLATFORM"]
BSPIntent = Literal["SUBMIT_BIORECORD", "READ_RECORDS", "REQUEST_CERTIFICATION", "ANALYZE_VITALITY", "REQUEST_SCORE", "SUBMIT_BIP"]


@dataclass
class RangeObject:
    optimal_low: float
    optimal_high: float
    functional_low: float
    functional_high: Optional[float]
    critical_low: float
    critical_high: Optional[float]
    unit: str
    population: str


@dataclass
class SourceMeta:
    ieo_id: str
    ieo_domain: str
    method: str
    equipment: Optional[str] = None
    operator: Optional[str] = None


@dataclass
class BioRecord:
    record_id: str
    beo_id: str
    version: str
    timestamp: str
    submitted_at: str
    source: SourceMeta
    category: str
    biomarker: str
    level: BioLevel
    value: float | str | dict
    unit: str
    ref_range: RangeObject
    confidence: float
    status: RecordStatus
    supersedes: Optional[str] = None
    arweave_tx: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class ConsentToken:
    token_id: str
    beo_id: str
    ieo_id: str
    intents: list[BSPIntent]
    categories: list[str]
    granted_at: str
    expires_at: Optional[str]
    revoked: bool
    signature: str
    arweave_tx: Optional[str] = None

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at.replace("Z", "+00:00")) < datetime.now().astimezone()

    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired()


@dataclass
class Guardian:
    contact_hash: str
    public_key: str
    accepted: bool
    added_at: str


@dataclass
class SovereigntyMeta:
    guardians: list[Guardian]
    recovery_scheme: str
    seed_phrase_hash: str
    consent_log: list[ConsentToken] = field(default_factory=list)


@dataclass
class BEO:
    beo_id: str
    domain: str
    created_at: str
    version: str
    public_key: str
    sovereignty: SovereigntyMeta
    arweave_tx: Optional[str] = None
