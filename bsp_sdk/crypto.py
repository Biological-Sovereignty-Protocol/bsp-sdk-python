"""
CryptoUtils — Ed25519 key generation, deterministic signing, and verification.

Paired with the TS SDK (`bsp-sdk-typescript/src/utils/CryptoUtils.ts`). Payloads
are signed using a sorted (deterministic) JSON representation so that signatures
produced in Python verify in TypeScript and vice-versa.

Example::

    from bsp_sdk.crypto import CryptoUtils

    keypair = CryptoUtils.generate_key_pair()
    sig = CryptoUtils.sign_payload({"foo": 1, "bar": 2}, keypair["private_key"])
    ok = CryptoUtils.verify_signature({"foo": 1, "bar": 2}, sig, keypair["public_key"])
    assert ok is True
"""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any, TypedDict

from nacl import signing
from nacl.exceptions import BadSignatureError


class KeyPair(TypedDict):
    """Ed25519 key pair (all hex-encoded)."""

    public_key: str   # 32 bytes, hex
    private_key: str  # 64 bytes (seed + public), hex — matches tweetnacl layout
    seed: str         # 32 bytes, hex — recovery material (store offline)


class CryptoUtils:
    """Ed25519 signing utilities — Python implementation paired with TS SDK."""

    # ── Key management ────────────────────────────────────────────────────────

    @staticmethod
    def generate_key_pair() -> KeyPair:
        """Generate a new Ed25519 key pair. Seed is random 32 bytes."""
        sk = signing.SigningKey.generate()
        return CryptoUtils._pack_keypair(sk)

    @staticmethod
    def key_pair_from_seed(seed_hex: str) -> KeyPair:
        """Restore a key pair from a 32-byte hex-encoded seed."""
        seed = bytes.fromhex(seed_hex.removeprefix("0x"))
        if len(seed) != 32:
            raise ValueError(f"Seed must be 32 bytes — got {len(seed)}")
        sk = signing.SigningKey(seed)
        return CryptoUtils._pack_keypair(sk)

    @staticmethod
    def generate_nonce() -> str:
        """Generate a 16-byte hex nonce for replay protection."""
        return secrets.token_hex(16)

    # ── Signing / verification ────────────────────────────────────────────────

    @staticmethod
    def sign_payload(payload: dict[str, Any], private_key_hex: str) -> str:
        """
        Sign a JSON payload deterministically with an Ed25519 private key.

        Expects the private key in the tweetnacl layout (64 bytes: seed ‖ pub).
        Returns the signature as a base64 string.
        """
        sk_bytes = bytes.fromhex(private_key_hex.removeprefix("0x"))
        if len(sk_bytes) != 64:
            raise ValueError(
                "Invalid private key length. Expected 64 bytes for Ed25519 "
                f"secret key (seed+public), got {len(sk_bytes)}",
            )
        seed = sk_bytes[:32]
        sk = signing.SigningKey(seed)
        message = CryptoUtils._stringify_deterministic(payload).encode("utf-8")
        signed = sk.sign(message)
        return base64.b64encode(signed.signature).decode("ascii")

    @staticmethod
    def verify_signature(
        payload: dict[str, Any],
        signature_b64: str,
        public_key_hex: str,
    ) -> bool:
        """Verify a base64 signature against a hex-encoded Ed25519 public key."""
        try:
            pk_bytes = bytes.fromhex(public_key_hex.removeprefix("0x"))
            if len(pk_bytes) != 32:
                return False
            sig_bytes = base64.b64decode(signature_b64)
            message = CryptoUtils._stringify_deterministic(payload).encode("utf-8")
            vk = signing.VerifyKey(pk_bytes)
            vk.verify(message, sig_bytes)
            return True
        except (BadSignatureError, ValueError, TypeError):
            return False

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _pack_keypair(sk: signing.SigningKey) -> KeyPair:
        seed_bytes = bytes(sk)                    # 32 bytes
        pub_bytes = bytes(sk.verify_key)          # 32 bytes
        secret_bytes = seed_bytes + pub_bytes     # 64 bytes (tweetnacl layout)
        return KeyPair(
            public_key=pub_bytes.hex(),
            private_key=secret_bytes.hex(),
            seed=seed_bytes.hex(),
        )

    @staticmethod
    def canonical_stringify(obj: Any) -> str:
        """Canonical JSON — public for cross-SDK parity with TypeScript SDK.

        Mirrors ``CryptoUtils.canonicalStringify`` in the TS SDK: recursive
        key sort + compact separators + ensure_ascii=False so UTF-8 strings
        pass through verbatim. Both SDKs must produce byte-identical output
        for the same input.
        """
        sorted_obj = CryptoUtils._sort_object_keys(obj)
        return json.dumps(sorted_obj, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _stringify_deterministic(obj: dict[str, Any]) -> str:
        """Alias kept for backward compatibility — delegates to canonical_stringify."""
        return CryptoUtils.canonical_stringify(obj)

    @staticmethod
    def _sort_object_keys(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: CryptoUtils._sort_object_keys(obj[k]) for k in sorted(obj)}
        if isinstance(obj, list):
            return [CryptoUtils._sort_object_keys(v) for v in obj]
        return obj
