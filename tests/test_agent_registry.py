"""
Tests for the agent registry — validates all 14 agents are properly defined,
have required fields, consistent categories, and valid prompts.
"""
import pytest
from app.agents.registry import AGENTS, AGENT_ORDER, CATEGORIES


# ========================================
# STRUCTURAL INTEGRITY
# ========================================

REQUIRED_AGENT_FIELDS = [
    "name", "icon", "tagline", "category",
    "deliverable", "deliverable_format", "description", "prompt",
]

VALID_CATEGORIES = {"Foundation", "Distribution", "Revenue", "Execution"}

EXPECTED_AGENT_COUNT = 14

EXPECTED_AGENT_IDS = [
    "icp_architect", "positioning_strategist", "competitor_intel",
    "channel_mapper", "outbound_engineer", "content_strategist",
    "pricing_analyst", "sales_playbook", "crm_architect",
    "launch_planner", "automation_engineer", "metrics_designer",
    "partnership_scout", "community_architect",
]


class TestAgentRegistryStructure:
    """Verify the registry is structurally sound."""

    def test_agent_count(self):
        assert len(AGENTS) == EXPECTED_AGENT_COUNT, (
            f"Expected {EXPECTED_AGENT_COUNT} agents, got {len(AGENTS)}"
        )

    def test_all_expected_agents_exist(self):
        for agent_id in EXPECTED_AGENT_IDS:
            assert agent_id in AGENTS, f"Missing agent: {agent_id}"

    def test_no_unexpected_agents(self):
        for agent_id in AGENTS:
            assert agent_id in EXPECTED_AGENT_IDS, f"Unexpected agent: {agent_id}"

    def test_agent_order_matches_agents(self):
        assert set(AGENT_ORDER) == set(AGENTS.keys()), (
            "AGENT_ORDER and AGENTS keys don't match"
        )

    def test_agent_order_has_no_duplicates(self):
        assert len(AGENT_ORDER) == len(set(AGENT_ORDER)), (
            "AGENT_ORDER contains duplicates"
        )

    def test_agent_order_length(self):
        assert len(AGENT_ORDER) == EXPECTED_AGENT_COUNT


class TestAgentFields:
    """Verify every agent has all required fields with valid values."""

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_required_fields_present(self, agent_id):
        agent = AGENTS[agent_id]
        for field in REQUIRED_AGENT_FIELDS:
            assert field in agent, f"{agent_id} missing field: {field}"

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_fields_are_non_empty_strings(self, agent_id):
        agent = AGENTS[agent_id]
        for field in REQUIRED_AGENT_FIELDS:
            value = agent[field]
            assert isinstance(value, str), f"{agent_id}.{field} is not a string"
            assert len(value.strip()) > 0, f"{agent_id}.{field} is empty"

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_category_is_valid(self, agent_id):
        agent = AGENTS[agent_id]
        assert agent["category"] in VALID_CATEGORIES, (
            f"{agent_id} has invalid category: {agent['category']}"
        )

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_icon_is_single_character_or_emoji(self, agent_id):
        icon = AGENTS[agent_id]["icon"]
        # Emojis can be 1-2 code points
        assert 1 <= len(icon) <= 4, f"{agent_id} icon too long: '{icon}'"

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_name_is_reasonable_length(self, agent_id):
        name = AGENTS[agent_id]["name"]
        assert 3 <= len(name) <= 50, f"{agent_id} name too short or long: '{name}'"

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_tagline_is_reasonable_length(self, agent_id):
        tagline = AGENTS[agent_id]["tagline"]
        assert 10 <= len(tagline) <= 100, f"{agent_id} tagline: '{tagline}'"


class TestAgentPrompts:
    """Verify agent prompts are well-formed and contain key elements."""

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_prompt_minimum_length(self, agent_id):
        prompt = AGENTS[agent_id]["prompt"]
        assert len(prompt) >= 200, (
            f"{agent_id} prompt too short ({len(prompt)} chars) — likely broken"
        )

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_prompt_contains_cold_start_reference(self, agent_id):
        prompt = AGENTS[agent_id]["prompt"]
        assert "Cold Start AI" in prompt, (
            f"{agent_id} prompt doesn't reference Cold Start AI"
        )

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_prompt_contains_markdown_headers(self, agent_id):
        prompt = AGENTS[agent_id]["prompt"]
        assert "##" in prompt, (
            f"{agent_id} prompt has no markdown headers — output won't be structured"
        )

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_prompt_requests_deliverable(self, agent_id):
        prompt = AGENTS[agent_id]["prompt"].lower()
        deliverable_words = ["produce", "create", "build", "design", "write", "generate"]
        has_deliverable_request = any(w in prompt for w in deliverable_words)
        assert has_deliverable_request, (
            f"{agent_id} prompt doesn't instruct the model to produce anything"
        )

    @pytest.mark.parametrize("agent_id", EXPECTED_AGENT_IDS)
    def test_prompt_has_company_info_reference(self, agent_id):
        prompt = AGENTS[agent_id]["prompt"].lower()
        assert "company info" in prompt or "company information" in prompt, (
            f"{agent_id} prompt doesn't reference company info input"
        )


class TestCategories:
    """Verify category definitions are consistent with agent data."""

    def test_all_valid_categories_defined(self):
        assert set(CATEGORIES.keys()) == VALID_CATEGORIES

    def test_every_agent_in_a_category(self):
        categorized = set()
        for cat in CATEGORIES.values():
            categorized.update(cat["agents"])
        assert categorized == set(AGENTS.keys()), (
            f"Agents not in any category: {set(AGENTS.keys()) - categorized}"
        )

    def test_no_agent_in_multiple_categories(self):
        seen = set()
        for cat_name, cat in CATEGORIES.items():
            for agent_id in cat["agents"]:
                assert agent_id not in seen, (
                    f"{agent_id} appears in multiple categories"
                )
                seen.add(agent_id)

    def test_agent_category_field_matches_categories_dict(self):
        for cat_name, cat in CATEGORIES.items():
            for agent_id in cat["agents"]:
                assert AGENTS[agent_id]["category"] == cat_name, (
                    f"{agent_id} category '{AGENTS[agent_id]['category']}' "
                    f"doesn't match CATEGORIES placement '{cat_name}'"
                )

    def test_categories_have_descriptions(self):
        for cat_name, cat in CATEGORIES.items():
            assert "description" in cat, f"Category '{cat_name}' missing description"
            assert len(cat["description"]) > 0

    def test_categories_have_agents(self):
        for cat_name, cat in CATEGORIES.items():
            assert "agents" in cat, f"Category '{cat_name}' missing agents list"
            assert len(cat["agents"]) > 0, f"Category '{cat_name}' has no agents"
