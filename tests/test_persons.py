"""Tests for person statement transformation."""

from bods_kyckr.ingestion.models import KyckrIndividual
from bods_kyckr.transform.persons import _build_person_names, transform_individual


class TestBuildPersonNames:
    def test_full_name(self, sample_individual):
        result = _build_person_names(sample_individual)
        assert len(result) == 1
        assert result[0]["fullName"] == "MARK CONSTANTINE"
        assert result[0]["type"] == "individual"
        assert result[0]["givenName"] == "Mark"
        assert result[0]["familyName"] == "Constantine"

    def test_single_name(self):
        ind = KyckrIndividual(name="MADONNA", entity_id="test", layer=2)
        result = _build_person_names(ind)
        assert len(result) == 1
        assert result[0]["fullName"] == "MADONNA"
        assert result[0]["familyName"] == "Madonna"
        assert "givenName" not in result[0]

    def test_three_part_name(self):
        ind = KyckrIndividual(name="JOHN MICHAEL SMITH", entity_id="test", layer=2)
        result = _build_person_names(ind)
        assert result[0]["givenName"] == "John"
        assert result[0]["familyName"] == "Michael Smith"

    def test_empty_name(self):
        ind = KyckrIndividual(name="", entity_id="test", layer=2)
        result = _build_person_names(ind)
        assert result == []


class TestTransformIndividual:
    def test_full_individual(self, sample_individual, test_config):
        result = transform_individual(sample_individual, test_config)

        assert result["recordType"] == "person"
        assert result["recordId"] == "kyckr-person-UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA"
        assert result["recordStatus"] == "new"

        details = result["recordDetails"]
        assert details["isComponent"] is False
        assert details["personType"] == "knownPerson"
        assert len(details["names"]) == 1
        assert details["names"][0]["fullName"] == "MARK CONSTANTINE"

    def test_publication_details(self, sample_individual, test_config):
        result = transform_individual(sample_individual, test_config)
        assert result["publicationDetails"]["bodsVersion"] == "0.4"

    def test_source(self, sample_individual, test_config):
        result = transform_individual(sample_individual, test_config)
        assert "thirdParty" in result["source"]["type"]

    def test_deterministic_id(self, sample_individual, test_config):
        r1 = transform_individual(sample_individual, test_config)
        r2 = transform_individual(sample_individual, test_config)
        assert r1["statementId"] == r2["statementId"]

    def test_retrieved_at(self, sample_individual, test_config):
        result = transform_individual(
            sample_individual, test_config,
            retrieved_at="2025-01-27T10:22:58Z",
        )
        assert result["source"]["retrievedAt"] == "2025-01-27T10:22:58Z"
