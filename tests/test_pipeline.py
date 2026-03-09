"""Tests for the pipeline orchestrator."""

import json
from pathlib import Path

from bods_kyckr.config import PublisherConfig
from bods_kyckr.ingestion.models import (
    KyckrAssociation,
    KyckrCaseHierarchy,
    KyckrCompany,
    KyckrIndividual,
    KyckrShareholdingSummary,
    KyckrUBO,
)
from bods_kyckr.pipeline import BODSPipeline


class TestPipelineFromHierarchy:
    def test_lush_example(self, sample_hierarchy, test_config, tmp_path):
        """Test the full LUSH LTD. example produces expected statements."""
        output_file = tmp_path / "output.json"
        test_config.output_path = str(output_file)

        pipeline = BODSPipeline(test_config)
        statements = pipeline.process_hierarchy(sample_hierarchy)
        pipeline.finalize()

        # Should produce: 2 entities + 1 person + 1 explicit relationship + 1 inferred relationship
        assert len(statements) == 5

        entities = [s for s in statements if s["recordType"] == "entity"]
        persons = [s for s in statements if s["recordType"] == "person"]
        relationships = [s for s in statements if s["recordType"] == "relationship"]

        assert len(entities) == 2
        assert len(persons) == 1
        assert len(relationships) == 2

        # Verify entity names
        entity_names = {e["recordDetails"]["name"] for e in entities}
        assert "LUSH LTD." in entity_names
        assert "LUSH COSMETICS LIMITED" in entity_names

        # Verify person
        assert persons[0]["recordDetails"]["names"][0]["fullName"] == "MARK CONSTANTINE"

        # Verify explicit relationship (LUSH COSMETICS -> LUSH LTD.)
        explicit_rel = [
            r for r in relationships
            if r["recordDetails"]["subject"] == "kyckr-gb-02940032"
            and r["recordDetails"]["interestedParty"] == "kyckr-gb-04162033"
        ]
        assert len(explicit_rel) == 1
        assert explicit_rel[0]["recordDetails"]["interests"][0]["share"]["exact"] == 100.0

        # Verify inferred relationship (MARK CONSTANTINE -> LUSH COSMETICS)
        inferred_rel = [
            r for r in relationships
            if "kyckr-person-" in r["recordDetails"]["interestedParty"]
        ]
        assert len(inferred_rel) == 1
        assert inferred_rel[0]["recordDetails"]["interests"][0]["beneficialOwnershipOrControl"] is True

    def test_all_statements_have_bods_version(self, sample_hierarchy, test_config, tmp_path):
        test_config.output_path = str(tmp_path / "output.json")
        pipeline = BODSPipeline(test_config)
        statements = pipeline.process_hierarchy(sample_hierarchy)
        pipeline.finalize()

        for stmt in statements:
            assert stmt["publicationDetails"]["bodsVersion"] == "0.4"

    def test_all_statements_have_record_id(self, sample_hierarchy, test_config, tmp_path):
        test_config.output_path = str(tmp_path / "output.json")
        pipeline = BODSPipeline(test_config)
        statements = pipeline.process_hierarchy(sample_hierarchy)
        pipeline.finalize()

        for stmt in statements:
            assert "recordId" in stmt
            assert len(stmt["recordId"]) > 0


class TestPipelineDeduplication:
    def test_entity_deduplication(self, test_config, tmp_path):
        """Processing two hierarchies with a shared company should not duplicate it."""
        test_config.output_path = str(tmp_path / "output.json")
        pipeline = BODSPipeline(test_config)

        h1 = KyckrCaseHierarchy(
            case_id="1",
            timestamp="2025-01-01T00:00:00Z",
            companies=[
                KyckrCompany(name="Shared Co", entity_id="S1", layer=1,
                             jurisdiction="GB", registration_number="111"),
                KyckrCompany(name="Child A", entity_id="A1", layer=2,
                             jurisdiction="GB", registration_number="222"),
            ],
            individuals=[],
            associations=[
                KyckrAssociation(
                    parent_entity_id="S1", parent_entity_name="Shared Co",
                    child_entity_id="A1", child_entity_name="Child A",
                    relationship_type="Shareholder",
                    shareholding_summary=KyckrShareholdingSummary(percentage=100.0),
                ),
            ],
            ubos=[],
        )
        h2 = KyckrCaseHierarchy(
            case_id="2",
            timestamp="2025-01-01T00:00:00Z",
            companies=[
                KyckrCompany(name="Shared Co", entity_id="S1", layer=1,
                             jurisdiction="GB", registration_number="111"),
                KyckrCompany(name="Child B", entity_id="B1", layer=2,
                             jurisdiction="GB", registration_number="333"),
            ],
            individuals=[],
            associations=[
                KyckrAssociation(
                    parent_entity_id="S1", parent_entity_name="Shared Co",
                    child_entity_id="B1", child_entity_name="Child B",
                    relationship_type="Shareholder",
                    shareholding_summary=KyckrShareholdingSummary(percentage=50.0),
                ),
            ],
            ubos=[],
        )

        s1 = pipeline.process_hierarchy(h1)
        s2 = pipeline.process_hierarchy(h2)
        pipeline.finalize()

        # h1: 2 entities + 1 relationship = 3
        # h2: 1 entity (Child B, Shared Co deduplicated) + 1 relationship = 2
        assert len(s1) == 3
        assert len(s2) == 2

        all_entities = [
            s for s in s1 + s2 if s["recordType"] == "entity"
        ]
        entity_ids = {e["recordId"] for e in all_entities}
        assert len(entity_ids) == 3  # Shared Co + Child A + Child B


class TestPipelineJsonFile:
    def test_json_file_input(self, sample_api_response, test_config, tmp_path):
        """Test processing from a saved JSON file."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"

        with open(input_file, "w") as f:
            json.dump(sample_api_response, f)

        test_config.output_path = str(output_file)
        pipeline = BODSPipeline(test_config)
        total = pipeline.process_json_file(input_file)
        pipeline.finalize()

        assert total == 5  # 2 entities + 1 person + 2 relationships

        with open(output_file) as f:
            statements = json.load(f)
        assert len(statements) == 5

    def test_jsonl_output(self, sample_api_response, test_config, tmp_path):
        """Test JSONL output format."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.jsonl"

        with open(input_file, "w") as f:
            json.dump(sample_api_response, f)

        test_config.output_path = str(output_file)
        test_config.output_format = "jsonl"
        pipeline = BODSPipeline(test_config)
        pipeline.process_json_file(input_file)
        pipeline.finalize()

        with open(output_file) as f:
            lines = f.readlines()
        assert len(lines) == 5

        # Each line should be valid JSON
        for line in lines:
            stmt = json.loads(line)
            assert "recordType" in stmt
