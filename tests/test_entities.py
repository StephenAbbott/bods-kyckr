"""Tests for entity statement transformation."""

from bods_kyckr.transform.entities import (
    _build_addresses,
    get_company_record_id,
    transform_company,
)
from bods_kyckr.ingestion.models import KyckrAddress


class TestGetCompanyRecordId:
    def test_with_jurisdiction_and_registration(self, sample_company):
        result = get_company_record_id(sample_company)
        assert result == "kyckr-gb-02940032"

    def test_without_registration(self, sample_company_minimal):
        result = get_company_record_id(sample_company_minimal)
        assert result == "kyckr-entity-XX|dW5rbm93bg"


class TestBuildAddresses:
    def test_registered_address(self, sample_address):
        result = _build_addresses([sample_address])
        assert len(result) == 1
        assert result[0]["type"] == "registered"
        assert result[0]["address"] == "29 High Street, Poole, Dorset, BH15 1AB"
        assert result[0]["postCode"] == "BH15 1AB"
        assert result[0]["country"]["code"] == "GB"

    def test_minimal_address(self):
        addr = KyckrAddress(full_address="123 Main St")
        result = _build_addresses([addr])
        assert len(result) == 1
        assert result[0]["address"] == "123 Main St"
        assert "type" not in result[0]

    def test_empty_addresses(self):
        result = _build_addresses([])
        assert result == []


class TestTransformCompany:
    def test_full_company(self, sample_company, test_config):
        result = transform_company(sample_company, test_config)

        assert result["recordType"] == "entity"
        assert result["recordId"] == "kyckr-gb-02940032"
        assert result["recordStatus"] == "new"
        assert result["statementDate"] == "2025-01-29"

        details = result["recordDetails"]
        assert details["isComponent"] is False
        assert details["entityType"] == {"type": "registeredEntity"}
        assert details["name"] == "LUSH LTD."
        assert details["jurisdiction"]["code"] == "GB"

        # Check identifiers include both registration and Kyckr ID
        ids = details["identifiers"]
        schemes = [i.get("scheme") or i.get("schemeName") for i in ids]
        assert "GB-COH" in schemes
        assert "Kyckr" in schemes

        # Check address
        assert len(details["addresses"]) == 1
        assert details["addresses"][0]["postCode"] == "BH15 1AB"

    def test_publication_details(self, sample_company, test_config):
        result = transform_company(sample_company, test_config)
        pub = result["publicationDetails"]
        assert pub["bodsVersion"] == "0.4"
        assert pub["publisher"]["name"] == "Test Publisher"

    def test_source(self, sample_company, test_config):
        result = transform_company(sample_company, test_config)
        source = result["source"]
        assert "thirdParty" in source["type"]
        assert source["assertedBy"][0]["name"] == "Kyckr"

    def test_deterministic_statement_id(self, sample_company, test_config):
        r1 = transform_company(sample_company, test_config)
        r2 = transform_company(sample_company, test_config)
        assert r1["statementId"] == r2["statementId"]

    def test_minimal_company(self, sample_company_minimal, test_config):
        result = transform_company(sample_company_minimal, test_config)
        assert result["recordType"] == "entity"
        assert result["recordDetails"]["name"] == "Mystery Corp"
        # Should not have addresses or identifiers with schemes
        assert "addresses" not in result["recordDetails"] or result["recordDetails"]["addresses"] == []
