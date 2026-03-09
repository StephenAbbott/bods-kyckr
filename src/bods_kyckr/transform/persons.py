"""Transform Kyckr individual data into BODS person statements."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bods_kyckr.ingestion.models import KyckrIndividual
from bods_kyckr.transform.identifiers import (
    generate_statement_id,
    person_record_id,
)
from bods_kyckr.utils.statements import (
    build_publication_details,
    build_source,
    clean_statement,
)

if TYPE_CHECKING:
    from bods_kyckr.config import PublisherConfig

logger = logging.getLogger(__name__)


def transform_individual(
    individual: KyckrIndividual,
    config: PublisherConfig,
    retrieved_at: str | None = None,
) -> dict:
    """Transform a Kyckr individual into a BODS person statement.

    Kyckr individuals are sparse — typically only name is available.
    No date of birth, nationality, or address data is provided.
    """
    rec_id = person_record_id(individual.entity_id)

    statement = {
        "statementId": generate_statement_id(rec_id, config.publication_date, "new"),
        "declarationSubject": rec_id,
        "statementDate": config.publication_date,
        "recordId": rec_id,
        "recordType": "person",
        "recordStatus": "new",
        "recordDetails": {
            "isComponent": False,
            "personType": "knownPerson",
            "names": _build_person_names(individual),
        },
        "publicationDetails": build_publication_details(config),
        "source": build_source(config, retrieved_at=retrieved_at),
    }

    return clean_statement(statement)


def _build_person_names(individual: KyckrIndividual) -> list[dict]:
    """Build BODS name objects from a Kyckr individual.

    Kyckr provides only a full name string (e.g., "MARK CONSTANTINE").
    We attempt to split into given/family name components.
    """
    if not individual.name or not individual.name.strip():
        return []

    name: dict = {
        "type": "individual",
        "fullName": individual.name.strip(),
    }

    # Attempt to split the name into components
    parts = individual.name.strip().split()
    if len(parts) >= 2:
        name["givenName"] = parts[0].title()
        name["familyName"] = " ".join(parts[1:]).title()
    elif len(parts) == 1:
        name["familyName"] = parts[0].title()

    return [name]
