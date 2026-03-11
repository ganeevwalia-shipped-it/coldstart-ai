# Cold Start AI — Full Agent Architecture Map

## "I replaced my own GTM engineering job. Now you can too."

---

## SYSTEM OVERVIEW

Cold Start AI is an autonomous GTM engine that takes a company URL + a guided
onboarding conversation and outputs a **complete go-to-market system** —
positioning, ICP, channels, messaging, playbooks, sequences, and metrics —
delivered in Notion templates, Google Docs/PDF, and raw markdown.

This is everything a GTM engineer does, compressed into agents.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        COLD START AI ENGINE                          │
│                                                                      │
│   LAYER 1          LAYER 2            LAYER 3           LAYER 4      │
│  ┌────────┐    ┌────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │INTAKE  │───▶│INTELLIGENCE│───▶│GTM GENERATION│───▶│  OUTPUT   │  │
│  │        │    │            │    │              │    │           │  │
│  │Onboard │    │ Research & │    │ Positioning  │    │ Notion    │  │
│  │Flow    │    │ Enrichment │    │ ICP          │    │ PDF/Docs  │  │
│  │Agent   │    │ Agents     │    │ Channels     │    │ Markdown  │  │
│  │        │    │ (parallel) │    │ Playbooks    │    │           │  │
│  └────────┘    └────────────┘    │ Sequences    │    └───────────┘  │
│                                  │ Metrics      │                    │
│                                  └──────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## LAYER 1: INTAKE

### Agent 1.1 — Onboarding Conductor

**Role:** Guides the user through a conversational 7-question onboarding that
feels like talking to a GTM strategist, not filling out a form. Pre-fills
what it can from the URL scrape so the user is confirming, not typing.

**Trigger:** User provides company URL.

**Step 0 (automatic):** Scrape the URL. Extract product description, pricing,
features, team info, any existing messaging. This seeds the conversation.

**The 7 Questions:**

```
Q1: "Here's what I think [Company] does: [scraped summary].
     How would YOU describe it in one sentence?"
     → Confirm/correct the product description
     → OUTPUT: product_description

Q2: "Who's in pain without this? Tell me about your ideal customer."
     → Prompt with: their role, company size, industry, what triggers them to search
     → OUTPUT: raw_icp_signal

Q3: "What stage are you at?"
     → Pre-revenue | First 10 customers | $100K–$1M ARR | $1M+ ARR
     → OUTPUT: company_stage

Q4: "What have you tried so far? What worked, what flopped?"
     → Free text — captures GTM history and existing constraints
     → OUTPUT: gtm_history

Q5: "What's your budget and team?"
     → Budget range (bootstrapped / <$5K/mo / $5-20K/mo / $20K+/mo)
     → Team (just me / 1-2 people / small team / funded team)
     → OUTPUT: resource_constraints

Q6: "What does winning look like in 90 days?"
     → Revenue target, pipeline target, customer count, or "just need a plan"
     → OUTPUT: success_criteria

Q7: "Anything else? Competitors, unfair advantages, hard constraints?"
     → Catch-all for context the system couldn't infer
     → OUTPUT: additional_context
```

**Output:** `onboarding_profile` JSON

```json
{
  "company_url": "string",
  "scraped_data": {
    "raw_html_summary": "string",
    "detected_features": [],
    "detected_pricing": "string",
    "detected_messaging": "string"
  },
  "product_description": "string",
  "raw_icp_signal": "string",
  "company_stage": "pre_revenue | first_10 | sub_1m | over_1m",
  "gtm_history": "string",
  "resource_constraints": {
    "budget_range": "bootstrapped | under_5k | 5k_to_20k | over_20k",
    "team_size": "solo | small | team | funded"
  },
  "success_criteria": "string",
  "additional_context": "string"
}
```

---

## LAYER 2: INTELLIGENCE

**All Layer 2 agents run in parallel** after onboarding completes.
Total wall-clock time: ~30-60 seconds.

---

### Agent 2.1 — Company Intelligence Agent

**Role:** Deep-enriches everything about the company beyond the initial scrape.

**Inputs:** `company_url`, `product_description`, `scraped_data`

**Actions:**
- Deep-scrape all website pages (landing, pricing, about, blog, docs, changelog)
- Extract product features and value propositions
- Identify pricing model, tiers, and packaging strategy
- Pull public case studies, testimonials, G2/Capterra reviews
- Analyze existing content footprint (blog cadence, topics, SEO presence)
- Check social presence (LinkedIn company page, Twitter/X, YouTube)
- Identify tech stack signals (BuiltWith, Wappalyzer equivalent)

