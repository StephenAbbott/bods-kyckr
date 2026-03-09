"""Kyckr UBO Verify V2 API client.

Optional module for direct API access. Requires a valid API token.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import requests

from bods_kyckr.ingestion.models import KyckrCaseHierarchy

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.kyckr.com"


class KyckrAPIClient:
    """Client for the Kyckr UBO Verify V2 API.

    Usage:
        client = KyckrAPIClient(api_token="your-token")
        hierarchy = client.get_case_hierarchy(case_id="2965422")
    """

    def __init__(
        self,
        api_token: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        })

    def get_case_hierarchy(self, case_id: str) -> KyckrCaseHierarchy:
        """Fetch the ownership hierarchy for a case.

        Calls GET /ubo/v2/cases/{case_id}/hierarchy
        """
        url = f"{self.base_url}/ubo/v2/cases/{case_id}/hierarchy"
        logger.info("Fetching case hierarchy: %s", url)

        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        return KyckrCaseHierarchy.from_api_response(data)

    def list_cases(self) -> list[dict]:
        """List all UBO cases.

        Calls GET /ubo/v2/cases
        """
        url = f"{self.base_url}/ubo/v2/cases"
        logger.info("Listing cases: %s", url)

        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])
