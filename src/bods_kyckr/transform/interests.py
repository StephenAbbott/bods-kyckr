"""Interest type mapping for BODS relationship statements.

Maps Kyckr relationship types and shareholding data to BODS
interest types from the interestType codelist.

See: https://standard.openownership.org/en/0.4.0/standard/reference.html
"""

from __future__ import annotations

import logging

from bods_kyckr.ingestion.models import KyckrAssociation, KyckrShareholdingSummary

logger = logging.getLogger(__name__)

# Mapping of Kyckr relationship types to BODS interest types
RELATIONSHIP_TYPE_MAP: dict[str, str] = {
    "shareholder": "shareholding",
    "director": "appointmentOfBoard",
    "secretary": "seniorManagingOfficial",
    "manager": "seniorManagingOfficial",
    "beneficiary": "beneficiaryOfLegalArrangement",
    "trustee": "trustee",
    "settlor": "settlor",
    "protector": "protector",
    "nominee": "nominee",
    "partner": "otherInfluenceOrControl",
    "member": "otherInfluenceOrControl",
    "officer": "seniorManagingOfficial",
    "authorized signatory": "otherInfluenceOrControl",
}


def map_relationship_type(relationship_type: str) -> str:
    """Map a Kyckr relationship type to a BODS interest type.

    Falls back to 'otherInfluenceOrControl' for unknown types.
    """
    if not relationship_type:
        return "unknownInterest"

    normalized = relationship_type.strip().lower()

    # Exact match
    if normalized in RELATIONSHIP_TYPE_MAP:
        return RELATIONSHIP_TYPE_MAP[normalized]

    # Substring match
    for known, bods_type in RELATIONSHIP_TYPE_MAP.items():
        if known in normalized:
            return bods_type

    logger.warning(
        "Unknown Kyckr relationship type '%s', defaulting to otherInfluenceOrControl",
        relationship_type,
    )
    return "otherInfluenceOrControl"


def build_share(percentage: float | None) -> dict | None:
    """Build a BODS share object from a percentage value."""
    if percentage is None:
        return None
    return {"exact": percentage}


def map_association_interest(association: KyckrAssociation) -> dict:
    """Map a Kyckr association to a BODS interest object."""
    interest_type = map_relationship_type(association.relationship_type)

    interest: dict = {
        "type": interest_type,
        "directOrIndirect": "direct",
    }

    summary = association.shareholding_summary
    if summary:
        interest["beneficialOwnershipOrControl"] = summary.is_beneficially_held

        share = build_share(summary.percentage)
        if share:
            interest["share"] = share
    else:
        # Default: assume beneficial if it's a shareholding
        interest["beneficialOwnershipOrControl"] = (
            interest_type in {"shareholding", "votingRights"}
        )

    return interest


def map_inferred_person_interest(
    percentage: float | None,
    is_ubo: bool = False,
) -> dict:
    """Build a BODS interest for an inferred person-to-company relationship.

    Used when person relationships are not explicit in the associations
    array and must be inferred from the hierarchy structure.
    """
    interest: dict = {
        "type": "shareholding",
        "directOrIndirect": "direct",
        "beneficialOwnershipOrControl": is_ubo,
    }

    share = build_share(percentage)
    if share:
        interest["share"] = share

    return interest
