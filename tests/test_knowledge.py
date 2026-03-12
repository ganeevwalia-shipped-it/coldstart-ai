"""
Tests for Cold Start AI — Curated GTM Knowledge Base
Tests knowledge canon content, filtering by stage/motion, and prompt injection.
"""
import pytest

from app.agents.knowledge import (
    GTM_CANON,
    get_knowledge_context,
    _normalize_stage,
    _normalize_motion,
    _item_matches,
)


class TestGTMCanon:
    def test_has_minimum_principles(self):
        assert len(GTM_CANON["principles"]) >= 15

    def test_has_minimum_do_donts(self):
        assert len(GTM_CANON["do_dont"]) >= 10

    def test_all_principles_have_required_fields(self):
        for p in GTM_CANON["principles"]:
            assert "id" in p
            assert "principle" in p
            assert "implication" in p
            assert "stages" in p
            assert "motion" in p
            assert isinstance(p["stages"], list)
            assert isinstance(p["motion"], list)
            assert len(p["stages"]) > 0
            assert len(p["motion"]) > 0

    def test_all_do_donts_have_required_fields(self):
        for dd in GTM_CANON["do_dont"]:
            assert "do" in dd
            assert "dont" in dd
            assert "stages" in dd
            assert "motion" in dd

    def test_principles_have_valid_stages(self):
        valid_stages = {"pre_revenue", "early_revenue", "scaling", "all"}
        for p in GTM_CANON["principles"]:
            for s in p["stages"]:
                assert s in valid_stages, f"Invalid stage '{s}' in principle '{p['id']}'"

    def test_principles_have_valid_motions(self):
        valid_motions = {"plg", "sales_led", "community_led", "all"}
        for p in GTM_CANON["principles"]:
            for m in p["motion"]:
                assert m in valid_motions, f"Invalid motion '{m}' in principle '{p['id']}'"


class TestNormalizeStage:
    @pytest.mark.parametrize("input_stage,expected", [
        ("Idea / Pre-product", "pre_revenue"),
        ("MVP / Pre-launch", "pre_revenue"),
        ("Post-launch / Early revenue", "early_revenue"),
        ("Growth / Scaling", "scaling"),
        ("Series B", "scaling"),
        ("Unknown", "pre_revenue"),
        ("", "pre_revenue"),
    ])
    def test_stage_normalization(self, input_stage, expected):
        assert _normalize_stage(input_stage) == expected


class TestNormalizeMotion:
    @pytest.mark.parametrize("input_motion,expected", [
        ("Product-led growth", "plg"),
        ("PLG", "plg"),
        ("Sales-led", "sales_led"),
        ("Outbound sales", "sales_led"),
        ("Community-led", "community_led"),
        ("Not sure", "all"),
        ("", "all"),
    ])
    def test_motion_normalization(self, input_motion, expected):
        assert _normalize_motion(input_motion) == expected


class TestItemMatches:
    def test_all_stage_matches_any(self):
        item = {"stages": ["all"], "motion": ["all"]}
        assert _item_matches(item, "pre_revenue", "plg") is True

    def test_specific_stage_matches(self):
        item = {"stages": ["pre_revenue"], "motion": ["all"]}
        assert _item_matches(item, "pre_revenue", "plg") is True
        assert _item_matches(item, "scaling", "plg") is False

    def test_specific_motion_matches(self):
        item = {"stages": ["all"], "motion": ["sales_led"]}
        assert _item_matches(item, "pre_revenue", "sales_led") is True
        assert _item_matches(item, "pre_revenue", "plg") is False


class TestGetKnowledgeContext:
    def test_returns_string(self):
        result = get_knowledge_context()
        assert isinstance(result, str)

    def test_includes_canon_header(self):
        result = get_knowledge_context()
        assert "INTERNAL GTM CANON" in result

    def test_includes_principles(self):
        result = get_knowledge_context(stage="MVP / Pre-launch")
        assert "→" in result  # principle → implication format

    def test_includes_do_dont(self):
        result = get_knowledge_context()
        assert "DO:" in result
        assert "DON'T:" in result

    def test_stage_filtering_works(self):
        pre_rev = get_knowledge_context(stage="Idea / Pre-product")
        scaling = get_knowledge_context(stage="Series B / Scaling")
        # Pre-revenue should include "do things that don't scale"
        assert "don't scale" in pre_rev.lower()
        # Both should have content but different content
        assert len(pre_rev) > 100
        assert len(scaling) > 100

    def test_motion_filtering_works(self):
        plg = get_knowledge_context(motion="Product-led growth")
        sales = get_knowledge_context(motion="Sales-led")
        # Both should have content
        assert len(plg) > 100
        assert len(sales) > 100

    def test_includes_stage_label(self):
        result = get_knowledge_context(stage="MVP / Pre-launch")
        assert "pre_revenue" in result

    def test_empty_inputs_handled(self):
        result = get_knowledge_context(stage="", motion="")
        assert isinstance(result, str)
        assert len(result) > 100
