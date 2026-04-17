"""
BSP Python SDK — Full Flow Example
===================================
Demonstrates the complete lifecycle:
  - IEO registration (institution)
  - BEO creation (individual)
  - Consent grant
  - BioRecord submission
  - Record query
  - Consent revocation
  - Sovereign data export

Run:
    BSP_IEO_PRIVATE_KEY=your_key python examples/full_flow.py
"""

import os
from datetime import datetime, timezone, timedelta

from bsp_sdk import (
    BSPConfig,
    BEOClient,
    IEOBuilder,
    BioRecordBuilder,
    AccessManager,
    ExchangeClient,
    ReadFilters,
    BSPError,
)


# ── 1. Configure ─────────────────────────────────────────────────────────────

config = BSPConfig(
    ieo_domain=os.environ.get("BSP_IEO_DOMAIN", "genomicslab.bsp"),
    private_key=os.environ["BSP_IEO_PRIVATE_KEY"],
    environment=os.environ.get("BSP_ENVIRONMENT", "testnet"),
)

print(f"Environment : {config.environment}")
print(f"Institution : {config.ieo_domain}")
print()


# ── 2. Register the institution (IEO) ────────────────────────────────────────

print("[1/6] Registering IEO...")
lab = IEOBuilder(
    config=config,
    domain="genomicslab.bsp",
    display_name="Genomics Lab",
    ieo_type="LABORATORY",
    country="BR",
    jurisdiction="BR-SP",
    legal_id="12.345.678/0001-99",
)

# Preview first — dry-run, no on-chain write
preview = lab.preview()
print(f"  IEO preview hash : {preview.get('hash', 'n/a')}")

# Register on-chain
registration = lab.register()
print(f"  IEO registered   : {registration.get('ieo_id', 'n/a')}")
print()


# ── 3. Alice creates her BEO ─────────────────────────────────────────────────

print("[2/6] Creating Alice's BEO...")
beo_client = BEOClient(config)

# Check availability first
if beo_client.is_available("alice.bsp"):
    alice = beo_client.create(domain="alice.bsp")
    print(f"  BEO created : {alice.beo_id}")
    print(f"  Domain      : {alice.domain}")
    print(f"  Status      : {alice.status}")
else:
    alice = beo_client.resolve("alice.bsp")
    print(f"  BEO exists  : {alice.beo_id}")
print()


# ── 4. Alice grants consent to the lab ───────────────────────────────────────

print("[3/6] Issuing consent token...")
access = AccessManager(config)

expires_at = (datetime.now(tz=timezone.utc) + timedelta(days=90)).isoformat()

token = access.issue_consent(
    beo_domain="alice.bsp",
    ieo_domain="genomicslab.bsp",
    intents=["SUBMIT_RECORD", "READ_RECORDS"],
    categories=["METABOLIC", "HORMONAL"],
    levels=["CORE", "STANDARD"],
    expires_at=expires_at,
)

print(f"  Token ID : {token.token_id}")
print(f"  Valid    : {token.is_valid()}")
print(f"  Expires  : {token.expires_at}")
print()


# ── 5. Lab builds and submits records ────────────────────────────────────────

print("[4/6] Building and submitting BioRecords...")

glucose = (
    BioRecordBuilder(ieo_domain="genomicslab.bsp")
    .set_beo_id(alice.beo_id)
    .set_biomarker("BSP-GL-001")        # Fasting glucose
    .set_value(94)
    .set_unit("mg/dL")
    .set_collection_time("2026-03-24T08:30:00Z")
    .set_ref_range(optimal="70-99", functional="60-125", unit="mg/dL")
    .set_confidence(0.99)
    .set_method("spectrophotometry")
    .set_equipment("Roche Cobas c502")
    .build()
)

hba1c = (
    BioRecordBuilder(ieo_domain="genomicslab.bsp")
    .set_beo_id(alice.beo_id)
    .set_biomarker("BSP-HBA1C-001")     # Glycated hemoglobin
    .set_value(5.4)
    .set_unit("%")
    .set_collection_time("2026-03-24T08:30:00Z")
    .set_ref_range(optimal="4.0-5.6", functional="4.0-6.4", unit="%")
    .set_confidence(0.98)
    .set_method("HPLC")
    .build()
)

insulin = (
    BioRecordBuilder(ieo_domain="genomicslab.bsp")
    .set_beo_id(alice.beo_id)
    .set_biomarker("BSP-INS-001")       # Fasting insulin
    .set_value(7.2)
    .set_unit("µIU/mL")
    .set_collection_time("2026-03-24T08:30:00Z")
    .set_ref_range(optimal="2.6-8.0", functional="2.0-16.0", unit="µIU/mL")
    .set_confidence(0.97)
    .build()
)

exchange = ExchangeClient(config)

try:
    result = exchange.submit_records([glucose, hba1c, insulin], token=token)
    print(f"  Status      : {result.status}")
    print(f"  Records     : {result.record_ids}")
    print(f"  Aptos TXs : {result.aptos_txs}")

    if result.error:
        err: BSPError = result.error
        print(f"  Error [{err.code}]: {err.message} (retryable={err.retryable})")

except PermissionError as e:
    print(f"  Consent error: {e}")
    raise
print()


# ── 6. Query records ─────────────────────────────────────────────────────────

print("[5/6] Querying records...")
filters = ReadFilters(
    categories=["METABOLIC"],
    from_date="2026-01-01T00:00:00Z",
    limit=20,
)

data = exchange.read_records(beo_id=alice.beo_id, token=token, filters=filters)
print(f"  Total records : {data.total}")
print(f"  Returned      : {len(data.records)}")
print(f"  Has more      : {data.has_more}")
print()

for rec in data.records:
    print(f"  {rec.biomarker:20s}  {rec.value:>8} {rec.unit}")
print()


# ── 7. Revoke consent ────────────────────────────────────────────────────────

print("[6/6] Revoking consent...")
revocation = access.revoke_consent(token.token_id)
print(f"  Revoked : {revocation.get('token_id', token.token_id)}")

# Verify it's no longer valid
assert not access.verify_consent(token, intent="READ_RECORDS"), (
    "Token should be invalid after revocation"
)
print("  Token correctly invalidated.")
print()

print("Full flow complete.")
