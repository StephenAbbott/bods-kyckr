"""Shared test fixtures for the Kyckr BODS pipeline."""

from __future__ import annotations

import json

import pytest

from bods_kyckr.config import PublisherConfig
from bods_kyckr.ingestion.models import (
    KyckrAddress,
    KyckrAssociation,
    KyckrCaseHierarchy,
    KyckrCompany,
    KyckrIndividual,
    KyckrShareholdingSummary,
    KyckrUBO,
)


@pytest.fixture
def test_config() -> PublisherConfig:
    """A standardised test configuration."""
    return PublisherConfig(
        publisher_name="Test Publisher",
        publisher_uri="https://test.example.com",
        publication_date="2025-01-29",
        output_path="test_output.json",
        output_format="json",
    )


@pytest.fixture
def sample_address() -> KyckrAddress:
    """A fully populated UK address."""
    return KyckrAddress(
        type="Registered",
        full_address="29 High Street, Poole, Dorset, BH15 1AB",
        building_name="29 High Street",
        street_name="Poole",
        city="Dorset",
        postcode="BH15 1AB",
        country="United Kingdom",
    )


@pytest.fixture
def sample_company(sample_address) -> KyckrCompany:
    """A fully populated UK company (LUSH LTD.)."""
    return KyckrCompany(
        name="LUSH LTD.",
        entity_id="GB|MDI5NDAwMzI",
        layer=1,
        type="Company",
        registration_number="02940032",
        jurisdiction="GB",
        kyckr_id="GB|MDI5NDAwMzI",
        rollup_percentage=100.0,
        status="COMPLETE",
        addresses=[sample_address],
    )


@pytest.fixture
def sample_company_subsidiary() -> KyckrCompany:
    """A subsidiary company (LUSH COSMETICS LIMITED)."""
    return KyckrCompany(
        name="LUSH COSMETICS LIMITED",
        entity_id="GB|MDQxNjIwMzM",
        layer=2,
        type="Company",
        registration_number="04162033",
        jurisdiction="GB",
        kyckr_id="GB|MDQxNjIwMzM",
        rollup_percentage=100.0,
        status="COMPLETE",
    )


@pytest.fixture
def sample_company_minimal() -> KyckrCompany:
    """A minimal company with no address or registration info."""
    return KyckrCompany(
        name="Mystery Corp",
        entity_id="XX|dW5rbm93bg",
        layer=2,
        type="Company",
    )


@pytest.fixture
def sample_individual() -> KyckrIndividual:
    """A natural person (MARK CONSTANTINE)."""
    return KyckrIndividual(
        name="MARK CONSTANTINE",
        entity_id="UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA",
        layer=3,
        type="Person",
        rollup_percentage=34.29,
    )


@pytest.fixture
def sample_association() -> KyckrAssociation:
    """A shareholding association (LUSH COSMETICS LIMITED -> LUSH LTD.)."""
    return KyckrAssociation(
        parent_entity_id="GB|MDI5NDAwMzI",
        parent_entity_name="LUSH LTD.",
        child_entity_id="GB|MDQxNjIwMzM",
        child_entity_name="LUSH COSMETICS LIMITED",
        relationship_type="Shareholder",
        shareholding_summary=KyckrShareholdingSummary(
            percentage=100.0,
            is_jointly_held=False,
            is_beneficially_held=True,
        ),
    )


@pytest.fixture
def sample_ubo() -> KyckrUBO:
    """A UBO (MARK CONSTANTINE)."""
    return KyckrUBO(
        id="UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA",
        name="MARK CONSTANTINE",
        percentage=34.29,
        type="Person",
    )


@pytest.fixture
def sample_hierarchy(
    sample_company,
    sample_company_subsidiary,
    sample_individual,
    sample_association,
    sample_ubo,
) -> KyckrCaseHierarchy:
    """A complete case hierarchy (LUSH LTD. example)."""
    return KyckrCaseHierarchy(
        case_id="2965422",
        timestamp="2025-01-27T10:22:58.1852216Z",
        companies=[sample_company, sample_company_subsidiary],
        individuals=[sample_individual],
        associations=[sample_association],
        ubos=[sample_ubo],
        stop_reason="COMPLETED",
    )


@pytest.fixture
def sample_api_response() -> dict:
    """The raw API response dict (LUSH LTD. example)."""
    return {
        "correlationId": "90b271d92b084f0bad3730e828a63d39",
        "customerReference": "",
        "cost": {"type": "credit", "value": 6},
        "timeStamp": "2025-01-29T00:15:22.5450819Z",
        "details": "Success",
        "links": {"hierarchy": "/ubo/v2/cases/2965422/hierarchy"},
        "data": {
            "id": "2945d173485e441bbca16bc1a2d20116",
            "caseId": "2965422",
            "timestamp": "2025-01-27T10:22:58.1852216Z",
            "algorithmState": {
                "nextNodes": [],
                "stopReason": "COMPLETED",
                "creditsUsed": 6,
            },
            "rootCompany": {
                "kyckrId": "GB|MDI5NDAwMzI",
                "legalEntityName": "LUSH LTD.",
                "registrationNumber": "02940032",
                "countryOfRegistration": "GB",
                "addresses": [
                    {
                        "type": "Registered",
                        "fullAddress": "29 High Street, Poole, Dorset, BH15 1AB",
                        "buildingName": "29 High Street",
                        "streetName": "Poole",
                        "city": "Dorset",
                        "postcode": "BH15 1AB",
                        "country": "United Kingdom",
                    }
                ],
            },
            "associatedEntities": {
                "companies": [
                    {
                        "name": "LUSH LTD.",
                        "rollupPercentage": 100,
                        "entityId": "GB|MDI5NDAwMzI",
                        "layer": 1,
                        "type": "Company",
                        "status": "COMPLETE",
                        "registrationNumber": "02940032",
                        "jurisdiction": "GB",
                        "kyckrId": "GB|MDI5NDAwMzI",
                        "addresses": [
                            {
                                "fullAddress": "29 High Street, Poole, Dorset, BH15 1AB"
                            }
                        ],
                    },
                    {
                        "name": "LUSH COSMETICS LIMITED",
                        "rollupPercentage": 100,
                        "entityId": "GB|MDQxNjIwMzM",
                        "layer": 2,
                        "type": "Company",
                        "status": "COMPLETE",
                        "registrationNumber": "04162033",
                        "jurisdiction": "GB",
                        "kyckrId": "GB|MDQxNjIwMzM",
                    },
                ],
                "individuals": [
                    {
                        "name": "MARK CONSTANTINE",
                        "rollupPercentage": 34.29,
                        "entityId": "UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA",
                        "layer": 3,
                        "type": "Person",
                    }
                ],
            },
            "associations": [
                {
                    "parentEntityId": "GB|MDI5NDAwMzI",
                    "parentEntityName": "LUSH LTD.",
                    "childEntityId": "GB|MDQxNjIwMzM",
                    "childEntityName": "LUSH COSMETICS LIMITED",
                    "relationshipType": "Shareholder",
                    "shareholdingSummary": {
                        "percentage": 100,
                        "isJointlyHeld": False,
                        "isBeneficiallyHeld": True,
                    },
                    "shareholdings": [
                        {"percentage": 100, "isJointlyHeld": False}
                    ],
                }
            ],
            "ultimateBeneficialOwners": [
                {
                    "id": "UGVyc29ufE1BUksgQ09OU1RBTlRJTkV8fA",
                    "name": "MARK CONSTANTINE",
                    "percentage": 34.29,
                    "type": "Person",
                }
            ],
            "reports": [],
        },
    }
