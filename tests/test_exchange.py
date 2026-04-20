"""Tests for ExchangeClient — submit_records and read_records."""

from __future__ import annotations

from typing import Any, Optional

import pytest

from bsp_sdk.exchange import ExchangeClient
from bsp_sdk.http_client import BSPApiError
from bsp_sdk.types import BSPConfig, BioRecord, ReadFilters


# ── Fake HTTP client (same pattern as test_access.py) ─────────────────────────

class FakeHttp:
    """Records every request and returns pre-seeded responses."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses: dict[tuple[str, str], Any] = {}
        self.errors: dict[tuple[str, str], BSPApiError] = {}

    def seed(self, method: str, path: str, response: Any) -> None:
        self.responses[(method.upper(), path)] = response

    def seed_error(self, method: str, path: str, err: BSPApiError) -> None:
        self.errors[(method.upper(), path)] = err

    def _dispatch(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append({"method": method.upper(), "path": path, **kwargs})
        key = (method.upper(), path)
        if key in self.errors:
            raise self.errors[key]
        if key in self.responses:
            return self.responses[key]
        return {}

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        return self._dispatch("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self._dispatch("POST", path, body=body)

    def delete(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self._dispatch("DELETE", path, body=body)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> tuple[ExchangeClient, FakeHttp]:
    config = BSPConfig(
        ieo_domain="fleury.bsp",
        private_key="a" * 64,
        environment="local",
        registry_url="http://localhost:3000",
    )
    http = FakeHttp()
    return ExchangeClient(config, http=http), http  # type: ignore[arg-type]


def _make_record(biomarker: str = "BSP-HM-001") -> dict[str, Any]:
    """Minimal dict that stands in for a BioRecord in HTTP payloads."""
    return {
        "record_id":    "00000000-0000-0000-0000-000000000001",
        "beo_id":       "550e8400-e29b-41d4-a716-446655440000",
        "ieo_id":       "770e8400-e29b-41d4-a716-446655440001",
        "version":      "1.0.0",
        "biomarker":    biomarker,
        "category":     "BSP-HM",
        "level":        "STANDARD",
        "value":        13.8,
        "unit":         "g/dL",
        "collected_at": "2026-04-19T08:00:00Z",
        "submitted_at": "2026-04-19T10:00:00Z",
        "status":       "ACTIVE",
        "supersedes":   None,
        "confidence":   None,
    }


def _submit_result() -> dict[str, Any]:
    return {
        "request_id": "req-abc123",
        "status":     "SUCCESS",
        "record_ids": ["00000000-0000-0000-0000-000000000001"],
        "aptos_txs":  ["0xdeadbeef"],
        "timestamp":  "2026-04-19T10:00:00Z",
    }


def _read_result(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if records is None:
        records = [_make_record()]
    return {
        "request_id": "req-read-001",
        "beo_id":     "550e8400-e29b-41d4-a716-446655440000",
        "records":    records,
        "total":      len(records),
        "has_more":   False,
    }


# ── submit_records ────────────────────────────────────────────────────────────

class TestSubmitRecords:
    def test_submit_records_success(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        """Happy path — HTTP 200 returns SubmitResult with aptos_txs."""
        exc, http = client
        http.seed("POST", "/api/exchange/records", _submit_result())

        result = exc.submit_records(
            target_beo="patient.bsp",
            records=[_make_record()],  # type: ignore[list-item]
            consent_token="tok_abc",
        )

        assert result["request_id"] == "req-abc123"
        assert result["status"] == "SUCCESS"
        assert "0xdeadbeef" in result["aptos_txs"]

        call = http.calls[0]
        assert call["method"] == "POST"

    def test_submit_empty_records_raises(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        exc, _ = client
        with pytest.raises(ValueError, match="At least one BioRecord"):
            exc.submit_records(
                target_beo="patient.bsp",
                records=[],
                consent_token="tok_abc",
            )

    def test_submit_too_many_records_raises(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        exc, _ = client
        records = [_make_record() for _ in range(101)]  # type: ignore[misc]
        with pytest.raises(ValueError, match="Maximum 100"):
            exc.submit_records(
                target_beo="patient.bsp",
                records=records,  # type: ignore[arg-type]
                consent_token="tok_abc",
            )


# ── read_records ──────────────────────────────────────────────────────────────

class TestReadRecords:
    def test_read_records_success(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        """Happy path — HTTP 200 returns ReadResult with records list."""
        exc, http = client
        http.seed("GET", "/api/exchange/records", _read_result())

        result = exc.read_records(
            target_beo="patient.bsp",
            consent_token="tok_abc",
        )

        assert result["beo_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert len(result["records"]) == 1
        assert result["records"][0]["biomarker"] == "BSP-HM-001"
        assert result["has_more"] is False

    def test_read_records_with_filters(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        exc, http = client
        http.seed("GET", "/api/exchange/records", _read_result([_make_record("BSP-LA-001")]))

        result = exc.read_records(
            target_beo="patient.bsp",
            consent_token="tok_abc",
            filters=ReadFilters(categories=["BSP-LA"]),
        )

        assert result["records"][0]["biomarker"] == "BSP-LA-001"

    def test_read_records_empty_list(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        exc, http = client
        http.seed("GET", "/api/exchange/records", _read_result([]))

        result = exc.read_records(
            target_beo="patient.bsp",
            consent_token="tok_abc",
        )

        assert result["records"] == []
        assert result["total"] == 0


# ── token requirements ────────────────────────────────────────────────────────

class TestTokenRequired:
    def test_submit_requires_token(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        """Calling submit_records with empty consent_token must raise."""
        exc, _ = client
        with pytest.raises((ValueError, TypeError, Exception)):
            exc.submit_records(
                target_beo="patient.bsp",
                records=[_make_record()],  # type: ignore[list-item]
                consent_token="",
            )

    def test_read_requires_token(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        """Calling read_records with empty consent_token must raise."""
        exc, _ = client
        with pytest.raises((ValueError, TypeError, Exception)):
            exc.read_records(
                target_beo="patient.bsp",
                consent_token="",
            )

    def test_expired_token_raises_bsp_error(self, client: tuple[ExchangeClient, FakeHttp]) -> None:
        """API returning TOKEN_EXPIRED (403) propagates as BSPApiError."""
        exc, http = client
        http.seed_error(
            "GET", "/api/exchange/records",
            BSPApiError("TOKEN_EXPIRED", 403),
        )

        with pytest.raises(BSPApiError) as exc_info:
            exc.read_records(
                target_beo="patient.bsp",
                consent_token="tok_expired",
            )

        assert exc_info.value.status_code == 403
