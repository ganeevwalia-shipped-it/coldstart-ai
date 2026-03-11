"""
Cold Start AI — Input validation and security.
Validates all user input before it reaches agents or the API.
"""
import re
import time
from collections import defaultdict
from fastapi import Request, HTTPException


# ========================================
# INPUT LIMITS
# ========================================

MAX_COMPANY_CONTEXT_LENGTH = 10_000  # chars
MAX_AGENT_OUTPUT_LENGTH = 50_000  # chars per agent in previous_outputs
MAX_PREVIOUS_OUTPUTS_COUNT = 14  # max agents
MAX_COMPANY_NAME_LENGTH = 200
MAX_FIELD_LENGTH = 5_000  # generic text fields
ALLOWED_AGENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,40}$")


def validate_agent_id(agent_id: str, valid_agents: dict) -> str:
    """Validate agent_id is well-formed and exists."""
    if not agent_id or not isinstance(agent_id, str):
        raise HTTPException(status_code=400, detail="agent_id is required")
    if not ALLOWED_AGENT_ID_PATTERN.match(agent_id):
        raise HTTPException(status_code=400, detail="Invalid agent_id format")
    if agent_id not in valid_agents:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_id}")
    return agent_id


def validate_company_context(ctx: str) -> str:
    """Validate and sanitize company context."""
    if not isinstance(ctx, str):
        raise HTTPException(status_code=400, detail="company_context must be a string")
    if len(ctx) > MAX_COMPANY_CONTEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"company_context too long ({len(ctx)} chars, max {MAX_COMPANY_CONTEXT_LENGTH})",
        )
    return ctx


def validate_previous_outputs(outputs: dict) -> dict:
    """Validate previous_outputs dict — used in chained mode."""
    if not isinstance(outputs, dict):
        raise HTTPException(status_code=400, detail="previous_outputs must be a dict")
    if len(outputs) > MAX_PREVIOUS_OUTPUTS_COUNT:
        raise HTTPException(status_code=400, detail="Too many previous_outputs")
    for key, value in outputs.items():
        if not isinstance(key, str) or not ALLOWED_AGENT_ID_PATTERN.match(key):
            raise HTTPException(status_code=400, detail=f"Invalid agent_id in previous_outputs: {key}")
        if not isinstance(value, str):
            raise HTTPException(status_code=400, detail=f"previous_outputs[{key}] must be a string")
        if len(value) > MAX_AGENT_OUTPUT_LENGTH:
            # Truncate silently — don't reject, just cap it
            outputs[key] = value[:MAX_AGENT_OUTPUT_LENGTH]
    return outputs


def validate_text_field(value: str, field_name: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """Validate a generic text input field."""
    if not isinstance(value, str):
        return ""
    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} too long ({len(value)} chars, max {max_length})",
        )
    return value


def validate_company_name(name: str) -> str:
    """Validate company name for exports (used in filenames)."""
    if not isinstance(name, str):
        return "Company"
    if len(name) > MAX_COMPANY_NAME_LENGTH:
        name = name[:MAX_COMPANY_NAME_LENGTH]
    return name


def validate_export_results(results: dict) -> dict:
    """Validate the results dict for export."""
    if not isinstance(results, dict):
        raise HTTPException(status_code=400, detail="results must be a dict")
    # Cap at 20 entries to prevent abuse
    if len(results) > 20:
        raise HTTPException(status_code=400, detail="Too many results to export")
    return results


# ========================================
# RATE LIMITING (in-memory, per-IP)
# ========================================

class RateLimiter:
    """Simple in-memory rate limiter. For production, use Redis."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, client_ip: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        now = time.time()
        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window
        ]
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        self.requests[client_ip].append(now)
        return True

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For behind reverse proxy."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Global rate limiters
generate_limiter = RateLimiter(max_requests=30, window_seconds=60)  # 30 gen/min
export_limiter = RateLimiter(max_requests=20, window_seconds=60)    # 20 exports/min
