"""BioRecordBuilder and TaxonomyResolver for BSP BioRecords."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from .types import BioRecord, BioLevel, RangeObject, SourceMeta, RecordStatus


class BioRecordBuilder:
    """
    Fluent builder for BSP BioRecords.

    Example:
        record = (BioRecordBuilder()
            .beo_id("550e8400-...")
            .biomarker("BSP-GL-001")
            .value(94)
            .unit("mg/dL")
            .timestamp("2026-02-24T08:30:00Z")
            .confidence(0.99)
            .build())
    """

    def __init__(self):
        self._record = {
            "record_id": str(uuid.uuid4()),
            "version": "0.2.0",
            "status": "ACTIVE",
            "supersedes": None,
        }

    def beo_id(self, beo_id: str) -> "BioRecordBuilder":
        self._record["beo_id"] = beo_id
        return self

    def biomarker(self, code: str) -> "BioRecordBuilder":
        self._record["biomarker"] = code
        return self

    def value(self, value: float | str | dict) -> "BioRecordBuilder":
        self._record["value"] = value
        return self

    def unit(self, unit: str) -> "BioRecordBuilder":
        self._record["unit"] = unit
        return self

    def timestamp(self, ts: str) -> "BioRecordBuilder":
        self._record["timestamp"] = ts
        return self

    def source(self, source: SourceMeta) -> "BioRecordBuilder":
        self._record["source"] = source
        return self

    def ref_range(self, range_obj: RangeObject) -> "BioRecordBuilder":
        self._record["ref_range"] = range_obj
        return self

    def confidence(self, confidence: float) -> "BioRecordBuilder":
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        self._record["confidence"] = confidence
        return self

    def supersedes(self, record_id: str) -> "BioRecordBuilder":
        self._record["supersedes"] = record_id
        return self

    def build(self) -> BioRecord:
        required = ["beo_id", "biomarker", "value", "unit", "timestamp"]
        for field in required:
            if field not in self._record:
                raise ValueError(f"BioRecord missing required field: {field}")

        self._record["submitted_at"] = datetime.now(timezone.utc).isoformat()

        return BioRecord(**self._record)


class TaxonomyResolver:
    """
    Validate and resolve BSP biomarker codes.

    Codes follow the format: BSP-[CATEGORY]-[NUMBER]
    Example: BSP-GL-001, BSP-LA-004, BSP-DV-001
    """

    _CORE = {"BSP-LA", "BSP-RC", "BSP-CV", "BSP-IM", "BSP-ME", "BSP-NR", "BSP-DH", "BSP-LF", "BSP-BC"}
    _STANDARD = {"BSP-HM", "BSP-VT", "BSP-MN", "BSP-HR", "BSP-RN", "BSP-LP", "BSP-GL", "BSP-LV", "BSP-IF"}
    _EXTENDED = {"BSP-FR", "BSP-GN", "BSP-MB", "BSP-TX", "BSP-IM2", "BSP-CV2"}
    _DEVICE = {"BSP-DV"}

    def is_valid(self, code: str) -> bool:
        import re
        return bool(re.match(r'^BSP-[A-Z0-9]{2,4}-\d{3}$', code))

    def get_category(self, code: str) -> Optional[str]:
        if not self.is_valid(code):
            return None
        parts = code.split("-")
        return f"BSP-{parts[1]}"

    def get_level(self, code: str) -> Optional[BioLevel]:
        category = self.get_category(code)
        if not category:
            return None
        if category in self._CORE:
            return "CORE"
        if category in self._STANDARD:
            return "STANDARD"
        if category in self._EXTENDED:
            return "EXTENDED"
        if category in self._DEVICE:
            return "DEVICE"
        return None
