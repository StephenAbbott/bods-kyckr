"""Pipeline orchestrator for transforming Kyckr UBO data to BODS.

Ties together ingestion, transformation, and output into a coherent
workflow. Supports both JSON file input and (optionally) direct API access.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from bods_kyckr.config import PublisherConfig
from bods_kyckr.ingestion.json_reader import read_case_hierarchies, read_case_hierarchy
from bods_kyckr.ingestion.models import KyckrCaseHierarchy
from bods_kyckr.output.writer import BODSWriter
from bods_kyckr.transform.entities import get_company_record_id, transform_company
from bods_kyckr.transform.identifiers import person_record_id
from bods_kyckr.transform.persons import transform_individual
from bods_kyckr.transform.relationships import (
    infer_person_relationships,
    transform_association,
)

logger = logging.getLogger(__name__)


class BODSPipeline:
    """Orchestrates the transformation of Kyckr UBO data to BODS format.

    Manages entity deduplication, statement generation, and output writing.

    Usage:
        config = PublisherConfig(output_path="output.json")
        pipeline = BODSPipeline(config)
        pipeline.process_json_file("kyckr_response.json")
        pipeline.finalize()
    """

    def __init__(self, config: PublisherConfig):
        self.config = config
        self.writer = BODSWriter(config.output_path, config.output_format)
        self._emitted_record_ids: set[str] = set()

    @property
    def statement_count(self) -> int:
        """Number of statements written so far."""
        return self.writer._count

    def process_json_file(self, filepath: Path | str) -> int:
        """Process a JSON file containing one or more case hierarchy responses.

        Supports:
        - Single hierarchy response (dict with "data" key)
        - Array of hierarchy responses
        - JSONL with one response per line

        Returns the number of statements generated.
        """
        filepath = Path(filepath)
        logger.info("Processing JSON file: %s", filepath)

        total = 0
        for hierarchy in read_case_hierarchies(filepath):
            statements = self._process_hierarchy(hierarchy)
            self.writer.write_statements(statements)
            total += len(statements)
            logger.info(
                "Processed case %s: %d statements (%d total)",
                hierarchy.case_id,
                len(statements),
                total,
            )

        return total

    def process_hierarchy(self, hierarchy: KyckrCaseHierarchy) -> list[dict]:
        """Process a single case hierarchy and write statements.

        Returns the list of generated statements.
        """
        statements = self._process_hierarchy(hierarchy)
        self.writer.write_statements(statements)
        return statements

    def finalize(self) -> None:
        """Finalize the output (flush buffers, close files)."""
        self.writer.finalize()
        logger.info(
            "Pipeline complete: %d total statements, %d unique entities tracked",
            self.writer._count,
            len(self._emitted_record_ids),
        )

    def _process_hierarchy(self, hierarchy: KyckrCaseHierarchy) -> list[dict]:
        """Transform a case hierarchy into BODS statements.

        Processing order:
        1. Entity statements for all companies
        2. Person statements for all individuals
        3. Relationship statements from explicit associations
        4. Relationship statements from inferred person relationships
        """
        statements: list[dict] = []
        retrieved_at = hierarchy.timestamp

        # Build entity_id -> record_id mapping for relationship resolution
        entity_id_to_record_id: dict[str, str] = {}

        # 1. Entity statements
        for company in hierarchy.companies:
            rec_id = get_company_record_id(company)
            entity_id_to_record_id[company.entity_id] = rec_id

            if rec_id not in self._emitted_record_ids:
                stmt = transform_company(company, self.config, retrieved_at)
                statements.append(stmt)
                self._emitted_record_ids.add(rec_id)

        # 2. Person statements
        for individual in hierarchy.individuals:
            rec_id = person_record_id(individual.entity_id)
            entity_id_to_record_id[individual.entity_id] = rec_id

            if rec_id not in self._emitted_record_ids:
                stmt = transform_individual(individual, self.config, retrieved_at)
                statements.append(stmt)
                self._emitted_record_ids.add(rec_id)

        # 3. Explicit association relationships
        for association in hierarchy.associations:
            stmt = transform_association(
                association, entity_id_to_record_id, self.config, retrieved_at
            )
            if stmt:
                statements.append(stmt)

        # 4. Inferred person relationships
        inferred = infer_person_relationships(
            hierarchy, entity_id_to_record_id, self.config, retrieved_at
        )
        statements.extend(inferred)

        return statements
