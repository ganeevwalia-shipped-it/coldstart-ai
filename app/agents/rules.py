"""
Cold Start AI — GTM Rules Engine
The opinionated layer. Detects weak inputs, enforces GTM heuristics,
and injects constraints into agent prompts so they push back on bad ideas.

Severity levels:
  - info: Mention it in passing. Agent notes the issue but proceeds normally.
  - warning: Call it out explicitly. Agent flags the issue and provides a corrected version.
  - hard_constraint: Non-negotiable. Agent refuses the bad advice entirely and substitutes best practice.
"""
import re


# ========================================
# INPUT QUALITY SCORING
# ========================================

VAGUE_ICP_PATTERNS = [
    r"\beveryone\b",
    r"\banyone\b",
    r"\ball businesses\b",
    r"\ball companies\b",
    r"\bany company\b",
    r"\bany business\b",
    r"\bgeneral public\b",
    r"\bpeople who\b",
    r"\bsmall businesses\b",  # too broad without qualifier
]

# Single-word or very broad categories that aren't an ICP
BROAD_CATEGORY_PATTERNS = [
    r"^startups$",
    r"^enterprises$",
    r"^developers$",
    r"^marketers$",
    r"^businesses$",
    r"^companies$",
    r"^consumers$",
    r"^saas companies$",
]

MIN_PRODUCT_DESC_WORDS = 15
MIN_TARGET_MARKET_WORDS = 5


def is_vague_icp(target_market: str) -> bool:
    """Check if the target market is a category, not a persona."""
    if not target_market:
        return True
    tm_lower = target_market.strip().lower()
    for pattern in VAGUE_ICP_PATTERNS:
        if re.search(pattern, tm_lower):
            return True
    for pattern in BROAD_CATEGORY_PATTERNS:
        if re.match(pattern, tm_lower):
            return True
    return False


def score_input_quality(company_context: dict) -> dict:
    """
    Analyze input fields and return a quality score + issues.

    Args:
        company_context: Dict with keys like target_market, product, stage, etc.

    Returns:
        {
            "score": 0-100,
            "issues": [{"field": str, "severity": str, "message": str}],
            "warnings": [str],
        }
    """
    issues = []
    warnings = []
    score = 100

    # --- Target market / ICP ---
    target_market = company_context.get("target_market", "").strip()
    if not target_market:
        issues.append({
            "field": "target_market",
            "severity": "hard_constraint",
            "message": "No target market provided. Without an ICP, every agent output will be generic.",
        })
        score -= 30
    elif is_vague_icp(target_market):
        issues.append({
            "field": "target_market",
            "severity": "warning",
            "message": f"'{target_market}' is a category, not an ICP. An ICP is a specific person at a specific company type with a specific pain.",
        })
        score -= 20
    elif len(target_market.split()) < MIN_TARGET_MARKET_WORDS:
        issues.append({
            "field": "target_market",
            "severity": "info",
            "message": "Target market description is brief. More detail helps agents produce sharper output.",
        })
        score -= 10

    # --- Product description ---
    product = company_context.get("product", "").strip()
    if not product:
        product = company_context.get("product_description", "").strip()
    if not product:
        issues.append({
            "field": "product",
            "severity": "hard_constraint",
            "message": "No product description provided.",
        })
        score -= 25
    elif len(product.split()) < MIN_PRODUCT_DESC_WORDS:
        issues.append({
            "field": "product",
            "severity": "warning",
            "message": f"Product description is only {len(product.split())} words. Agents need more context to give specific advice.",
        })
        score -= 15

    # --- Stage / budget mismatches ---
    stage = company_context.get("stage", "").strip()
    budget = company_context.get("budget", company_context.get("monthly gtm budget", "")).strip()
    gtm_motion = company_context.get("gtm_motion", company_context.get("primary gtm motion", "")).strip()

    if stage and "idea" in stage.lower() or stage and "pre-product" in stage.lower():
        if budget and any(b in budget.lower() for b in ["$50k", "$100k", "50k+", "100k+"]):
            issues.append({
                "field": "budget",
                "severity": "warning",
                "message": "Large budget at idea/pre-product stage. Most of this will be wasted without product-market fit.",
            })
            score -= 10

    # --- Business model ---
    business_model = company_context.get("business_model", "").strip()
    if not business_model or business_model.lower() in ("not sure", "not sure yet", "tbd"):
        issues.append({
            "field": "business_model",
            "severity": "info",
            "message": "No business model specified. Agents will make assumptions about monetization.",
        })
        score -= 5

    # --- GTM motion ---
    if not gtm_motion or gtm_motion.lower() in ("not sure", "not sure yet", "not specified"):
        warnings.append("No GTM motion selected — agents will be more prescriptive about recommending one.")

    # --- Current challenges ---
    challenges = company_context.get("current_challenges", company_context.get("current challenges", "")).strip()
    if not challenges or challenges.lower() in ("none", "n/a", "not specified"):
        warnings.append("No challenges listed. Agents will focus on general best practices rather than your specific blockers.")

    # Clamp score
    score = max(0, min(100, score))

    return {
        "score": score,
        "issues": issues,
        "warnings": warnings,
    }