**Output:** `company_intel`
```json
{
  "product_features": ["string"],
  "current_positioning": "string",
  "pricing_model": { "type": "string", "tiers": [] },
  "social_proof": { "case_studies": [], "testimonials": [], "reviews": [] },
  "content_footprint": {
    "blog_posts_count": "number",
    "blog_cadence": "string",
    "top_performing_content": [],
    "seo_keywords_ranking": []
  },
  "social_presence": { "linkedin": {}, "twitter": {}, "youtube": {} },
  "tech_stack_signals": [],
  "messaging_analysis": {
    "strengths": [],
    "weaknesses": [],
    "inconsistencies": []
  }
}
```

---

### Agent 2.2 — Market Intelligence Agent

**Role:** Maps the competitive landscape and market dynamics.

**Inputs:** `product_description`, `raw_icp_signal`, `company_url`

**Actions:**
- Identify 5-10 direct competitors and 3-5 indirect/adjacent competitors
- Analyze each competitor's positioning, messaging, pricing, and GTM motion
- Map market categories and adjacent categories
- Identify market trends, tailwinds, and headwinds
- Find whitespace — gaps in competitor coverage
- Research recent funding/M&A activity in the space

**Output:** `market_intel`
```json
{
  "direct_competitors": [
    {
      "name": "string",
      "url": "string",
      "positioning": "string",
      "pricing": "string",
      "strengths": [],
      "weaknesses": [],
      "gtm_motion": "string",
      "estimated_size": "string"
    }
  ],
  "indirect_competitors": [],
  "market_category": "string",
  "adjacent_categories": [],
  "market_size_signals": "string",
  "trends_and_tailwinds": [],
  "headwinds": [],
  "competitive_whitespace": [],
  "recent_funding_activity": []
}
```

---

### Agent 2.3 — ICP Research Agent

**Role:** Builds a deep, validated Ideal Customer Profile with persona-level detail.

**Inputs:** `raw_icp_signal`, `product_description`, `company_stage`

**Actions:**
- Research target personas: titles, responsibilities, daily workflows, KPIs
- Identify buying triggers (what makes them search for a solution NOW)
- Map the full buying committee (champion, decision maker, influencer, blocker)
- Research where these people congregate (communities, Slack groups, subreddits, events, newsletters, podcasts)
- Identify common objections by persona type
- Research budget authority levels and typical procurement process
- Build firmographic filters (company size, industry, tech stack, growth signals)

**Output:** `icp_profile`
```json
{
  "primary_persona": {
    "title_variants": ["VP Marketing", "Head of Marketing", "CMO"],
    "seniority": "string",
    "responsibilities": [],
    "daily_workflow": "string",
    "kpis_they_own": [],
    "pain_points": [],
    "buying_triggers": [],
    "objections": [],
    "watering_holes": {
      "communities": [],
      "slack_groups": [],
      "subreddits": [],
      "newsletters": [],
      "podcasts": [],
      "events": [],
      "linkedin_influencers": []
    },
    "content_preferences": [],
    "how_they_evaluate": "string"
  },
  "secondary_personas": [],
  "buying_committee": {
    "champion": { "title": "", "cares_about": "", "how_to_arm": "" },
    "decision_maker": { "title": "", "cares_about": "", "how_to_sell": "" },
    "influencer": { "title": "", "cares_about": "" },
    "blocker": { "title": "", "concerns": "", "how_to_neutralize": "" }
  },
  "firmographics": {
    "company_size": "string",
    "industries": [],
    "tech_stack_signals": [],
    "growth_signals": [],
    "funding_stage": "string",
    "geographic_focus": "string"
  },
  "disqualification_criteria": []
}
```

---

### Agent 2.4 — Channel Intelligence Agent

**Role:** Scores and ranks GTM channels by fit, stage, budget, and expected ROI.

**Inputs:** `company_stage`, `resource_constraints`, `raw_icp_signal`, `gtm_history`

**Actions:**
- Score every viable channel: outbound email, LinkedIn outbound, cold calling,
  content/SEO, paid search, paid social, PLG, partnerships, community, events,
  referrals, influencer/creator, marketplace listings
- Weight by: stage appropriateness, budget fit, ICP reachability, time-to-impact
- Factor in what's already been tried (and results)
- Identify channel combinations that compound (e.g., content + outbound)

**Output:** `channel_strategy`
```json
{
  "primary_channels": [
    {
      "channel": "string",
      "why": "string",
      "how_it_works_for_your_stage": "string",
      "expected_time_to_first_results": "string",
      "estimated_monthly_cost": "string",
      "effort_level": "low | medium | high",
      "priority_rank": 1
    }
  ],
  "secondary_channels": [],
  "channel_combinations": [
    {
      "combo": ["content", "outbound"],
      "why_they_compound": "string"
    }
  ],
  "channels_to_avoid_now": [
    {
      "channel": "string",
      "why_not_yet": "string",
      "revisit_when": "string"
    }
  ],
  "recommended_channel_sequence": {
    "month_1": [],
    "month_2_3": [],
    "month_4_6": []
  }
}
```

