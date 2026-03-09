"""Tests for relationship statement transformation."""

from bods_kyckr.ingestion.models import (
    KyckrAssociation,
    KyckrCaseHierarchy,
    KyckrCompany,
    KyckrIndividual,
    KyckrShareholdingSummary,
    KyckrUBO,
)
from bods_kyckr.transform.relationships import (
    infer_person_relationships,
    transform_association,
    transform_inferred_person_relationship,
)


class TestTransformAssociation:
    def test_shareholding_association(self, sample_association, test_config):
        entity_map = {
            "GB|MDI5NDAwMzI": "kyckr-gb-02940032",
            "GB|MDQxNjIwMzM": "kyckr-gb-04162033",
        }
        result = transform_association(
            sample_association, entity_map, test_config
        )

        assert result is not None
        assert result["recordType"] == "relationship"
        assert result["recordStatus"] == "new"

        details = result["recordDetails"]
        assert details["isComponent"] is False
        assert details["subject"] == "kyckr-gb-02940032"  # LUSH LTD (parent)
        assert details["interestedParty"] == "kyckr-gb-04162033"  # LUSH COSMETICS (child/owner)

        interests = details["interests"]
        assert len(interests) == 1
        assert interests[0]["type"] == "shareholding"
        assert interests[0]["share"]["exact"] == 100.0

    def test_missing_entity_id(self, sample_association, test_config):
        """Should return None if entity IDs can't be resolved."""
        result = transform_association(sample_association, {}, test_config)
        assert result is None


class TestTransformInferredPersonRelationship:
    def test_inferred_relationship(self, sample_individual, test_config):
        result = transform_inferred_person_relationship(
            individual=sample_individual,
            parent_company_record_id="kyckr-gb-04162033",
            percentage=34.29,
            is_ubo=True,
            config=test_config,
        )

        assert result["recordType"] == "relationship"
        details = result["recordDetails"]
        assert details["subject"] == "kyckr-gb-04162033"
        assert details["interestedParty"] == "kyckr-person-UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA"
        assert details["interests"][0]["type"] == "shareholding"
        assert details["interests"][0]["beneficialOwnershipOrControl"] is True
        assert details["interests"][0]["share"]["exact"] == 34.29


class TestInferPersonRelationships:
    def test_infer_from_hierarchy(self, sample_hierarchy, test_config):
        entity_map = {
            "GB|MDI5NDAwMzI": "kyckr-gb-02940032",
            "GB|MDQxNjIwMzM": "kyckr-gb-04162033",
            "UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA": "kyckr-person-UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA",
        }
        result = infer_person_relationships(
            sample_hierarchy, entity_map, test_config
        )

        # Should infer one relationship: MARK CONSTANTINE -> LUSH COSMETICS
        assert len(result) == 1
        stmt = result[0]
        assert stmt["recordType"] == "relationship"
        details = stmt["recordDetails"]
        # Parent company should be at layer 2 (LUSH COSMETICS)
        assert details["subject"] == "kyckr-gb-04162033"
        assert details["interestedParty"] == "kyckr-person-UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA"

    def test_no_inference_when_explicit(self, test_config):
        """Should not infer if individual is already in associations."""
        hierarchy = KyckrCaseHierarchy(
            case_id="test",
            timestamp="2025-01-01T00:00:00Z",
            companies=[
                KyckrCompany(name="Parent", entity_id="C1", layer=1, jurisdiction="GB", registration_number="111"),
            ],
            individuals=[
                KyckrIndividual(name="Person", entity_id="P1", layer=2),
            ],
            associations=[
                KyckrAssociation(
                    parent_entity_id="C1",
                    parent_entity_name="Parent",
                    child_entity_id="P1",
                    child_entity_name="Person",
                    relationship_type="Shareholder",
                ),
            ],
            ubos=[],
        )
        entity_map = {"C1": "kyckr-gb-111", "P1": "kyckr-person-P1"}
        result = infer_person_relationships(hierarchy, entity_map, test_config)
        assert len(result) == 0

    def test_multi_layer_inference(self, test_config):
        """Should find parent at layer N-1."""
        hierarchy = KyckrCaseHierarchy(
            case_id="test",
            timestamp="2025-01-01T00:00:00Z",
            companies=[
                KyckrCompany(name="Root", entity_id="C1", layer=1, jurisdiction="GB", registration_number="001"),
                KyckrCompany(name="Middle", entity_id="C2", layer=2, jurisdiction="GB", registration_number="002"),
                KyckrCompany(name="Leaf", entity_id="C3", layer=3, jurisdiction="GB", registration_number="003"),
            ],
            individuals=[
                KyckrIndividual(name="Owner", entity_id="P1", layer=4, rollup_percentage=50.0),
            ],
            associations=[
                KyckrAssociation(
                    parent_entity_id="C1", parent_entity_name="Root",
                    child_entity_id="C2", child_entity_name="Middle",
                    relationship_type="Shareholder",
                ),
                KyckrAssociation(
                    parent_entity_id="C2", parent_entity_name="Middle",
                    child_entity_id="C3", child_entity_name="Leaf",
                    relationship_type="Shareholder",
                ),
            ],
            ubos=[KyckrUBO(id="P1", name="Owner", percentage=50.0)],
        )
        entity_map = {
            "C1": "kyckr-gb-001", "C2": "kyckr-gb-002",
            "C3": "kyckr-gb-003", "P1": "kyckr-person-P1",
        }
        result = infer_person_relationships(hierarchy, entity_map, test_config)

        assert len(result) == 1
        # Person at layer 4 should connect to company at layer 3
        assert result[0]["recordDetails"]["subject"] == "kyckr-gb-003"