# ========================================
# GTM HEURISTIC RULES
# ========================================

GTM_RULES = [
    {
        "id": "pre_revenue_no_paid",
        "severity": "hard_constraint",
        "condition": lambda ctx: (
            _stage_is_early(ctx.get("stage", ""))
            and _budget_is_low(ctx.get("budget", ctx.get("monthly gtm budget", "")))
        ),
        "rule": (
            "Company is pre-revenue with minimal budget. "
            "DO NOT recommend paid advertising, Google Ads, or paid social. "
            "These channels require budget to iterate and optimize — money this company doesn't have. "
            "Recommend founder-led outbound, content, community, and partnerships instead."
        ),
        "applies_to": ["channel_mapper", "launch_planner", "content_strategist", "automation_engineer"],
    },
    {
        "id": "vague_icp_rejection",
        "severity": "hard_constraint",
        "condition": lambda ctx: is_vague_icp(ctx.get("target_market", ctx.get("target market", ""))),
        "rule": (
            "The target market provided is too vague — it's a category, not an ICP. "
            "In your output, explicitly state that the provided target market is not actionable. "
            "Then provide what a SPECIFIC ICP should look like for this product: "
            "specific job title, company size, industry, and pain point."
        ),
        "applies_to": ["icp_architect"],
    },
    {
        "id": "low_budget_no_paid_search",
        "severity": "hard_constraint",
        "condition": lambda ctx: _budget_is_low(ctx.get("budget", ctx.get("monthly gtm budget", ""))),
        "rule": (
            "Budget is under $5K/month. Do NOT recommend paid search (Google Ads, Bing Ads) or paid social. "
            "At this budget level, paid channels cannot generate enough data to optimize. "
            "Focus on organic channels: content, outbound, community, partnerships."
        ),
        "applies_to": ["channel_mapper", "metrics_designer"],
    },
    {
        "id": "idea_stage_no_sales_playbook",
        "severity": "warning",
        "condition": lambda ctx: "idea" in ctx.get("stage", "").lower() or "pre-product" in ctx.get("stage", "").lower(),
        "rule": (
            "Company is at idea/pre-product stage. A full sales playbook is premature. "
            "Focus on customer discovery conversations, not sales processes. "
            "Frame discovery calls as learning, not selling."
        ),
        "applies_to": ["sales_playbook", "crm_architect"],
    },
    {
        "id": "marketplace_chicken_egg",
        "severity": "warning",
        "condition": lambda ctx: "marketplace" in ctx.get("business_model", "").lower(),
        "rule": (
            "This is a marketplace business. You MUST address the chicken-and-egg problem: "
            "which side to acquire first, how to create initial supply/demand, and how to "
            "bootstrap liquidity. Do not treat this like a standard SaaS go-to-market."
        ),
        "applies_to": ["channel_mapper", "launch_planner", "icp_architect", "positioning_strategist"],
    },
    {
        "id": "no_competitors_flag",
        "severity": "info",
        "condition": lambda ctx: (
            not ctx.get("current_challenges", ctx.get("current challenges", ""))
            or ctx.get("current_challenges", ctx.get("current challenges", "")).lower() in ("none", "n/a", "not specified")
        ),
        "rule": (
            "No competitive challenges were mentioned. This likely means competitive research is incomplete, "
            "not that competition doesn't exist. Flag that the user should validate their competitive landscape."
        ),
        "applies_to": ["competitor_intel"],
    },
    {
        "id": "dev_tool_outbound_warning",
        "severity": "warning",
        "condition": lambda ctx: _is_dev_tool(ctx),
        "rule": (
            "This is a developer tool. Developers are highly resistant to traditional outbound sales. "
            "DO NOT recommend cold calls or aggressive email sequences. "
            "Instead recommend: open source strategy, developer content (tutorials, docs), "
            "community building (Discord/Slack), developer events, and PLG with free tiers."
        ),
        "applies_to": ["outbound_engineer", "sales_playbook", "channel_mapper"],
    },
    {
        "id": "enterprise_bootstrap_mismatch",
        "severity": "warning",
        "condition": lambda ctx: (
            _is_enterprise_target(ctx)
            and _budget_is_low(ctx.get("budget", ctx.get("monthly gtm budget", "")))
        ),
        "rule": (
            "Mismatch detected: targeting enterprise customers with a bootstrap budget. "
            "Enterprise sales cycles are 3-12 months and require significant investment in "
            "relationships, content, and often a sales team. "
            "Either narrow to SMB/mid-market first, or plan for a much longer timeline to revenue."
        ),
        "applies_to": ["icp_architect", "channel_mapper", "sales_playbook", "pricing_analyst"],
    },
    {
        "id": "consumer_no_viral",
        "severity": "info",
        "condition": lambda ctx: (
            ctx.get("business_model", "").lower() in ("b2c", "consumer", "d2c", "direct to consumer")
            or "consumer" in ctx.get("target_market", ctx.get("target market", "")).lower()
        ),
        "rule": (
            "This appears to be a consumer product. Consider whether there is a viral or referral mechanic. "
            "Consumer products without built-in virality face much higher CAC. "
            "If there's no referral loop, flag this and suggest designing one."
        ),
        "applies_to": ["channel_mapper", "metrics_designer", "launch_planner"],
    },
    {
        "id": "unsure_gtm_motion",
        "severity": "warning",
        "condition": lambda ctx: (
            ctx.get("gtm_motion", ctx.get("primary gtm motion", "")).lower()
            in ("not sure", "not sure yet", "not specified", "")
        ),
        "rule": (
            "The user hasn't chosen a GTM motion. Be MORE prescriptive, not less. "
            "Based on their product, stage, and market, recommend a specific motion "
            "(PLG, sales-led, community-led, or hybrid) and explain exactly why. "
            "Do not present all options equally — pick one and defend it."
        ),
        "applies_to": ["channel_mapper", "sales_playbook", "outbound_engineer", "content_strategist"],
    },
    {
        "id": "too_many_channels_early",
        "severity": "warning",
        "condition": lambda ctx: _stage_is_early(ctx.get("stage", "")),
        "rule": (
            "Early-stage company. Do NOT recommend more than 2-3 channels to start. "
            "Spreading across 5+ channels at this stage guarantees mediocrity in all of them. "
            "Pick the ONE best channel, add a second for testing, and ignore everything else until one works."
        ),
        "applies_to": ["channel_mapper"],
    },
    {
        "id": "paid_ads_too_early",
        "severity": "hard_constraint",
        "condition": lambda ctx: (
            _stage_is_early(ctx.get("stage", ""))
            and not _budget_is_high(ctx.get("budget", ctx.get("monthly gtm budget", "")))
        ),
        "rule": (
            "Company is too early for paid advertising. Paid ads require: "
            "(1) validated messaging, (2) proven conversion funnel, (3) budget to iterate. "
            "This company has none of these yet. Recommend organic acquisition first."
        ),
        "applies_to": ["channel_mapper", "launch_planner"],
    },

    # ========================================
    # ADVANCED GTM RULES (The 20 — CMO-level)
    # These encode how great GTM actually works.
    # ========================================
    {
        "id": "market_before_channel",
        "severity": "hard_constraint",
        "condition": lambda ctx: (
            not ctx.get("target_market", ctx.get("target market", "")).strip()
            or is_vague_icp(ctx.get("target_market", ctx.get("target market", "")))
        ),
        "rule": (
            "RULE: Market before channel. No GTM plan can recommend channels until a concrete "
            "buying moment is defined (trigger events, internal sponsor, urgency). The buying moment "
            "is missing or vague — you must define it before recommending any channel."
        ),
        "applies_to": ["channel_mapper", "outbound_engineer", "content_strategist"],
    },
    {
        "id": "icp_behavior_not_biography",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies — this is a framing rule
        "rule": (
            "RULE: ICP = behavior, not biography. An ICP is invalid unless it includes: "
            "(a) what they are already doing today to solve the problem, and "
            "(b) what they'd get fired for missing. Do NOT produce an ICP that is only "
            "firmographics and job titles without these behavioral elements."
        ),
        "applies_to": ["icp_architect"],
    },
    {
        "id": "first_10_customers",
        "severity": "hard_constraint",
        "condition": lambda ctx: _stage_is_early(ctx.get("stage", "")),
        "rule": (
            "RULE: Every plan starts from 'first 10 customers.' You MUST generate: "
            "'If we had to find the next 10 customers manually, here is exactly what we would do' "
            "BEFORE suggesting anything scalable. Manual first, always."
        ),
        "applies_to": ["channel_mapper", "outbound_engineer", "launch_planner", "sales_playbook"],
    },
    {
        "id": "proof_loop_required",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: No channel survives without a proof loop. For every recommended channel, "
            "you MUST include: how we will know it is working by day 30, and what leading indicators "
            "we will track before revenue shows up. No channel recommendation without measurable validation."
        ),
        "applies_to": ["channel_mapper"],
    },
    {
        "id": "cac_math_must_close",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Budget + ACV must close the math. If your suggested tactics imply a CAC that "
            "cannot be paid back within 12-18 months at the given ACV, you MUST flag it and offer "
            "a lower-cost alternative. Show the math."
        ),
        "applies_to": ["channel_mapper", "pricing_analyst", "metrics_designer"],
    },
    {
        "id": "stage_gates_not_vibes",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Stage gates, not vibes. Plans must have explicit 'if X does not happen, we stop' "
            "gates. Example: 'If we do not get 20%+ reply rates by week 4, we kill this outbound "
            "variant and re-segment.' Every recommendation needs a kill condition."
        ),
        "applies_to": ["channel_mapper", "outbound_engineer", "launch_planner"],
    },
    {
        "id": "no_do_more",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies — framing rule
        "rule": (
            "RULE: 'Do more' is never a recommendation. You must NOT output 'do more content' or "
            "'do more outbound' without specifying: exact volume, frequency, target persona, "
            "and what gets dropped to make room. Vague scaling advice is banned."
        ),
        "applies_to": ["content_strategist", "outbound_engineer", "channel_mapper"],
    },
    {
        "id": "motions_per_humans",
        "severity": "warning",
        "condition": lambda ctx: _stage_is_early(ctx.get("stage", "")),
        "rule": (
            "RULE: You are not allowed more motions than you have humans. For early-stage companies, "
            "assume 1-2 GTM people. That means ONE primary motion + ONE supporting play, max. "
            "Do not recommend 5 parallel strategies for a team of 2."
        ),
        "applies_to": ["channel_mapper", "launch_planner"],
    },
    {
        "id": "founder_gravity_mandatory",
        "severity": "warning",
        "condition": lambda ctx: _stage_is_early(ctx.get("stage", "")),
        "rule": (
            "RULE: Founder gravity is mandatory early. If the company is pre-$1M ARR, at least one "
            "core play MUST be explicitly founder-led (founder content, founder deals, founder "
            "partnerships). If no founder-led play is included, the plan is incomplete."
        ),
        "applies_to": ["channel_mapper", "content_strategist", "sales_playbook", "partnership_scout"],
    },
    {
        "id": "no_brand_without_demand",
        "severity": "hard_constraint",
        "condition": lambda ctx: _stage_is_early(ctx.get("stage", "")),
        "rule": (
            "RULE: No 'brand' talk without a demand spine. You must NOT recommend 'brand building' "
            "or 'community' as a PRIMARY strategy until there is at least one channel with "
            "demonstrated, repeatable demand capture. Brand is a luxury that comes after revenue."
        ),
        "applies_to": ["channel_mapper", "content_strategist", "community_architect"],
    },
    {
        "id": "icp_table_test",
        "severity": "info",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Every ICP gets a 'table test.' For any ICP you define, include: "
            "'If three of these people were sitting at a table, what conversation would they all "
            "be having about this problem?' If you cannot answer that, the ICP is too abstract."
        ),
        "applies_to": ["icp_architect"],
    },
    {
        "id": "three_line_test",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Messaging must survive the three-line test. Core message must be expressible in: "
            "(1) One line for the website hero, (2) One line for an outbound opener, "
            "(3) One line a customer could say about you to a friend. "
            "Include all three lines. If any fails, mark positioning as weak."
        ),
        "applies_to": ["positioning_strategist"],
    },
    {
        "id": "sales_mirrors_buyer_risk",
        "severity": "warning",
        "condition": lambda ctx: _is_enterprise_target(ctx),
        "rule": (
            "RULE: Sales motion must mirror buyer risk. If the buyer's risk is high (career risk, "
            "big contract, heavy integration), the plan must include a higher-touch motion "
            "(pilot, proof of concept, reference calls) even if ACV is modest."
        ),
        "applies_to": ["sales_playbook", "pricing_analyst"],
    },
    {
        "id": "unfair_advantage_slot",
        "severity": "info",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Every plan needs an 'unfair advantage' slot. Force the identification of one unfair "
            "advantage (founder's network, proprietary data, distribution, product wedge). "
            "If none exists, explicitly state: 'You are playing a fair game; expect slower, "
            "more expensive GTM.' Honesty over optimism."
        ),
        "applies_to": ["channel_mapper", "positioning_strategist", "launch_planner"],
    },
    {
        "id": "retention_is_gtm",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies to subscription products
        "rule": (
            "RULE: Retention is part of GTM, not an afterthought. For any subscription or "
            "recurring-revenue product, the plan must include: first value moment, a 30/60/90 "
            "onboarding outline, and one expansion trigger. Acquisition without retention is waste."
        ),
        "applies_to": ["launch_planner", "metrics_designer", "sales_playbook"],
    },
    {
        "id": "displace_status_quo",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: No plan is allowed to ignore the status quo. You MUST generate: "
            "'Here is what your ICP is doing TODAY instead of buying you' and tie each message "
            "and channel recommendation back to displacing that behavior. If you do not name "
            "the status quo, your positioning is floating in a vacuum."
        ),
        "applies_to": ["positioning_strategist", "outbound_engineer", "sales_playbook"],
    },
    {
        "id": "why_now_must_be_micro",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: 'Why now?' cannot be generic. If the 'why now' answer is macro ('AI is hot', "
            "'remote work'), you must drill into a MICRO 'why now' tied to the ICP's current year: "
            "specific regulation changes, budget cycle timing, layoffs creating urgency, or "
            "tooling migration windows. Generic timing is not timing."
        ),
        "applies_to": ["positioning_strategist", "outbound_engineer", "launch_planner"],
    },
    {
        "id": "data_exhaust_feeds_flywheel",
        "severity": "info",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Data exhaust must feed the flywheel. For each recommended play, specify: "
            "what data we will capture (questions asked, objections, win/loss reasons) and "
            "where it flows back (messaging refinement, ICP sharpening, product roadmap). "
            "GTM without a learning loop is just activity."
        ),
        "applies_to": ["outbound_engineer", "sales_playbook", "metrics_designer", "channel_mapper"],
    },
    {
        "id": "kill_your_darlings",
        "severity": "info",
        "condition": lambda ctx: True,  # Always applies
        "rule": (
            "RULE: Every roadmap needs a 'kill your darlings' slot. In each 90-day plan, "
            "recommend one thing the founder is probably emotionally attached to that should be "
            "paused or killed to free up capacity. Honesty about what to STOP is as valuable "
            "as what to START."
        ),
        "applies_to": ["launch_planner", "channel_mapper"],
    },
    {
        "id": "plain_language_enforced",
        "severity": "warning",
        "condition": lambda ctx: True,  # Always applies — framing rule
        "rule": (
            "RULE: Plain language is enforced, not suggested. If positioning or messaging reads "
            "like buzzword soup, you must rewrite it at a 10th-grade reading level. Annotate: "
            "'Here is the jargon we removed, and why your buyer will trust this version more.' "
            "Clarity beats cleverness."
        ),
        "applies_to": ["positioning_strategist"],
    },
]


