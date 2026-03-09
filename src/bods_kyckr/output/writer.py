"""Output writer for BODS statements.

Supports JSON (array of statements) and JSONL (one statement per line) formats.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BODSWriter:
    """Writes BODS statements to JSON or JSONL files."""

    def __init__(self, output_path: str | Path, output_format: str = "json"):
        self.output_path = Path(output_path)
        self.output_format = output_format.lower()
        self._statements: list[dict] = []
        self._count = 0
        self._file = None

        if self.output_format == "jsonl":
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(self.output_path, "w", encoding="utf-8")

    def write_statements(self, statements: list[dict]) -> None:
        """Write one or more statements to the output."""
        for stmt in statements:
            self._count += 1
            if self.output_format == "jsonl":
                self._file.write(json.dumps(stmt, ensure_ascii=False) + "\n")
            else:
                self._statements.append(stmt)

    def finalize(self) -> None:
        """Finalize the output (flush buffers, close files)."""
        if self.output_format == "jsonl":
            if self._file:
                self._file.close()
                self._file = None
        else:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(self._statements, f, indent=2, ensure_ascii=False)

        logger.info("Wrote %d statements to %s", self._count, self.output_path)
