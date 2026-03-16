"""
Cold Start AI — CSV/JSON Export Connector
Generates downloadable CSV files from parsed agent outputs.
Also generates platform-formatted CSVs for HubSpot and Apollo import.
"""
from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

from .base import BaseConnector, register_connector
from .parsers import parse_agent_output

logger = logging.getLogger("coldstart.connectors.csv")


# ---------------------------------------------------------------------------
# Agent → CSV column mappings
# ---------------------------------------------------------------------------

AGENT_CSV_CONFIGS: dict[str, list[dict[str, Any]]] = {
    "icp_architect": [
        {
            "filename": "icp-criteria",
            "data_key": "lead_qualification",
            "columns": ["criteria", "weight", "score_1-3_(low)", "score_4-6_(med)", "score_7-10_(high)"],
        },
        {
            "filename": "search-queries",
            "data_key": "search_strings",
            "is_list": True,
            "columns": ["query"],
        },
    ],
    "outbound_engineer": [
        {
            "filename": "email-sequences",
            "data_key": "email_sequences",
            "columns": ["touch", "subject_a", "subject_b", "body"],
        },
        {
            "filename": "linkedin-sequences",
            "data_key": "linkedin_messages",
            "columns": ["touch", "message"],
        },
    ],
    "content_strategist": [
        {
            "filename": "content-calendar",
            "data_key": "calendar",
            "columns": ["day", "platform", "type", "title", "hook_(first_line)", "cta", "time_to_create"],
        },
    ],
    "crm_architect": [
        {
            "filename": "pipeline-stages",
            "data_key": "pipeline_stages",
            "columns": ["stage", "definition", "entry_criteria", "exit_criteria", "typical_time", "win_probability"],
        },
        {
            "filename": "custom-fields",
            "data_key": "contact_fields",
            "columns": ["field", "type", "why_it_matters", "required?"],
        },
    ],
    "channel_mapper": [
        {
            "filename": "channel-plan",
            "data_key": "roadmap",
            "columns": ["week", "action", "channel", "budget", "expected_result"],
        },
    ],
    "pricing_analyst": [
        {
            "filename": "pricing-tiers",
            "data_key": "tiers",
            "columns": ["name", "price", "details"],
        },
        {
            "filename": "revenue-model",
            "data_key": "revenue_model",
            "columns": ["scenario", "users", "avg_price", "mrr", "arr"],
        },
    ],
    "sales_playbook": [
        {
            "filename": "objection-handling",
            "data_key": "objections",
            "columns": ["#", "objection", "what_they_really_mean", "response_script"],
        },
        {
            "filename": "discovery-questions",
            "data_key": "discovery_questions",
            "is_list": True,
            "columns": ["question"],
        },
    ],
    "metrics_designer": [
        {
            "filename": "kpi-dashboard",
            "data_key": "dashboard_metrics",
            "columns": ["metric", "formula", "target", "red_flag", "green_flag", "data_source"],
        },
        {
            "filename": "tracking-events",
            "data_key": "tracking_events",
            "columns": ["event_name", "trigger", "properties", "priority"],
        },
    ],
    "partnership_scout": [
        {
            "filename": "partnership-targets",
            "data_key": "targets",
            "columns": ["#", "company", "type", "why_they_fit", "what_we_give", "what_we_get", "contact_(role)", "priority"],
        },
    ],
    "launch_planner": [
        {
            "filename": "launch-timeline",
            "data_key": "outreach",
            "columns": ["category", "who_to_contact", "how", "template"],
        },
    ],
}


# ---------------------------------------------------------------------------
# HubSpot-formatted CSV mappings
# ---------------------------------------------------------------------------

HUBSPOT_MAPPINGS: dict[str, dict[str, Any]] = {
    "crm_architect": {
        "filename": "hubspot-pipeline-stages",
        "data_key": "pipeline_stages",
        "columns": {
            "stage": "Stage Name",
            "definition": "Description",
            "win_probability": "Win Probability (%)",
            "typical_time": "Days in Stage",
        },
    },
    "outbound_engineer": {
        "filename": "hubspot-email-templates",
        "data_key": "email_sequences",
        "columns": {
            "subject_a": "Email Subject",
            "body": "Email Body",
            "touch": "Sequence Step",
        },
    },
}


# ---------------------------------------------------------------------------
# Apollo-formatted CSV mappings
# ---------------------------------------------------------------------------

APOLLO_MAPPINGS: dict[str, dict[str, Any]] = {
    "outbound_engineer": {
        "filename": "apollo-sequences",
        "data_key": "email_sequences",
        "columns": {
            "touch": "Step",
            "subject_a": "Subject Line",
            "body": "Body",
        },
    },
}


def _rows_to_csv(rows: list[dict], columns: list[str] | None = None) -> str:
    """Convert a list of dicts to CSV string."""
    if not rows:
        return ""
    output = io.StringIO()
    if columns:
        fieldnames = columns
    else:
        fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def _list_to_csv(items: list[str], column_name: str = "value") -> str:
    """Convert a simple list to single-column CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([column_name])
    for item in items:
        writer.writerow([item])
    return output.getvalue()


def generate_csv(agent_id: str, content: str) -> list[dict[str, str]]:
    """
    Generate CSV exports for an agent.
    Returns list of {filename, csv_content} dicts.
    """
    parsed = parse_agent_output(agent_id, content)
    data = parsed["data"]
    configs = AGENT_CSV_CONFIGS.get(agent_id, [])
    results = []

    for config in configs:
        raw = data.get(config["data_key"])
        if not raw:
            continue

        if config.get("is_list") and isinstance(raw, list):
            csv_content = _list_to_csv(raw, config["columns"][0])
        elif isinstance(raw, list) and raw and isinstance(raw[0], dict):
            csv_content = _rows_to_csv(raw, config.get("columns"))
        else:
            continue

        if csv_content:
            results.append({
                "filename": config["filename"],
                "content": csv_content,
            })

    return results


def generate_platform_csv(
    agent_id: str,
    content: str,
    platform: str,
) -> dict[str, str] | None:
    """
    Generate a platform-formatted CSV (HubSpot or Apollo).
    Returns {filename, csv_content} or None.
    """
    mappings = HUBSPOT_MAPPINGS if platform == "hubspot" else APOLLO_MAPPINGS
    mapping = mappings.get(agent_id)
    if not mapping:
        return None

    parsed = parse_agent_output(agent_id, content)
    data = parsed["data"]
    raw = data.get(mapping["data_key"])
    if not raw or not isinstance(raw, list):
        return None

    # Remap column names to platform-specific headers
    col_map = mapping["columns"]
    remapped_rows = []
    for row in raw:
        new_row = {}
        for src_key, dest_key in col_map.items():
            new_row[dest_key] = row.get(src_key, "")
        remapped_rows.append(new_row)

    csv_content = _rows_to_csv(remapped_rows)
    if not csv_content:
        return None

    return {
        "filename": mapping["filename"],
        "content": csv_content,
    }


class CSVConnector(BaseConnector):
    platform = "csv"
    supported_agents = list(AGENT_CSV_CONFIGS.keys())

    async def export(
        self,
        agent_id: str,
        parsed_data: dict[str, Any],
        credentials: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        content = parsed_data.get("raw", "")
        csvs = generate_csv(agent_id, content)
        return {
            "status": "success",
            "files": csvs,
            "count": len(csvs),
        }

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        return True  # CSV needs no credentials


# Auto-register
register_connector(CSVConnector())
