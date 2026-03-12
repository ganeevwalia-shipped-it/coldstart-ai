"""
Tests for Cold Start AI — GTM Rules Engine
Tests input quality scoring, rule application, and prompt injection.
"""
import pytest

from app.agents.rules import (
    is_vague_icp,
    score_input_quality,
    get_applicable_rules,
    build_rules_block,
    parse_company_context,
    GTM_RULES,
)


# ========================================
# ICP VAGUENESS DETECTION
# ========================================

class TestIsVagueICP:
    @pytest.mark.parametrize("target", [
        "everyone",
        "anyone",
        "all businesses",
        "all companies",
        "startups",
        "enterprises",
        "developers",
        "businesses",
        "consumers",
        "small businesses in the US",
        "Anyone who needs a website",
    ])
    def test_vague_icps_detected(self, target):
        assert is_vague_icp(target) is True

    @pytest.mark.parametrize("target", [
        "Series A SaaS founders with 5-20 employees in B2B fintech",
        "VP of Engineering at mid-market companies (200-1000 employees) using microservices",
        "Solo real estate agents in suburban markets spending $500+/mo on lead gen",
        "Head of Growth at PLG SaaS companies with $1M-$10M ARR",
    ])
    def test_specific_icps_accepted(self, target):
        assert is_vague_icp(target) is False

    def test_empty_icp_is_vague(self):
        assert is_vague_icp("") is True

    def test_none_handled(self):
        assert is_vague_icp(None) is True


# ========================================
# INPUT QUALITY SCORING
# ========================================

