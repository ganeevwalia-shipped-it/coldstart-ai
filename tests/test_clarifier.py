"""
Tests for Cold Start AI — Interactive Clarification Engine
Tests clarifying questions, plan variants, and the refine endpoint.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.agents.clarifier import get_clarifying_questions, get_plan_variants, MAX_CLARIFYING_QUESTIONS


# ========================================
# CLARIFYING QUESTIONS
# ========================================

class TestGetClarifyingQuestions:
    def test_vague_icp_triggers_question(self):
        ctx = {"target_market": "startups", "product_description": "A tool for collaboration and communication"}
        questions = get_clarifying_questions(ctx)
        ids = [q["id"] for q in questions]
        assert "icp_vague" in ids

    def test_missing_icp_triggers_question(self):
        ctx = {"target_market": "", "product_description": "A tool for analytics"}
        questions = get_clarifying_questions(ctx)
        ids = [q["id"] for q in questions]
        assert "icp_missing" in ids

    def test_good_input_minimal_questions(self):
        ctx = {
            "target_market": "Series A B2B SaaS founders with 10-50 employees building in fintech",
            "product_description": "An AI-powered outbound email tool that personalizes cold emails using LinkedIn activity and company news",
            "stage": "MVP / Pre-launch",
            "business_model": "SaaS",
            "budget": "$5K-$15K/month",
            "gtm_motion": "Sales-led",
            "current_challenges": "Low reply rates on cold outbound, unclear positioning",
        }
        questions = get_clarifying_questions(ctx)
        assert len(questions) == 0

    def test_max_questions_capped(self):
        # Worst case: everything missing/vague
        ctx = {}
        questions = get_clarifying_questions(ctx)
        assert len(questions) <= MAX_CLARIFYING_QUESTIONS

    def test_questions_ordered_by_priority(self):
        ctx = {
            "target_market": "everyone",
            "product_description": "tool",
            "gtm_motion": "Not sure",
            "business_model": "Not sure",
        }
        questions = get_clarifying_questions(ctx)
        priorities = [q["priority"] for q in questions]
        assert priorities == sorted(priorities)

    def test_required_flag_on_icp_question(self):
        ctx = {"target_market": "businesses"}
        questions = get_clarifying_questions(ctx)
        icp_q = next(q for q in questions if "icp" in q["id"])
        assert icp_q["required"] is True

    def test_missing_product_triggers_question(self):
        ctx = {"target_market": "B2B SaaS founders with 10-50 employees in fintech"}
        questions = get_clarifying_questions(ctx)
        ids = [q["id"] for q in questions]
        assert "product_missing" in ids

    def test_thin_product_triggers_question(self):
        ctx = {
            "target_market": "B2B SaaS founders with 10-50 employees in fintech",
            "product_description": "Email tool",
        }
        questions = get_clarifying_questions(ctx)
        ids = [q["id"] for q in questions]
        assert "product_thin" in ids

    def test_missing_gtm_motion_triggers_question(self):
        ctx = {
            "target_market": "B2B SaaS founders with 10-50 employees in fintech vertical SaaS",
            "product_description": "AI-powered outbound email tool that writes personalized cold emails at scale",
            "gtm_motion": "Not sure yet",
        }
        questions = get_clarifying_questions(ctx)
        ids = [q["id"] for q in questions]
        assert "gtm_motion_unclear" in ids

    def test_missing_challenges_triggers_question(self):
        ctx = {
            "target_market": "B2B SaaS founders with 10-50 employees in fintech vertical",
            "product_description": "AI-powered outbound email tool for personalizing cold emails using LinkedIn data",
            "current_challenges": "Not specified",
        }
        questions = get_clarifying_questions(ctx)
        ids = [q["id"] for q in questions]
        assert "challenges_missing" in ids

    def test_each_question_has_required_fields(self):
        ctx = {}
        questions = get_clarifying_questions(ctx)
        for q in questions:
            assert "id" in q
            assert "question" in q
            assert "field" in q
            assert "priority" in q
            assert "required" in q


# ========================================
# PLAN VARIANTS
# ========================================

class TestGetPlanVariants:
    def test_always_includes_full_system(self):
        variants = get_plan_variants({})
        ids = [v["id"] for v in variants]
        assert "full_system" in ids

    def test_early_stage_gets_sprint_variant(self):
        variants = get_plan_variants({"stage": "MVP / Pre-launch"})
        ids = [v["id"] for v in variants]
        assert "first_10_customers" in ids

    def test_bootstrap_gets_bootstrap_variant(self):
        variants = get_plan_variants({"budget": "$0 - Bootstrap"})
        ids = [v["id"] for v in variants]
        assert "bootstrap_playbook" in ids

    def test_high_budget_gets_scale_variant(self):
        variants = get_plan_variants({"budget": "$50K+/month"})
        ids = [v["id"] for v in variants]
        assert "scale_ready" in ids

    def test_returns_at_least_two_variants(self):
        variants = get_plan_variants({})
        assert len(variants) >= 2


# ========================================
# API ENDPOINTS
# ========================================

@pytest.mark.asyncio
class TestClarifyEndpoint:
    async def test_clarify_returns_questions_for_weak_input(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/clarify", json={
                "target_market": "everyone",
                "product_description": "tool",
            })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "questions" in data
        assert "variants" in data
        assert len(data["questions"]) > 0

    async def test_clarify_returns_no_questions_for_strong_input(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/clarify", json={
                "target_market": "Series A B2B SaaS founders with 10-50 employees building developer tools",
                "product_description": "AI-powered outbound email platform that writes highly personalized cold emails using prospect LinkedIn activity data and recent company news signals",
                "stage": "MVP / Pre-launch",
                "business_model": "SaaS",
                "budget": "$5K-$15K/month",
                "gtm_motion": "Sales-led",
                "current_challenges": "Low reply rates, unclear positioning versus competitors",
            })
        data = response.json()
        assert len(data["questions"]) == 0


@pytest.mark.asyncio
class TestRefineEndpoint:
    async def test_refine_agent_demo_mode(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/refine-agent", json={
                "agent_id": "icp_architect",
                "company_context": "COMPANY: TestCo\nPRODUCT: Test product for B2B teams",
                "previous_output": "## ICP Document\nSome previous output here",
                "user_feedback": "Make the ICP more focused on fintech",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "demo"
        assert "fintech" in data["content"]

    async def test_refine_agent_empty_feedback_400(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/refine-agent", json={
                "agent_id": "icp_architect",
                "company_context": "COMPANY: TestCo",
                "previous_output": "Some output",
                "user_feedback": "",
            })
        assert response.status_code == 400

    async def test_refine_agent_invalid_agent_400(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/refine-agent", json={
                "agent_id": "nonexistent_agent",
                "company_context": "COMPANY: TestCo",
                "previous_output": "Some output",
                "user_feedback": "Make it better",
            })
        assert response.status_code == 400


@pytest.mark.asyncio
class TestScoreInputEndpoint:
    async def test_score_input_returns_score(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/score-input", json={
                "target_market": "startups",
                "product": "tool",
            })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "issues" in data
        assert data["score"] < 80  # weak input should score low