---

## LAYER 3: GTM GENERATION

Layer 3 agents run **sequentially** where there are dependencies.
Agent 3.1 (Positioning) runs first — everything downstream depends on it.
Agents 3.2, 3.3, 3.4 can run **in parallel** after 3.1 completes.
Agent 3.5 runs after 3.3 + 3.4. Agent 3.6 runs last.

---

### Agent 3.1 — Positioning & Messaging Agent (RUNS FIRST)

**Role:** Creates the foundational positioning and messaging framework that
every other output builds on. This is the most important agent.

**Inputs:** `company_intel`, `market_intel`, `icp_profile`, `onboarding_profile`

**Outputs:**

```
positioning_framework:
│
├── One-Liner (≤10 words)
│   "We help [persona] [achieve outcome] without [pain]."
│
├── Elevator Pitch (30 seconds / 3 sentences)
│
├── Positioning Statement (April Dunford format)
│   For [target], who [need], [Product] is a [category]
│   that [key benefit]. Unlike [alternatives], we [differentiator].
│
├── Category Play
│   ├── Existing category to win in, OR
│   └── New category to create (with naming options)
│
├── Key Differentiators (3-5)
│   Each with: claim, evidence, and "so what?" for the buyer
│
├── Value Propositions by Persona
│   ├── Champion: "what you tell your boss"
│   ├── Decision Maker: "what moves the needle"
│   └── End User: "what makes your life easier"
│
├── Messaging Pillars (3)
│   Each with:
│   ├── Pillar headline
│   ├── Supporting points (3)
│   ├── Proof points / evidence
│   └── Objection it preempts
│
├── Competitive Positioning Matrix
│   ├── Feature comparison table
│   ├── Positioning map (2x2)
│   └── "Why us over X" for top 3 competitors
│
├── "Why Now?" Narrative
│   The market/technology/regulatory shift that makes
│   this the right time for this solution
│
├── Anti-Positioning
│   "We are NOT [X]. We don't [Y]. If you need [Z], we're not for you."
│   (Clarity through exclusion)
│
└── Messaging Do's and Don'ts
    Words/phrases to use vs. avoid
```

---

### Agent 3.2 — Content & Narrative Agent (after 3.1)

**Role:** Generates the full content system — calendar, templates, frameworks.

**Inputs:** `positioning_framework`, `icp_profile`, `channel_strategy`

**Outputs:**

```
content_system:
│
├── Homepage Messaging Wireframe
│   ├── Hero: headline, subhead, CTA
│   ├── Social proof bar
│   ├── Problem section
│   ├── Solution section (3 pillars)
│   ├── How it works (3 steps)
│   ├── Use cases / personas
│   ├── Testimonials
│   ├── Pricing CTA
│   └── Final CTA
│
├── Key Landing Page Copy Frameworks (3 pages)
│   ├── Use case page
│   ├── Competitor comparison page ("vs [Competitor]")
│   └── Persona-specific page
│
├── Blog/Content Calendar (12 weeks)
│   Each entry:
│   ├── Week number
│   ├── Topic / working title
│   ├── Target keyword + search volume estimate
│   ├── Funnel stage (TOFU / MOFU / BOFU)
│   ├── Content type (how-to, listicle, comparison, thought leadership)
│   ├── Distribution channels
│   └── Internal link targets
│
├── LinkedIn Content Playbook (Founder-Led)
│   ├── Content pillars (3-4 themes)
│   ├── Post templates (5 types with examples)
│   │   ├── Hot take / contrarian opinion
│   │   ├── Lesson learned / story
│   │   ├── Framework / how-to
│   │   ├── Social proof / customer win
│   │   └── Behind-the-scenes / building in public
│   ├── Weekly posting cadence (5x/week)
│   ├── Engagement strategy (who to comment on, how)
│   ├── Hashtag strategy
│   └── 30 pre-written post hooks
│
├── Email Newsletter Framework
│   ├── Newsletter positioning
│   ├── Cadence recommendation
│   ├── Template structure
│   └── First 4 edition outlines
│
├── Case Study Template
│   ├── Challenge → Solution → Results format
│   ├── Interview questions to ask customers
│   └── Distribution checklist
│
├── Sales Deck Narrative (10 slides)
│   1. The world has changed (why now)
│   2. The old way is broken (problem)
│   3. There's a better way (vision)
│   4. Introducing [Product] (solution)
│   5. How it works (3 steps)
│   6. Proof (case studies / metrics)
│   7. Why us (differentiators)
│   8. Who we serve (ICP)
│   9. Pricing / packages
│   10. Next steps / CTA
│
└── One-Pager / Leave-Behind Template
    Front: positioning + key benefits
    Back: social proof + how it works + CTA
```