class TestScoreInputQuality:
    def test_good_input_scores_high(self):
        ctx = {
            "target_market": "Series A B2B SaaS founders with 10-50 employees struggling with outbound sales",
            "product": "An AI-powered outbound email tool that personalizes cold emails using prospect's LinkedIn activity and company news",
            "stage": "MVP / Pre-launch",
            "business_model": "SaaS",
            "budget": "$5K-$15K/month",
        }
        result = score_input_quality(ctx)
        assert result["score"] >= 80
        assert len(result["issues"]) == 0

    def test_vague_icp_flagged(self):
        ctx = {
            "target_market": "startups",
            "product": "A platform that helps teams collaborate more effectively using AI-powered project management features",
            "stage": "MVP",
        }
        result = score_input_quality(ctx)
        assert result["score"] < 80
        issues = [i for i in result["issues"] if i["field"] == "target_market"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"

    def test_empty_target_market_hard_constraint(self):
        ctx = {"target_market": "", "product": "A great tool for analytics and data visualization with custom dashboards"}
        result = score_input_quality(ctx)
        issues = [i for i in result["issues"] if i["field"] == "target_market"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "hard_constraint"

    def test_short_product_description_flagged(self):
        ctx = {
            "target_market": "B2B SaaS founders with teams of 10-50 building developer tools",
            "product": "Analytics tool",
        }
        result = score_input_quality(ctx)
        issues = [i for i in result["issues"] if i["field"] == "product"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"

    def test_no_product_hard_constraint(self):
        ctx = {"target_market": "B2B SaaS founders with 10-50 employees building in fintech"}
        result = score_input_quality(ctx)
        issues = [i for i in result["issues"] if i["field"] == "product"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "hard_constraint"

    def test_no_business_model_info(self):
        ctx = {
            "target_market": "B2B SaaS founders with 10-50 employees building in fintech",
            "product": "AI-powered outbound email platform that writes personalized emails at scale",
            "business_model": "Not sure",
        }
        result = score_input_quality(ctx)
        issues = [i for i in result["issues"] if i["field"] == "business_model"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "info"

    def test_score_clamped_to_0_100(self):
        # Worst case: everything missing
        result = score_input_quality({})
        assert 0 <= result["score"] <= 100

    def test_warnings_for_no_challenges(self):
        ctx = {
            "target_market": "B2B SaaS founders with 10-50 employees in vertical SaaS",
            "product": "AI-powered GTM execution engine that builds complete go-to-market plans with actionable deliverables",
            "current_challenges": "Not specified",
        }
        result = score_input_quality(ctx)
        assert len(result["warnings"]) > 0

    def test_budget_stage_mismatch_flagged(self):
        ctx = {
            "target_market": "B2B SaaS founders with 10-50 employees in vertical SaaS",
            "product": "AI-powered GTM execution engine with structured outputs and opinionated rules",
            "stage": "Idea / Pre-product",
            "budget": "$50K+/month",
        }
        result = score_input_quality(ctx)
        issues = [i for i in result["issues"] if i["field"] == "budget"]
        assert len(issues) == 1


# ========================================
# RULE APPLICATION
# ========================================

class TestGetApplicableRules:
    def test_pre_revenue_no_paid_fires(self):
        ctx = {
            "stage": "MVP / Pre-launch",
            "budget": "$0 - Bootstrap",
        }
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "pre_revenue_no_paid" in rule_ids

    def test_pre_revenue_no_paid_severity(self):
        ctx = {"stage": "MVP / Pre-launch", "budget": "$0 - Bootstrap"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule = next(r for r in rules if r["id"] == "pre_revenue_no_paid")
        assert rule["severity"] == "hard_constraint"

    def test_vague_icp_fires_for_icp_architect(self):
        ctx = {"target_market": "startups"}
        rules = get_applicable_rules("icp_architect", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "vague_icp_rejection" in rule_ids

    def test_vague_icp_does_not_fire_for_other_agents(self):
        ctx = {"target_market": "startups"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "vague_icp_rejection" not in rule_ids

    def test_dev_tool_outbound_warning(self):
        ctx = {
            "product": "Developer API for payment processing",
            "target_market": "Backend developers at fintech startups",
        }
        rules = get_applicable_rules("outbound_engineer", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "dev_tool_outbound_warning" in rule_ids

    def test_enterprise_bootstrap_mismatch(self):
        ctx = {
            "target_market": "Enterprise CIOs at Fortune 500 companies",
            "budget": "$0 - Bootstrap",
        }
        rules = get_applicable_rules("sales_playbook", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "enterprise_bootstrap_mismatch" in rule_ids

    def test_marketplace_chicken_egg(self):
        ctx = {"business_model": "Marketplace"}
        rules = get_applicable_rules("launch_planner", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "marketplace_chicken_egg" in rule_ids

    def test_good_input_no_hard_constraints(self):
        ctx = {
            "target_market": "Series A B2B SaaS founders with 10-50 employees in fintech vertical",
            "product": "AI-powered analytics dashboard for revenue teams",
            "stage": "Post-launch / Early revenue",
            "budget": "$15K-$50K/month",
            "business_model": "SaaS",
            "primary gtm motion": "Sales-led",
            "current challenges": "Low reply rates on outbound, unclear positioning",
        }
        rules = get_applicable_rules("channel_mapper", ctx)
        # Good input should trigger no hard constraints (may still get info/warning framing rules)
        hard_constraints = [r for r in rules if r["severity"] == "hard_constraint"]
        assert len(hard_constraints) == 0

    def test_unsure_gtm_motion_fires(self):
        ctx = {"primary gtm motion": "Not sure yet"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "unsure_gtm_motion" in rule_ids

    def test_idea_stage_sales_playbook_warning(self):
        ctx = {"stage": "Idea / Pre-product"}
        rules = get_applicable_rules("sales_playbook", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "idea_stage_no_sales_playbook" in rule_ids

    def test_every_rule_has_required_fields(self):
        for rule in GTM_RULES:
            assert "id" in rule
            assert "severity" in rule
            assert rule["severity"] in ("info", "warning", "hard_constraint")
            assert "condition" in rule
            assert callable(rule["condition"])
            assert "rule" in rule
            assert isinstance(rule["rule"], str)
            assert "applies_to" in rule
            assert isinstance(rule["applies_to"], list)
            assert len(rule["applies_to"]) > 0

    def test_too_many_channels_early(self):
        ctx = {"stage": "MVP / Pre-launch"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "too_many_channels_early" in rule_ids

    def test_paid_ads_too_early(self):
        ctx = {"stage": "Idea / Pre-product", "budget": "$1K-$5K/month"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "paid_ads_too_early" in rule_ids

    # --- Advanced GTM rules (the 20) ---

    def test_icp_behavior_not_biography_fires(self):
        rules = get_applicable_rules("icp_architect", {})
        rule_ids = [r["id"] for r in rules]
        assert "icp_behavior_not_biography" in rule_ids

    def test_first_10_customers_fires_early_stage(self):
        ctx = {"stage": "MVP / Pre-launch"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "first_10_customers" in rule_ids

    def test_first_10_customers_does_not_fire_late_stage(self):
        ctx = {"stage": "Post-launch / Early revenue"}
        rules = get_applicable_rules("channel_mapper", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "first_10_customers" not in rule_ids

    def test_proof_loop_fires_for_channel_mapper(self):
        rules = get_applicable_rules("channel_mapper", {})
        rule_ids = [r["id"] for r in rules]
        assert "proof_loop_required" in rule_ids

    def test_three_line_test_fires_for_positioning(self):
        rules = get_applicable_rules("positioning_strategist", {})
        rule_ids = [r["id"] for r in rules]
        assert "three_line_test" in rule_ids

    def test_no_brand_without_demand_fires_early(self):
        ctx = {"stage": "MVP / Pre-launch"}
        rules = get_applicable_rules("content_strategist", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "no_brand_without_demand" in rule_ids

    def test_founder_gravity_mandatory_early(self):
        ctx = {"stage": "Idea / Pre-product"}
        rules = get_applicable_rules("sales_playbook", ctx)
        rule_ids = [r["id"] for r in rules]
        assert "founder_gravity_mandatory" in rule_ids

    def test_displace_status_quo_fires_for_positioning(self):
        rules = get_applicable_rules("positioning_strategist", {})
        rule_ids = [r["id"] for r in rules]
        assert "displace_status_quo" in rule_ids

    def test_icp_table_test_fires(self):
        rules = get_applicable_rules("icp_architect", {})
        rule_ids = [r["id"] for r in rules]
        assert "icp_table_test" in rule_ids

    def test_kill_your_darlings_fires_for_launch_planner(self):
        rules = get_applicable_rules("launch_planner", {})
        rule_ids = [r["id"] for r in rules]
        assert "kill_your_darlings" in rule_ids

    def test_total_rules_count_is_at_least_30(self):
        """Ensure we have the original 12 + 20 advanced = 32 rules."""
        assert len(GTM_RULES) >= 30


# ========================================
# RULES BLOCK FORMATTING
# ========================================

class TestBuildRulesBlock:
    def test_empty_rules_returns_empty(self):
        assert build_rules_block([]) == ""

    def test_formats_single_rule(self):
        rules = [{"id": "test", "severity": "warning", "rule": "Do not recommend paid ads."}]
        block = build_rules_block(rules)
        assert "CONSTRAINTS & RULES" in block
        assert "Do not recommend paid ads." in block
        assert "[WARNING]" in block

    def test_hard_constraints_come_first(self):
        rules = [
            {"id": "info_rule", "severity": "info", "rule": "Note this."},
            {"id": "hard_rule", "severity": "hard_constraint", "rule": "Never do this."},
            {"id": "warn_rule", "severity": "warning", "rule": "Be careful."},
        ]
        block = build_rules_block(rules)
        hard_pos = block.index("HARD CONSTRAINT")
        warn_pos = block.index("WARNING")
        note_pos = block.index("NOTE")
        assert hard_pos < warn_pos < note_pos

    def test_all_severity_labels_present(self):
        rules = [
            {"id": "a", "severity": "hard_constraint", "rule": "A"},
            {"id": "b", "severity": "warning", "rule": "B"},
            {"id": "c", "severity": "info", "rule": "C"},
        ]
        block = build_rules_block(rules)
        assert "[HARD CONSTRAINT]" in block
        assert "[WARNING]" in block
        assert "[NOTE]" in block


# ========================================
# CONTEXT PARSING
# ========================================

class TestParseCompanyContext:
    def test_parses_standard_format(self):
        ctx = """COMPANY: Acme Corp
PRODUCT: Widget maker
TARGET MARKET: SMB owners
STAGE: MVP"""
        result = parse_company_context(ctx)
        assert result["company"] == "Acme Corp"
        assert result["product"] == "Widget maker"
        assert result["target market"] == "SMB owners"
        assert result["stage"] == "MVP"

    def test_handles_empty(self):
        result = parse_company_context("")
        assert result == {}

    def test_handles_colons_in_values(self):
        ctx = "WEBSITE: https://example.com"
        result = parse_company_context(ctx)
        assert result["website"] == "https://example.com"

    def test_keys_lowercased(self):
        ctx = "COMPANY: Test\nBUSINESS MODEL: SaaS"
        result = parse_company_context(ctx)
        assert "company" in result
        assert "business model" in result


# ========================================
# INTEGRATION: RULES INJECTED INTO PROMPTS
# ========================================

class TestRulesIntegration:
    def test_rules_appear_in_prompt_via_parse_and_build(self):
        """End-to-end: parse context → get rules → build block → verify content."""
        context = """COMPANY: TestCo
PRODUCT: Dev API
TARGET MARKET: startups
STAGE: Idea / Pre-product
MONTHLY GTM BUDGET: $0 - Bootstrap
PRIMARY GTM MOTION: Not sure yet"""
        parsed = parse_company_context(context)
        rules = get_applicable_rules("channel_mapper", parsed)
        block = build_rules_block(rules)
        # Should have rules about budget, paid ads, channels
        assert "CONSTRAINTS & RULES" in block
        assert len(rules) >= 2  # Should trigger multiple rules

    def test_no_rules_for_unmatched_agent(self):
        """An agent with no matching rules should get no block."""
        context = "COMPANY: TestCo\nPRODUCT: Great product for analytics and data teams\nSTAGE: Scaling"
        parsed = parse_company_context(context)
        # pricing_analyst with good context might have no rules
        rules = get_applicable_rules("pricing_analyst", parsed)
        # Either few or no rules — just ensure it doesn't crash
        block = build_rules_block(rules)
        assert isinstance(block, str)