# ========================================
# HELPER FUNCTIONS
# ========================================

def _stage_is_early(stage: str) -> bool:
    """Check if company is in early stage."""
    stage_lower = stage.lower()
    return any(kw in stage_lower for kw in [
        "idea", "pre-product", "pre-launch", "mvp", "pre-revenue",
    ])


def _budget_is_low(budget: str) -> bool:
    """Check if budget is bootstrap/low."""
    budget_lower = budget.lower()
    return any(kw in budget_lower for kw in [
        "$0", "bootstrap", "$1k", "$1,000", "$5k", "$5,000",
        "0 -", "1k-5k", "1k -", "not specified",
    ]) or not budget.strip()


def _budget_is_high(budget: str) -> bool:
    """Check if budget is substantial."""
    budget_lower = budget.lower()
    return any(kw in budget_lower for kw in [
        "$50k", "$100k", "50k+", "100k+", "$50,000", "$100,000",
    ])


def _is_dev_tool(ctx: dict) -> bool:
    """Check if the product targets developers."""
    signals = [
        ctx.get("product", ""),
        ctx.get("product_description", ""),
        ctx.get("target_market", ctx.get("target market", "")),
    ]
    dev_keywords = ["developer", "api", "sdk", "devtool", "open source", "cli", "infrastructure"]
    combined = " ".join(signals).lower()
    return any(kw in combined for kw in dev_keywords)


