"""
BSP TaxonomyResolver — Validate and look up BSP biomarker codes.
All 25 BSP taxonomy categories mapped.
"""

from __future__ import annotations
from typing import Optional
from .types import BioLevel

# All 25 BSP categories: code → (level, name)
_TAXONOMY: dict[str, tuple[BioLevel, str]] = {
    # Level 1 — Core Longevity (9)
    "BSP-LA": ("CORE",     "Longevity & Aging"),
    "BSP-RC": ("CORE",     "Regeneration & Cellular Health"),
    "BSP-CV": ("CORE",     "Cardiovascular Health"),
    "BSP-IM": ("CORE",     "Immune Function & Inflammation"),
    "BSP-ME": ("CORE",     "Metabolism & Cellular Energy"),
    "BSP-NR": ("CORE",     "Neurological Health"),
    "BSP-DH": ("CORE",     "Detoxification & Hepatic Function"),
    "BSP-LF": ("CORE",     "Lymphatic System & Clearance"),
    "BSP-BC": ("CORE",     "Biological Clock & Senescence"),
    # Level 2 — Standard Laboratory (9)
    "BSP-HM": ("STANDARD", "Hematology"),
    "BSP-VT": ("STANDARD", "Vitamins"),
    "BSP-MN": ("STANDARD", "Minerals & Electrolytes"),
    "BSP-HR": ("STANDARD", "Hormones"),
    "BSP-RN": ("STANDARD", "Renal Function"),
    "BSP-LP": ("STANDARD", "Conventional Lipids"),
    "BSP-GL": ("STANDARD", "Glycemia & Metabolic Markers"),
    "BSP-LV": ("STANDARD", "Hepatic Function"),
    "BSP-IF": ("STANDARD", "Inflammatory Markers"),
    # Level 3 — Extended/Specialized (6)
    "BSP-GN": ("EXTENDED", "Genomics & Epigenomics"),
    "BSP-MB": ("EXTENDED", "Microbiome"),
    "BSP-PR": ("EXTENDED", "Proteomics"),
    "BSP-MT": ("EXTENDED", "Metabolomics"),
    "BSP-TX": ("EXTENDED", "Toxicology"),
    "BSP-CL": ("EXTENDED", "Clinical Assessment"),
    # Level 4 — Device (1)
    "BSP-DV": ("DEVICE",   "Device & Wearable Data"),
}

import re
_CODE_RE = re.compile(r"^(BSP-[A-Z]{2})-(\d{3})$")


class TaxonomyResolver:
    """
    Validate and look up BSP biomarker taxonomy.

    Example::

        resolver = TaxonomyResolver()
        resolver.is_valid_code("BSP-HM-001")   # True
        resolver.get_level("BSP-LA-003")        # "CORE"
        resolver.list_categories()              # all 25
        resolver.list_by_level("STANDARD")      # 9 categories
    """

    def is_valid_code(self, code: str) -> bool:
        """Return True if code matches BSP-XX-NNN format and category exists."""
        m = _CODE_RE.match(code)
        if not m:
            return False
        return m.group(1) in _TAXONOMY

    def get_level(self, code: str) -> BioLevel:
        """
        Return taxonomy level (CORE, STANDARD, EXTENDED, DEVICE)
        for a biomarker code (BSP-HM-001) or category code (BSP-HM).
        """
        cat = code if len(code) == 6 else "-".join(code.split("-")[:2])
        if cat not in _TAXONOMY:
            raise ValueError(f"Unknown BSP category: '{cat}'")
        return _TAXONOMY[cat][0]

    def get_category(self, category_code: str) -> Optional[dict]:
        """Return {'level': ..., 'name': ...} for a category code, or None."""
        if category_code not in _TAXONOMY:
            return None
        level, name = _TAXONOMY[category_code]
        return {"level": level, "name": name}

    def list_categories(self) -> list[dict]:
        """Return all 25 BSP categories with code, level, and name."""
        return [
            {"code": code, "level": level, "name": name}
            for code, (level, name) in _TAXONOMY.items()
        ]

    def list_by_level(self, level: BioLevel) -> list[dict]:
        """Return all categories for a specific taxonomy level."""
        return [
            {"code": code, "name": name}
            for code, (lvl, name) in _TAXONOMY.items()
            if lvl == level
        ]
