"""
Shared test fixtures for Cold Start AI test suite.
"""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

# Ensure no real API calls during tests
os.environ.pop("ANTHROPIC_API_KEY", None)

from app.main import app
from app.agents.registry import AGENTS, AGENT_ORDER, CATEGORIES


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_company_context():
    """Realistic company context for testing."""
    return """
COMPANY: TestCo
WEBSITE: https://testco.io
PRODUCT: AI-powered code review tool that catches bugs before they hit production
TARGET MARKET: Engineering teams at Series A-C SaaS startups with 10-50 developers
STAGE: Pre-revenue
BUSINESS MODEL: B2B SaaS, usage-based pricing
MONTHLY GTM BUDGET: $5,000
PRIMARY GTM MOTION: Product-led
CURRENT CHALLENGES: Getting first 10 paying customers, no outbound process
"""


@pytest.fixture
def sample_company_context_minimal():
    """Minimal company context — just a name."""
    return "COMPANY: MinimalCo"


@pytest.fixture
def mock_anthropic_response():
    """Mock a successful Claude API response."""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="## ICP Document\n\nThis is the generated output.")]
    return mock_message


@pytest.fixture
def all_agent_ids():
    """All 14 agent IDs."""
    return list(AGENTS.keys())
