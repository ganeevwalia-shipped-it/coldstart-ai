"""
Cold Start AI — Curated GTM Knowledge Base
The internal canon. Every principle here is tagged by stage and motion
so agents get targeted wisdom, not generic platitudes.

Tags:
  stages: ["pre_revenue", "early_revenue", "scaling", "all"]
  motion: ["plg", "sales_led", "community_led", "all"]
"""


GTM_CANON = {
    "principles": [
        {
            "id": "distribution_over_product",
            "principle": "Distribution wins over product. A mediocre product with great distribution beats a great product with no distribution.",
            "implication": "Prioritize channels and outbound before polishing features.",
            "source": "Reid Hoffman / Peter Thiel",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["all"],
        },
        {
            "id": "do_things_that_dont_scale",
            "principle": "Do things that don't scale first. Manual outreach, personal onboarding, hand-holding.",
            "implication": "Before automating, do it manually 100 times to learn what works.",
            "source": "Paul Graham",
            "stages": ["pre_revenue"],
            "motion": ["all"],
        },
        {
            "id": "find_ten_who_pay",
            "principle": "Your only job pre-revenue is to find 10 people who will pay. Everything else is a distraction.",
            "implication": "No brand work, no automation, no scaling. Just find 10 paying customers.",
            "source": "First Round Capital",
            "stages": ["pre_revenue"],
            "motion": ["all"],
        },
        {
            "id": "one_channel_mastery",
            "principle": "Master one channel before adding a second. Spreading across 5 channels guarantees mediocrity in all.",
            "implication": "Pick the single best channel for your ICP and go deep.",
            "source": "Gabriel Weinberg / Traction",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["all"],
        },
        {
            "id": "icp_is_a_person",
            "principle": "An ICP is a specific person at a specific company with a specific pain, not a demographic category.",
            "implication": "'Startups' is not an ICP. 'Series A SaaS founders with 5-20 employees struggling with outbound' is.",
            "source": "Close.com / Steli Efti",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "id": "measure_cac_from_day_one",
            "principle": "Measure CAC and payback period from day 1. If you can't measure it, you can't improve it.",
            "implication": "Track cost per lead, cost per meeting, cost per customer from the first dollar spent.",
            "source": "David Sacks",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "id": "pricing_is_a_feature",
            "principle": "Price is a feature, not an afterthought. Underpricing kills more startups than overpricing.",
            "implication": "Charge more than you're comfortable with. If nobody pushes back, you're too cheap.",
            "source": "Patrick Campbell / ProfitWell",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["all"],
        },
        {
            "id": "founder_led_sales_first",
            "principle": "Founders must sell the first 20 deals themselves. You cannot delegate what you haven't done.",
            "implication": "Don't hire salespeople until you can close deals and articulate the playbook yourself.",
            "source": "Mark Roberge / HubSpot",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["sales_led"],
        },
        {
            "id": "plg_requires_aha_moment",
            "principle": "PLG only works if the product has a clear aha moment within the first session.",
            "implication": "If users need training or hand-holding, PLG will fail. Use sales-assisted or hybrid.",
            "source": "Wes Bush / ProductLed",
            "stages": ["all"],
            "motion": ["plg"],
        },
        {
            "id": "community_is_a_moat",
            "principle": "Community is the only GTM moat that gets stronger over time. But it takes 6-12 months to compound.",
            "implication": "Start community early but don't expect pipeline from it for months. It's an investment.",
            "source": "David Spinks",
            "stages": ["all"],
            "motion": ["community_led"],
        },
        {
            "id": "outbound_before_inbound",
            "principle": "Outbound gives you feedback in days. Inbound takes months. Start with outbound to learn, then layer in inbound.",
            "implication": "Send 100 cold emails before writing a single blog post. The replies will teach you your messaging.",
            "source": "Aaron Ross / Predictable Revenue",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["sales_led"],
        },
        {
            "id": "validate_before_optimize",
            "principle": "You cannot optimize what you haven't validated. Skip A/B testing, skip automation, skip funnels — until you have signal.",
            "implication": "Optimization is for things that work. First prove it works manually.",
            "source": "Eric Ries / Lean Startup",
            "stages": ["pre_revenue"],
            "motion": ["all"],
        },
        {
            "id": "talk_to_customers",
            "principle": "Talk to 50 potential customers before writing a single email sequence or launching a campaign.",
            "implication": "Customer conversations are the highest-ROI activity pre-revenue. Everything else is guessing.",
            "source": "Steve Blank",
            "stages": ["pre_revenue"],
            "motion": ["all"],
        },
        {
            "id": "double_down_on_what_works",
            "principle": "Double down on the channel that got your first 10 customers. Don't diversify until you've exhausted it.",
            "implication": "Build repeatability before adding complexity.",
            "source": "Brian Balfour",
            "stages": ["early_revenue"],
            "motion": ["all"],
        },
        {
            "id": "content_compounds",
            "principle": "Content compounds but ads don't. A blog post written today drives traffic for years. An ad stops the day you stop paying.",
            "implication": "For budget-constrained companies, content is the only scalable channel.",
            "source": "Tomasz Tunguz",
            "stages": ["all"],
            "motion": ["plg", "community_led"],
        },
        {
            "id": "enterprise_requires_trust",
            "principle": "Enterprise sales is about trust, not features. Case studies, references, and security reviews matter more than demos.",
            "implication": "Invest heavily in social proof, compliance, and relationship building for enterprise.",
            "source": "Jacco van der Kooij",
            "stages": ["early_revenue", "scaling"],
            "motion": ["sales_led"],
        },
        {
            "id": "vanity_metrics_kill",
            "principle": "Vanity metrics (followers, impressions, website visits) are comforting and useless. Track revenue metrics only.",
            "implication": "The only metrics that matter pre-scale: revenue, pipeline, and conversion rates.",
            "source": "Andrew Chen",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "id": "positioning_is_context",
            "principle": "Positioning is not what you say about your product. It's the context you set so customers understand why they should care.",
            "implication": "Define the category first. If the category is wrong, nothing else matters.",
            "source": "April Dunford",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "id": "sales_cycle_matches_price",
            "principle": "Your sales cycle must match your price point. $50/mo products cannot support 6-month sales cycles.",
            "implication": "If your ACV is low, you need PLG or high-volume outbound, not enterprise sales.",
            "source": "Jason Lemkin / SaaStr",
            "stages": ["all"],
            "motion": ["sales_led", "plg"],
        },
        {
            "id": "referral_loops_by_design",
            "principle": "Viral loops don't happen by accident. They must be designed into the product experience.",
            "implication": "If you want organic growth, build the referral mechanic before launch, not after.",
            "source": "Andrew Chen",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["plg"],
        },
    ],

    "do_dont": [
        {
            "do": "Pick one channel and master it before adding a second",
            "dont": "Spray across 5 channels at once",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["all"],
        },
        {
            "do": "Define ICP as a specific person at a specific company type",
            "dont": "Target 'startups' or 'enterprises' as an ICP",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "do": "Measure CAC and payback period from day 1",
            "dont": "Track followers, impressions, or vanity metrics",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "do": "Send 100 cold emails to learn messaging before writing sequences",
            "dont": "Build elaborate automation before validating the message",
            "stages": ["pre_revenue"],
            "motion": ["sales_led"],
        },
        {
            "do": "Charge more than you're comfortable with",
            "dont": "Compete on price or default to freemium without strategy",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["all"],
        },
        {
            "do": "Build one landing page with one CTA",
            "dont": "Create 5 landing pages for 5 segments before validating any",
            "stages": ["pre_revenue"],
            "motion": ["all"],
        },
        {
            "do": "Use customer language in your copy (steal from support tickets and calls)",
            "dont": "Write marketing copy in a conference room without customer input",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "do": "Set kill criteria for every channel experiment",
            "dont": "Keep running a channel 'because we've always done it'",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "do": "Build a repeatable sales process before hiring salespeople",
            "dont": "Hire AEs before founders can close deals themselves",
            "stages": ["early_revenue"],
            "motion": ["sales_led"],
        },
        {
            "do": "Invest in developer documentation and community for dev tools",
            "dont": "Use traditional B2B outbound for developer products",
            "stages": ["all"],
            "motion": ["plg", "community_led"],
        },
        {
            "do": "Create content that addresses ICP pain points directly",
            "dont": "Write thought leadership that impresses peers but doesn't reach buyers",
            "stages": ["all"],
            "motion": ["all"],
        },
        {
            "do": "Follow up within 5 minutes of an inbound lead",
            "dont": "Let leads sit in a queue for 24+ hours",
            "stages": ["early_revenue", "scaling"],
            "motion": ["sales_led"],
        },
        {
            "do": "Use case studies with specific metrics (e.g., '43% reduction in churn')",
            "dont": "Use generic testimonials ('Great product!')",
            "stages": ["early_revenue", "scaling"],
            "motion": ["all"],
        },
        {
            "do": "Design referral mechanics into the product before launch",
            "dont": "Add 'refer a friend' as an afterthought 6 months later",
            "stages": ["pre_revenue"],
            "motion": ["plg"],
        },
        {
            "do": "Start community building with 20 hand-picked founding members",
            "dont": "Launch a community publicly and hope people show up",
            "stages": ["pre_revenue", "early_revenue"],
            "motion": ["community_led"],
        },
    ],
}


