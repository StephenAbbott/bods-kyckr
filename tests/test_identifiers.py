"""Tests for identifier construction."""

from bods_kyckr.transform.identifiers import (
    build_company_identifier,
    company_record_id,
    company_record_id_from_entity_id,
    generate_statement_id,
    person_record_id,
    relationship_record_id,
)


class TestCompanyRecordId:
    def test_gb_company(self):
        assert company_record_id("GB", "02940032") == "kyckr-gb-02940032"

    def test_lowercase_jurisdiction(self):
        assert company_record_id("gb", "02940032") == "kyckr-gb-02940032"

    def test_missing_jurisdiction(self):
        assert company_record_id(None, "02940032") == "kyckr-02940032"

    def test_missing_registration(self):
        assert company_record_id("GB", None) == "kyckr-gb-unknown"

    def test_both_missing(self):
        assert company_record_id(None, None) == "kyckr-entity-unknown"


class TestCompanyRecordIdFromEntityId:
    def test_from_entity_id(self):
        result = company_record_id_from_entity_id("GB|MDI5NDAwMzI")
        assert result == "kyckr-entity-GB|MDI5NDAwMzI"


class TestPersonRecordId:
    def test_person_id(self):
        result = person_record_id("UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA")
        assert result == "kyckr-person-UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA"


class TestRelationshipRecordId:
    def test_relationship_id(self):
        result = relationship_record_id("kyckr-gb-02940032", "kyckr-gb-04162033")
        assert result == "kyckr-gb-02940032-rel-kyckr-gb-04162033"


class TestGenerateStatementId:
    def test_deterministic(self):
        """Same inputs should produce same output."""
        id1 = generate_statement_id("kyckr-gb-02940032", "2025-01-29", "new")
        id2 = generate_statement_id("kyckr-gb-02940032", "2025-01-29", "new")
        assert id1 == id2

    def test_different_inputs(self):
        """Different inputs should produce different output."""
        id1 = generate_statement_id("kyckr-gb-02940032", "2025-01-29", "new")
        id2 = generate_statement_id("kyckr-gb-04162033", "2025-01-29", "new")
        assert id1 != id2

    def test_valid_uuid(self):
        """Output should be a valid UUID string."""
        import uuid
        result = generate_statement_id("kyckr-gb-02940032", "2025-01-29", "new")
        parsed = uuid.UUID(result)
        assert str(parsed) == result


class TestBuildCompanyIdentifier:
    def test_gb_company(self):
        result = build_company_identifier("GB", "02940032")
        assert result == {
            "id": "02940032",
            "scheme": "GB-COH",
            "schemeName": "Companies House",
        }

    def test_de_company(self):
        result = build_company_identifier("DE", "HRB12345")
        assert result == {
            "id": "HRB12345",
            "scheme": "DE-CR",
            "schemeName": "Handelsregister",
        }

    def test_unknown_jurisdiction(self):
        result = build_company_identifier("ZZ", "12345")
        assert result == {
            "id": "12345",
            "schemeName": "Company register (ZZ)",
        }

    def test_no_registration_number(self):
        result = build_company_identifier("GB", None)
        assert result is None

    def test_case_insensitive(self):
        result = build_company_identifier("gb", "02940032")
        assert result["scheme"] == "GB-COH"
