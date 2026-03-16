"""
Cold Start AI — Markdown-to-Structured-Data Parsers
Extracts structured data from agent markdown outputs for export connectors.
Parsers are fault-tolerant — they return partial data rather than fail.
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger("coldstart.parsers")


def parse_agent_output(agent_id: str, content: str) -> dict:
    """Route to the correct parser for an agent. Returns structured data dict."""
    parser = PARSERS.get(agent_id)
    if not parser:
        return {"agent_id": agent_id, "data": {}, "raw": content}
    try:
        data = parser(content)
    except Exception:
        logger.exception(f"Parser failed for {agent_id}")
        data = {}
    return {"agent_id": agent_id, "data": data, "raw": content}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _extract_section(content: str, heading: str) -> str:
    """Extract text under a markdown heading (### level) until the next heading."""
    pattern = rf"###?\s*\d*\.?\s*{re.escape(heading)}.*?\n(.*?)(?=\n###?\s|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_table_rows(text: str) -> list[dict[str, str]]:
    """Parse a markdown table into a list of dicts keyed by header columns."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    table_lines = [l for l in lines if "|" in l]
    if len(table_lines) < 3:
        return []

    headers = [h.strip() for h in table_lines[0].split("|") if h.strip()]
    rows = []
    for line in table_lines[2:]:  # skip header + separator
        if re.match(r"^\|?\s*[-:]+", line):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if cells:
            row = {}
            for i, header in enumerate(headers):
                row[header.lower().replace(" ", "_")] = cells[i] if i < len(cells) else ""
            rows.append(row)
    return rows


def _extract_code_blocks(text: str) -> list[str]:
    """Extract all fenced code block contents."""
    return re.findall(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL)


def _extract_numbered_items(text: str) -> list[str]:
    """Extract numbered list items."""
    return re.findall(r"^\d+\.\s+(.+)$", text, re.MULTILINE)


# ---------------------------------------------------------------------------
# Agent-specific parsers
# ---------------------------------------------------------------------------

def _parse_icp_architect(content: str) -> dict:
    data: dict = {}

    # Primary ICP section
    primary = _extract_section(content, "Primary ICP")
    if primary:
        data["primary_icp"] = primary

    # Anti-ICP
    anti = _extract_section(content, "Anti-ICP")
    if anti:
        data["anti_icp"] = anti

    # Buying signals
    signals = _extract_section(content, "Buying Signals")
    if signals:
        data["buying_signals"] = _extract_numbered_items(signals) or [signals]

    # Lead Qualification scorecard
    qualification = _extract_section(content, "Lead Qualification")
    if qualification:
        data["lead_qualification"] = _extract_table_rows(qualification)

    # Prospecting search strings
    search = _extract_section(content, "Prospecting Search Strings")
    if search:
        data["search_strings"] = _extract_code_blocks(search) or _extract_numbered_items(search) or [search]

    # Ad Platform audiences
    ads = _extract_section(content, "Ad Platform Audience Definitions")
    if ads:
        data["ad_audiences"] = ads

    return data


def _parse_positioning_strategist(content: str) -> dict:
    data: dict = {}

    core = _extract_section(content, "Core Positioning")
    if core:
        data["positioning"] = core

    hierarchy = _extract_section(content, "Messaging Hierarchy")
    if hierarchy:
        data["messaging_hierarchy"] = hierarchy

    copy_bank = _extract_section(content, "Copy Bank")
    if copy_bank:
        data["copy_bank"] = _extract_table_rows(copy_bank)

    website = _extract_section(content, "Website Section Copy")
    if website:
        data["website_copy"] = website

    return data


def _parse_competitor_intel(content: str) -> dict:
    data: dict = {}

    landscape = _extract_section(content, "Competitive Landscape")
    if landscape:
        data["landscape"] = landscape

    # Extract all battlecard sections
    battlecards = re.findall(
        r"###?\s*\d*\.?\s*Battlecard[:\s]*(.*?)\n(.*?)(?=\n###?\s|\Z)",
        content, re.DOTALL | re.IGNORECASE,
    )
    if battlecards:
        data["battlecards"] = [
            {"competitor": name.strip(), "content": body.strip()}
            for name, body in battlecards
        ]

    gaps = _extract_section(content, "Market Gaps")
    if gaps:
        data["market_gaps"] = _extract_numbered_items(gaps) or [gaps]

    win_loss = _extract_section(content, "Win/Loss Quick Reference")
    if win_loss:
        data["win_loss"] = win_loss

    return data


def _parse_channel_mapper(content: str) -> dict:
    data: dict = {}

    channels = _extract_section(content, "Channel Stack")
    if channels:
        data["channels"] = channels

    kill_list = _extract_section(content, "Channel Kill List")
    if kill_list:
        data["kill_list"] = _extract_table_rows(kill_list) or [kill_list]

    roadmap = _extract_section(content, "90-Day Channel Roadmap")
    if roadmap:
        data["roadmap"] = _extract_table_rows(roadmap)

    budget = _extract_section(content, "Budget Scenarios")
    if budget:
        data["budget_scenarios"] = _extract_table_rows(budget)

    sprint = _extract_section(content, "Week 1 Sprint Plan")
    if sprint:
        data["week1_sprint"] = _extract_table_rows(sprint) or [sprint]

    return data


def _parse_outbound_engineer(content: str) -> dict:
    data: dict = {}

    # Extract email sequence touches
    email_pattern = r"\*\*Email\s+(\d+).*?\*\*.*?Subject\s*[AB]?:\s*(.*?)(?:\n.*?Subject\s*B:\s*(.*?))?\n.*?```\s*\n(.*?)```"
    emails = re.findall(email_pattern, content, re.DOTALL | re.IGNORECASE)
    if emails:
        data["email_sequences"] = [
            {
                "touch": int(e[0]),
                "subject_a": e[1].strip(),
                "subject_b": e[2].strip() if e[2] else "",
                "body": e[3].strip(),
            }
            for e in emails
        ]

    # LinkedIn sequence
    linkedin_pattern = r"\*\*Touch\s+(\d+).*?\*\*.*?```\s*\n(.*?)```"
    linkedin_section = _extract_section(content, "LinkedIn")
    if linkedin_section:
        linkedin_msgs = re.findall(linkedin_pattern, linkedin_section, re.DOTALL)
        if linkedin_msgs:
            data["linkedin_messages"] = [
                {"touch": int(m[0]), "message": m[1].strip()}
                for m in linkedin_msgs
            ]

    # Objection bank
    objections = _extract_section(content, "Objection Response")
    if objections:
        data["objections"] = _extract_table_rows(objections)

    # Metrics targets
    metrics = _extract_section(content, "Metrics Targets")
    if metrics:
        data["metrics_targets"] = _extract_table_rows(metrics)

    return data


def _parse_content_strategist(content: str) -> dict:
    data: dict = {}

    pillars = _extract_section(content, "Content Pillars")
    if pillars:
        data["pillars"] = _extract_table_rows(pillars) or [pillars]

    calendar = _extract_section(content, "30-Day Content Calendar")
    if calendar:
        data["calendar"] = _extract_table_rows(calendar)

    # LinkedIn posts
    posts_section = _extract_section(content, "LinkedIn Post")
    if posts_section:
        data["linkedin_posts"] = _extract_code_blocks(posts_section)

    lead_magnet = _extract_section(content, "Lead Magnet")
    if lead_magnet:
        data["lead_magnet"] = lead_magnet

    return data


def _parse_pricing_analyst(content: str) -> dict:
    data: dict = {}

    model = _extract_section(content, "Pricing Model")
    if model:
        data["pricing_model"] = model

    tiers = _extract_section(content, "Tier Architecture")
    if tiers:
        # Extract individual tiers
        tier_blocks = re.findall(
            r"\*\*Tier\s+\d+:\s*(.*?)\*\*\s*—\s*\$?([\d,./]+).*?\n(.*?)(?=\*\*Tier|\Z)",
            tiers, re.DOTALL,
        )
        if tier_blocks:
            data["tiers"] = [
                {"name": t[0].strip(), "price": t[1].strip(), "details": t[2].strip()}
                for t in tier_blocks
            ]

    revenue = _extract_section(content, "Revenue Model")
    if revenue:
        data["revenue_model"] = _extract_table_rows(revenue)

    return data


def _parse_sales_playbook(content: str) -> dict:
    data: dict = {}

    discovery = _extract_section(content, "Discovery Call Script")
    if discovery:
        scripts = _extract_code_blocks(discovery)
        data["opening_script"] = scripts[0] if scripts else discovery

    questions = _extract_section(content, "Discovery Questions")
    if questions:
        data["discovery_questions"] = _extract_numbered_items(questions)

    demo = _extract_section(content, "Demo Flow")
    if demo:
        data["demo_flow"] = _extract_table_rows(demo)

    objections = _extract_section(content, "Objection Handling")
    if objections:
        data["objections"] = _extract_table_rows(objections)

    closing = _extract_section(content, "Closing Framework")
    if closing:
        data["closing_scripts"] = _extract_code_blocks(closing) or [closing]

    return data


def _parse_crm_architect(content: str) -> dict:
    data: dict = {}

    pipeline = _extract_section(content, "Pipeline Stages")
    if pipeline:
        data["pipeline_stages"] = _extract_table_rows(pipeline)

    contact_fields = _extract_section(content, "Custom Fields (Contact)")
    if not contact_fields:
        contact_fields = _extract_section(content, "Custom Fields")
    if contact_fields:
        data["contact_fields"] = _extract_table_rows(contact_fields)

    deal_fields = _extract_section(content, "Custom Fields (Deal)")
    if deal_fields:
        data["deal_fields"] = _extract_table_rows(deal_fields)

    scoring = _extract_section(content, "Lead Scoring")
    if scoring:
        data["lead_scoring"] = _extract_table_rows(scoring)

    automations = _extract_section(content, "Automation Rules")
    if automations:
        data["automations"] = _extract_table_rows(automations)

    templates = _extract_section(content, "Email Templates")
    if templates:
        data["email_templates"] = _extract_code_blocks(templates) or _extract_numbered_items(templates)

    return data


def _parse_launch_planner(content: str) -> dict:
    data: dict = {}

    strategy = _extract_section(content, "Launch Strategy")
    if strategy:
        data["strategy"] = strategy

    assets = _extract_section(content, "Launch Assets")
    if assets:
        data["assets"] = assets
        data["asset_copy"] = _extract_code_blocks(assets)

    outreach = _extract_section(content, "Launch Outreach")
    if outreach:
        data["outreach"] = _extract_table_rows(outreach) or [outreach]

    return data


def _parse_automation_engineer(content: str) -> dict:
    data: dict = {}

    # Extract all workflow blocks
    workflows = re.findall(
        r"###?\s*Workflow\s+(\d+):\s*(.*?)\n(.*?)(?=###?\s*Workflow|\Z)",
        content, re.DOTALL,
    )
    if workflows:
        data["workflows"] = [
            {
                "number": int(w[0]),
                "name": w[1].strip(),
                "steps": _extract_code_blocks(w[2]) or [w[2].strip()],
            }
            for w in workflows
        ]

    stack = _extract_section(content, "Automation Stack")
    if stack:
        data["tool_stack"] = _extract_table_rows(stack)

    return data


def _parse_metrics_designer(content: str) -> dict:
    data: dict = {}

    north_star = _extract_section(content, "North Star Metric")
    if north_star:
        data["north_star"] = north_star

    dashboard = _extract_section(content, "Weekly Dashboard")
    if dashboard:
        data["dashboard_metrics"] = _extract_table_rows(dashboard)

    leading = _extract_section(content, "Leading Indicators")
    if leading:
        data["leading_indicators"] = _extract_table_rows(leading)

    formulas = _extract_section(content, "Google Sheets Formulas")
    if formulas:
        data["sheets_formulas"] = _extract_table_rows(formulas) or [formulas]

    sql = _extract_section(content, "SQL Dashboard Queries")
    if sql:
        data["sql_queries"] = _extract_code_blocks(sql) or [sql]

    events = _extract_section(content, "Tracking Event Spec")
    if events:
        data["tracking_events"] = _extract_table_rows(events)

    return data


def _parse_partnership_scout(content: str) -> dict:
    data: dict = {}

    targets = _extract_section(content, "Partnership Targets")
    if not targets:
        targets = _extract_section(content, "Top 15 Partnership Targets")
    if targets:
        data["targets"] = _extract_table_rows(targets)

    emails = _extract_section(content, "Partnership Outreach Emails")
    if not emails:
        emails = _extract_section(content, "Partnership Outreach")
    if emails:
        data["outreach_emails"] = _extract_code_blocks(emails)

    tiers = _extract_section(content, "Partnership Tiers")
    if tiers:
        data["tiers"] = tiers

    linkedin = _extract_section(content, "LinkedIn Partnership Outreach")
    if linkedin:
        data["linkedin_sequence"] = _extract_code_blocks(linkedin)

    return data


def _parse_community_architect(content: str) -> dict:
    data: dict = {}

    strategy = _extract_section(content, "Community Strategy")
    if strategy:
        data["strategy"] = strategy

    architecture = _extract_section(content, "Community Architecture")
    if architecture:
        data["channels"] = _extract_code_blocks(architecture) or [architecture]

    welcome = _extract_section(content, "Welcome Sequence")
    if welcome:
        data["welcome_messages"] = _extract_code_blocks(welcome)

    playbook = _extract_section(content, "Engagement Playbook")
    if playbook:
        data["engagement"] = _extract_table_rows(playbook)

    setup = _extract_section(content, "Platform Setup Guide")
    if setup:
        data["setup_guide"] = setup

    prompts = _extract_section(content, "First 10 Discussion Prompts")
    if prompts:
        data["discussion_prompts"] = _extract_numbered_items(prompts)

    return data


# ---------------------------------------------------------------------------
# Parser registry
# ---------------------------------------------------------------------------

PARSERS = {
    "icp_architect": _parse_icp_architect,
    "positioning_strategist": _parse_positioning_strategist,
    "competitor_intel": _parse_competitor_intel,
    "channel_mapper": _parse_channel_mapper,
    "outbound_engineer": _parse_outbound_engineer,
    "content_strategist": _parse_content_strategist,
    "pricing_analyst": _parse_pricing_analyst,
    "sales_playbook": _parse_sales_playbook,
    "crm_architect": _parse_crm_architect,
    "launch_planner": _parse_launch_planner,
    "automation_engineer": _parse_automation_engineer,
    "metrics_designer": _parse_metrics_designer,
    "partnership_scout": _parse_partnership_scout,
    "community_architect": _parse_community_architect,
}
