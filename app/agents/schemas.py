"""
Cold Start AI — Structured Output Schemas
Defines required output sections per agent and validates completeness.
Schema validation failures are logged to validation_log.jsonl for prompt tuning.
"""
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("coldstart.schemas")

# Path for validation failure log (append-only JSONL for prompt tuning)
VALIDATION_LOG_PATH = os.environ.get(
    "VALIDATION_LOG_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "validation_log.jsonl"),
)

AGENT_SCHEMAS = {
    "icp_architect": {
        "required_sections": [
            "Primary ICP",
            "Qualifying Criteria",
            "Disqualifying Criteria",
            "Core Pains",
            "Desired Outcomes",
            "Anti-ICP",
            "Buying Signals",
            "Lead Qualification",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections in your output:
- **Primary ICP**: ONE specific persona (job title + company profile), not a category
- **Qualifying Criteria**: Exactly 3-5 firmographic/behavioral signals that CONFIRM fit
- **Disqualifying Criteria**: Exactly 3-5 signals to REJECT a lead
- **Core Pains**: Exactly 3 specific, quotable pain statements (what they'd say out loud)
- **Desired Outcomes**: Exactly 3 outcomes (what success looks like for them after buying)
- **Anti-ICP**: At least 3 specific company/persona types to AVOID selling to
- **Buying Signals**: 10 observable signals indicating purchase intent
- **Lead Qualification**: Scoring table with criteria, weights, and score ranges
""",
    },

    "positioning_strategist": {
        "required_sections": [
            "Core Positioning",
            "One-Liner",
            "Value Props",
            "Proof Points",
            "Objections",
            "Rebuttals",
            "Messaging Hierarchy",
            "Copy Bank",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Core Positioning**: Positioning statement, category choice, elevator pitch
- **One-Liner**: Single sentence (under 15 words) usable as tagline
- **Value Props**: Exactly 3, each with pillar name, headline, supporting sentence, proof point
- **Proof Points**: Exactly 3 concrete proof points (metrics, case studies, or data)
- **Objections**: Exactly 3 most common objections buyers raise
- **Rebuttals**: Exactly 3 rebuttals — one for each objection, with exact scripts
- **Messaging Hierarchy**: Hero headline (8 words max) + subheadline + 3 pillars
- **Copy Bank**: Ready-to-use copy for website hero, LinkedIn bio, cold email opener, conference intro
""",
    },

    "channel_mapper": {
        "required_sections": [
            "Channel Stack",
            "Channel Kill List",
            "90-Day Roadmap",
            "Budget Scenarios",
            "Kill Criteria",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Channel Stack**: Top 3-5 channels, RANKED by priority. Each with: why it fits, expected CAC, time to results, specific tactics, success metric
- **Channel Kill List**: 3 channels that seem obvious but are TRAPS for this company
- **90-Day Roadmap**: Week-by-week action plan (12 weeks minimum) with channel, action, budget, expected result
- **Budget Scenarios**: Dollar allocation table for $5K/mo, $15K/mo, $50K/mo
- **Kill Criteria**: For each recommended channel, the specific threshold at which to abandon it
""",
    },

    "sales_playbook": {
        "required_sections": [
            "Discovery Script",
            "Discovery Questions",
            "Demo Flow",
            "Objection Handling",
            "Closing Framework",
            "Disqualification Signals",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Discovery Script**: Exact opening script (word for word, not a template)
- **Discovery Questions**: At least 8 questions, each with "listen for" annotations
- **Demo Flow**: 15-minute structure table with time, section, what to show, what to say
- **Objection Handling**: At least 8 objections with exact response scripts
- **Closing Framework**: Word-for-word close script + follow-up cadence (7-day sequence)
- **Disqualification Signals**: At least 3 signals that mean "end the call"
""",
    },

    "outbound_engineer": {
        "required_sections": [
            "Cold Email Sequence",
            "LinkedIn Sequence",
            "Objection Response",
            "Metrics Targets",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Cold Email Sequence**: 5-touch email sequence with exact subject lines and full email bodies (not templates with [brackets])
- **LinkedIn Sequence**: 4-touch LinkedIn sequence with exact messages
- **Objection Response**: At least 8 objections with "what they really mean" + response
- **Metrics Targets**: Target table for open rate, reply rate, meeting book rate with red flag thresholds
""",
    },

    "content_strategist": {
        "required_sections": [
            "Content Pillars",
            "30-Day Calendar",
            "LinkedIn Posts",
            "Lead Magnet",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Content Pillars**: 3-4 core themes with ICP pain connection and content ratio
- **30-Day Calendar**: All 30 days with platform, type, title, hook, CTA
- **LinkedIn Posts**: 5 ready-to-publish posts (full text, 150-200 words each, not outlines)
- **Lead Magnet**: Title, format, full chapter outline, landing page headline, CTA
""",
    },

    "pricing_analyst": {
        "required_sections": [
            "Pricing Model",
            "Tier Architecture",
            "Pricing Page Copy",
            "Revenue Model",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Pricing Model**: Recommended model (per seat/usage/flat/hybrid) with value metric and reasoning
- **Tier Architecture**: 3 tiers, each with exact price, target persona, feature list, limits, and goal
- **Pricing Page Copy**: Ready-to-implement pricing page layout with headlines, features, CTAs
- **Revenue Model**: Scenario table with conservative/moderate/aggressive projections at 6mo and 12mo
""",
    },
}


def validate_output_structure(agent_id: str, content: str) -> dict:
    """
    Check if agent output contains required sections.

    Returns:
        {
            "valid": bool,
            "missing": [str],
            "completeness": float (0.0 - 1.0),
        }
    """
    schema = AGENT_SCHEMAS.get(agent_id)
    if not schema:
        return {"valid": True, "missing": [], "completeness": 1.0}

    content_lower = content.lower()
    missing = []
    for section in schema["required_sections"]:
        if section.lower() not in content_lower:
            missing.append(section)

    total = len(schema["required_sections"])
    completeness = (total - len(missing)) / total if total > 0 else 1.0

    result = {
        "valid": len(missing) == 0,
        "missing": missing,
        "completeness": round(completeness, 2),
    }

    # Log validation failures for prompt tuning
    if missing:
        _log_validation_failure(agent_id, missing, completeness)

    return result


def get_format_instructions(agent_id: str) -> str:
    """Get format instructions for an agent, or empty string if no schema."""
    schema = AGENT_SCHEMAS.get(agent_id)
    if schema and schema.get("format_instructions"):
        return schema["format_instructions"]
    return ""


def _log_validation_failure(agent_id: str, missing: list[str], completeness: float):
    """Append validation failure to JSONL log for prompt tuning analysis."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "missing_sections": missing,
        "completeness": completeness,
    }
    try:
        with open(VALIDATION_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        logger.warning(f"Could not write validation log to {VALIDATION_LOG_PATH}")
