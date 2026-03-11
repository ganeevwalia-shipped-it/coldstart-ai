"""
Tests for the agent orchestrator — dependency graph, chaining, execution plans.
This is the brain of the system. If it breaks, agents run out of order.
"""
import pytest
from app.agents.orchestrator import (
    AGENT_DEPENDENCIES,
    EXECUTION_LAYERS,
    build_chained_prompt,
    get_execution_plan,
)
from app.agents.registry import AGENTS, AGENT_ORDER


# ========================================
# DEPENDENCY GRAPH INTEGRITY
# ========================================

class TestDependencyGraph:
    """The dependency graph defines the entire chaining system."""

    def test_all_agents_have_dependency_entry(self):
        for agent_id in AGENTS:
            assert agent_id in AGENT_DEPENDENCIES, (
                f"{agent_id} missing from AGENT_DEPENDENCIES"
            )

    def test_no_unknown_agents_in_dependencies(self):
        for agent_id in AGENT_DEPENDENCIES:
            assert agent_id in AGENTS, (
                f"Unknown agent in AGENT_DEPENDENCIES: {agent_id}"
            )

    def test_dependency_targets_are_valid_agents(self):
        for agent_id, deps in AGENT_DEPENDENCIES.items():
            for dep in deps:
                assert dep in AGENTS, (
                    f"{agent_id} depends on unknown agent: {dep}"
                )

    def test_no_self_dependencies(self):
        for agent_id, deps in AGENT_DEPENDENCIES.items():
            assert agent_id not in deps, (
                f"{agent_id} depends on itself"
            )

    def test_no_circular_dependencies(self):
        """DFS cycle detection — circular deps would deadlock execution."""
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for dep in AGENT_DEPENDENCIES.get(node, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for agent_id in AGENT_DEPENDENCIES:
            if agent_id not in visited:
                assert not has_cycle(agent_id), (
                    f"Circular dependency detected involving {agent_id}"
                )

    def test_icp_architect_has_no_dependencies(self):
        """ICP is the root — it must have zero dependencies."""
        assert AGENT_DEPENDENCIES["icp_architect"] == []

    def test_layer_4_agents_have_dependencies(self):
        """Execution layer agents must depend on earlier agents."""
        execution_agents = [
            "launch_planner", "automation_engineer",
            "metrics_designer", "partnership_scout", "community_architect",
        ]
        for agent_id in execution_agents:
            assert len(AGENT_DEPENDENCIES[agent_id]) > 0, (
                f"Execution agent {agent_id} has no dependencies — should chain"
            )

    def test_dependencies_respect_layer_ordering(self):
        """An agent should only depend on agents in earlier layers."""
        # Build layer map
        layer_of = {}
        for layer_idx, layer in enumerate(EXECUTION_LAYERS):
            for agent_id in layer:
                layer_of[agent_id] = layer_idx

        for agent_id, deps in AGENT_DEPENDENCIES.items():
            if agent_id not in layer_of:
                continue
            for dep in deps:
                if dep not in layer_of:
                    continue
                assert layer_of[dep] < layer_of[agent_id], (
                    f"{agent_id} (layer {layer_of[agent_id]}) depends on "
                    f"{dep} (layer {layer_of[dep]}) — must be earlier layer"
                )


# ========================================
# EXECUTION LAYERS
# ========================================

class TestExecutionLayers:
    """Execution layers determine parallel vs sequential execution."""

    def test_all_agents_in_execution_layers(self):
        agents_in_layers = set()
        for layer in EXECUTION_LAYERS:
            agents_in_layers.update(layer)
        for agent_id in AGENTS:
            assert agent_id in agents_in_layers, (
                f"{agent_id} not in any execution layer"
            )

    def test_no_duplicate_agents_across_layers(self):
        seen = set()
        for layer in EXECUTION_LAYERS:
            for agent_id in layer:
                assert agent_id not in seen, (
                    f"{agent_id} appears in multiple execution layers"
                )
                seen.add(agent_id)

    def test_first_layer_is_icp(self):
        assert EXECUTION_LAYERS[0] == ["icp_architect"]

    def test_layers_are_non_empty(self):
        for i, layer in enumerate(EXECUTION_LAYERS):
            assert len(layer) > 0, f"Execution layer {i} is empty"

    def test_agents_in_same_layer_dont_depend_on_each_other(self):
        """Agents in the same layer run in parallel — they can't depend on each other."""
        for layer in EXECUTION_LAYERS:
            for agent_id in layer:
                deps = set(AGENT_DEPENDENCIES.get(agent_id, []))
                layer_peers = set(layer) - {agent_id}
                overlap = deps & layer_peers
                assert not overlap, (
                    f"{agent_id} depends on {overlap} but they're in the same layer"
                )


# ========================================
# EXECUTION PLAN GENERATION
# ========================================

class TestGetExecutionPlan:
    """Test the execution plan generator."""

    def test_full_plan_includes_all_layers(self):
        plan = get_execution_plan(list(AGENTS.keys()))
        total_agents = sum(len(layer) for layer in plan)
        assert total_agents == len(AGENTS)

    def test_single_agent_plan(self):
        plan = get_execution_plan(["icp_architect"])
        assert plan == [["icp_architect"]]

    def test_subset_plan_only_includes_selected(self):
        selected = ["icp_architect", "positioning_strategist", "outbound_engineer"]
        plan = get_execution_plan(selected)
        all_in_plan = [a for layer in plan for a in layer]
        assert set(all_in_plan) == set(selected)

    def test_empty_selection_returns_empty_plan(self):
        plan = get_execution_plan([])
        assert plan == []

    def test_plan_preserves_layer_order(self):
        selected = ["icp_architect", "positioning_strategist", "launch_planner"]
        plan = get_execution_plan(selected)
        flat = [a for layer in plan for a in layer]
        assert flat.index("icp_architect") < flat.index("positioning_strategist")
        assert flat.index("positioning_strategist") < flat.index("launch_planner")

    def test_parallel_agents_in_same_layer(self):
        selected = [
            "icp_architect", "positioning_strategist", "competitor_intel",
        ]
        plan = get_execution_plan(selected)
        # positioning and competitor should be in same layer
        for layer in plan:
            if "positioning_strategist" in layer:
                assert "competitor_intel" in layer
                break

    def test_unknown_agents_excluded(self):
        plan = get_execution_plan(["icp_architect", "nonexistent_agent"])
        flat = [a for layer in plan for a in layer]
        assert "nonexistent_agent" not in flat
        assert "icp_architect" in flat


# ========================================
# PROMPT CHAINING
# ========================================

class TestBuildChainedPrompt:
    """Test the core chaining logic — where the magic happens."""

    def test_no_deps_returns_base_prompt_with_context(self):
        prompt = build_chained_prompt(
            "icp_architect",
            "You are the ICP expert.",
            "COMPANY: TestCo",
            {},
        )
        assert "You are the ICP expert." in prompt
        assert "COMPANY: TestCo" in prompt
        assert "INTELLIGENCE FROM OTHER" not in prompt

    def test_with_deps_includes_chain_header(self):
        prompt = build_chained_prompt(
            "positioning_strategist",
            "You are the positioning expert.",
            "COMPANY: TestCo",
            {"icp_architect": "ICP output here"},
        )
        assert "INTELLIGENCE FROM OTHER SPECIALIST AGENTS" in prompt
        assert "ICP output here" in prompt

    def test_chain_includes_dependency_agent_name(self):
        prompt = build_chained_prompt(
            "positioning_strategist",
            "Base prompt",
            "Context",
            {"icp_architect": "Some output"},
        )
        assert "ICP Architect" in prompt

    def test_chain_truncates_long_outputs(self):
        long_output = "x" * 5000
        prompt = build_chained_prompt(
            "positioning_strategist",
            "Base prompt",
            "Context",
            {"icp_architect": long_output},
        )
        assert "truncated" in prompt.lower()
        # Should not include the full 5000 chars
        assert len(prompt) < len(long_output) + 1000

    def test_chain_skips_missing_deps(self):
        """If a dependency output is missing, don't crash."""
        prompt = build_chained_prompt(
            "outbound_engineer",
            "Base prompt",
            "Context",
            {"icp_architect": "ICP output"},
            # Missing: positioning_strategist, competitor_intel
        )
        assert "ICP output" in prompt
        # Should still work — just with partial chain
        assert "Base prompt" in prompt

    def test_chain_includes_build_on_instruction(self):
        prompt = build_chained_prompt(
            "positioning_strategist",
            "Base prompt",
            "Context",
            {"icp_architect": "Output"},
        )
        assert "BUILD ON" in prompt

    def test_multiple_deps_all_included(self):
        outputs = {
            "icp_architect": "ICP data",
            "positioning_strategist": "Positioning data",
            "competitor_intel": "Competitor data",
        }
        prompt = build_chained_prompt(
            "outbound_engineer",
            "Base prompt",
            "Context",
            outputs,
        )
        assert "ICP data" in prompt
        assert "Positioning data" in prompt
        assert "Competitor data" in prompt

    def test_empty_previous_outputs_with_deps(self):
        """Agent has deps but no outputs provided — should not crash."""
        prompt = build_chained_prompt(
            "positioning_strategist",
            "Base prompt",
            "Context",
            {},
        )
        assert "Base prompt" in prompt
