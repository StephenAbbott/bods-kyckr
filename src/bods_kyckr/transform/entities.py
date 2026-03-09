"""Transform Kyckr company data into BODS entity statements."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bods_kyckr.ingestion.models import KyckrAddress, KyckrCompany
from bods_kyckr.transform.identifiers import (
    build_company_identifier,
    company_record_id,
    company_record_id_from_entity_id,
    generate_statement_id,
)
from bods_kyckr.utils.countries import resolve_country, resolve_jurisdiction
from bods_kyckr.utils.statements import (
    build_publication_details,
    build_source,
    clean_statement,
)

if TYPE_CHECKING:
    from bods_kyckr.config import PublisherConfig

logger = logging.getLogger(__name__)

# Mapping of Kyckr address types to BODS address types
ADDRESS_TYPE_MAP: dict[str, str] = {
    "registered": "registered",
    "business": "business",
    "service": "service",
    "correspondence": "service",
    "trading": "business",
    "principal": "business",
    "head office": "business",
}


def get_company_record_id(company: KyckrCompany) -> str:
    """Get the record ID for a company, using registration info if available."""
    if company.jurisdiction and company.registration_number:
        return company_record_id(company.jurisdiction, company.registration_number)
    return company_record_id_from_entity_id(company.entity_id)


def transform_company(
    company: KyckrCompany,
    config: PublisherConfig,
    retrieved_at: str | None = None,
) -> dict:
    """Transform a Kyckr company into a BODS entity statement."""
    rec_id = get_company_record_id(company)

    statement = {
        "statementId": generate_statement_id(rec_id, config.publication_date, "new"),
        "declarationSubject": rec_id,
        "statementDate": config.publication_date,
        "recordId": rec_id,
        "recordType": "entity",
        "recordStatus": "new",
        "recordDetails": {
            "isComponent": False,
            "entityType": {"type": "registeredEntity"},
            "name": company.name,
            "jurisdiction": resolve_jurisdiction(company.jurisdiction),
            "identifiers": _build_identifiers(company),
            "addresses": _build_addresses(company.addresses),
        },
        "publicationDetails": build_publication_details(config),
        "source": build_source(config, retrieved_at=retrieved_at),
    }

    return clean_statement(statement)


def _build_identifiers(company: KyckrCompany) -> list[dict]:
    """Build identifier objects for a company."""
    identifiers = []

    # Primary registration identifier
    primary = build_company_identifier(
        company.jurisdiction, company.registration_number
    )
    if primary:
        identifiers.append(primary)

    # Kyckr ID as supplementary identifier
    if company.kyckr_id:
        identifiers.append({
            "id": company.kyckr_id,
            "schemeName": "Kyckr",
        })

    return identifiers


def _build_addresses(addresses: list[KyckrAddress]) -> list[dict]:
    """Build BODS address objects from Kyckr addresses."""
    result = []
    for addr in addresses:
        bods_addr: dict = {}

        # Map address type
        if addr.type:
            addr_type_lower = addr.type.strip().lower()
            bods_addr["type"] = ADDRESS_TYPE_MAP.get(addr_type_lower, "registered")

        # Address string
        if addr.full_address:
            bods_addr["address"] = addr.full_address

        # Postcode
        if addr.postcode:
            bods_addr["postCode"] = addr.postcode

        # Country
        if addr.country:
            country = resolve_country(addr.country)
            if country:
                bods_addr["country"] = country

        if bods_addr:
            result.append(bods_addr)

    return result
