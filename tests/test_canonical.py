"""Cross-SDK canonical JSON + signature roundtrip tests.

These vectors MUST stay byte-identical to the ones in
`bsp-sdk-typescript/tests/canonical-stringify.test.ts`. Both SDKs
must produce the exact same canonical string for the same input,
otherwise signatures generated in one SDK will fail in the other.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bsp_sdk.crypto import CryptoUtils


# ─── Test vectors (MUST match TS file byte-for-byte) ─────────────────────────

VECTORS: list[tuple[str, object, str]] = [
    ("empty object", {}, "{}"),
    ("single key", {"a": 1}, '{"a":1}'),
    ("keys get sorted", {"b": 2, "a": 1}, '{"a":1,"b":2}'),
    (
        "nested keys sorted recursively",
        {"outer": {"z": 1, "a": 2}},
        '{"outer":{"a":2,"z":1}}',
    ),
    ("arrays preserve order", {"arr": [3, 1, 2]}, '{"arr":[3,1,2]}'),
    (
        "arrays of objects sort each object",
        {"arr": [{"z": 1, "a": 2}, {"m": 0}]},
        '{"arr":[{"a":2,"z":1},{"m":0}]}',
    ),
    ("null value", {"v": None}, '{"v":null}'),
    ("booleans", {"t": True, "f": False}, '{"f":false,"t":true}'),
    ("integer and float", {"i": 1, "f": 1.5}, '{"f":1.5,"i":1}'),
    (
        "string with unicode (ensure_ascii=False)",
        {"s": "olá"},
        '{"s":"olá"}',
    ),
    (
        "biorecord-like payload",
        {"biomarker": "BSP-HM-001", "value": 13.8, "unit": "g/dL"},
        '{"biomarker":"BSP-HM-001","unit":"g/dL","value":13.8}',
    ),
]


@pytest.mark.parametrize("name,input_,expected", VECTORS, ids=[v[0] for v in VECTORS])
def test_canonical_vectors(name, input_, expected):
    assert CryptoUtils.canonical_stringify(input_) == expected


def test_no_spaces_in_output():
    out = CryptoUtils.canonical_stringify({"a": 1, "b": [1, 2, {"c": 3}]})
    assert ": " not in out
    assert ", " not in out
    assert out == '{"a":1,"b":[1,2,{"c":3}]}'


def test_insertion_order_does_not_change_output():
    a = CryptoUtils.canonical_stringify({"z": 1, "a": 2, "m": 3})
    b = CryptoUtils.canonical_stringify({"a": 2, "m": 3, "z": 1})
    assert a == b


# ─── Cross-SDK signature fixture ─────────────────────────────────────────────

# Fixed seed shared with TS fixture — identical bytes on both sides.
FIXED_SEED = "0101010101010101010101010101010101010101010101010101010101010101"
FIXED_PAYLOAD = {
    "biomarker": "BSP-HM-001",
    "value": 13.8,
    "unit": "g/dL",
    "collected_at": "2026-02-26T08:00:00Z",
    "nested": {"z": 1, "a": [1, 2, 3]},
}
EXPECTED_CANONICAL = (
    '{"biomarker":"BSP-HM-001","collected_at":"2026-02-26T08:00:00Z",'
    '"nested":{"a":[1,2,3],"z":1},"unit":"g/dL","value":13.8}'
)


def test_python_sign_verify_roundtrip():
    kp = CryptoUtils.key_pair_from_seed(FIXED_SEED)
    sig = CryptoUtils.sign_payload(FIXED_PAYLOAD, kp["private_key"])
    assert CryptoUtils.verify_signature(FIXED_PAYLOAD, sig, kp["public_key"]) is True


def test_canonical_matches_expected_string():
    assert CryptoUtils.canonical_stringify(FIXED_PAYLOAD) == EXPECTED_CANONICAL


def test_cross_sdk_fixture_verifies():
    """
    Read the fixture produced by the TS SDK (or committed from a previous run)
    and verify the signature. If Python and TS disagree on the canonical
    bytes, this test is the early-warning siren.

    Fixture location (relative to repo root):
        ../bsp-sdk-typescript/tests/fixtures/canonical-sig.json
    """
    here = Path(__file__).resolve().parent
    candidates = [
        # sibling repo layout (monorepo / checkout-style)
        here.parent.parent / "bsp-sdk-typescript" / "tests" / "fixtures" / "canonical-sig.json",
        # explicit override for CI
        Path(os.environ.get("BSP_TS_FIXTURE", "")),
    ]
    fixture_path = next((p for p in candidates if p and p.is_file()), None)
    if fixture_path is None:
        pytest.skip(
            "TS fixture not available — set BSP_TS_FIXTURE or check out sibling repo",
        )

    with fixture_path.open("r", encoding="utf-8") as f:
        fixture = json.load(f)

    # 1. Our canonical string must match the one TS computed
    assert (
        CryptoUtils.canonical_stringify(fixture["payload"]) == fixture["canonical"]
    ), "Canonical JSON disagreement between Python and TS SDKs"

    # 2. Signature produced by TS must verify with Python
    ok = CryptoUtils.verify_signature(
        fixture["payload"],
        fixture["signature"],
        fixture["public_key"],
    )
    assert ok is True, "TS-generated signature failed to verify in Python"


def test_python_generated_signature_round_trip_with_fixed_seed():
    """Mirror test: Python generates a signature that TS will verify.

    TS reads the fixture in its own test suite. This test ensures that
    Python consistently produces the *same* signature bytes as the fixture
    (deterministic Ed25519 + deterministic canonical bytes ⇒ same signature).
    """
    here = Path(__file__).resolve().parent
    fixture_path = (
        here.parent.parent
        / "bsp-sdk-typescript"
        / "tests"
        / "fixtures"
        / "canonical-sig.json"
    )
    if not fixture_path.is_file():
        pytest.skip("TS fixture not available for signature parity check")

    with fixture_path.open("r", encoding="utf-8") as f:
        fixture = json.load(f)

    kp = CryptoUtils.key_pair_from_seed(fixture["seed"])
    sig = CryptoUtils.sign_payload(fixture["payload"], kp["private_key"])

    assert kp["public_key"] == fixture["public_key"]
    assert sig == fixture["signature"], (
        "Python-generated signature differs from TS fixture — "
        "canonical JSON drift suspected"
    )
