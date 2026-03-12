"""
Cold Start AI — Interactive Clarification Engine
Generates clarifying questions when input quality is low.
Questions are capped at 3-5 and prioritized by anti-pattern severity.

Priority order (matches worst GTM anti-patterns):
1. Vague ICP (most damaging — every downstream agent suffers)
2. Too many channels / paid ads too early
3. Missing business model or GTM motion
4. Short product description
5. Budget/stage mismatches
"""
from app.agents.rules import score_input_quality, is_vague_icp


MAX_CLARIFYING_QUESTIONS = 5


def get_clarifying_questions(company_context: dict) -> list[dict]:
    """
    Given company context, return 0-5 clarifying questions
    prioritized by anti-pattern severity.

    Returns list of:
        {
            "id": str,
            "question": str,
            "field": str (which form field to update),
            "priority": int (1=highest),
            "required": bool,
        }
    """
    questions = []
    scored = score_input_quality(company_context)

    target_market = company_context.get("target_market", "").strip()
    product = company_context.get("product_description", company_context.get("product", "")).strip()
    stage = company_context.get("stage", "").strip()
    business_model = company_context.get("business_model", "").strip()
    budget = company_context.get("budget", "").strip()
    gtm_motion = company_context.get("gtm_motion", company_context.get("primary gtm motion", "")).strip()
    challenges = company_context.get("current_challenges", company_context.get("current challenges", "")).strip()

    # Priority 1: Vague ICP (most damaging anti-pattern)
    if not target_market:
        questions.append({
            "id": "icp_missing",
            "question": "Who is your ideal customer? Be specific: job title, company size, industry, and what problem they have RIGHT NOW.",
            "field": "target_market",
            "priority": 1,
            "required": True,
        })
    elif is_vague_icp(target_market):
        questions.append({
            "id": "icp_vague",
            "question": f"'{target_market}' is a category, not an ICP. Can you narrow it? Example: 'Series A SaaS founders with 5-20 employees who can't scale outbound.' Who specifically?",
            "field": "target_market",
            "priority": 1,
            "required": True,
        })

    # Priority 2: Product description too thin
    if not product:
        questions.append({
            "id": "product_missing",
            "question": "What does your product do? In 2-3 sentences, describe the specific problem it solves and how.",
            "field": "product_description",
            "priority": 2,
            "required": True,
        })
    elif len(product.split()) < 15:
        questions.append({
            "id": "product_thin",
            "question": "Your product description is brief. Can you add: (1) the specific problem you solve, (2) how you solve it differently, and (3) what the user gets?",
            "field": "product_description",
            "priority": 2,
            "required": False,
        })

    # Priority 3: No GTM motion selected
    if not gtm_motion or gtm_motion.lower() in ("not sure", "not sure yet", "not specified"):
        questions.append({
            "id": "gtm_motion_unclear",
            "question": "How do you plan to sell? (a) Product-led / self-serve signup, (b) Outbound sales / founder-led deals, (c) Community / content-led inbound, or (d) Not sure — let us recommend.",
            "field": "gtm_motion",
            "priority": 3,
            "required": False,
        })

    # Priority 4: No business model
    if not business_model or business_model.lower() in ("not sure", "not sure yet", "tbd"):
        questions.append({
            "id": "business_model_unclear",
            "question": "What's your business model? SaaS subscription, marketplace, usage-based, services, or something else?",
            "field": "business_model",
            "priority": 4,
            "required": False,
        })

    # Priority 5: No challenges listed
    if not challenges or challenges.lower() in ("none", "n/a", "not specified"):
        questions.append({
            "id": "challenges_missing",
            "question": "What's your biggest GTM blocker right now? Examples: 'low reply rates on cold email', 'unclear positioning', 'no pipeline visibility', 'don't know which channel to start with.'",
            "field": "current_challenges",
            "priority": 5,
            "required": False,
        })

    # Sort by priority, cap at MAX
    questions.sort(key=lambda q: q["priority"])
    return questions[:MAX_CLARIFYING_QUESTIONS]


def get_plan_variants(company_context: dict) -> list[dict]:
    """
    Offer plan variants based on company context.
    Returns 2-3 options the user can choose from.
    """
    stage = company_context.get("stage", "").lower()
    budget = company_context.get("budget", "").lower()

    variants = []

    # Always offer the default
    variants.append({
        "id": "full_system",
        "name": "Full GTM System",
        "description": "Run all selected agents with chained intelligence. Complete go-to-market package.",
        "default": True,
    })

    # Early stage: offer tight sprint
    if any(kw in stage for kw in ["idea", "pre-product", "mvp", "pre-launch"]):
        variants.append({
            "id": "first_10_customers",
            "name": "First 10 Customers Sprint",
            "description": "Focused plan: ICP + Positioning + one channel + outbound. Everything you need to find your first 10 paying customers.",
        })

    # Budget-constrained: offer bootstrap version
    if any(kw in budget for kw in ["$0", "bootstrap", "$1k", "$5k", "not specified"]) or not budget:
        variants.append({
            "id": "bootstrap_playbook",
            "name": "Bootstrap Playbook",
            "description": "Zero-budget GTM: founder-led outbound, organic content, community. No paid channels.",
        })

    # If they have budget, offer scaling version
    if any(kw in budget for kw in ["$15k", "$50k", "$100k"]):
        variants.append({
            "id": "scale_ready",
            "name": "Scale-Ready System",
            "description": "Full system with paid channels, automation workflows, and team playbooks. For companies ready to pour fuel on fire.",
        })

    return variants
