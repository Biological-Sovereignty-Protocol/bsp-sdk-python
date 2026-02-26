# bsp-sdk — Python SDK for the Biological Sovereignty Protocol

> Official Python SDK for the [Biological Sovereignty Protocol (BSP)](https://github.com/Biological-Sovereignty-Protocol/bsp-spec)
> Published by the Ambrósio Institute · ambrosio.health · bsp.dev

## Installation

```bash
pip install bsp-sdk
```

## Quick Start

```python
from bsp_sdk import BEOClient, BioRecordBuilder, ExchangeClient

# Create a BEO
client = BEOClient()
beo = client.create(domain="andre.bsp")

# Build a BioRecord
record = (BioRecordBuilder()
    .beo_id(beo.beo_id)
    .biomarker("BSP-GL-001")    # Fasting glucose
    .value(94)
    .unit("mg/dL")
    .timestamp("2026-02-24T08:30:00Z")
    .confidence(0.99)
    .build())

# Submit with consent token
exchange = ExchangeClient(ieo_id="my-lab.bsp")
result = exchange.submit(record, token=consent_token)
```

## Modules

| Module | Description |
|---|---|
| `BEOClient` | Create and manage Biological Entity Objects |
| `BioRecordBuilder` | Build and validate BioRecords |
| `ExchangeClient` | Submit and read biological data |
| `TaxonomyResolver` | Validate and resolve BSP biomarker codes |
| `AccessManager` | Manage consent tokens on-chain |

## Documentation

Full documentation: [bsp.dev](https://bsp.dev)
Protocol specification: [bsp-spec](https://github.com/Biological-Sovereignty-Protocol/bsp-spec)

## Requirements

- Python >= 3.10

## License

Apache 2.0 — Ambrósio Institute
