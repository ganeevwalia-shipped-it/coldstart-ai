"""
Cold Start AI — Meta Ads Connector
Pushes ICP audience definitions and campaign structures to Meta Marketing API.
Uses httpx for HTTP calls. Requires System User Token + Ad Account ID.
"""
from __future__ import annotations

import logging
import re
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

from .base import BaseConnector, register_connector
from .parsers import parse_agent_output

logger = logging.getLogger("coldstart.connectors.meta_ads")

META_API_BASE = "https://graph.facebook.com/v21.0"


class MetaAdsConnector(BaseConnector):
    platform = "meta_ads"
    supported_agents = ["icp_architect", "channel_mapper"]

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Validate Meta System User Token with a test API call."""
        if not httpx:
            return False
        token = credentials.get("access_token", "")
        if not token:
            return False
        try:
            resp = httpx.get(
                f"{META_API_BASE}/me",
                params={"access_token": token},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            logger.exception("Meta Ads credential validation failed")
            return False

    async def export(
        self,
        agent_id: str,
        parsed_data: dict[str, Any],
        credentials: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not httpx:
            return {"status": "error", "message": "httpx not installed. Run: pip install httpx"}
        if not credentials or not credentials.get("access_token"):
            return {"status": "error", "message": "Meta access token required"}
        if not credentials.get("ad_account_id"):
            return {"status": "error", "message": "Meta Ad Account ID required (format: act_XXXXXXXXX)"}

        token = credentials["access_token"]
        ad_account_id = credentials["ad_account_id"]
        # Normalize ad account ID format
        if not ad_account_id.startswith("act_"):
            ad_account_id = f"act_{ad_account_id}"

        content = parsed_data.get("raw", "")
        parsed = parse_agent_output(agent_id, content)
        data = parsed["data"]

        if agent_id == "icp_architect":
            return await self._export_audiences(data, content, token, ad_account_id)
        elif agent_id == "channel_mapper":
            return await self._export_campaign(data, content, token, ad_account_id)
        else:
            return {"status": "error", "message": f"Agent {agent_id} not supported for Meta Ads export"}

    async def _export_audiences(
        self, data: dict, content: str, token: str, ad_account_id: str
    ) -> dict:
        """Export ICP audience definitions as Meta Saved Audiences."""
        results: dict[str, Any] = {"created": [], "errors": []}

        # Extract audience targeting from the ad_audiences section
        ad_audiences = data.get("ad_audiences", "")
        if not ad_audiences:
            # Try to extract from raw content
            ad_audiences = self._extract_meta_section(content)

        if not ad_audiences:
            return {
                "status": "info",
                "message": "No Meta/Facebook audience definitions found in agent output. "
                "Ensure the ICP Architect output includes an 'Ad Platform Audience Definitions' section.",
            }

        # Parse audience segments from the text
        audiences = self._parse_audience_segments(ad_audiences)

        for audience in audiences:
            payload = {
                "name": f"Cold Start AI - {audience['name']}",
                "targeting": audience["targeting"],
                "access_token": token,
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{META_API_BASE}/{ad_account_id}/saved_audiences",
                        json=payload,
                        timeout=10,
                    )
                    if resp.status_code in (200, 201):
                        resp_data = resp.json()
                        results["created"].append(
                            f"Saved Audience: {audience['name']} (ID: {resp_data.get('id', 'N/A')})"
                        )
                    else:
                        error_msg = resp.text[:200]
                        results["errors"].append(
                            f"Audience '{audience['name']}': {resp.status_code} - {error_msg}"
                        )
            except Exception as e:
                results["errors"].append(f"Audience '{audience['name']}': {str(e)}")

        status = "success" if results["created"] and not results["errors"] else (
            "partial" if results["created"] else "error"
        )
        return {"status": status, **results}

    async def _export_campaign(
        self, data: dict, content: str, token: str, ad_account_id: str
    ) -> dict:
        """Export channel mapper recommendations as a Meta campaign structure."""
        results: dict[str, Any] = {"created": [], "errors": []}

        # Create a campaign based on channel recommendations
        campaign_name = "Cold Start AI - GTM Campaign"

        payload = {
            "name": campaign_name,
            "objective": "OUTCOME_LEADS",
            "status": "PAUSED",
            "special_ad_categories": [],
            "access_token": token,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{META_API_BASE}/{ad_account_id}/campaigns",
                    json=payload,
                    timeout=10,
                )
                if resp.status_code in (200, 201):
                    resp_data = resp.json()
                    campaign_id = resp_data.get("id", "")
                    results["created"].append(f"Campaign: {campaign_name} (ID: {campaign_id})")
                else:
                    error_msg = resp.text[:200]
                    results["errors"].append(f"Campaign creation: {resp.status_code} - {error_msg}")
        except Exception as e:
            results["errors"].append(f"Campaign creation: {str(e)}")

        status = "success" if results["created"] and not results["errors"] else (
            "partial" if results["created"] else "error"
        )
        return {"status": status, **results}

    def _extract_meta_section(self, content: str) -> str:
        """Extract Facebook/Meta specific section from raw content."""
        # Look for Facebook/Meta subsection in Ad Platform Audience Definitions
        patterns = [
            r"(?:Facebook|Meta)\s*(?:Ads?|Audience)?[:\s]*\n([\s\S]*?)(?=\n(?:Google|LinkedIn|###|\Z))",
            r"Ad Platform Audience Definitions[\s\S]*?(?:Facebook|Meta)([\s\S]*?)(?=\n###|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _parse_audience_segments(self, text: str) -> list[dict]:
        """Parse audience text into structured targeting specs."""
        audiences = []

        # Split by numbered items or bullet points
        segments = re.split(r"\n(?:\d+[\.\)]\s*|[-•]\s*)", text)
        segments = [s.strip() for s in segments if s.strip() and len(s.strip()) > 10]

        for i, segment in enumerate(segments[:5]):  # Max 5 audiences
            name = segment.split("\n")[0][:80].strip()
            if not name:
                name = f"ICP Audience {i + 1}"

            # Build targeting spec from text signals
            targeting: dict[str, Any] = {}

            # Extract age range if mentioned
            age_match = re.search(r"(\d{2})\s*[-–]\s*(\d{2})\s*(?:years?|age)", segment, re.IGNORECASE)
            if age_match:
                targeting["age_min"] = int(age_match.group(1))
                targeting["age_max"] = int(age_match.group(2))

            # Extract interests as flexible_spec
            interest_keywords = re.findall(
                r"interest(?:s|ed\s+in)?[:\s]+([^\n]+)", segment, re.IGNORECASE
            )
            if interest_keywords:
                targeting["flexible_spec"] = [
                    {"interests": [{"name": kw.strip()} for kw in interest_keywords[0].split(",")]}
                ]

            # Extract job titles
            title_keywords = re.findall(
                r"(?:job\s+)?title(?:s)?[:\s]+([^\n]+)", segment, re.IGNORECASE
            )
            if title_keywords:
                if "flexible_spec" not in targeting:
                    targeting["flexible_spec"] = [{}]
                targeting["flexible_spec"][0]["work_positions"] = [
                    {"name": t.strip()} for t in title_keywords[0].split(",")
                ]

            audiences.append({"name": name, "targeting": targeting})

        # If no segments parsed, create one generic audience from the whole text
        if not audiences:
            audiences.append({
                "name": "ICP Target Audience",
                "targeting": {},
            })

        return audiences


# Auto-register
register_connector(MetaAdsConnector())