---

### Agent 3.3 — Outbound Playbook Agent (after 3.1, parallel with 3.2 & 3.4)

**Role:** Builds the complete outbound motion — targeting, sequences, templates, tools.

**Inputs:** `icp_profile`, `positioning_framework`, `channel_strategy`, `resource_constraints`

**Outputs:**

```
outbound_system:
│
├── Prospecting Criteria & Lead Sourcing
│   ├── LinkedIn Sales Navigator saved searches (exact filters)
│   ├── Apollo.io search criteria
│   ├── Clay enrichment workflow
│   ├── Intent signal triggers to monitor
│   │   ├── Job postings signals
│   │   ├── Tech stack changes
│   │   ├── Funding announcements
│   │   ├── Leadership changes
│   │   └── Competitor mentions
│   └── Manual prospecting checklist (communities, events, content engagement)
│
├── Email Sequences (3 complete sequences)
│
│   Sequence 1: Cold Outbound (5 emails, 14 days)
│   ├── Email 1 (Day 1): Pain-led opener
│   │   ├── Subject lines (3 variants)
│   │   ├── Body copy
│   │   ├── Personalization framework
│   │   └── CTA
│   ├── Email 2 (Day 3): Value-add follow-up
│   ├── Email 3 (Day 6): Social proof / case study
│   ├── Email 4 (Day 10): Different angle / new pain point
│   └── Email 5 (Day 14): Breakup email
│
│   Sequence 2: Warm Trigger-Based (3 emails, 7 days)
│   (For prospects who hit an intent signal)
│
│   Sequence 3: Referral / Warm Intro (3 emails, 5 days)
│
├── LinkedIn Outbound Sequences
│   ├── Connection request messages (3 variants)
│   ├── Post-connect message sequence (4 messages, 10 days)
│   ├── Voice note scripts (2 variants)
│   └── InMail templates (for non-connections)
│
├── Cold Call Scripts
│   ├── Opening (pattern interrupt, 15 seconds)
│   ├── Permission-based opener
│   ├── Pain discovery bridge
│   ├── Quick pitch (30 seconds)
│   ├── Objection responses
│   │   ├── "Not interested" →
│   │   ├── "Send me an email" →
│   │   ├── "We already use [competitor]" →
│   │   ├── "No budget" →
│   │   └── "Bad timing" →
│   ├── Meeting set script
│   └── Voicemail script (< 20 seconds)
│
├── Multi-Channel Cadence (the full play)
│   Day 1: Email 1 + LinkedIn connect
│   Day 2: LinkedIn engage with their content
│   Day 3: Email 2
│   Day 4: LinkedIn message
│   Day 6: Email 3 + cold call attempt
│   Day 8: LinkedIn voice note
│   Day 10: Email 4
│   Day 12: Call attempt 2
│   Day 14: Email 5 (breakup)
│
├── Personalization Framework
│   ├── Tier 1 (top 50 accounts): deep research, custom first line
│   ├── Tier 2 (next 200): template + 1-2 personalized lines
│   └── Tier 3 (volume): template with dynamic fields only
│
└── Outbound Tool Stack
    ├── Sequencing: [recommendation based on budget]
    ├── Data/enrichment: [recommendation]
    ├── Email warmup: [recommendation]
    ├── LinkedIn automation: [recommendation]
    ├── Call tool: [recommendation]
    └── Setup checklist for each tool
```

---

### Agent 3.4 — Inbound & PLG Playbook Agent (after 3.1, parallel with 3.2 & 3.3)

**Role:** Builds the inbound engine and product-led growth motion (if applicable).

**Inputs:** `icp_profile`, `positioning_framework`, `channel_strategy`, `company_intel`

**Outputs:**

