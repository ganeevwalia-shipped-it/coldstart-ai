"""
Tests for input validation, rate limiting, and security hardening.
"""
import time
import pytest
from fastapi import HTTPException
from app.validation import (
    validate_agent_id,
    validate_company_context,
    validate_previous_outputs,
    validate_text_field,
    validate_company_name,
    validate_export_results,
    RateLimiter,
    MAX_COMPANY_CONTEXT_LENGTH,
    MAX_AGENT_OUTPUT_LENGTH,
)
from app.agents.registry import AGENTS


# ========================================
# AGENT ID VALIDATION
# ========================================

class TestValidateAgentId:

    def test_valid_agent_id(self):
        result = validate_agent_id("icp_architect", AGENTS)
        assert result == "icp_architect"

    def test_empty_string_raises(self):
        with pytest.raises(HTTPException) as exc:
            validate_agent_id("", AGENTS)
        assert exc.value.status_code == 400

    def test_none_raises(self):
        with pytest.raises(HTTPException):
            validate_agent_id(None, AGENTS)

    def test_unknown_agent_raises(self):
        with pytest.raises(HTTPException) as exc:
            validate_agent_id("fake_agent", AGENTS)
        assert "Unknown agent" in exc.value.detail

    def test_sql_injection_attempt(self):
        with pytest.raises(HTTPException):
            validate_agent_id("'; DROP TABLE agents; --", AGENTS)

    def test_path_traversal_attempt(self):
        with pytest.raises(HTTPException):
            validate_agent_id("../../etc/passwd", AGENTS)

    def test_very_long_id_rejected(self):
        with pytest.raises(HTTPException):
            validate_agent_id("a" * 100, AGENTS)

    def test_uppercase_rejected(self):
        with pytest.raises(HTTPException):
            validate_agent_id("ICP_ARCHITECT", AGENTS)

    def test_special_chars_rejected(self):
        with pytest.raises(HTTPException):
            validate_agent_id("agent<script>", AGENTS)


# ========================================
# COMPANY CONTEXT VALIDATION
# ========================================

class TestValidateCompanyContext:

    def test_valid_context(self):
        result = validate_company_context("COMPANY: TestCo")
        assert result == "COMPANY: TestCo"

    def test_empty_context_allowed(self):
        result = validate_company_context("")
        assert result == ""

    def test_max_length_context(self):
        ctx = "x" * MAX_COMPANY_CONTEXT_LENGTH
        result = validate_company_context(ctx)
        assert len(result) == MAX_COMPANY_CONTEXT_LENGTH

    def test_over_max_length_raises(self):
        with pytest.raises(HTTPException) as exc:
            validate_company_context("x" * (MAX_COMPANY_CONTEXT_LENGTH + 1))
        assert exc.value.status_code == 400

    def test_non_string_raises(self):
        with pytest.raises(HTTPException):
            validate_company_context(12345)

    def test_unicode_context_allowed(self):
        result = validate_company_context("公司: テスト会社 🚀")
        assert "テスト" in result


# ========================================
# PREVIOUS OUTPUTS VALIDATION
# ========================================

class TestValidatePreviousOutputs:

    def test_valid_outputs(self):
        outputs = {"icp_architect": "output here"}
        result = validate_previous_outputs(outputs)
        assert result == outputs

    def test_empty_dict_allowed(self):
        result = validate_previous_outputs({})
        assert result == {}

    def test_non_dict_raises(self):
        with pytest.raises(HTTPException):
            validate_previous_outputs("not a dict")

    def test_too_many_entries_raises(self):
        outputs = {f"agent_{i}": "output" for i in range(20)}
        with pytest.raises(HTTPException):
            validate_previous_outputs(outputs)

    def test_invalid_key_raises(self):
        with pytest.raises(HTTPException):
            validate_previous_outputs({"<script>alert(1)</script>": "output"})

    def test_non_string_value_raises(self):
        with pytest.raises(HTTPException):
            validate_previous_outputs({"icp_architect": 12345})

    def test_long_output_truncated(self):
        long = "x" * (MAX_AGENT_OUTPUT_LENGTH + 1000)
        result = validate_previous_outputs({"icp_architect": long})
        assert len(result["icp_architect"]) == MAX_AGENT_OUTPUT_LENGTH


# ========================================
# TEXT FIELD VALIDATION
# ========================================

class TestValidateTextField:

    def test_valid_text(self):
        assert validate_text_field("hello", "test") == "hello"

    def test_non_string_returns_empty(self):
        assert validate_text_field(None, "test") == ""
        assert validate_text_field(123, "test") == ""

    def test_over_max_raises(self):
        with pytest.raises(HTTPException):
            validate_text_field("x" * 6000, "test", max_length=5000)


# ========================================
# COMPANY NAME VALIDATION
# ========================================

class TestValidateCompanyName:

    def test_valid_name(self):
        assert validate_company_name("Acme Corp") == "Acme Corp"

    def test_non_string_returns_default(self):
        assert validate_company_name(None) == "Company"

    def test_long_name_truncated(self):
        long_name = "A" * 300
        result = validate_company_name(long_name)
        assert len(result) == 200


# ========================================
# RATE LIMITER
# ========================================

class TestRateLimiter:

    def test_allows_requests_under_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.check("1.2.3.4") is True

    def test_blocks_after_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("1.2.3.4")
        assert limiter.check("1.2.3.4") is False

    def test_different_ips_independent(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.check("1.1.1.1")
        limiter.check("1.1.1.1")
        assert limiter.check("1.1.1.1") is False
        assert limiter.check("2.2.2.2") is True

    def test_window_expiry(self):
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.check("1.2.3.4") is True
        assert limiter.check("1.2.3.4") is False
        time.sleep(1.1)
        assert limiter.check("1.2.3.4") is True