def _normalize_stage(stage: str) -> str:
    """Map user-facing stage strings to canonical keys."""
    stage_lower = stage.lower()
    if any(kw in stage_lower for kw in ["idea", "pre-product"]):
        return "pre_revenue"
    if any(kw in stage_lower for kw in ["mvp", "pre-launch", "pre-revenue"]):
        return "pre_revenue"
    if any(kw in stage_lower for kw in ["scaling", "scale", "series"]):
        return "scaling"
    if any(kw in stage_lower for kw in ["early", "post-launch"]):
        return "early_revenue"
    if "growth" in stage_lower:
        return "scaling"
    return "pre_revenue"  # default to pre-revenue


def _normalize_motion(motion: str) -> str:
    """Map user-facing motion strings to canonical keys."""
    motion_lower = motion.lower()
    if any(kw in motion_lower for kw in ["product-led", "plg", "self-serve"]):
        return "plg"
    if any(kw in motion_lower for kw in ["sales", "outbound", "enterprise"]):
        return "sales_led"
    if any(kw in motion_lower for kw in ["community", "open source"]):
        return "community_led"
    return "all"


def _item_matches(item: dict, stage_key: str, motion_key: str) -> bool:
    """Check if a canon item matches the given stage and motion."""
    stage_match = "all" in item.get("stages", []) or stage_key in item.get("stages", [])
    motion_match = "all" in item.get("motion", []) or motion_key in item.get("motion", [])
    return stage_match and motion_match


