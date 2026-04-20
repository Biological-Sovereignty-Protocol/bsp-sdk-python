"""
Example 03 — Submit a signed BioRecord

An IEO builds a BioRecord via BioRecordBuilder, signs it, and submits it
through ExchangeClient. Consent is verified automatically on the relayer.

Run:
    python examples/03_submit_biorecord.py
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone

from bsp_sdk import BioRecordBuilder, BSPConfig, ExchangeClient


def main() -> None:
    simulate = "BSP_RELAYER_URL" not in os.environ

    beo_domain = os.environ.get("BSP_BEO_DOMAIN", "alice.bsp")
    ieo_domain = os.environ.get("BSP_IEO_DOMAIN", "genomicslab.bsp")

    print("─── Example 03 — Submit BioRecord ───────────────────────────")
    print(f"Mode : {'SIMULATED' if simulate else 'LIVE'}")
    print(f"BEO  : {beo_domain}")
    print(f"IEO  : {ieo_domain}")
    print()

    payload = {
        "beo_domain": beo_domain,
        "ieo_domain": ieo_domain,
        "level": "CORE",
        "category": "METABOLIC",
        "taxonomy_code": "GLU-FAST-001",
        "value": 92,
        "unit": "mg/dL",
        "collected_at": datetime.now(tz=timezone.utc).isoformat(),
        "source": {
            "device": "lab-analyzer-v3",
            "method": "enzymatic",
            "operator_id": "op_42",
        },
    }

    print("BioRecord payload:")
    for k, v in payload.items():
        print(f"  {k:14s}: {v}")
    print()

    if simulate:
        result = {
            "record_id": f"rec_{secrets.token_hex(4)}",
            "submitted_at": datetime.now(tz=timezone.utc).isoformat(),
            "aptos_tx": f"aptos_tx_{secrets.token_hex(6)}",
            "status": "ACCEPTED",
        }
        print("SubmitResult (simulated):")
        for k, v in result.items():
            print(f"  {k:13s}: {v}")
        print()
        print("Next step: examples/04_destroy_beo.py")
        return

    config = BSPConfig(
        ieo_domain=ieo_domain,
        private_key=os.environ["BSP_IEO_PRIVATE_KEY"],
        environment=os.environ.get("BSP_NETWORK", "testnet"),
    )

    record = (
        BioRecordBuilder(config)
        .for_beo(beo_domain)
        .with_level("CORE")
        .with_category("METABOLIC")
        .with_code("GLU-FAST-001")
        .with_value(92, "mg/dL")
        .collected_at(payload["collected_at"])
        .build()
    )

    exchange = ExchangeClient(config)
    result = exchange.submit_record(record)

    print("SubmitResult:")
    print(f"  record_id    : {result.record_id}")
    print(f"  submitted_at : {result.submitted_at}")
    print(f"  aptos_tx     : {result.aptos_tx}")
    print(f"  status       : {result.status}")
    print()
    print("Next step: examples/04_destroy_beo.py")


if __name__ == "__main__":
    main()