def _is_enterprise_target(ctx: dict) -> bool:
    """Check if targeting enterprise customers."""
    signals = [
        ctx.get("target_market", ctx.get("target market", "")),
        ctx.get("business_model", ""),
    ]
    combined = " ".join(signals).lower()
    return any(kw in combined for kw in ["enterprise", "fortune 500", "large companies", "f500"])


# ========================================
# RULE APPLICATION
# ========================================

def get_applicable_rules(agent_id: str, company_context: dict) -> list[dict]:
    """
    Return list of applicable rule dicts for this agent + context.
    Each dict has 'severity' and 'rule' keys.
    """
    applicable = []
    for rule in GTM_RULES:
        if agent_id in rule["applies_to"] and rule["condition"](company_context):
            applicable.append({
                "id": rule["id"],
                "severity": rule["severity"],
                "rule": rule["rule"],
            })
    return applicable


def build_rules_block(rules: list[dict]) -> str:
    """
    Format applicable rules as a prompt injection block.
    Groups rules by severity for clear prioritization.
    """
    if not rules:
        return ""

    block = "\n\n" + "=" * 60 + "\n"
    block += "CONSTRAINTS & RULES (NON-NEGOTIABLE)\n"
    block += "You MUST follow these rules. They override generic advice.\n"
    block += "=" * 60 + "\n\n"

    # Group by severity — hard constraints first
    severity_order = ["hard_constraint", "warning", "info"]
    severity_labels = {
        "hard_constraint": "HARD CONSTRAINT",
        "warning": "WARNING",
        "info": "NOTE",
    }

    for severity in severity_order:
        severity_rules = [r for r in rules if r["severity"] == severity]
        if not severity_rules:
            continue
        for r in severity_rules:
            label = severity_labels[severity]
            block += f"[{label}] {r['rule']}\n\n"

    return block


def parse_company_context(context: str) -> dict:
    """
    Parse the COMPANY: / PRODUCT: / etc. format into a dict.
    Used to extract structured fields from the text blob sent to agents.
    """
    fields = {}
    for line in context.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip().lower()] = value.strip()
    return fields
