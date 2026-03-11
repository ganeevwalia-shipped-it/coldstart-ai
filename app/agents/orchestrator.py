"""
Cold Start AI — Agent Orchestration Engine
The difference between 14 independent consultants and a coordinated war room.

FREE MODE: All agents run independently with the same base context.
PRO MODE: Agents chain — each one builds on the outputs before it.

The dependency graph:

    Layer 0 (Foundation):
        ICP Architect ─────────────────────────────┐
                                                    │
    Layer 1 (Positioning):                          ▼
        Positioning Strategist ◄── ICP output ──────┤
        Competitor Intel ◄──────── ICP output ──────┘
                                                    │
    Layer 2 (Distribution):                         ▼
        Channel Mapper ◄────── ICP + Positioning ───┤
        Outbound Engineer ◄─── ICP + Positioning + Competitors
        Content Strategist ◄── ICP + Positioning ───┘
                                                    │
    Layer 3 (Revenue):                              ▼
        Pricing Analyst ◄───── ICP + Positioning + Competitors
        Sales Playbook ◄────── ICP + Positioning + Competitors + Outbound
        CRM Architect ◄─────── ICP + Sales Playbook
                                                    │
    Layer 4 (Execution):                            ▼
        Launch Planner ◄────── ALL above
        Automation Engineer ◄─ Outbound + CRM + Content + Channels
        Metrics Designer ◄──── Channels + Pricing + ICP
        Partnership Scout ◄─── ICP + Positioning + Channels
        Community Architect ◄─ ICP + Content + Channels
"""

# Which agents feed into which
AGENT_DEPENDENCIES = {
    # Layer 0: No dependencies — runs first
    "icp_architect": [],

    # Layer 1: Needs ICP
    "positioning_strategist": ["icp_architect"],
    "competitor_intel": ["icp_architect"],

    # Layer 2: Needs ICP + Positioning + Competitors
    "channel_mapper": ["icp_architect", "positioning_strategist"],
    "outbound_engineer": ["icp_architect", "positioning_strategist", "competitor_intel"],
    "content_strategist": ["icp_architect", "positioning_strategist"],

    # Layer 3: Needs Distribution layer
    "pricing_analyst": ["icp_architect", "positioning_strategist", "competitor_intel"],
    "sales_playbook": ["icp_architect", "positioning_strategist", "competitor_intel", "outbound_engineer"],
    "crm_architect": ["icp_architect", "sales_playbook"],

    # Layer 4: Needs everything
    "launch_planner": ["icp_architect", "positioning_strategist", "competitor_intel",
                        "channel_mapper", "content_strategist", "outbound_engineer"],
    "automation_engineer": ["outbound_engineer", "crm_architect", "content_strategist", "channel_mapper"],
    "metrics_designer": ["icp_architect", "channel_mapper", "pricing_analyst"],
    "partnership_scout": ["icp_architect", "positioning_strategist", "channel_mapper"],
    "community_architect": ["icp_architect", "content_strategist", "channel_mapper"],
}

# Execution layers — agents in the same layer can run in parallel
EXECUTION_LAYERS = [
    # Layer 0
    ["icp_architect"],
    # Layer 1
    ["positioning_strategist", "competitor_intel"],
    # Layer 2
    ["channel_mapper", "outbound_engineer", "content_strategist"],
    # Layer 3
    ["pricing_analyst", "sales_playbook"],
    # Layer 3b (needs sales_playbook)
    ["crm_architect"],
    # Layer 4
    ["launch_planner", "automation_engineer", "metrics_designer", "partnership_scout", "community_architect"],
]


def build_chained_prompt(agent_id: str, base_prompt: str, company_context: str,
                          previous_outputs: dict[str, str]) -> str:
    """
    Build a prompt that includes outputs from dependency agents.
    This is what makes chained mode 10x better than independent mode.
    """
    deps = AGENT_DEPENDENCIES.get(agent_id, [])
    if not deps:
        return f"{base_prompt}\n\n---\n\nHere is the company information:\n{company_context}"

    # Build the context from previous agent outputs
    chain_context = "\n\n" + "=" * 60 + "\n"
    chain_context += "INTELLIGENCE FROM OTHER SPECIALIST AGENTS\n"
    chain_context += "(Use this to make your output specific and connected to the overall GTM strategy)\n"
    chain_context += "=" * 60 + "\n\n"

    for dep_id in deps:
        if dep_id in previous_outputs:
            from app.agents.registry import AGENTS
            dep_agent = AGENTS.get(dep_id, {})
            dep_name = dep_agent.get("name", dep_id)
            chain_context += f"--- OUTPUT FROM: {dep_name} ---\n"
            # Truncate if too long to stay within token limits
            output = previous_outputs[dep_id]
            if len(output) > 3000:
                output = output[:3000] + "\n\n[... truncated for brevity — full output available]"
            chain_context += output + "\n\n"

    chain_context += "=" * 60 + "\n\n"
    chain_context += "IMPORTANT: Your output should BUILD ON the intelligence above. "
    chain_context += "Reference specific ICPs, positioning angles, competitive gaps, and channel strategies "
    chain_context += "mentioned by other agents. Make your deliverable connect to the overall system.\n"

    return (
        f"{base_prompt}\n\n---\n\n"
        f"Here is the company information:\n{company_context}\n\n"
        f"{chain_context}"
    )


def get_execution_plan(selected_agents: list[str]) -> list[list[str]]:
    """
    Given selected agents, return the execution layers
    (which agents can run in parallel at each step).
    """
    plan = []
    for layer in EXECUTION_LAYERS:
        layer_agents = [a for a in layer if a in selected_agents]
        if layer_agents:
            plan.append(layer_agents)
    return plan
