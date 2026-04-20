"""
Example 01 — Create a BEO (Biological Entity Object)

Shows how to create a new BEO, capture its identifiers, and safely store
the returned private key / seed phrase.

Run:
    python examples/01_create_beo.py

Env (optional):
    BSP_RELAYER_URL   — if unset, runs in SIMULATED mode
    BSP_NETWORK       — "mainnet" | "testnet" (default: testnet)
    BSP_BEO_DOMAIN    — default: alice.bsp
"""

from __future__ import annotations

import os
import secrets

from bsp_sdk import BEOClient, BSPConfig


def main() -> None:
    simulate = "BSP_RELAYER_URL" not in os.environ
    domain = os.environ.get("BSP_BEO_DOMAIN", "alice.bsp")

    print("─── Example 01 — Create BEO ─────────────────────────────────")
    print(f"Mode   : {'SIMULATED' if simulate else 'LIVE'}")
    print(f"Domain : {domain}")
    print()

    if simulate:
        print(f"[SIM] Would create BEO for domain: {domain}")
        simulated = {
            "beo_id": f"beo_{domain.replace('.', '_')}_{secrets.token_hex(4)}",
            "domain": domain,
            "aptos_tx": f"aptos_tx_{secrets.token_hex(6)}",
            "private_key": f"BSP_BEO_PRIVATE_KEY_{secrets.token_hex(8)}",
            "seed_phrase": "word1 word2 ... word24",
        }
        print()
        print("BEO (simulated):")
        for k, v in simulated.items():
            print(f"  {k:11s}: {v}")
        print()
        print("⚠  Store private_key in .env as BSP_BEO_PRIVATE_KEY.")
        print("⚠  Write the 24-word seed_phrase on paper and keep it offline.")
        return

    config = BSPConfig(
        ieo_domain=os.environ.get("BSP_IEO_DOMAIN", "bsp.network"),
        private_key=os.environ.get("BSP_PRIVATE_KEY", ""),
        environment=os.environ.get("BSP_NETWORK", "testnet"),
    )
    beo_client = BEOClient(config)

    if beo_client.is_available(domain):
        beo = beo_client.create(domain=domain)
        print("BEO created:")
    else:
        beo = beo_client.resolve(domain)
        print("BEO already exists:")

    print(f"  beo_id : {beo.beo_id}")
    print(f"  domain : {beo.domain}")
    print(f"  status : {beo.status}")
    print()
    print("Next step: examples/02_grant_consent.py")


if __name__ == "__main__":
    main()
