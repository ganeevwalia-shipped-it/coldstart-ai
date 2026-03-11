"""
Cold Start AI — Vertical-Specific GTM Intelligence
Every vertical has unique GTM patterns. A fintech SaaS sells nothing like a dev tool.
This module injects vertical-specific context into agent prompts.
"""

VERTICALS = {
    "b2b_saas": {
        "name": "B2B SaaS",
        "detect_keywords": ["saas", "b2b", "subscription", "enterprise", "software as a service", "platform"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: B2B SaaS

Key GTM patterns for B2B SaaS:
- Sales cycles: 14-90 days depending on ACV. Under $5K ACV = self-serve/PLG. $5K-$50K = sales-assisted. $50K+ = enterprise sales.
- Critical metrics: CAC payback period (target <12 months), LTV:CAC ratio (target >3:1), net revenue retention (target >110%), time to value.
- Channel priority by stage: Pre-revenue → outbound + content + communities. $10K-$50K MRR → add paid + partnerships. $50K+ → add enterprise sales + events.
- Pricing: Land with a low-friction entry point. Expand through usage or seats. 80% of revenue should come from expansion, not new logos.
- Content that works: Comparison pages, ROI calculators, case studies with specific metrics, "how we do X" behind-the-scenes content.
- Outbound that works: Pain-first messaging, trigger-based outreach (funding, hiring, tech stack changes), multi-threading into accounts.
- Common mistakes: Going enterprise too early, building features instead of distribution, pricing too low, not tracking activation metrics.
"""
    },

    "dev_tool": {
        "name": "Developer Tool / API",
        "detect_keywords": ["developer", "api", "sdk", "cli", "devtool", "infrastructure", "open source", "developer tool"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: Developer Tools

Key GTM patterns for dev tools:
- Developers hate being sold to. Product-led growth is non-negotiable. The product IS the marketing.
- Distribution channels: GitHub (stars, contributions), Hacker News, dev communities (Discord, Reddit r/programming), Twitter/X dev community, Stack Overflow, dev.to, technical blog posts.
- Pricing: Freemium is almost mandatory. Free tier must be genuinely useful (not crippled). Monetize on usage/scale, not features.
- Content that works: Technical tutorials, "how we built X" posts, benchmarks, migration guides, documentation-as-marketing.
- Outbound that works: It mostly doesn't for individual devs. Target engineering managers/CTOs for enterprise. Use "bottom-up" adoption signals.
- Key metrics: GitHub stars, weekly active developers, API calls, time-to-first-API-call, documentation page views.
- Common mistakes: Marketing-speak (devs will roast you), gating the free tier too aggressively, ignoring documentation, not having a CLI.
- The playbook: Open source or generous free tier → developer adoption → bottom-up enterprise → sales team closes expansion.
"""
    },

    "marketplace": {
        "name": "Marketplace",
        "detect_keywords": ["marketplace", "two-sided", "platform connecting", "match", "supply and demand"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: Marketplace

Key GTM patterns for marketplaces:
- Chicken-and-egg problem is THE challenge. Always start with supply side (it's easier to recruit supply than demand).
- Go hyper-local or hyper-niche first. Own one zip code or one category before expanding.
- Manual-first: Do things that don't scale. Personally onboard first 100 supply-side users. Curate quality aggressively.
- Pricing: Take rate between 10-25% typically. Consider who pays — buyer, seller, or both.
- Liquidity is the only metric that matters early on. What % of listings/searches result in a transaction?
- Content: SEO for long-tail supply-side searches. User-generated content is your moat.
- Common mistakes: Launching in too many cities/categories at once, not curating supply quality, disintermediating too late.
"""
    },

    "ecommerce_dtc": {
        "name": "E-commerce / DTC",
        "detect_keywords": ["ecommerce", "e-commerce", "dtc", "direct to consumer", "shopify", "physical product", "brand"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: E-commerce / DTC

Key GTM patterns for DTC:
- Paid social (Meta, TikTok) is the primary growth engine, but it's expensive. ROAS target: 3-4x minimum.
- Email/SMS is your highest-ROI channel. Build the list from day 1. Klaviyo flows: welcome, abandoned cart, post-purchase, win-back.
- Content: UGC (user-generated content) outperforms studio content 3:1 on paid social. Invest in creators, not agencies.
- Influencer marketing: Micro-influencers (10K-100K followers) have highest ROI. Seed product generously. Affiliate programs work.
- Key metrics: CAC, ROAS, AOV, LTV, repeat purchase rate, email list growth rate, contribution margin.
- Pricing: Keystone markup (2x cost) is minimum. Premium positioning allows 4-8x. Bundles increase AOV 20-40%.
- Common mistakes: Spending on paid before nailing product-market fit, ignoring retention/repeat purchase, not building a brand (just performance marketing).
"""
    },

    "fintech": {
        "name": "Fintech",
        "detect_keywords": ["fintech", "financial", "banking", "payments", "lending", "insurance", "investing", "crypto", "defi"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: Fintech

Key GTM patterns for fintech:
- Trust is everything. Social proof, security badges, compliance certifications, and transparent pricing are non-negotiable.
- Regulatory awareness: Your GTM must account for compliance constraints. Can't make certain claims. Need disclaimers.
- B2B fintech: Long sales cycles (3-12 months). Security reviews, compliance checks, procurement. Need champion + economic buyer.
- B2C fintech: Referral programs are 10x more effective than paid (trust transfer). Waitlists create FOMO.
- Content: Educational content builds trust. "How X works" explainers, comparison guides, financial literacy content.
- Partnerships: Banks, accounting firms, and financial advisors are distribution channels, not just partners.
- Key metrics: Trust score (NPS), time to first transaction, regulatory approval timelines, cost of compliance.
- Common mistakes: Underestimating compliance costs, not having a trust-building strategy, trying to compete with banks on brand.
"""
    },

    "ai_ml": {
        "name": "AI / ML Product",
        "detect_keywords": ["ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt", "model", "neural", "generative"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: AI / ML Products

Key GTM patterns for AI products:
- The market is NOISY. Every product claims to be "AI-powered." Your positioning must be outcome-based, not technology-based.
- Don't sell AI. Sell the outcome. "AI-powered writing tool" loses to "Write 10x faster." Nobody cares about the model.
- Demo-driven sales: AI products sell on "wow moments." Your demo must have a clear before/after that makes jaws drop.
- Pricing: Usage-based pricing aligns with value. Per-API-call, per-generation, per-seat-with-usage-limits.
- Content: Show don't tell. Live demos, case studies with metrics, comparison with manual workflows, ROI calculators.
- Moat: AI itself is not a moat (models commoditize). Data, workflows, integrations, and distribution are moats.
- Key metrics: Time to "aha moment," usage frequency, output quality scores, cost per inference, expansion revenue.
- Common mistakes: Leading with technology instead of outcomes, not having a clear "wow moment," pricing on seats when usage-based is better.
"""
    },

    "agency_services": {
        "name": "Agency / Services",
        "detect_keywords": ["agency", "consulting", "services", "freelance", "done for you", "managed"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: Agency / Services

Key GTM patterns for agencies:
- Your personal brand IS your marketing. Founders who build audience convert 5-10x better than cold outreach alone.
- Productize your service: Fixed scope, fixed price, clear deliverable. "We do X for $Y in Z days." This is how you scale.
- Content: Case studies are king. "How we got [client] from X to Y" posts. Share frameworks publicly, sell implementation.
- Outbound works great: Agencies have clear ICP. Target companies at specific stages with specific problems.
- Referrals: 60-80% of agency revenue comes from referrals. Build a systematic referral program.
- Pricing: Value-based, not hourly. Retainers > projects. Anchor with your most expensive package.
- Key metrics: Client acquisition cost, lifetime value, utilization rate, profit margin per client, referral rate.
- Common mistakes: Not niching down, competing on price, being too dependent on referrals with no outbound.
"""
    },

    "consumer_app": {
        "name": "Consumer App",
        "detect_keywords": ["consumer", "app", "mobile", "social", "gen z", "b2c app", "consumer app"],
        "gtm_context": """
VERTICAL-SPECIFIC GTM INTELLIGENCE: Consumer App

Key GTM patterns for consumer apps:
- Virality must be built into the product. If the product doesn't have a sharing/invitation mechanic, add one before launch.
- TikTok and Instagram Reels are the primary discovery channels. Short-form video is non-negotiable.
- Launch strategy: Build waitlist → exclusive beta → public launch with social proof. Create FOMO.
- Influencer seeding: Give the product to 50-100 creators before launch. Let them create the narrative.
- ASO (App Store Optimization): Keywords, screenshots, and ratings matter enormously. Optimize before spending on paid.
- Key metrics: DAU/MAU ratio (target >25%), D1/D7/D30 retention, viral coefficient (k-factor), time in app.
- Pricing: Freemium with premium features. Subscription > one-time purchase. Keep free tier generous enough for word-of-mouth.
- Common mistakes: Building for everyone (niche down to a specific community first), ignoring retention for growth, not having shareable moments.
"""
    },
}


def detect_vertical(product_description: str, business_model: str, target_market: str) -> list[dict]:
    """
    Auto-detect which vertical(s) match the product.
    Returns list of matching verticals with their GTM context.
    """
    combined_text = f"{product_description} {business_model} {target_market}".lower()
    matches = []

    for vertical_id, vertical in VERTICALS.items():
        score = 0
        for keyword in vertical["detect_keywords"]:
            if keyword.lower() in combined_text:
                score += 1

        if score > 0:
            matches.append({
                "id": vertical_id,
                "name": vertical["name"],
                "score": score,
                "context": vertical["gtm_context"],
            })

    # Sort by score (most relevant first)
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def get_vertical_context(product_description: str, business_model: str, target_market: str) -> str:
    """
    Get the vertical-specific GTM context to inject into agent prompts.
    Returns empty string if no vertical detected.
    """
    matches = detect_vertical(product_description, business_model, target_market)

    if not matches:
        return ""

    context = "\n\n" + "=" * 60 + "\n"
    context += "VERTICAL-SPECIFIC GTM INTELLIGENCE\n"
    context += "=" * 60 + "\n"

    # Include top 2 matching verticals
    for match in matches[:2]:
        context += match["context"]

    return context
