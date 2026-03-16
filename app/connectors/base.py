"""
Cold Start AI — Base Connector & Registry
Abstract base for all export connectors.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("coldstart.connectors")


class BaseConnector:
    """Abstract base for export connectors."""

    platform: str = ""
    supported_agents: list[str] = []

    async def export(
        self,
        agent_id: str,
        parsed_data: dict[str, Any],
        credentials: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute the export. Returns status + details."""
        raise NotImplementedError

    def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Validate platform credentials. Returns True if valid."""
        raise NotImplementedError


# Connector registry — populated by imports
_CONNECTORS: dict[str, BaseConnector] = {}


def register_connector(connector: BaseConnector) -> None:
    _CONNECTORS[connector.platform] = connector


def get_connector(platform: str) -> BaseConnector | None:
    return _CONNECTORS.get(platform)


def list_connectors() -> list[str]:
    return list(_CONNECTORS.keys())
