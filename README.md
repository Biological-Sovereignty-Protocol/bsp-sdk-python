# bsp-sdk — Python SDK for the Biological Sovereignty Protocol

[![PyPI version](https://img.shields.io/pypi/v/bsp-sdk.svg)](https://pypi.org/project/bsp-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/bsp-sdk.svg)](https://pypi.org/project/bsp-sdk/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Official Python SDK for the [Biological Sovereignty Protocol (BSP)](https://github.com/Biological-Sovereignty-Protocol/bsp-spec).
Published by the Ambrósio Institute · [ambrosioinstitute.org](https://ambrosioinstitute.org) · [biologicalsovereigntyprotocol.com](https://biologicalsovereigntyprotocol.com)

---

## Installation

```bash
pip install bsp-sdk
```

```bash
poetry add bsp-sdk
```

Requires Python >= 3.10.

---

## Quick Start

```python
import os
from bsp_sdk import BSPClient, BEOClient, BioRecordBuilder, AccessManager, ExchangeClient

# 1. Configure the client (as an institution / IEO)
client = BSPClient(
    ieo_domain="genomicslab.bsp",
    private_key=os.environ["BSP_IEO_PRIVATE_KEY"],
    environment="mainnet",
)

# 2. Alice creates her BEO (Biological Entity Object)
beo_client = BEOClient(client.config)
alice = beo_client.create(domain="alice.bsp")

# 3. Alice grants consent to the lab
access = AccessManager(client.config)
token = access.issue_consent(
    beo_domain="alice.bsp",
    ieo_domain="genomicslab.bsp",
    intents=["SUBMIT_RECORD", "READ_RECORDS"],
    categories=["METABOLIC"],
)

# 4. Lab submits a biomarker record
record = (
    BioRecordBuilder(ieo_domain="genomicslab.bsp")
    .set_beo_id(alice.beo_id)
    .set_biomarker("BSP-GL-001")
    .set_value(94)
    .set_unit("mg/dL")
    .set_collection_time("2026-02-24T08:30:00Z")
    .set_confidence(0.99)
    .build()
)

exchange = ExchangeClient(client.config)
result = exchange.submit_records([record], token=token)
print(result.aptos_txs)  # permanent tx hashes on Aptos
```

---

## Full API Reference

### `BEOClient`

Manages Biological Entity Objects — the sovereign identity anchors for individuals.

```python
from bsp_sdk import BEOClient, BSPConfig

config = BSPConfig(ieo_domain="lab.bsp", private_key="...", environment="mainnet")
beo = BEOClient(config)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `create` | `(domain, guardians?, recovery_threshold?) -> BEO` | Register a new BEO on Aptos |
| `resolve` | `(domain: str) -> BEO` | Resolve a `.bsp` domain to its BEO |
| `get` | `(beo_id: str) -> BEO` | Fetch a BEO by ID |
| `is_available` | `(domain: str) -> bool` | Check if a domain is unclaimed |
| `lock` | `(reason?) -> dict` | Lock a BEO against new writes |
| `unlock` | `() -> dict` | Unlock a previously locked BEO |
| `update_recovery` | `(config: RecoveryConfig) -> dict` | Update guardian recovery settings |

```python
# Create with guardians
from bsp_sdk import Guardian, RecoveryConfig

guardians = [
    Guardian(name="Bob", contact="bob@email.com", public_key="0xabc...",
             role="primary", accepted=True, added_at="2026-01-01T00:00:00Z")
]
recovery = RecoveryConfig(enabled=True, threshold=1, guardians=guardians)
beo = beo_client.create(domain="alice.bsp", guardians=guardians, recovery_threshold=1)

# Rotate key — lock old BEO, create new one
beo_client.lock(reason="key rotation")
new_beo = beo_client.create(domain="alice.bsp")
```

---

### `IEOBuilder`

Builds and registers Institutional Entity Objects — identity anchors for labs, hospitals, and platforms.

```python
from bsp_sdk import IEOBuilder, BSPConfig

ieo = IEOBuilder(
    config=config,
    domain="genomicslab.bsp",
    display_name="Genomics Lab Inc.",
    ieo_type="LABORATORY",
    country="BR",
    jurisdiction="BR-SP",
    legal_id="12.345.678/0001-99",
)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `() -> dict` | Register the IEO on Aptos |
| `preview` | `() -> dict` | Dry-run — validate without committing |

---

### `BioRecordBuilder`

Constructs and validates `BioRecord` objects before submission. All setter methods return `self` for chaining.

```python
from bsp_sdk import BioRecordBuilder

record = (
    BioRecordBuilder(ieo_domain="lab.bsp")
    .set_beo_id("beo_alice_xyz")
    .set_biomarker("BSP-GL-001")       # BSP taxonomy code
    .set_value(94)
    .set_unit("mg/dL")
    .set_collection_time("2026-02-24T08:30:00Z")
    .set_ref_range(optimal="70-99", functional="60-125", unit="mg/dL")
    .set_confidence(0.99)
    .set_method("spectrophotometry")
    .set_equipment("Roche Cobas c502")
    .build()
)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `set_beo_id` | `(beo_id: str) -> self` | Target BEO |
| `set_biomarker` | `(code: str) -> self` | BSP taxonomy code (e.g. `BSP-GL-001`) |
| `set_value` | `(value: float | str | dict) -> self` | Measurement value |
| `set_unit` | `(unit: str) -> self` | Unit of measure |
| `set_collection_time` | `(iso8601: str) -> self` | ISO-8601 collection timestamp |
| `set_ref_range` | `(optimal, functional, unit, ...) -> self` | Reference ranges |
| `set_confidence` | `(confidence: float) -> self` | 0.0–1.0 confidence score |
| `set_method` | `(method: str) -> self` | Measurement method |
| `set_equipment` | `(equipment: str) -> self` | Equipment identifier |
| `supersedes` | `(record_id: str) -> self` | ID of record being superseded |
| `build` | `() -> BioRecord` | Validate and return the record |

---

### `ExchangeClient`

Submit and read biological data through the BSP exchange layer.

```python
from bsp_sdk import ExchangeClient

exchange = ExchangeClient(config)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `submit_records` | `(records: list[BioRecord], token: ConsentToken) -> SubmitResult` | Submit one or more records |
| `read_records` | `(beo_id: str, token: ConsentToken, filters?: ReadFilters) -> ReadResult` | Read records with consent |
| `sovereign_export` | `(beo_id: str, format?: ExportFormat) -> bytes` | Export all data for a BEO |

```python
# Submit multiple records
result = exchange.submit_records([glucose_record, hba1c_record], token=token)
# result.status == "SUCCESS"
# result.aptos_txs == ["0xabc...", "0xdef..."]

# Read with filters
from bsp_sdk import ReadFilters
filters = ReadFilters(categories=["METABOLIC"], from_date="2026-01-01T00:00:00Z", limit=50)
data = exchange.read_records(beo_id=alice.beo_id, token=token, filters=filters)
for record in data.records:
    print(record.biomarker, record.value, record.unit)
```

---

### `AccessManager`

Grant, revoke, and verify consent tokens — the authorization layer of BSP.

```python
from bsp_sdk import AccessManager

access = AccessManager(config)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `issue_consent` | `(beo_domain, ieo_domain, intents, categories, levels?, expires_at?) -> ConsentToken` | Grant consent |
| `verify_consent` | `(token: ConsentToken, intent, category?, level?) -> bool` | Verify a token is valid for an operation |
| `revoke_consent` | `(token_id: str) -> dict` | Revoke a specific token |
| `revoke_all_from_ieo` | `(ieo_domain: str) -> dict` | Revoke all tokens for one institution |
| `revoke_all_tokens` | `() -> dict` | Nuclear option — revoke everything |
| `get_token_history` | `(beo_domain: str) -> list[ConsentToken]` | Audit trail of all issued tokens |

```python
# Grant time-limited consent
from datetime import datetime, timezone, timedelta

expires = (datetime.now(tz=timezone.utc) + timedelta(days=90)).isoformat()
token = access.issue_consent(
    beo_domain="alice.bsp",
    ieo_domain="genomicslab.bsp",
    intents=["SUBMIT_RECORD", "READ_RECORDS"],
    categories=["METABOLIC", "GENETIC"],
    levels=["CORE", "STANDARD"],
    expires_at=expires,
)

# Verify before use
if access.verify_consent(token, intent="SUBMIT_RECORD", category="METABOLIC"):
    exchange.submit_records([record], token=token)

# Revoke when done
access.revoke_consent(token.token_id)
```

---

## Complete Flow Example

```python
"""
Full BSP flow: alice.bsp → genomicslab.bsp
- BEO creation
- IEO registration
- Consent grant
- Record submission
- Querying
"""
import os
from bsp_sdk import (
    BSPClient, BEOClient, IEOBuilder, BioRecordBuilder,
    AccessManager, ExchangeClient, BSPConfig, ReadFilters,
)

# ── Config ──────────────────────────────────────────────────────────────────
config = BSPConfig(
    ieo_domain="genomicslab.bsp",
    private_key=os.environ["BSP_IEO_PRIVATE_KEY"],
    environment="testnet",
)

# ── Register the lab (IEO) ───────────────────────────────────────────────────
lab = IEOBuilder(
    config=config,
    domain="genomicslab.bsp",
    display_name="Genomics Lab",
    ieo_type="LABORATORY",
    country="BR",
    jurisdiction="BR-SP",
    legal_id="12.345.678/0001-99",
)
lab.register()

# ── Alice creates her BEO ───────────────────────────────────────────────────
beo_client = BEOClient(config)
alice = beo_client.create(domain="alice.bsp")
print(f"Alice BEO: {alice.beo_id}")

# ── Alice grants consent ─────────────────────────────────────────────────────
access = AccessManager(config)
token = access.issue_consent(
    beo_domain="alice.bsp",
    ieo_domain="genomicslab.bsp",
    intents=["SUBMIT_RECORD", "READ_RECORDS"],
    categories=["METABOLIC"],
    levels=["CORE", "STANDARD"],
)

# ── Lab builds records ───────────────────────────────────────────────────────
glucose = (
    BioRecordBuilder(ieo_domain="genomicslab.bsp")
    .set_beo_id(alice.beo_id)
    .set_biomarker("BSP-GL-001")
    .set_value(94)
    .set_unit("mg/dL")
    .set_collection_time("2026-03-24T08:30:00Z")
    .set_ref_range(optimal="70-99", functional="60-125", unit="mg/dL")
    .set_confidence(0.99)
    .set_method("spectrophotometry")
    .build()
)

hba1c = (
    BioRecordBuilder(ieo_domain="genomicslab.bsp")
    .set_beo_id(alice.beo_id)
    .set_biomarker("BSP-HBA1C-001")
    .set_value(5.4)
    .set_unit("%")
    .set_collection_time("2026-03-24T08:30:00Z")
    .set_ref_range(optimal="4.0-5.6", functional="4.0-6.4", unit="%")
    .set_confidence(0.98)
    .build()
)

# ── Submit ───────────────────────────────────────────────────────────────────
exchange = ExchangeClient(config)
result = exchange.submit_records([glucose, hba1c], token=token)
print(f"Submitted: {result.status}")
print(f"Aptos TXs: {result.aptos_txs}")

# ── Query ────────────────────────────────────────────────────────────────────
filters = ReadFilters(categories=["METABOLIC"], limit=10)
data = exchange.read_records(beo_id=alice.beo_id, token=token, filters=filters)
print(f"Total records: {data.total}")
for record in data.records:
    print(f"  {record.biomarker}: {record.value} {record.unit}")

# ── Alice revokes consent when done ──────────────────────────────────────────
access.revoke_consent(token.token_id)
print("Consent revoked.")
```

---

## Error Handling

```python
from bsp_sdk import BSPError, ExchangeClient, AccessManager

exchange = ExchangeClient(config)
access = AccessManager(config)

try:
    result = exchange.submit_records([record], token=token)
    if result.error:
        err: BSPError = result.error
        print(f"[{err.code}] {err.message}")
        if err.retryable:
            # safe to retry
            result = exchange.submit_records([record], token=token)

except ValueError as e:
    # Validation errors (missing fields, invalid biomarker codes, etc.)
    print(f"Validation error: {e}")

except PermissionError as e:
    # Consent token invalid, expired, or revoked
    print(f"Access denied: {e}")
    # Re-request consent
    new_token = access.issue_consent(...)

except ConnectionError as e:
    # Network or registry unreachable
    print(f"Network error: {e}")
```

### Error codes

| Code | Retryable | Meaning |
|------|-----------|---------|
| `BSP_CONSENT_EXPIRED` | No | Token past its `expires_at` |
| `BSP_CONSENT_REVOKED` | No | Token was explicitly revoked |
| `BSP_CONSENT_SCOPE` | No | Intent/category not covered by token |
| `BSP_BIOMARKER_UNKNOWN` | No | Code not in BSP taxonomy |
| `BSP_IEO_SUSPENDED` | No | Institution suspended |
| `BSP_REGISTRY_TIMEOUT` | Yes | Registry unreachable |
| `APTOS_TIMEOUT` | Yes | Aptos transaction timed out; record is pending |

---

## Async Support

All blocking I/O methods have async equivalents via the `bsp_sdk.async_` submodule:

```python
import asyncio
import os
from bsp_sdk.async_ import AsyncBSPClient, AsyncExchangeClient
from bsp_sdk import BSPConfig, ReadFilters

config = BSPConfig(
    ieo_domain="genomicslab.bsp",
    private_key=os.environ["BSP_IEO_PRIVATE_KEY"],
)

async def main():
    async with AsyncBSPClient(config) as client:
        exchange = AsyncExchangeClient(client.config)
        result = await exchange.submit_records([record], token=token)
        print(result.status)

        data = await exchange.read_records(
            beo_id="alice.bsp",
            token=token,
            filters=ReadFilters(limit=50),
        )
        return data.records

asyncio.run(main())
```

---

## Configuration

All config values can be passed to `BSPConfig` directly or loaded from environment variables.

| `BSPConfig` field | Environment variable | Default | Description |
|-------------------|---------------------|---------|-------------|
| `ieo_domain` | `BSP_IEO_DOMAIN` | required | Your institution's `.bsp` domain |
| `private_key` | `BSP_IEO_PRIVATE_KEY` | required | Ed25519 private key (hex) |
| `environment` | `BSP_ENVIRONMENT` | `mainnet` | `mainnet`, `testnet`, or `local` |
| `registry_url` | `BSP_REGISTRY_URL` | auto | Override BSP registry endpoint |
| `contract_address` | `BSP_CONTRACT_ADDRESS` | auto | Aptos Move contract address |
| `aptos_network` | `BSP_APTOS_NETWORK` | auto | `mainnet`, `testnet`, `devnet`, or `local` |
| `aptos_node_url` | `BSP_APTOS_NODE_URL` | auto | Override Aptos fullnode URL |
| `timeout_s` | `BSP_TIMEOUT_S` | `30.0` | Request timeout in seconds |

```python
# Explicit config
from bsp_sdk import BSPConfig

config = BSPConfig(
    ieo_domain="lab.bsp",
    private_key="ed25519_hex_key",
    environment="testnet",
    timeout_s=60.0,
)

# Or from env vars
import os
config = BSPConfig(
    ieo_domain=os.environ["BSP_IEO_DOMAIN"],
    private_key=os.environ["BSP_IEO_PRIVATE_KEY"],
)
```

---

## Contributing

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Run type checks: `mypy bsp_sdk/`
5. Run linter: `ruff check bsp_sdk/`
6. Open a pull request against `main`

All contributions must pass CI before merging.

---

## License

Apache 2.0 — Ambrósio Institute

See [LICENSE](LICENSE) for details.