```
inbound_system:
│
├── SEO Strategy
│   ├── Keyword universe (30-50 keywords)
│   │   Each: keyword, search volume, difficulty, intent, priority
│   ├── Content clusters (3-4 pillar topics)
│   ├── Quick-win pages (low difficulty, high intent)
│   ├── Programmatic SEO opportunities
│   └── Technical SEO checklist
│
├── Lead Magnets (3 concepts)
│   Each:
│   ├── Type (template, calculator, tool, guide, benchmark report)
│   ├── Title and hook
│   ├── What it contains
│   ├── Landing page outline
│   ├── Promotion plan
│   └── Follow-up nurture sequence (5 emails)
│
├── Conversion Funnel
│   ├── Traffic sources → Landing pages
│   ├── Landing page → Lead capture (form, free tool, content gate)
│   ├── Lead → MQL nurture sequence (7 emails, 21 days)
│   │   ├── Welcome + immediate value
│   │   ├── Educational content
│   │   ├── Social proof
│   │   ├── Problem agitation
│   │   ├── Solution positioning
│   │   ├── Offer / demo invite
│   │   └── Final nudge
│   └── MQL → SQL handoff criteria
│
├── PLG Motion (if applicable)
│   ├── Free tier / trial strategy
│   ├── Activation definition + metrics
│   │   ├── "Aha moment" definition
│   │   ├── Time-to-value target
│   │   └── Activation checklist (what user must do)
│   ├── Onboarding email sequence (7 emails)
│   ├── In-app nudges and tooltips
│   ├── Upgrade triggers
│   │   ├── Usage-based triggers
│   │   ├── Feature-based triggers
│   │   └── Time-based triggers
│   └── PQL (Product Qualified Lead) definition + scoring
│
├── Paid Acquisition Framework
│   ├── Channel recommendations (Google, LinkedIn, Meta, Reddit)
│   ├── Budget allocation by channel
│   ├── Audience targeting criteria per channel
│   ├── Ad copy frameworks (3 angles per channel)
│   ├── Landing page requirements
│   └── Expected unit economics (target CAC, LTV)
│
└── Community & Partnerships
    ├── Community strategy (own community vs. participate in others)
    ├── Partnership types to pursue (integration, co-marketing, referral)
    ├── Partner outreach templates
    └── Community engagement playbook
```

---

### Agent 3.5 — Sales Process Agent (after 3.3 + 3.4)

**Role:** Builds the complete sales process from first touch to closed deal.

**Inputs:** `icp_profile`, `positioning_framework`, `company_stage`, `resource_constraints`

**Outputs:**

```
sales_system:
│
├── Qualification Framework
│   ├── BANT/MEDDIC adapted for company stage
│   ├── Scoring criteria (1-5 per dimension)
│   ├── Auto-qualify signals
│   ├── Auto-disqualify signals
│   └── "Fast track" criteria (skip steps)
│
├── Discovery Call Script (30 min)
│   ├── Opening / rapport (2 min)
│   ├── Agenda setting (1 min)
│   ├── Situation questions (5 min)
│   ├── Pain discovery questions — 10 specific questions (10 min)
│   ├── Impact quantification (5 min)
│   │   "What does this problem cost you in [time/money/headcount]?"
│   ├── Decision process mapping (5 min)
│   │   "Walk me through how you'd evaluate and buy something like this"
│   ├── Next steps + mutual action plan (2 min)
│   └── Disqualification script (graceful exit)
│
├── Demo Script
│   ├── Re-confirm pain points (2 min)
│   ├── Show, don't tell — map features to their specific pains
│   ├── "Day in the life" narrative
│   ├── Wow moments (3 planned)
│   └── Trial/next steps close
│
├── Objection Handling Playbook
│   ├── Price: "It's too expensive"
│   │   → Reframe to cost-of-inaction, ROI calculation
│   ├── Competitor: "We're looking at [X] too"
│   │   → Acknowledge, differentiate, offer comparison framework
│   ├── Timing: "Not the right time"
│   │   → Quantify delay cost, offer low-commitment start
│   ├── Authority: "I need to check with my boss"
│   │   → Arm the champion, offer to join the conversation
│   ├── Status quo: "We're fine with how things are"
│   │   → Future-state pain, competitive pressure
│   └── Each objection: acknowledge → question → reframe → proof → advance
│
├── Proposal Template
│   ├── Executive summary (their words, their pain)
│   ├── Recommended solution
│   ├── Expected outcomes / ROI
│   ├── Investment options (3 tiers: good/better/best)
│   ├── Timeline
│   ├── Mutual action plan
│   └── Terms
│
├── Pipeline Management
│   ├── Stages + exit criteria
│   │   1. Lead → Qualified (meets ICP + BANT)
│   │   2. Discovery Complete (pain confirmed, budget exists)
│   │   3. Demo/Evaluation (solution fit confirmed)
│   │   4. Proposal Sent (pricing delivered)
│   │   5. Negotiation (terms in discussion)
│   │   6. Closed Won / Closed Lost
│   ├── Stage conversion benchmarks
│   ├── Deal velocity targets by stage
│   └── Stalled deal playbook (re-engagement sequences)
│
├── Follow-Up Cadences
│   ├── Post-discovery (if no demo scheduled)
│   ├── Post-demo (if no proposal requested)
│   ├── Post-proposal (if no response)
│   └── Closed-lost re-engagement (30/60/90 day)
│
└── CRM Setup Guide
    ├── Recommended CRM (based on stage + budget)
    ├── Required custom fields
    ├── Deal stages configuration
    ├── Automation rules (stage changes, task creation, alerts)
    ├── Email integration setup
    ├── Reporting dashboard configuration
    └── Weekly pipeline review template
```

---

### Agent 3.6 — Metrics & Dashboard Agent (runs last)

