"""Transform Kyckr associations into BODS relationship statements.

Handles both explicit company-to-company associations from the API
response and inferred person-to-company relationships derived from
the ownership hierarchy layers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bods_kyckr.ingestion.models import (
    KyckrAssociation,
    KyckrCaseHierarchy,
    KyckrCompany,
    KyckrIndividual,
)
from bods_kyckr.transform.entities import get_company_record_id
from bods_kyckr.transform.identifiers import (
    generate_statement_id,
    person_record_id,
    relationship_record_id,
)
from bods_kyckr.transform.interests import (
    map_association_interest,
    map_inferred_person_interest,
)
from bods_kyckr.utils.statements import (
    build_publication_details,
    build_source,
    clean_statement,
)

if TYPE_CHECKING:
    from bods_kyckr.config import PublisherConfig

logger = logging.getLogger(__name__)


def transform_association(
    association: KyckrAssociation,
    entity_id_to_record_id: dict[str, str],
    config: PublisherConfig,
    retrieved_at: str | None = None,
) -> dict | None:
    """Transform a Kyckr association into a BODS relationship statement.

    In Kyckr's model:
    - parentEntityId = the company being owned (BODS subject)
    - childEntityId = the entity that owns/controls (BODS interestedParty)
    """
    subject_rec_id = entity_id_to_record_id.get(association.parent_entity_id)
    interested_party_rec_id = entity_id_to_record_id.get(association.child_entity_id)

    if not subject_rec_id or not interested_party_rec_id:
        logger.warning(
            "Could not resolve entity IDs for association: %s -> %s",
            association.parent_entity_name,
            association.child_entity_name,
        )
        return None

    rel_rec_id = relationship_record_id(subject_rec_id, interested_party_rec_id)

    statement = {
        "statementId": generate_statement_id(
            rel_rec_id, config.publication_date, "new"
        ),
        "declarationSubject": subject_rec_id,
        "statementDate": config.publication_date,
        "recordId": rel_rec_id,
        "recordType": "relationship",
        "recordStatus": "new",
        "recordDetails": {
            "isComponent": False,
            "subject": subject_rec_id,
            "interestedParty": interested_party_rec_id,
            "interests": [map_association_interest(association)],
        },
        "publicationDetails": build_publication_details(config),
        "source": build_source(config, retrieved_at=retrieved_at),
    }

    return clean_statement(statement)


def transform_inferred_person_relationship(
    individual: KyckrIndividual,
    parent_company_record_id: str,
    percentage: float | None,
    is_ubo: bool,
    config: PublisherConfig,
    retrieved_at: str | None = None,
) -> dict:
    """Transform an inferred person-to-company relationship into a BODS relationship.

    Used when person relationships are not explicit in the associations
    array and must be inferred from the hierarchy structure.
    """
    person_rec_id = person_record_id(individual.entity_id)
    rel_rec_id = relationship_record_id(parent_company_record_id, person_rec_id)

    statement = {
        "statementId": generate_statement_id(
            rel_rec_id, config.publication_date, "new"
        ),
        "declarationSubject": parent_company_record_id,
        "statementDate": config.publication_date,
        "recordId": rel_rec_id,
        "recordType": "relationship",
        "recordStatus": "new",
        "recordDetails": {
            "isComponent": False,
            "subject": parent_company_record_id,
            "interestedParty": person_rec_id,
            "interests": [map_inferred_person_interest(percentage, is_ubo)],
        },
        "publicationDetails": build_publication_details(config),
        "source": build_source(config, retrieved_at=retrieved_at),
    }

    return clean_statement(statement)


def infer_person_relationships(
    hierarchy: KyckrCaseHierarchy,
    entity_id_to_record_id: dict[str, str],
    config: PublisherConfig,
    retrieved_at: str | None = None,
) -> list[dict]:
    """Infer person-to-company relationships from the hierarchy structure.

    Strategy:
    1. Build a set of entity IDs already covered by explicit associations
    2. For each individual not in an explicit association:
       a. Find companies at layer N-1 (the individual is at layer N)
       b. If multiple companies exist at N-1, use the association data
          to narrow down which company is the parent
       c. Look up the UBO percentage if available
    3. Create relationship statements for each inferred connection
    """
    # Entity IDs already in explicit associations (as children)
    explicit_child_ids = {a.child_entity_id for a in hierarchy.associations}

    # UBO lookup by entity ID
    ubo_lookup = {u.id: u for u in hierarchy.ubos}

    # Company lookup by entity ID
    company_by_entity_id = {c.entity_id: c for c in hierarchy.companies}

    # Build layer-to-companies mapping
    layer_companies: dict[int, list[KyckrCompany]] = {}
    for company in hierarchy.companies:
        layer_companies.setdefault(company.layer, []).append(company)

    # Build parent lookup from associations: child_entity_id -> parent_entity_id
    child_to_parent: dict[str, str] = {}
    for assoc in hierarchy.associations:
        child_to_parent[assoc.child_entity_id] = assoc.parent_entity_id

    statements: list[dict] = []

    for individual in hierarchy.individuals:
        # Skip if already in explicit associations
        if individual.entity_id in explicit_child_ids:
            continue

        # Find the parent company
        parent_company = _find_parent_company(
            individual,
            layer_companies,
            child_to_parent,
            company_by_entity_id,
        )

        if not parent_company:
            logger.warning(
                "Could not infer parent company for individual '%s' at layer %d",
                individual.name,
                individual.layer,
            )
            continue

        parent_rec_id = entity_id_to_record_id.get(parent_company.entity_id)
        if not parent_rec_id:
            logger.warning(
                "No record ID found for parent company '%s'",
                parent_company.name,
            )
            continue

        # Check if this person is a UBO
        ubo = ubo_lookup.get(individual.entity_id)
        is_ubo = ubo is not None

        # Use the individual's rollup percentage as the direct percentage
        # since this is their direct holding in the parent company
        percentage = individual.rollup_percentage

        stmt = transform_inferred_person_relationship(
            individual=individual,
            parent_company_record_id=parent_rec_id,
            percentage=percentage,
            is_ubo=is_ubo,
            config=config,
            retrieved_at=retrieved_at,
        )
        statements.append(stmt)

    return statements


def _find_parent_company(
    individual: KyckrIndividual,
    layer_companies: dict[int, list[KyckrCompany]],
    child_to_parent: dict[str, str],
    company_by_entity_id: dict[str, KyckrCompany],
) -> KyckrCompany | None:
    """Find the parent company for an individual in the hierarchy.

    Strategy:
    1. Look at companies at layer N-1 (one level up from the individual)
    2. If exactly one company at that layer, use it
    3. If multiple companies, check which ones appear as children in
       associations (meaning they're owned by someone else) and identify
       the one most likely to be the individual's parent
    4. Walk up layers if no match at N-1
    """
    target_layer = individual.layer - 1

    # Try each layer from target_layer up to layer 1
    for layer in range(target_layer, 0, -1):
        candidates = layer_companies.get(layer, [])

        if len(candidates) == 1:
            return candidates[0]

        if len(candidates) > 1:
            # Prefer companies that are themselves children in associations
            # (they're part of the ownership chain)
            child_companies = [
                c for c in candidates if c.entity_id in child_to_parent
            ]
            if len(child_companies) == 1:
                return child_companies[0]

            # If still ambiguous, return the first candidate
            if candidates:
                return candidates[0]

    return None
