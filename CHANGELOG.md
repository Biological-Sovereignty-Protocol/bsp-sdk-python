# Changelog — bsp-sdk (Python)

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-03-24

### Added

- `BSPClient` — top-level client with unified config (`BSPConfig`)
- `BEOClient` — create, resolve, get, lock/unlock, update_recovery, is_available
- `IEOBuilder` — register and preview Institutional Entity Objects
- `BioRecordBuilder` — fluent builder for `BioRecord` with full validation
- `ExchangeClient` — submit_records, read_records, sovereign_export
- `AccessManager` — issue_consent, verify_consent, revoke_consent, revoke_all_from_ieo, revoke_all_tokens, get_token_history
- `TaxonomyResolver` — validate and resolve BSP biomarker taxonomy codes
- Full type system in `bsp_sdk/types.py`:
  - `BEO`, `Guardian`, `RecoveryConfig`
  - `IEO`, `IEOCertification`
  - `BioRecord`, `RangeObject`, `SourceMeta`
  - `ConsentToken`, `TokenScope`
  - `SubmitResult`, `ReadResult`, `ReadFilters`
  - `BSPConfig`, `BSPError`, `BSPStatus`
  - Literals: `BEOStatus`, `IEOStatus`, `IEOType`, `CertLevel`, `BioLevel`, `RecordStatus`, `BSPIntent`, `TokenScope`
- `ConsentToken.is_valid()` and `is_expired()` helper methods
- `bsp_sdk.async_` submodule with async equivalents of all I/O clients
- Python 3.10, 3.11, 3.12 support
- Full type annotations throughout (`mypy --strict` clean)
- `examples/full_flow.py` — runnable end-to-end example

### Infrastructure

- Build system: Hatchling via `pyproject.toml`
- Linting: Ruff (line-length 100, target py310)
- Type checking: mypy strict mode
- Test runner: pytest with coverage

---

## [2.0.0] — 2026-04-17

### Changed — Aptos Migration

- **BREAKING**: Migrated execution layer from AO/Arweave to **Aptos** (Move smart contracts)
- All `arweave_tx` fields renamed to `aptos_tx` across types (`BEO`, `IEO`, `BioRecord`, `ConsentToken`)
- `SubmitResult.arweave_txs` renamed to `aptos_txs`
- `BSPConfig.arweave_node` removed, replaced with `contract_address`, `aptos_network`, and `aptos_node_url`
- Added `AptosNetwork` type literal (`mainnet`, `testnet`, `devnet`, `local`)
- Error code `BSP_ARWEAVE_UNAVAILABLE` replaced with `APTOS_TIMEOUT`
- Updated all docstrings and comments to reference Aptos instead of Arweave
- Updated `BSPClient.__init__` to accept new Aptos config parameters

### Note

- Arweave references for **data storage** context remain valid (historical)
- The SDK talks to the `bsp-registry-api`, not directly to the Aptos chain
- The registry API acts as a relayer (pays gas on behalf of users)

---

## [Unreleased]

### Planned

- `bsp_sdk.async_` — async client implementations (currently interface only)
- `TaxonomyResolver.search()` — fuzzy search across BSP taxonomy
- `BioRecordBuilder.from_fhir()` — import from FHIR R4 Observation
- `ExchangeClient.batch_export()` — paginated bulk export
- Streaming support for large `sovereign_export` payloads
- CLI tool: `bsp-sdk` command for registry lookups and token management
