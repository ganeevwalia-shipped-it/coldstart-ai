"""
Cold Start AI — HubSpot Live Connector
Pushes agent outputs directly to HubSpot via REST API v3.
Uses httpx for HTTP calls (consistent with codebase style, no SDK dependency).
"""
from __future__ import annotations

import logging
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

from .base import BaseConnector, register_connector
from .parsers import parse_agent_output

logger = logging.getLogger("coldstart.connectors.hubspot")

HUBSPOT_API_BASE = "https://api.hubapi.com"


class HubSpotConnector(BaseConnector):
    platform = "hubspot"
    supported_agents = ["crm_architect", "outbound_engineer", "icp_architect"]

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Validate HubSpot Private App token with a test API call."""
        if not httpx:
            return False
        token = credentials.get("api_key", "")
        if not token:
            return False
        try:
            resp = httpx.get(
                f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {token}"},
                params={"limit": 1},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            logger.exception("HubSpot credential validation failed")
            return False

    async def export(
        self,
        agent_id: str,
        parsed_data: dict[str, Any],
        credentials: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not httpx:
            return {"status": "error", "message": "httpx not installed. Run: pip install httpx"}
        if not credentials or not credentials.get("api_key"):
            return {"status": "error", "message": "HubSpot API key required"}

        token = credentials["api_key"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        content = parsed_data.get("raw", "")
        parsed = parse_agent_output(agent_id, content)
        data = parsed["data"]

        if agent_id == "crm_architect":
            return await self._export_crm(data, headers)
        elif agent_id == "outbound_engineer":
            return await self._export_emails(data, headers)
        elif agent_id == "icp_architect":
            return await self._export_contacts(data, headers)
        else:
            return {"status": "error", "message": f"Agent {agent_id} not supported for HubSpot export"}

    async def _export_crm(self, data: dict, headers: dict) -> dict:
        """Export CRM pipeline stages and custom properties to HubSpot."""
        results = {"created": [], "errors": []}

        # Create custom contact properties
        contact_fields = data.get("contact_fields", [])
        for field in contact_fields:
            field_name = field.get("field", "").lower().replace(" ", "_").replace("/", "_")
            if not field_name:
                continue
            payload = {
                "name": f"cs_{field_name}",
                "label": field.get("field", field_name),
                "type": "string",
                "fieldType": "text",
                "groupName": "contactinformation",
                "description": field.get("why_it_matters", ""),
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{HUBSPOT_API_BASE}/crm/v3/properties/contacts",
                        headers=headers,
                        json=payload,
                        timeout=10,
                    )
                    if resp.status_code in (200, 201):
                        results["created"].append(f"Contact property: {field_name}")
                    elif resp.status_code == 409:
                        results["created"].append(f"Contact property already exists: {field_name}")
                    else:
                        results["errors"].append(f"Contact property {field_name}: {resp.status_code}")
            except Exception as e:
                results["errors"].append(f"Contact property {field_name}: {str(e)}")

        # Create deal custom properties
        deal_fields = data.get("deal_fields", [])
        for field in deal_fields:
            field_name = field.get("field", "").lower().replace(" ", "_").replace("/", "_")
            if not field_name:
                continue
            payload = {
                "name": f"cs_{field_name}",
                "label": field.get("field", field_name),
                "type": "string",
                "fieldType": "text",
                "groupName": "dealinformation",
                "description": field.get("why_it_matters", ""),
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{HUBSPOT_API_BASE}/crm/v3/properties/deals",
                        headers=headers,
                        json=payload,
                        timeout=10,
                    )
                    if resp.status_code in (200, 201):
                        results["created"].append(f"Deal property: {field_name}")
                    elif resp.status_code == 409:
                        results["created"].append(f"Deal property already exists: {field_name}")
                    else:
                        results["errors"].append(f"Deal property {field_name}: {resp.status_code}")
            except Exception as e:
                results["errors"].append(f"Deal property {field_name}: {str(e)}")

        status = "success" if not results["errors"] else "partial"
        return {"status": status, **results}

    async def _export_emails(self, data: dict, headers: dict) -> dict:
        """Export email sequences as HubSpot email templates (marketing emails)."""
        results = {"created": [], "errors": []}
        sequences = data.get("email_sequences", [])

        for seq in sequences:
            subject = seq.get("subject_a", f"Cold Start Email {seq.get('touch', '')}")
            body = seq.get("body", "")
            if not body:
                continue

            # Create as a marketing email template
            payload = {
                "name": f"Cold Start - Touch {seq.get('touch', 'N')} - {subject}",
                "subject": subject,
                "body": {"value": f"<html><body><p>{body.replace(chr(10), '<br>')}</p></body></html>"},
                "type": "REGULAR",
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{HUBSPOT_API_BASE}/marketing/v3/emails",
                        headers=headers,
                        json=payload,
                        timeout=10,
                    )
                    if resp.status_code in (200, 201):
                        results["created"].append(f"Email template: Touch {seq.get('touch')}")
                    else:
                        results["errors"].append(f"Email Touch {seq.get('touch')}: {resp.status_code}")
            except Exception as e:
                results["errors"].append(f"Email Touch {seq.get('touch')}: {str(e)}")

        status = "success" if not results["errors"] else "partial"
        return {"status": status, **results}

    async def _export_contacts(self, data: dict, headers: dict) -> dict:
        """Note: ICP architect doesn't generate actual contact records.
        This exports the ICP as a note/description for reference."""
        primary_icp = data.get("primary_icp", "")
        if not primary_icp:
            return {"status": "skipped", "message": "No ICP data to export"}

        return {
            "status": "info",
            "message": "ICP data exported as reference. Use the HubSpot CSV import to bulk-create contacts matching this ICP.",
            "icp_summary": primary_icp[:500],
        }


# Auto-register
register_connector(HubSpotConnector())
