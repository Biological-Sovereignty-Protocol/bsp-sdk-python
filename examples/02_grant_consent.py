"""
Example 02 — Grant consent from a BEO to an IEO

Issues a ConsentToken that authorizes an institution (IEO) to submit and
read records for a specific individual (BEO) within a scoped set of
intents, categories, and levels.

Run:
    python examples/02_grant_consent.py
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

from bsp_sdk import AccessManager, BSPConfig


def main() -> None:
    simulate = "BSP_RELAYER_URL" not in os.environ

    beo_domain = os.environ.get("BSP_BEO_DOMAIN", "alice.bsp")
    ieo_domain = os.environ.get("BSP_IEO_DOMAIN", "genomicslab.bsp")

    expires_at = (datetime.now(tz=timezone.utc) + timedelta(days=90)).isoformat()

    print("─── Example 02 — Grant Consent ──────────────────────────────")
    print(f"Mode : {'SIMULATED' if simulate else 'LIVE'}")
    print(f"BEO  : {beo_domain}")
    print(f"IEO  : {ieo_domain}")
    print()

    if simulate:
        token = {
            "token_id": f"tok_{secrets.token_hex(4)}",
            "beo_domain": beo_domain,
            "ieo_domain": ieo_domain,
            "intents": ["SUBMIT_RECORD", "READ_RECORDS"],
            "categories": ["METABOLIC", "HORMONAL"],
            "levels": ["CORE", "STANDARD"],
            "granted_at": datetime.now(tz=timezone.utc).isoformat(),
            "expires_at": expires_at,
            "revoked_at": None,
        }
        print("ConsentToken (simulated):")
        for k, v in token.items():
            print(f"  {k:12s}: {v}")
        print()
        print("Next step: examples/03_submit_biorecord.py")
        return

    config = BSPConfig(
        ieo_domain=ieo_domain,
        private_key=os.environ["BSP_PRIVATE_KEY"],
        environment=os.environ.get("BSP_NETWORK", "testnet"),
    )
    access = AccessManager(config)

    token = access.issue_consent(
        beo_domain=beo_domain,
        ieo_domain=ieo_domain,
        intents=["SUBMIT_RECORD", "READ_RECORDS"],
        categories=["METABOLIC", "HORMONAL"],
        levels=["CORE", "STANDARD"],
        expires_at=expires_at,
    )

    print("ConsentToken issued:")
    print(f"  token_id   : {token.token_id}")
    print(f"  granted_at : {token.granted_at}")
    print(f"  expires_at : {token.expires_at}")
    print()
    print("Next step: examples/03_submit_biorecord.py")


if __name__ == "__main__":
    main()
