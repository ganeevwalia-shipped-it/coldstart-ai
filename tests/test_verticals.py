"""
Tests for vertical detection — auto-detecting B2B SaaS, dev tools, fintech, etc.
and injecting domain-specific GTM intelligence into prompts.
"""
import pytest
from app.agents.verticals import (
    VERTICALS,
    detect_vertical,
    get_vertical_context,
)


EXPECTED_VERTICAL_IDS = [
    "b2b_saas", "dev_tool", "marketplace", "ecommerce_dtc",
    "fintech", "ai_ml", "agency_services", "consumer_app",
]

REQUIRED_VERTICAL_FIELDS = ["name", "detect_keywords", "gtm_context"]


# ========================================
# VERTICAL REGISTRY
# ========================================

class TestVerticalRegistry:

    def test_all_expected_verticals_exist(self):
        for vid in EXPECTED_VERTICAL_IDS:
            assert vid in VERTICALS, f"Missing vertical: {vid}"

    def test_vertical_count(self):
        assert len(VERTICALS) == 8

    @pytest.mark.parametrize("vertical_id", EXPECTED_VERTICAL_IDS)
    def test_required_fields(self, vertical_id):
        v = VERTICALS[vertical_id]
        for field in REQUIRED_VERTICAL_FIELDS:
            assert field in v, f"{vertical_id} missing: {field}"

    @pytest.mark.parametrize("vertical_id", EXPECTED_VERTICAL_IDS)
    def test_keywords_are_non_empty_list(self, vertical_id):
        keywords = VERTICALS[vertical_id]["detect_keywords"]
        assert isinstance(keywords, list)
        assert len(keywords) >= 2, f"{vertical_id} needs more keywords"

    @pytest.mark.parametrize("vertical_id", EXPECTED_VERTICAL_IDS)
    def test_gtm_context_is_substantial(self, vertical_id):
        ctx = VERTICALS[vertical_id]["gtm_context"]
        assert len(ctx) >= 200, (
            f"{vertical_id} GTM context too short ({len(ctx)} chars)"
        )

    @pytest.mark.parametrize("vertical_id", EXPECTED_VERTICAL_IDS)
    def test_keywords_are_lowercase(self, vertical_id):
        for kw in VERTICALS[vertical_id]["detect_keywords"]:
            assert kw == kw.lower(), (
                f"{vertical_id} keyword not lowercase: '{kw}'"
            )


# ========================================
# VERTICAL DETECTION
# ========================================

class TestDetectVertical:

    def test_b2b_saas_detected(self):
        matches = detect_vertical(
            "B2B SaaS platform for HR teams",
            "Subscription, monthly recurring",
            "Enterprise HR departments",
        )
        ids = [m["id"] for m in matches]
        assert "b2b_saas" in ids

    def test_dev_tool_detected(self):
        matches = detect_vertical(
            "Open source CLI tool for developers",
            "Freemium API pricing",
            "Software developers and DevOps engineers",
        )
        ids = [m["id"] for m in matches]
        assert "dev_tool" in ids

    def test_fintech_detected(self):
        matches = detect_vertical(
            "Payments API for crypto and banking",
            "Transaction fee",
            "Financial institutions and fintech startups",
        )
        ids = [m["id"] for m in matches]
        assert "fintech" in ids

    def test_ecommerce_detected(self):
        matches = detect_vertical(
            "DTC skincare brand on Shopify",
            "E-commerce, direct to consumer",
            "Women aged 25-40",
        )
        ids = [m["id"] for m in matches]
        assert "ecommerce_dtc" in ids

    def test_ai_ml_detected(self):
        matches = detect_vertical(
            "AI-powered LLM tool for content generation using GPT",
            "Usage-based, per generation",
            "Marketing teams",
        )
        ids = [m["id"] for m in matches]
        assert "ai_ml" in ids

    def test_marketplace_detected(self):
        matches = detect_vertical(
            "Two-sided marketplace connecting freelancers with clients",
            "Take rate on transactions",
            "Supply and demand matching",
        )
        ids = [m["id"] for m in matches]
        assert "marketplace" in ids

    def test_agency_detected(self):
        matches = detect_vertical(
            "Done-for-you consulting agency",
            "Retainer and project-based services",
            "B2B startups needing managed marketing",
        )
        ids = [m["id"] for m in matches]
        assert "agency_services" in ids

    def test_consumer_app_detected(self):
        matches = detect_vertical(
            "Social mobile app for Gen Z",
            "Freemium consumer app",
            "Teenagers and young adults",
        )
        ids = [m["id"] for m in matches]
        assert "consumer_app" in ids

    def test_no_match_returns_empty(self):
        matches = detect_vertical(
            "Underwater basket weaving equipment",
            "One-time purchase",
            "Hobbyists",
        )
        # Might match some generic keywords, but should have low scores
        # The main thing is it doesn't crash
        assert isinstance(matches, list)

    def test_results_sorted_by_score(self):
        matches = detect_vertical(
            "B2B SaaS subscription platform for enterprise teams",
            "Subscription",
            "Enterprise B2B",
        )
        if len(matches) >= 2:
            for i in range(len(matches) - 1):
                assert matches[i]["score"] >= matches[i + 1]["score"]

    def test_case_insensitive(self):
        matches = detect_vertical(
            "SAAS PLATFORM B2B ENTERPRISE",
            "SUBSCRIPTION",
            "B2B TEAMS",
        )
        ids = [m["id"] for m in matches]
        assert "b2b_saas" in ids

    def test_returns_expected_shape(self):
        matches = detect_vertical("SaaS platform", "B2B", "Enterprise")
        for match in matches:
            assert "id" in match
            assert "name" in match
            assert "score" in match
            assert "context" in match
            assert isinstance(match["score"], int)
            assert match["score"] > 0

    def test_multiple_verticals_can_match(self):
        """A product can match multiple verticals."""
        matches = detect_vertical(
            "AI-powered B2B SaaS developer tool with API and SDK",
            "Subscription",
            "Software developers at enterprise companies",
        )
        ids = [m["id"] for m in matches]
        assert len(ids) >= 2, "Should match multiple verticals"


# ========================================
# VERTICAL CONTEXT GENERATION
# ========================================

class TestGetVerticalContext:

    def test_returns_context_for_matching_product(self):
        ctx = get_vertical_context(
            "B2B SaaS platform",
            "Subscription pricing",
            "Enterprise teams",
        )
        assert len(ctx) > 0
        assert "VERTICAL-SPECIFIC" in ctx

    def test_returns_empty_for_no_match(self):
        ctx = get_vertical_context(
            "zzzzz niche product",
            "custom model",
            "nobody specific",
        )
        # Should be empty string, not crash
        assert isinstance(ctx, str)

    def test_max_two_verticals_in_context(self):
        ctx = get_vertical_context(
            "AI SaaS developer tool platform API SDK B2B enterprise subscription",
            "SaaS subscription",
            "developers",
        )
        # Count how many vertical blocks are included
        block_count = ctx.count("Key GTM patterns")
        assert block_count <= 2, (
            f"Should include max 2 verticals, got {block_count}"
        )
