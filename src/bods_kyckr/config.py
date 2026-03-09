"""Pipeline configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from bods_kyckr.utils.dates import current_date_iso


@dataclass
class PublisherConfig:
    """Configuration for BODS statement publication metadata."""

    publisher_name: str = "Kyckr UBO Verify"
    publisher_uri: str | None = "https://www.kyckr.com"
    publication_date: str = ""
    license_url: str | None = None
    retrieved_at: str | None = None
    output_path: str = "output.json"
    output_format: str = "json"  # "json" or "jsonl"
    api_token: str | None = None
    api_base_url: str = "https://api.kyckr.com"

    def __post_init__(self):
        if not self.publication_date:
            self.publication_date = current_date_iso()
