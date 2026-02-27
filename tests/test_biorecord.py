"""Tests for TaxonomyResolver and BioRecordBuilder."""

import pytest
from bsp_sdk.taxonomy import TaxonomyResolver
from bsp_sdk.biorecord import BioRecordBuilder


# ─── TaxonomyResolver ────────────────────────────────────────────────────────

class TestTaxonomyResolver:
    def setup_method(self):
        self.r = TaxonomyResolver()

    def test_is_valid_code_accepts_valid(self):
        assert self.r.is_valid_code("BSP-HM-001") is True
        assert self.r.is_valid_code("BSP-LA-003") is True
        assert self.r.is_valid_code("BSP-DV-001") is True
        assert self.r.is_valid_code("BSP-GL-001") is True

    def test_is_valid_code_rejects_invalid(self):
        assert self.r.is_valid_code("HM-001")     is False   # missing prefix
        assert self.r.is_valid_code("BSP-HM-1")   is False   # wrong format
        assert self.r.is_valid_code("BSP-XX-001")  is False   # unknown category
        assert self.r.is_valid_code("")            is False
        assert self.r.is_valid_code("BSP-HM")     is False   # no number

    def test_get_level_core(self):
        assert self.r.get_level("BSP-LA-001") == "CORE"
        assert self.r.get_level("BSP-CV-001") == "CORE"
        assert self.r.get_level("BSP-BC-001") == "CORE"

    def test_get_level_standard(self):
        assert self.r.get_level("BSP-HM-001") == "STANDARD"
        assert self.r.get_level("BSP-GL-001") == "STANDARD"

    def test_get_level_extended(self):
        assert self.r.get_level("BSP-GN-001") == "EXTENDED"

    def test_get_level_device(self):
        assert self.r.get_level("BSP-DV-001") == "DEVICE"

    def test_get_level_accepts_category_code(self):
        assert self.r.get_level("BSP-HM") == "STANDARD"

    def test_get_level_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown BSP category"):
            self.r.get_level("BSP-XX")

    def test_list_categories_returns_25(self):
        cats = self.r.list_categories()
        assert len(cats) == 25
        assert all("code" in c and "level" in c and "name" in c for c in cats)

    def test_list_by_level_counts(self):
        assert len(self.r.list_by_level("CORE"))     == 9
        assert len(self.r.list_by_level("STANDARD")) == 9
        assert len(self.r.list_by_level("EXTENDED")) == 6
        assert len(self.r.list_by_level("DEVICE"))   == 1

    def test_get_category_known(self):
        cat = self.r.get_category("BSP-HM")
        assert cat is not None
        assert cat["level"] == "STANDARD"
        assert cat["name"]  == "Hematology"

    def test_get_category_unknown_returns_none(self):
        assert self.r.get_category("BSP-XX") is None


# ─── BioRecordBuilder ────────────────────────────────────────────────────────

def _valid_builder() -> BioRecordBuilder:
    return (
        BioRecordBuilder(ieo_domain="fleury.bsp")
        .set_beo_id("550e8400-e29b-41d4-a716-446655440000")
        .set_biomarker("BSP-HM-001")
        .set_value(13.8)
        .set_unit("g/dL")
        .set_collection_time("2026-02-26T08:00:00Z")
    )


class TestBioRecordBuilder:
    def test_build_valid_record(self):
        record = _valid_builder().build()
        assert record.biomarker    == "BSP-HM-001"
        assert record.category     == "BSP-HM"
        assert record.level        == "STANDARD"
        assert record.value        == 13.8
        assert record.unit         == "g/dL"
        assert record.status       == "ACTIVE"
        assert record.supersedes   is None
        assert record.submitted_at is not None
        assert record.record_id    is not None

    def test_invalid_bsp_code_raises(self):
        with pytest.raises(ValueError, match="Invalid BSP biomarker code"):
            BioRecordBuilder("fleury.bsp").set_biomarker("INVALID")

    def test_unknown_category_raises(self):
        with pytest.raises(ValueError, match="Invalid BSP biomarker code"):
            BioRecordBuilder("fleury.bsp").set_biomarker("BSP-XX-001")

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValueError, match="missing required fields"):
            BioRecordBuilder("fleury.bsp").set_biomarker("BSP-HM-001").build()

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValueError, match="confidence must be between"):
            _valid_builder().set_confidence(1.5).build()
        with pytest.raises(ValueError, match="confidence must be between"):
            _valid_builder().set_confidence(-0.1).build()

    def test_confidence_valid(self):
        record = _valid_builder().set_confidence(0.95).build()
        assert record.confidence == 0.95

    def test_supersedes(self):
        prev_id = "00000000-0000-0000-0000-000000000001"
        record = _valid_builder().supersedes(prev_id).build()
        assert record.supersedes == prev_id
        assert record.status     == "ACTIVE"

    def test_ref_range(self):
        record = _valid_builder().set_ref_range(
            optimal="13.5-17.5", functional="12.0-17.5",
            deficiency="<12.0", toxicity=None, unit="g/dL"
        ).build()
        assert record.ref_range.optimal == "13.5-17.5"

    def test_unique_record_ids(self):
        r1 = _valid_builder().build()
        r2 = _valid_builder().build()
        assert r1.record_id != r2.record_id