def get_knowledge_context(stage: str = "", motion: str = "") -> str:
    """
    Build a knowledge base context block for agent prompts.
    Filters principles and do/don'ts by stage and motion for relevance.
    """
    stage_key = _normalize_stage(stage) if stage else "pre_revenue"
    motion_key = _normalize_motion(motion) if motion else "all"

    block = "\n\n" + "=" * 60 + "\n"
    block += "INTERNAL GTM CANON (Treat as ground truth)\n"
    block += f"Stage: {stage_key} | Motion: {motion_key}\n"
    block += "=" * 60 + "\n\n"

    # Add relevant principles (max 7 to avoid prompt bloat)
    relevant_principles = [
        p for p in GTM_CANON["principles"]
        if _item_matches(p, stage_key, motion_key)
    ]
    for p in relevant_principles[:7]:
        block += f"- {p['principle']} → {p['implication']}\n"

    # Add relevant do/don'ts (max 5)
    block += "\nDO / DON'T:\n"
    relevant_dodont = [
        dd for dd in GTM_CANON["do_dont"]
        if _item_matches(dd, stage_key, motion_key)
    ]
    for dd in relevant_dodont[:5]:
        block += f"- DO: {dd['do']}. DON'T: {dd['dont']}.\n"

    block += "\n"
    return block
