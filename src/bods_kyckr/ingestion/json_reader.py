"""Read Kyckr UBO V2 API responses from saved JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterator

from bods_kyckr.ingestion.models import KyckrCaseHierarchy

logger = logging.getLogger(__name__)


def read_case_hierarchy(filepath: Path | str) -> KyckrCaseHierarchy:
    """Read a single get-case-hierarchy response from a JSON file."""
    filepath = Path(filepath)
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return KyckrCaseHierarchy.from_api_response(data)


def read_case_hierarchies(filepath: Path | str) -> Iterator[KyckrCaseHierarchy]:
    """Read case hierarchies from a JSON file.

    Supports:
    - A single hierarchy response (dict with "data" key)
    - An array of hierarchy responses
    - A JSONL file with one response per line
    """
    filepath = Path(filepath)

    if filepath.suffix == ".jsonl":
        with open(filepath, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield KyckrCaseHierarchy.from_api_response(data)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Skipping invalid JSON at line %d: %s", line_num, e)
    else:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                yield KyckrCaseHierarchy.from_api_response(item)
        else:
            yield KyckrCaseHierarchy.from_api_response(data)
