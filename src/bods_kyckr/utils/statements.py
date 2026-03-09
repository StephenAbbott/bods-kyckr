"""Builders for BODS statement envelope fields.

These functions construct the shared metadata fields that appear on
every BODS statement: publicationDetails, source, and annotations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bods_kyckr.config import PublisherConfig


def build_publication_details(config: PublisherConfig) -> dict:
    """Build the publicationDetails object for a BODS statement."""
    details: dict = {
        "publicationDate": config.publication_date,
        "bodsVersion": "0.4",
        "publisher": {
            "name": config.publisher_name,
        },
    }
    if config.publisher_uri:
        details["publisher"]["url"] = config.publisher_uri
    if config.license_url:
        details["license"] = config.license_url
    return details


def build_source(
    config: PublisherConfig,
    retrieved_at: str | None = None,
    description: str | None = None,
) -> dict:
    """Build the source object for a BODS statement.

    Kyckr is a third-party aggregator of official register data.
    """
    source: dict = {
        "type": ["thirdParty"],
        "description": description or (
            "Kyckr UBO Verify - ownership data sourced from "
            "official company registers via Kyckr"
        ),
        "assertedBy": [
            {
                "name": "Kyckr",
                "uri": "https://www.kyckr.com",
            }
        ],
    }
    ts = retrieved_at or config.retrieved_at
    if ts:
        source["retrievedAt"] = ts
    return source


def clean_statement(statement: dict) -> dict:
    """Remove None values and empty collections from a BODS statement.

    BODS schema requires that optional fields are either present with valid
    values or absent entirely.
    """
    cleaned = {}
    for key, value in statement.items():
        if value is None:
            continue
        if isinstance(value, dict):
            nested = clean_statement(value)
            if nested:
                cleaned[key] = nested
        elif isinstance(value, list):
            cleaned_list = []
            for item in value:
                if isinstance(item, dict):
                    nested_item = clean_statement(item)
                    if nested_item:
                        cleaned_list.append(nested_item)
                elif item is not None:
                    cleaned_list.append(item)
            if cleaned_list:
                cleaned[key] = cleaned_list
        else:
            cleaned[key] = value
    return cleaned
