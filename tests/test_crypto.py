"""Tests for CryptoUtils — Ed25519 signing and verification."""

import pytest
from bsp_sdk.crypto import CryptoUtils, KeyPair


class TestKeyGeneration:
    def test_generate_key_pair_returns_keypair(self):
        kp = CryptoUtils.generate_key_pair()
        assert isinstance(kp, dict)
        assert "public_key" in kp
        assert "private_key" in kp
        assert "seed" in kp

    def test_key_lengths(self):
        kp = CryptoUtils.generate_key_pair()
        # hex-encoded: 32 bytes = 64 hex chars, 64 bytes = 128 hex chars
        assert len(kp["public_key"]) == 64
        assert len(kp["private_key"]) == 128
        assert len(kp["seed"]) == 64

    def test_unique_keys(self):
        kp1 = CryptoUtils.generate_key_pair()
        kp2 = CryptoUtils.generate_key_pair()
        assert kp1["public_key"] != kp2["public_key"]
        assert kp1["private_key"] != kp2["private_key"]

    def test_key_pair_from_seed_deterministic(self):
        kp1 = CryptoUtils.generate_key_pair()
        kp2 = CryptoUtils.key_pair_from_seed(kp1["seed"])
        assert kp1["public_key"] == kp2["public_key"]
        assert kp1["private_key"] == kp2["private_key"]

    def test_key_pair_from_seed_with_0x_prefix(self):
        kp1 = CryptoUtils.generate_key_pair()
        kp2 = CryptoUtils.key_pair_from_seed("0x" + kp1["seed"])
        assert kp1["public_key"] == kp2["public_key"]

    def test_key_pair_from_seed_invalid_length(self):
        with pytest.raises(ValueError, match="Seed must be 32 bytes"):
            CryptoUtils.key_pair_from_seed("abcd")


class TestSignAndVerify:
    def setup_method(self):
        self.kp = CryptoUtils.generate_key_pair()
        self.payload = {"biomarker": "BSP-HM-001", "value": 13.8, "unit": "g/dL"}

    def test_sign_returns_base64(self):
        sig = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        assert isinstance(sig, str)
        # Ed25519 signature = 64 bytes = ~88 base64 chars (with padding)
        assert len(sig) > 80
        assert len(sig) < 100

    def test_verify_valid_signature(self):
        sig = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        assert CryptoUtils.verify_signature(self.payload, sig, self.kp["public_key"]) is True

    def test_verify_wrong_payload_fails(self):
        sig = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        wrong_payload = {"biomarker": "BSP-HM-002", "value": 14.0, "unit": "g/dL"}
        assert CryptoUtils.verify_signature(wrong_payload, sig, self.kp["public_key"]) is False

    def test_verify_wrong_key_fails(self):
        sig = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        other_kp = CryptoUtils.generate_key_pair()
        assert CryptoUtils.verify_signature(self.payload, sig, other_kp["public_key"]) is False

    def test_verify_tampered_signature_fails(self):
        sig = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        tampered = "X" + sig[1:]
        assert CryptoUtils.verify_signature(self.payload, tampered, self.kp["public_key"]) is False

    def test_deterministic_signing(self):
        sig1 = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        sig2 = CryptoUtils.sign_payload(self.payload, self.kp["private_key"])
        assert sig1 == sig2

    def test_sign_with_0x_prefix(self):
        sig = CryptoUtils.sign_payload(self.payload, "0x" + self.kp["private_key"])
        assert CryptoUtils.verify_signature(self.payload, sig, self.kp["public_key"]) is True

    def test_sign_invalid_key_length(self):
        with pytest.raises(ValueError, match="Invalid private key length"):
            CryptoUtils.sign_payload(self.payload, "abcd1234")


class TestDeterministicSerialization:
    def test_key_order_does_not_affect_signature(self):
        kp = CryptoUtils.generate_key_pair()
        payload1 = {"z": 1, "a": 2, "m": 3}
        payload2 = {"a": 2, "m": 3, "z": 1}
        sig1 = CryptoUtils.sign_payload(payload1, kp["private_key"])
        sig2 = CryptoUtils.sign_payload(payload2, kp["private_key"])
        assert sig1 == sig2

    def test_nested_objects_sorted(self):
        kp = CryptoUtils.generate_key_pair()
        payload1 = {"outer": {"z": 1, "a": 2}}
        payload2 = {"outer": {"a": 2, "z": 1}}
        sig1 = CryptoUtils.sign_payload(payload1, kp["private_key"])
        sig2 = CryptoUtils.sign_payload(payload2, kp["private_key"])
        assert sig1 == sig2


class TestNonceGeneration:
    def test_nonce_is_hex(self):
        nonce = CryptoUtils.generate_nonce()
        assert isinstance(nonce, str)
        int(nonce, 16)  # should not raise

    def test_nonce_length(self):
        nonce = CryptoUtils.generate_nonce()
        assert len(nonce) == 32  # 16 bytes = 32 hex chars

    def test_nonce_unique(self):
        nonces = [CryptoUtils.generate_nonce() for _ in range(100)]
        assert len(set(nonces)) == 100
