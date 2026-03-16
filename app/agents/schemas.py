"""
Cold Start AI — Structured Output Schemas
Defines required output sections per agent and validates completeness.
Schema validation failures are logged to validation_log.jsonl for prompt tuning.
"""
import json
import logging
import os
import re
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
            "Ad Platform Audience Definitions",
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
- **Ad Platform Audience Definitions**: Ready-to-paste targeting for Google Ads, Facebook/Meta Ads, and LinkedIn Ads
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
            "Website Section Copy",
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
- **Website Section Copy**: Hero section, About page, Features section, and CTA variations
""",
    },

    "channel_mapper": {
        "required_sections": [
            "Channel Stack",
            "Channel Kill List",
            "90-Day Roadmap",
            "Budget Scenarios",
            "Kill Criteria",
            "Week 1 Sprint Plan",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Channel Stack**: Top 3-5 channels, RANKED by priority. Each with: why it fits, expected CAC, time to results, specific tactics, success metric
- **Channel Kill List**: 3 channels that seem obvious but are TRAPS for this company
- **90-Day Roadmap**: Week-by-week action plan (12 weeks minimum) with channel, action, budget, expected result
- **Budget Scenarios**: Dollar allocation table for $5K/mo, $15K/mo, $50K/mo
- **Kill Criteria**: For each recommended channel, the specific threshold at which to abandon it
- **Week 1 Sprint Plan**: Monday-Friday daily breakdown with exact morning and afternoon actions
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

    "competitor_intel": {
        "required_sections": [
            "Competitive Landscape",
            "Battlecard",
            "Market Gaps",
            "Competitive Moat",
            "Printable Battle Cards",
            "Win/Loss Quick Reference",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Competitive Landscape**: Direct, indirect, and future competitors with positioning and weaknesses
- **Battlecard**: At least 3 competitor battlecards with comparison tables and objection responses
- **Market Gaps**: At least 3 gaps no competitor does well, with exploitation strategy
- **Competitive Moat**: Current defensibility + 6mo/12mo moat-building plan
- **Printable Battle Cards**: Self-contained one-page card per competitor with comparison, objection handlers, and killer question
- **Win/Loss Quick Reference**: 3-bullet summary per direct competitor (win when, lose when, key move)
""",
    },

    "metrics_designer": {
        "required_sections": [
            "North Star Metric",
            "Metrics Tree",
            "Weekly Dashboard",
            "Leading Indicators",
            "Metrics Anti-Patterns",
            "Google Sheets Formulas",
            "SQL Dashboard Queries",
            "Tracking Event Spec",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **North Star Metric**: Metric name, formula, reasoning, current and 6-month targets
- **Metrics Tree**: AARRR framework with formulas and targets per metric
- **Weekly Dashboard**: 7-10 metrics with formula, target, red/green flags, data source
- **Leading Indicators**: 5 early warning indicators with lag time and thresholds
- **Metrics Anti-Patterns**: 5 vanity metrics to ignore with alternatives
- **Google Sheets Formulas**: Ready-to-paste formulas with column definitions for each KPI
- **SQL Dashboard Queries**: 5 PostgreSQL queries with schema assumptions for key dashboards
- **Tracking Event Spec**: 12-15 analytics events in Segment/Mixpanel format with properties and triggers
""",
    },

    "partnership_scout": {
        "required_sections": [
            "Partnership Strategy",
            "Partnership Targets",
            "Partnership Outreach Emails",
            "Partnership Tiers",
            "Ecosystem Play",
            "LinkedIn Partnership Outreach",
            "Partnership One-Pager",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Partnership Strategy**: Primary partnership type, reasoning, expected impact
- **Partnership Targets**: Top 15 companies with type, fit reason, give/get, contact role, priority
- **Partnership Outreach Emails**: 5 ready-to-send emails with personalization tokens and PS lines
- **Partnership Tiers**: Strategic, Growth, and Affiliate tier structures with deal terms
- **Ecosystem Play**: Platform bet, how to become essential, marketplace strategy
- **LinkedIn Partnership Outreach**: 3-touch sequence (connection note, follow-up, pitch)
- **Partnership One-Pager**: Full draft partnership proposal document
""",
    },

    "community_architect": {
        "required_sections": [
            "Community Strategy",
            "Community Architecture",
            "First 100 Members",
            "Welcome Sequence",
            "Engagement Playbook",
            "Member Progression",
            "Community Health Metrics",
            "Platform Setup Guide",
            "First 10 Discussion Prompts",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Community Strategy**: Community type, platform recommendation, reasoning
- **Community Architecture**: Channel/space setup with descriptions and permissions
- **First 100 Members**: Week-by-week plan to seed and grow to 100 members
- **Welcome Sequence**: Auto-DM message and introduction prompt template
- **Engagement Playbook**: Day-by-day weekly activity plan with templates
- **Member Progression**: Level system with criteria, perks, and expected distribution
- **Community Health Metrics**: 8-10 metrics to track weekly
- **Platform Setup Guide**: Step-by-step setup instructions for recommended platform (channels, bots, permissions)
- **First 10 Discussion Prompts**: Ready-to-post conversation starters for first 2 weeks
""",
    },

    "launch_planner": {
        "required_sections": [
            "Launch Strategy",
            "Pre-Launch Phase",
            "Launch Week",
            "Launch Assets",
            "Post-Launch",
            "Launch Outreach",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Launch Strategy**: Launch type, reasoning, target date logic, success metric
- **Pre-Launch Phase**: Week -4 to -1 with day-by-day actions, details, and copy/assets
- **Launch Week**: Day-by-day plan (Mon-Fri) with morning/afternoon/evening actions and exact copy
- **Launch Assets**: Checklist with landing page headline, Product Hunt listing, launch email, tweet thread, LinkedIn post
- **Post-Launch**: Week +1 to +4 plan with focus, actions, and metrics
- **Launch Outreach**: Contact list by category (press, influencers, communities, partners) with templates
""",
    },

    "automation_engineer": {
        "required_sections": [
            "Lead Capture",
            "Content Distribution",
            "Outbound Sequence",
            "Meeting Booking",
            "Post-Demo Follow-up",
            "Automation Stack",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **Lead Capture**: Trigger→step→action workflow for lead capture, enrichment, and CRM routing
- **Content Distribution**: Automated workflow for cross-platform content publishing
- **Outbound Sequence**: Automated outbound workflow with enrichment, personalization, and follow-up logic
- **Meeting Booking**: Pre-meeting prep automation with enrichment and brief generation
- **Post-Demo Follow-up**: Automated follow-up sequence with CRM stage updates
- **Automation Stack**: Complete tool stack with purpose, cost, and priority
""",
    },

    "crm_architect": {
        "required_sections": [
            "CRM Recommendation",
            "Pipeline Stages",
            "Custom Fields",
            "Lead Scoring",
            "Automation Rules",
            "Email Templates",
        ],
        "format_instructions": """

OUTPUT FORMAT REQUIREMENTS (MANDATORY):
You MUST include ALL of the following sections:
- **CRM Recommendation**: Tool recommendation with setup time and monthly cost
- **Pipeline Stages**: 5-7 stages with definition, entry/exit criteria, typical time, win probability
- **Custom Fields**: Contact and deal custom fields with type, purpose, and required flag
- **Lead Scoring**: 10 scoring signals with point values and qualification threshold
- **Automation Rules**: 8-10 automation rules with trigger, action, and reasoning
- **Email Templates**: 5 pre-written email templates to load into CRM
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


# ---------------------------------------------------------------------------
# Output Quality Scoring
# ---------------------------------------------------------------------------

GENERIC_FILLER_PHRASES = [
    "leverage your network",
    "optimize your funnel",
    "best-in-class",
    "drive growth",
    "take it to the next level",
    "move the needle",
    "low-hanging fruit",
    "streamline your process",
    "unlock potential",
    "double down on",
    "game changer",
    "paradigm shift",
    "synergy",
    "thought leadership",
    "value proposition",
    "holistic approach",
    "deep dive",
    "circle back",
    "at the end of the day",
    "scalable solution",
]

QUALITY_LOG_PATH = os.environ.get(
    "QUALITY_LOG_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "quality_log.jsonl"),
)


def score_output_quality(agent_id: str, content: str, company_context: str) -> dict:
    """
    Score the quality of agent output based on specificity, actionability,
    and tailoring to the company context.

    Returns:
        {
            "score": 0-100,
            "specificity": 0-40,
            "actionability": 0-30,
            "tailoring": 0-30,
            "flags": [str],
        }
    """
    flags: list[str] = []
    content_lower = content.lower()
    context_lower = company_context.lower()

    # ---- Parse company_context ----
    company_name = ""
    product_keywords: list[str] = []
    target_market_keywords: list[str] = []
    stage = ""
    budget = ""

    for line in company_context.splitlines():
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if line_lower.startswith("company:"):
            company_name = line_stripped.split(":", 1)[1].strip()
        elif line_lower.startswith("product:"):
            raw = line_stripped.split(":", 1)[1].strip()
            product_keywords = [w for w in re.split(r"[\s,;/]+", raw) if len(w) > 3]
        elif line_lower.startswith("target market:"):
            raw = line_stripped.split(":", 1)[1].strip()
            target_market_keywords = [w for w in re.split(r"[\s,;/]+", raw) if len(w) > 3]
        elif line_lower.startswith("stage:"):
            stage = line_stripped.split(":", 1)[1].strip().lower()
        elif line_lower.startswith("monthly gtm budget:"):
            budget = line_stripped.split(":", 1)[1].strip().lower()

    # ---- Specificity scoring (0-40) ----
    if company_name:
        company_count = len(re.findall(re.escape(company_name), content, re.IGNORECASE))
    else:
        company_count = 0

    product_count = sum(
        len(re.findall(re.escape(kw), content, re.IGNORECASE))
        for kw in product_keywords
    )

    market_count = sum(
        len(re.findall(re.escape(kw), content, re.IGNORECASE))
        for kw in target_market_keywords
    )

    specificity = (
        min(company_count / 3, 1.0) * 15
        + min(product_count / 5, 1.0) * 15
        + min(market_count / 3, 1.0) * 10
    )

    if company_name and company_count == 0:
        flags.append("Company name not mentioned in output")

    # ---- Actionability scoring (0-30) ----
    concrete_patterns = [
        r"\d+%",                         # percentages
        r"\$[\d,]+",                     # dollar amounts
        r"\d+\s*(days?|weeks?|months?|hours?)",  # timeframes
        r"@\w+",                         # tool names / handles
    ]
    concrete_count = sum(
        len(re.findall(pat, content)) for pat in concrete_patterns
    )

    filler_count = sum(
        1 for phrase in GENERIC_FILLER_PHRASES
        if phrase.lower() in content_lower
    )

    concrete_score = min(concrete_count / 10, 1.0) * 20
    filler_penalty_score = max(0, 10 - filler_count)
    actionability = concrete_score + filler_penalty_score

    if filler_count > 5:
        flags.append(f"{filler_count} generic filler phrases detected")

    # ---- Tailoring scoring (0-30) ----
    # Stage check (0-10)
    stage_score = 0.0
    if "mvp" in stage or "idea" in stage or "pre" in stage:
        early_terms = ["early", "first", "validate", "founder"]
        early_hits = sum(1 for t in early_terms if t in content_lower)
        stage_score = min(early_hits / len(early_terms), 1.0) * 10
    elif "growth" in stage or "scale" in stage:
        growth_terms = ["scale", "team", "process"]
        growth_hits = sum(1 for t in growth_terms if t in content_lower)
        stage_score = min(growth_hits / len(growth_terms), 1.0) * 10

    # Budget check (0-10)
    budget_score = 10.0  # default full marks
    if "$0" in budget or "$1k" in budget or "bootstrap" in budget:
        expensive_terms = ["paid ads", "large budget", "$50k"]
        expensive_hits = sum(1 for t in expensive_terms if t in content_lower)
        if expensive_hits > 0:
            budget_score = max(0, 10 - expensive_hits * 5)
            flags.append("Budget mismatch detected")

    # Vertical check (0-10)
    vertical_score = 0.0
    # Extract vertical or business model keywords from context lines
    vertical_keywords: list[str] = []
    for line in company_context.splitlines():
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        if line_lower.startswith("vertical:") or line_lower.startswith("business model:"):
            raw = line_stripped.split(":", 1)[1].strip()
            vertical_keywords = [w for w in re.split(r"[\s,;/]+", raw) if len(w) > 3]

    if vertical_keywords:
        vertical_hits = sum(
            1 for kw in vertical_keywords
            if kw.lower() in content_lower
        )
        vertical_score = min(vertical_hits / max(len(vertical_keywords), 1), 1.0) * 10

    tailoring = stage_score + budget_score + vertical_score

    # ---- Final score ----
    raw_score = specificity + actionability + tailoring
    final_score = max(0, min(100, round(raw_score)))

    result = {
        "score": final_score,
        "specificity": round(specificity, 1),
        "actionability": round(actionability, 1),
        "tailoring": round(tailoring, 1),
        "flags": flags,
    }

    _log_quality_score(agent_id, result)
    return result


def _log_quality_score(agent_id: str, score: dict):
    """Append quality score to JSONL log for analysis."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "score": score["score"],
        "specificity": score["specificity"],
        "actionability": score["actionability"],
        "tailoring": score["tailoring"],
        "flags": score["flags"],
    }
    try:
        with open(QUALITY_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        logger.warning(f"Could not write quality log to {QUALITY_LOG_PATH}")