**Role:** Defines measurement framework, KPIs, targets, and tracking.

**Inputs:** `channel_strategy`, `success_criteria`, `company_stage`, `resource_constraints`, all Layer 3 outputs

**Outputs:**

```
metrics_system:
│
├── North Star Metric
│   The ONE number that defines GTM success for this stage
│   (e.g., "Monthly Qualified Meetings" for pre-revenue,
│    "Net New ARR" for $1M+)
│
├── Input Metrics (Leading — what you control)
│   ├── Outbound: emails sent, connection requests, calls made
│   ├── Inbound: content published, SEO keywords tracked
│   ├── Paid: ad spend, impressions, clicks
│   └── Product: signups, activation rate (if PLG)
│
├── Throughput Metrics (Pipeline health)
│   ├── Reply rate, positive reply rate
│   ├── Meetings booked (outbound vs. inbound)
│   ├── MQL → SQL conversion rate
│   ├── Discovery → Demo rate
│   └── Demo → Proposal rate
│
├── Output Metrics (Lagging — what matters)
│   ├── Pipeline generated ($)
│   ├── Pipeline velocity (days)
│   ├── Win rate
│   ├── Closed revenue
│   ├── CAC (by channel)
│   └── LTV
│
├── Weekly Scorecard Template
│   ┌─────────────────┬──────┬──────┬────────┐
│   │ Metric          │ Goal │ Actual│ Status │
│   ├─────────────────┼──────┼──────┼────────┤
│   │ Emails sent     │      │      │ 🟢🟡🔴 │
│   │ Reply rate      │      │      │        │
│   │ Meetings booked │      │      │        │
│   │ Pipeline added  │      │      │        │
│   │ Deals advanced  │      │      │        │
│   │ Revenue closed  │      │      │        │
│   └─────────────────┴──────┴──────┴────────┘
│
├── 30/60/90 Day Targets
│   ├── Day 30: [specific milestones based on stage + channels]
│   ├── Day 60: [specific milestones]
│   └── Day 90: [specific milestones tied to success_criteria]
│
├── Channel Benchmarks
│   Per channel: what "good" looks like at this stage
│   (e.g., cold email: 40%+ open rate, 5%+ reply rate, 2% meeting rate)
│
├── Dashboard Specification
│   ├── Data sources (CRM, email tool, analytics, ad platforms)
│   ├── Key charts and widgets
│   ├── Recommended tool (Databox, Google Sheets, HubSpot dashboard)
│   └── Refresh cadence
│
└── Weekly GTM Review Meeting
    ├── Agenda template (30 min)
    │   1. Scorecard review (5 min)
    │   2. Pipeline review (10 min)
    │   3. What worked this week (5 min)
    │   4. What to adjust (5 min)
    │   5. Next week's priorities (5 min)
    └── Quarterly review template
```

---

## LAYER 4: OUTPUT

### Agent 4.1 — Output Formatter Agent

**Role:** Takes all Layer 3 outputs and renders them into three delivery formats.

---

#### Format 1: Notion Workspace (Duplicatable Template)

```
Cold Start GTM System/
│
├── 🏠 Dashboard
│   ├── Quick links to every section
│   ├── 90-day milestones tracker
│   └── Weekly scorecard (inline database)
│
├── 📍 Positioning & Messaging
│   ├── Positioning Framework
│   ├── Messaging Matrix (by persona)
│   ├── Competitive Battlecards
│   ├── One-pager content
│   └── Messaging Do's and Don'ts
│
├── 🎯 ICP & Personas
│   ├── Primary Persona Profile
│   ├── Secondary Personas
│   ├── Buying Committee Map
│   ├── Firmographic Criteria
│   └── Disqualification Criteria
│
├── 📤 Outbound Playbook
│   ├── Prospecting Criteria + Saved Searches
│   ├── Email Sequences (with copy)
│   ├── LinkedIn Sequences (with copy)
│   ├── Cold Call Scripts
│   ├── Multi-Channel Cadence
│   └── Personalization Framework
│
├── 📥 Inbound Playbook
│   ├── SEO Keyword Universe (database)
│   ├── Content Calendar (database, 12 weeks)
│   ├── Lead Magnet Specs
│   ├── Nurture Sequences
│   ├── PLG Playbook (if applicable)
│   └── Paid Acquisition Plan
│
├── 🤝 Sales Process
│   ├── Qualification Framework
│   ├── Discovery Call Script
│   ├── Demo Script
│   ├── Objection Handling Playbook
│   ├── Proposal Template
│   ├── Pipeline Stages
│   └── Follow-Up Cadences
│
├── 📊 Metrics & Tracking
│   ├── North Star + KPI Definitions
│   ├── Weekly Scorecard (template)
│   ├── 30/60/90 Day Targets
│   ├── Channel Benchmarks
│   └── Weekly Review Agenda
│
├── 💬 Content Library
│   ├── LinkedIn Post Templates + 30 Hooks
│   ├── Sales Deck Outline
│   ├── Case Study Template
│   ├── Email Newsletter Framework
│   └── One-Pager Template
│
└── 🛠 Tool Stack & Setup
    ├── Recommended Tools (with links)
    ├── CRM Setup Guide
    ├── Budget Allocation
    └── Implementation Checklist (30-day)
```

