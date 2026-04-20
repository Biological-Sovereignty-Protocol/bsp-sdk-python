"""
Example 04 — Destroy / retire a BEO

Sovereign exit flow: the individual revokes all active consent tokens and
then locks the BEO, rendering it permanently inaccessible without the
recovery seed phrase.

A BEO cannot be forcibly deleted on-chain (immutability), but it can be
LOCKED. Re-activation requires the seed phrase used at creation time.

Run:
    python examples/04_destroy_beo.py
"""

from __future__ import annotations

import os
import secrets

from bsp_sdk import AccessManager, BEOClient, BSPConfig


def main() -> None:
    simulate = "BSP_RELAYER_URL" not in os.environ
    beo_domain = os.environ.get("BSP_BEO_DOMAIN", "alice.bsp")

    print("─── Example 04 — Destroy / Lock BEO ─────────────────────────")
    print(f"Mode : {'SIMULATED' if simulate else 'LIVE'}")
    print(f"BEO  : {beo_domain}")
    print()

    if simulate:
        print("[SIM] Step 1 — revoke all active consent tokens...")
        print("[SIM]   revoked 2 tokens")
        print("[SIM] Step 2 — lock BEO on-chain...")
        print("[SIM]   beo status : LOCKED")
        print(f"[SIM]   aptos_tx   : aptos_tx_{secrets.token_hex(6)}")
        print()
        print("BEO is now locked. To re-activate, use the 24-word seed phrase")
        print("with BEOClient.recover(seed_phrase, domain).")
        return

    config = BSPConfig(
        ieo_domain=os.environ.get("BSP_IEO_DOMAIN", "bsp.network"),
        private_key=os.environ["BSP_BEO_PRIVATE_KEY"],
        environment=os.environ.get("BSP_NETWORK", "testnet"),
    )

    # Step 1 — revoke every active token
    print("Step 1 — revoking all active consent tokens...")
    access = AccessManager(config)
    revoked = access.revoke_all_tokens(beo_domain=beo_domain)
    print(f"  revoked: {revoked}")
    print()

    # Step 2 — lock the BEO
    print("Step 2 — locking BEO...")
    beo_client = BEOClient(config)
    result = beo_client.lock(beo_domain)
    print(f"  status : {result.status}")
    print()
    print("BEO locked. The 24-word seed phrase is the only way back in.")


if __name__ == "__main__":
    main()
