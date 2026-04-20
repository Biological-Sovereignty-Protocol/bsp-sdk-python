"""
BioRecordBuilder — Fluent builder for BSP BioRecords.

Example::

    from bsp_sdk import BioRecordBuilder

    record = (
        BioRecordBuilder(ieo_domain="fleury.bsp")
        .set_beo_id("550e8400-e29b-41d4-a716-446655440000")
        .set_biomarker("BSP-HM-001")   # Hemoglobin — validates against taxonomy
        .set_value(13.8)
        .set_unit("g/dL")
        .set_collection_time("2026-02-26T08:00:00Z")
        .set_ref_range(optimal="13.5-17.5", functional="12.0-17.5",
                       deficiency="<12.0", toxicity=None, unit="g/dL")
        .build()
    )
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Union
from .types import BioRecord, BioLevel, RangeObject, SourceMeta, RecordStatus
from .taxonomy import TaxonomyResolver

_resolver = TaxonomyResolver()


class BioRecordBuilder:
    """Fluent builder that validates biomarker codes and required fields."""

    def __init__(self, ieo_domain: str) -> None:
        self._ieo_domain   = ieo_domain
        self._record_id    = str(uuid.uuid4())
        self._beo_id:      Optional[str] = None
        self._biomarker:   Optional[str] = None
        self._category:    Optional[str] = None
        self._level:       Optional[BioLevel] = None
        self._value:       Optional[Union[float, str, dict]] = None
        self._unit:        Optional[str] = None
        self._collected_at: Optional[str] = None
        self._ref_range:   Optional[RangeObject] = None
        self._confidence:  Optional[float] = None
        self._method:      Optional[str] = None
        self._equipment:   Optional[str] = None
        self._supersedes:  Optional[str] = None

    def set_beo_id(self, beo_id: str) -> "BioRecordBuilder":
        self._beo_id = beo_id
        return self

    def set_biomarker(self, code: str) -> "BioRecordBuilder":
        """Validate BSP code format and look up taxonomy level."""
        if not _resolver.is_valid_code(code):
            raise ValueError(
                f'Invalid BSP biomarker code: "{code}". '
                f'Expected format: BSP-XX-NNN (e.g. BSP-HM-001)'
            )
        self._biomarker = code
        self._category  = "-".join(code.split("-")[:2])  # BSP-HM
        self._level     = _resolver.get_level(code)
        return self

    def set_value(self, value: Union[float, str, dict]) -> "BioRecordBuilder":
        self._value = value
        return self

    def set_unit(self, unit: str) -> "BioRecordBuilder":
        self._unit = unit
        return self

    def set_collection_time(self, iso8601: str) -> "BioRecordBuilder":
        """Validate that iso8601 is a parseable ISO 8601 datetime string."""
        # Normalise trailing 'Z' to '+00:00' so fromisoformat() accepts it on Python < 3.11
        normalized = iso8601.replace("Z", "+00:00") if iso8601.endswith("Z") else iso8601
        try:
            datetime.fromisoformat(normalized)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f'collection_time must be a valid ISO 8601 datetime string — got: "{iso8601}"'
            ) from exc
        self._collected_at = iso8601
        return self

    def set_ref_range(
        self,
        optimal: str,
        functional: str,
        unit: str,
        deficiency: Optional[str] = None,
        toxicity: Optional[str] = None,
        population: Optional[str] = None,
    ) -> "BioRecordBuilder":
        self._ref_range = RangeObject(
            optimal=optimal,
            functional=functional,
            unit=unit,
            deficiency=deficiency,
            toxicity=toxicity,
            population=population,
        )
        return self

    def set_confidence(self, confidence: float) -> "BioRecordBuilder":
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        self._confidence = confidence
        return self

    def set_method(self, method: str) -> "BioRecordBuilder":
        self._method = method
        return self

    def set_equipment(self, equipment: str) -> "BioRecordBuilder":
        self._equipment = equipment
        return self

    def supersedes(self, record_id: str) -> "BioRecordBuilder":
        """Mark this as a correction superseding a previous record."""
        self._supersedes = record_id
        return self

    def build(self) -> BioRecord:
        """Validate all required fields and return a BioRecord."""
        required = {
            "beo_id":       self._beo_id,
            "biomarker":    self._biomarker,
            "value":        self._value,
            "unit":         self._unit,
            "collected_at": self._collected_at,
        }
        missing = [k for k, v in required.items() if v is None]
        if missing:
            raise ValueError(f'BioRecord missing required fields: {", ".join(missing)}')

        now = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

        source = SourceMeta(
            ieo_id=     "",
            ieo_domain= self._ieo_domain,
            method=     self._method or "unknown",
            signature=  "",
            equipment=  self._equipment,
        )

        return BioRecord(
            record_id=    self._record_id,
            beo_id=       self._beo_id,
            ieo_id=       "",
            version=      "1.0.0",
            biomarker=    self._biomarker,
            category=     self._category,
            level=        self._level,
            value=        self._value,
            unit=         self._unit,
            ref_range=    self._ref_range or RangeObject(
                              optimal="", functional="", unit=self._unit),
            collected_at= self._collected_at,
            submitted_at= now,
            source=       source,
            status=       "ACTIVE",
            supersedes=   self._supersedes,
            confidence=   self._confidence,
        )
