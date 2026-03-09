"""Dataclass models for Kyckr UBO Verify V2 API responses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KyckrAddress:
    """An address from the Kyckr API."""

    type: str | None = None
    full_address: str | None = None
    building_name: str | None = None
    street_name: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None

    @classmethod
    def from_api_dict(cls, data: dict) -> KyckrAddress:
        return cls(
            type=data.get("type"),
            full_address=data.get("fullAddress"),
            building_name=data.get("buildingName"),
            street_name=data.get("streetName"),
            city=data.get("city"),
            postcode=data.get("postcode"),
            country=data.get("country"),
        )


@dataclass
class KyckrCompany:
    """A company entity from the Kyckr ownership hierarchy."""

    name: str
    entity_id: str
    layer: int
    type: str = "Company"
    registration_number: str | None = None
    jurisdiction: str | None = None
    kyckr_id: str | None = None
    rollup_percentage: float | None = None
    status: str | None = None
    addresses: list[KyckrAddress] = field(default_factory=list)

    @classmethod
    def from_api_dict(cls, data: dict) -> KyckrCompany:
        addresses = [
            KyckrAddress.from_api_dict(a) for a in (data.get("addresses") or [])
        ]
        return cls(
            name=data.get("name", ""),
            entity_id=data.get("entityId", ""),
            layer=data.get("layer", 0),
            type=data.get("type", "Company"),
            registration_number=data.get("registrationNumber"),
            jurisdiction=data.get("jurisdiction"),
            kyckr_id=data.get("kyckrId"),
            rollup_percentage=data.get("rollupPercentage"),
            status=data.get("status"),
            addresses=addresses,
        )

    @classmethod
    def from_root_company(cls, data: dict) -> KyckrCompany:
        """Create from the rootCompany object which has different field names."""
        addresses = [
            KyckrAddress.from_api_dict(a) for a in (data.get("addresses") or [])
        ]
        return cls(
            name=data.get("legalEntityName", ""),
            entity_id=data.get("kyckrId", ""),
            layer=0,
            type="Company",
            registration_number=data.get("registrationNumber"),
            jurisdiction=data.get("countryOfRegistration"),
            kyckr_id=data.get("kyckrId"),
            rollup_percentage=100.0,
            status=None,
            addresses=addresses,
        )


@dataclass
class KyckrIndividual:
    """A natural person from the Kyckr ownership hierarchy."""

    name: str
    entity_id: str
    layer: int
    type: str = "Person"
    rollup_percentage: float | None = None

    @classmethod
    def from_api_dict(cls, data: dict) -> KyckrIndividual:
        return cls(
            name=data.get("name", ""),
            entity_id=data.get("entityId", ""),
            layer=data.get("layer", 0),
            type=data.get("type", "Person"),
            rollup_percentage=data.get("rollupPercentage"),
        )


@dataclass
class KyckrShareholdingSummary:
    """Summary of a shareholding relationship."""

    percentage: float | None = None
    is_jointly_held: bool = False
    is_beneficially_held: bool = False

    @classmethod
    def from_api_dict(cls, data: dict | None) -> KyckrShareholdingSummary | None:
        if not data:
            return None
        return cls(
            percentage=data.get("percentage"),
            is_jointly_held=data.get("isJointlyHeld", False),
            is_beneficially_held=data.get("isBeneficiallyHeld", False),
        )


@dataclass
class KyckrAssociation:
    """An ownership association between two entities."""

    parent_entity_id: str
    parent_entity_name: str
    child_entity_id: str
    child_entity_name: str
    relationship_type: str
    shareholding_summary: KyckrShareholdingSummary | None = None

    @classmethod
    def from_api_dict(cls, data: dict) -> KyckrAssociation:
        summary = KyckrShareholdingSummary.from_api_dict(
            data.get("shareholdingSummary")
        )
        return cls(
            parent_entity_id=data.get("parentEntityId", ""),
            parent_entity_name=data.get("parentEntityName", ""),
            child_entity_id=data.get("childEntityId", ""),
            child_entity_name=data.get("childEntityName", ""),
            relationship_type=data.get("relationshipType", ""),
            shareholding_summary=summary,
        )


@dataclass
class KyckrUBO:
    """An ultimate beneficial owner identified by Kyckr."""

    id: str
    name: str
    percentage: float | None = None
    type: str = "Person"

    @classmethod
    def from_api_dict(cls, data: dict) -> KyckrUBO:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            percentage=data.get("percentage"),
            type=data.get("type", "Person"),
        )


@dataclass
class KyckrCaseHierarchy:
    """A complete case hierarchy response from Kyckr UBO V2 API."""

    case_id: str
    timestamp: str
    companies: list[KyckrCompany] = field(default_factory=list)
    individuals: list[KyckrIndividual] = field(default_factory=list)
    associations: list[KyckrAssociation] = field(default_factory=list)
    ubos: list[KyckrUBO] = field(default_factory=list)
    stop_reason: str | None = None

    @classmethod
    def from_api_response(cls, response: dict) -> KyckrCaseHierarchy:
        """Parse a full get-case-hierarchy API response."""
        data = response.get("data", response)

        associated = data.get("associatedEntities", {})
        companies = [
            KyckrCompany.from_api_dict(c)
            for c in (associated.get("companies") or [])
        ]
        individuals = [
            KyckrIndividual.from_api_dict(i)
            for i in (associated.get("individuals") or [])
        ]
        associations = [
            KyckrAssociation.from_api_dict(a)
            for a in (data.get("associations") or [])
        ]
        ubos = [
            KyckrUBO.from_api_dict(u)
            for u in (data.get("ultimateBeneficialOwners") or [])
        ]

        # Merge rootCompany info into companies if not already present
        root = data.get("rootCompany")
        if root:
            root_id = root.get("kyckrId", "")
            existing_ids = {c.entity_id for c in companies}
            if root_id and root_id not in existing_ids:
                companies.insert(0, KyckrCompany.from_root_company(root))
            else:
                # Enrich existing company with rootCompany address data
                for c in companies:
                    if c.entity_id == root_id and not c.addresses and root.get("addresses"):
                        c.addresses = [
                            KyckrAddress.from_api_dict(a)
                            for a in root["addresses"]
                        ]

        algo = data.get("algorithmState", {})

        return cls(
            case_id=data.get("caseId", ""),
            timestamp=data.get("timestamp", ""),
            companies=companies,
            individuals=individuals,
            associations=associations,
            ubos=ubos,
            stop_reason=algo.get("stopReason"),
        )
