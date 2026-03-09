"""BODS schema compliance tests.

Uses lib-cove-bods to validate output against the official BODS v0.4 JSON schema.
Tests are skipped if lib-cove-bods is not installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bods_kyckr.config import PublisherConfig
from bods_kyckr.pipeline import BODSPipeline

try:
    from libcovebods.config import LibCoveBODS
    from libcovebods.jsonschemavalidate import JSONSchemaValidator
    from libcovebods.schema import SchemaBODS
    from libcovebods.data_reader import DataReader

    HAS_LIBCOVEBODS = True
except ImportError:
    HAS_LIBCOVEBODS = False

skip_without_libcovebods = pytest.mark.skipif(
    not HAS_LIBCOVEBODS,
    reason="lib-cove-bods not installed",
)


@skip_without_libcovebods
class TestBODSSchemaCompliance:
    """Validate generated BODS statements against the official schema."""

    def _validate_file(self, json_file: Path) -> list:
        """Validate a JSON file against the BODS schema."""
        data_reader = DataReader(str(json_file))
        schema = SchemaBODS(data_reader)
        validator = JSONSchemaValidator(schema)
        return validator.validate(data_reader)

    def test_full_pipeline_compliance(
        self, sample_api_response, tmp_path
    ):
        """Full pipeline output should pass BODS schema validation."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"

        with open(input_file, "w") as f:
            json.dump(sample_api_response, f)

        config = PublisherConfig(
            publisher_name="Test Publisher",
            output_path=str(output_file),
            output_format="json",
            publication_date="2025-01-29",
        )

        pipeline = BODSPipeline(config)
        pipeline.process_json_file(input_file)
        pipeline.finalize()

        errors = self._validate_file(output_file)
        assert len(errors) == 0, f"BODS validation errors: {errors}"

    def test_entity_statement_compliance(
        self, sample_company, tmp_path
    ):
        """A single entity statement should pass validation."""
        from bods_kyckr.transform.entities import transform_company

        config = PublisherConfig(
            publisher_name="Test Publisher",
            publication_date="2025-01-29",
            output_path=str(tmp_path / "output.json"),
        )

        stmt = transform_company(sample_company, config)
        output_file = tmp_path / "output.json"
        with open(output_file, "w") as f:
            json.dump([stmt], f)

        errors = self._validate_file(output_file)
        assert len(errors) == 0, f"BODS validation errors: {errors}"

    def test_person_statement_compliance(
        self, sample_individual, tmp_path
    ):
        """A single person statement should pass validation."""
        from bods_kyckr.transform.persons import transform_individual

        config = PublisherConfig(
            publisher_name="Test Publisher",
            publication_date="2025-01-29",
            output_path=str(tmp_path / "output.json"),
        )

        stmt = transform_individual(sample_individual, config)
        output_file = tmp_path / "output.json"
        with open(output_file, "w") as f:
            json.dump([stmt], f)

        errors = self._validate_file(output_file)
        assert len(errors) == 0, f"BODS validation errors: {errors}"
