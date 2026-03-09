"""Tests for interest type mapping."""

from bods_kyckr.ingestion.models import KyckrAssociation, KyckrShareholdingSummary
from bods_kyckr.transform.interests import (
    build_share,
    map_association_interest,
    map_inferred_person_interest,
    map_relationship_type,
)


class TestMapRelationshipType:
    def test_shareholder(self):
        assert map_relationship_type("Shareholder") == "shareholding"

    def test_director(self):
        assert map_relationship_type("Director") == "appointmentOfBoard"

    def test_secretary(self):
        assert map_relationship_type("Secretary") == "seniorManagingOfficial"

    def test_beneficiary(self):
        assert map_relationship_type("Beneficiary") == "beneficiaryOfLegalArrangement"

    def test_trustee(self):
        assert map_relationship_type("Trustee") == "trustee"

    def test_unknown(self):
        assert map_relationship_type("SomeOtherType") == "otherInfluenceOrControl"

    def test_empty(self):
        assert map_relationship_type("") == "unknownInterest"

    def test_case_insensitive(self):
        assert map_relationship_type("SHAREHOLDER") == "shareholding"
        assert map_relationship_type("shareholder") == "shareholding"

    def test_substring_match(self):
        assert map_relationship_type("Major Shareholder") == "shareholding"


class TestBuildShare:
    def test_exact_percentage(self):
        assert build_share(100.0) == {"exact": 100.0}

    def test_fractional_percentage(self):
        assert build_share(34.29) == {"exact": 34.29}

    def test_none(self):
        assert build_share(None) is None

    def test_zero(self):
        assert build_share(0.0) == {"exact": 0.0}


class TestMapAssociationInterest:
    def test_shareholding_with_summary(self, sample_association):
        result = map_association_interest(sample_association)
        assert result["type"] == "shareholding"
        assert result["directOrIndirect"] == "direct"
        assert result["beneficialOwnershipOrControl"] is True
        assert result["share"] == {"exact": 100.0}

    def test_association_without_summary(self):
        assoc = KyckrAssociation(
            parent_entity_id="A",
            parent_entity_name="Parent",
            child_entity_id="B",
            child_entity_name="Child",
            relationship_type="Director",
        )
        result = map_association_interest(assoc)
        assert result["type"] == "appointmentOfBoard"
        assert result["beneficialOwnershipOrControl"] is False

    def test_shareholding_without_summary(self):
        assoc = KyckrAssociation(
            parent_entity_id="A",
            parent_entity_name="Parent",
            child_entity_id="B",
            child_entity_name="Child",
            relationship_type="Shareholder",
        )
        result = map_association_interest(assoc)
        assert result["type"] == "shareholding"
        assert result["beneficialOwnershipOrControl"] is True


class TestMapInferredPersonInterest:
    def test_ubo_with_percentage(self):
        result = map_inferred_person_interest(34.29, is_ubo=True)
        assert result["type"] == "shareholding"
        assert result["directOrIndirect"] == "direct"
        assert result["beneficialOwnershipOrControl"] is True
        assert result["share"] == {"exact": 34.29}

    def test_non_ubo(self):
        result = map_inferred_person_interest(10.0, is_ubo=False)
        assert result["beneficialOwnershipOrControl"] is False

    def test_no_percentage(self):
        result = map_inferred_person_interest(None, is_ubo=True)
        assert "share" not in result