#### Format 2: PDF / Google Docs Package

```
documents/
├── 00_GTM_Executive_Summary.pdf           (5 pages — the full strategy at a glance)
├── 01_Positioning_Framework.pdf            (standalone, shareable with team/investors)
├── 02_ICP_Persona_Profiles.pdf            (visual persona cards)
├── 03_Competitive_Analysis.pdf            (battlecards + positioning matrix)
├── 04_Channel_Strategy.pdf                (prioritized channels + rationale)
├── 05_Outbound_Playbook.pdf              (sequences, templates, scripts — ready to use)
├── 06_Inbound_Playbook.pdf               (SEO, content, lead magnets, paid)
├── 07_Sales_Process_Guide.pdf            (discovery to close)
├── 08_Content_Calendar.pdf               (12-week plan)
├── 09_Metrics_Framework.pdf              (KPIs, scorecard, dashboards)
└── 10_Tool_Stack_Setup_Guide.pdf         (vendor recs + implementation checklist)
```

#### Format 3: Raw Markdown

```
markdown/
├── README.md                              (index + how to use this system)
├── 01-positioning-and-messaging.md
├── 02-icp-and-personas.md
├── 03-competitive-analysis.md
├── 04-channel-strategy.md
├── 05-outbound-playbook.md
├── 06-inbound-playbook.md
├── 07-sales-process.md
├── 08-content-calendar.md
├── 09-metrics-framework.md
├── 10-tool-stack.md
└── templates/
    ├── email-sequences.md
    ├── linkedin-sequences.md
    ├── call-scripts.md
    ├── discovery-call.md
    ├── objection-handling.md
    └── proposal-template.md
```

---

## ORCHESTRATION FLOW — FULL SEQUENCE

```
USER ENTERS URL
      │
      ▼
┌──────────────────────────┐
│  Agent 1.1: Onboarding   │  ← 3-5 min (user interaction)
│  Conductor                │
│  • Scrape URL             │
│  • 7-question guided flow │
└────────────┬─────────────┘
             │
      onboarding_profile
             │
             ▼
┌──────────────────────────────────────────┐
│  LAYER 2: INTELLIGENCE (parallel)        │  ← 30-60 sec
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 2.1      │  │ 2.2      │  │ 2.3    │ │
│  │ Company  │  │ Market   │  │ ICP    │ │
│  │ Intel    │  │ Intel    │  │Research│ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │            │      │
│       └──────┬───────┴────────────┘      │
│              ▼                            │
│       ┌────────────┐                     │
│       │ 2.4 Channel│  ← needs ICP data   │
│       │ Intel      │                     │
│       └─────┬──────┘                     │
└─────────────┼────────────────────────────┘
              │
     intelligence_bundle
              │
              ▼
┌──────────────────────────────────────────┐
│  LAYER 3: GTM GENERATION                 │  ← 2-4 min
│                                          │
│  ┌─────────────────────┐                 │
│  │ 3.1 Positioning &   │  ← FIRST       │
│  │     Messaging        │                 │
│  └──────────┬──────────┘                 │
│             │                            │
│    ┌────────┼────────┐   (parallel)      │
│    ▼        ▼        ▼                   │
│  ┌──────┐ ┌──────┐ ┌──────┐             │
│  │ 3.2  │ │ 3.3  │ │ 3.4  │             │
│  │Contnt│ │Outbnd│ │Inbnd │             │
│  └──┬───┘ └──┬───┘ └──┬───┘             │
│     │        │        │                  │
│     └────────┼────────┘                  │
│              ▼                           │
│       ┌────────────┐                     │
│       │ 3.5 Sales  │                     │
│       │ Process    │                     │
│       └─────┬──────┘                     │
│             ▼                            │
│       ┌────────────┐                     │
│       │ 3.6 Metrics│                     │
│       └─────┬──────┘                     │
└─────────────┼────────────────────────────┘
              │
       all_gtm_outputs
              │
              ▼
┌──────────────────────────────────────────┐
│  LAYER 4: OUTPUT (parallel)              │  ← 30-60 sec
│                                          │
│  ┌──────┐   ┌──────────┐   ┌─────────┐  │
│  │Notion│   │PDF/Google│   │Markdown │  │
│  │Templ.│   │Docs      │   │Files    │  │
│  └──┬───┘   └────┬─────┘   └────┬────┘  │
│     └────────────┼───────────────┘       │
└──────────────────┼───────────────────────┘
                   │
                   ▼
          USER RECEIVES COMPLETE
            GTM SYSTEM IN ALL
             THREE FORMATS

     Total time after onboarding: ~4-6 min
```

---

## TECH STACK

| Component | Recommended | Why |
|-----------|------------|-----|
| **LLM (Strategy)** | Claude Opus 4.6 | Best reasoning for positioning, strategy, analysis |
| **LLM (Volume)** | Claude Sonnet 4.6 | Fast + good enough for templates, sequences, formatting |
| **Agent Framework** | Claude Agent SDK | Native tool use, multi-agent orchestration |
| **Web Scraping** | Firecrawl | Reliable, handles JS-rendered sites |
| **Web Research** | Tavily API | Real-time search for market/competitor intel |
| **Data Enrichment** | Clay API + Apollo | Firmographic + contact data for ICP validation |
| **Frontend** | Next.js 15 + Tailwind | Conversational onboarding UI |
| **Backend** | Next.js API Routes | Agent orchestration + state management |
| **Job Queue** | Inngest | Long-running agent tasks with retries + fan-out |
| **Database** | Supabase (Postgres) | User data, generated outputs, usage analytics |
| **File Storage** | Supabase Storage | PDFs, markdown bundles |
| **Notion Output** | Notion API | Programmatic workspace/page creation |
| **Doc Generation** | Puppeteer + markdown-pdf | Clean PDF generation from structured output |
| **Auth** | Clerk | User management, waitlist |
| **Payments** | Stripe | Subscriptions + one-time purchases |
| **Hosting** | Vercel | Next.js native, edge functions |
| **Monitoring** | Helicone or LangSmith | LLM call tracing, cost tracking, quality monitoring |

---

## AGENT COMMUNICATION PROTOCOL

```typescript
// Every agent receives and returns this contract

interface AgentInput {
  task_id: string;              // unique run ID
  agent_id: string;             // e.g., "2.1_company_intel"
  inputs: Record<string, any>;  // agent-specific inputs
  context: {
    onboarding_profile: OnboardingProfile;
    previous_outputs?: Record<string, any>;  // outputs from upstream agents
  };
  config: {
    model: "opus" | "sonnet";   // which LLM to use
    max_retries: number;
    timeout_ms: number;
  };
}

interface AgentOutput {
  task_id: string;
  agent_id: string;
  status: "success" | "partial" | "failed";
  outputs: Record<string, any>;
  metadata: {
    confidence_score: number;       // 0-1
    execution_time_ms: number;
    model_used: string;
    tokens_used: { input: number; output: number };
    citations: string[];            // URLs/sources used
  };
  follow_up_questions?: string[];   // if agent needs user clarification
}
```

**Error handling:**
- `confidence_score < 0.6` → flag section for user review with explanation
- Agent failure → generate section with "[needs manual input]" placeholder, don't block pipeline
- User can regenerate any individual section after reviewing

---

## ESTIMATED EXECUTION COST PER RUN

| Phase | Model | Est. Tokens | Est. Cost |
|-------|-------|-------------|-----------|
| Layer 2 (4 agents) | Opus | ~40K in / ~20K out | ~$2.50 |
| Layer 3 (6 agents) | Opus + Sonnet | ~80K in / ~60K out | ~$5.00 |
| Layer 4 (formatting) | Sonnet | ~60K in / ~40K out | ~$1.50 |
| **Total per run** | | | **~$9-12** |

---

## MONETIZATION

| Tier | Price | Includes | Margin |
|------|-------|----------|--------|
| **Single Run** | $149 | 1 complete GTM system, all 3 formats | ~$137 |
| **Pro** | $399/mo | Unlimited runs, quarterly refresh, A/B variants, priority | ~90%+ |
| **Agency** | $1,499/mo | White-label, client workspaces, bulk generation, API access | ~90%+ |

---

## V2 ROADMAP

| Agent | Description |
|-------|-------------|
| **GTM Refresh Agent** | Quarterly re-run with updated market data, auto-detects what changed |
| **A/B Variant Generator** | Creates alternative messaging, subject lines, and sequences for testing |
| **Performance Analyst** | Connects to CRM + email tool, recommends adjustments based on real data |
| **Hiring Planner** | Based on metrics + stage, recommends when/who to hire next |
| **Board Deck Generator** | Creates investor-ready GTM slides from the system |
| **Competitor Monitor** | Ongoing alerts when competitors change positioning, pricing, or messaging |
| **Account-Based Agent** | Deep research on specific target accounts, custom messaging per account |
| **Event Playbook Agent** | Pre/during/post event playbook for conferences and trade shows |
