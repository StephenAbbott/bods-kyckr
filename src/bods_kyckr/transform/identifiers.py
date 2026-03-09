"""Identifier construction for BODS statements.

Builds deterministic record IDs, statement IDs, and company identifiers
following org-id.guide scheme codes.
"""

from __future__ import annotations

import uuid

# Fixed UUID v5 namespace for deterministic statement ID generation.
BODS_KYCKR_NAMESPACE = uuid.UUID("b8c3d1a2-9f4e-5a6b-7c8d-3e2f1a4b5c6d")


def company_record_id(jurisdiction: str | None, registration_number: str | None) -> str:
    """Build a record ID for a company entity.

    Pattern: kyckr-{jurisdiction_lower}-{registration_number}
    Fallback: kyckr-entity-unknown if both are missing.
    """
    jur = (jurisdiction or "").strip().lower()
    num = (registration_number or "").strip()

    if jur and num:
        return f"kyckr-{jur}-{num}"
    if num:
        return f"kyckr-{num}"
    if jur:
        return f"kyckr-{jur}-unknown"
    return "kyckr-entity-unknown"


def company_record_id_from_entity_id(entity_id: str) -> str:
    """Build a record ID from a Kyckr entity ID when no registration info available.

    Used as fallback when jurisdiction/registration number are not present.
    Pattern: kyckr-entity-{entity_id}
    """
    return f"kyckr-entity-{entity_id}"


def person_record_id(entity_id: str) -> str:
    """Build a record ID for a person.

    Pattern: kyckr-person-{entity_id}
    """
    return f"kyckr-person-{entity_id}"


def relationship_record_id(subject_record_id: str, interested_party_record_id: str) -> str:
    """Build a record ID for a relationship.

    Pattern: {subject_record_id}-rel-{interested_party_record_id}
    """
    return f"{subject_record_id}-rel-{interested_party_record_id}"


def generate_statement_id(
    record_id: str,
    statement_date: str,
    record_status: str = "new",
) -> str:
    """Generate a deterministic statement ID using UUID v5.

    Identical inputs always produce identical outputs, ensuring
    reproducibility across pipeline runs.
    """
    name = f"{record_id}:{statement_date}:{record_status}"
    return str(uuid.uuid5(BODS_KYCKR_NAMESPACE, name))


# Mapping of Kyckr jurisdiction codes (ISO 3166-1 alpha-2) to
# org-id.guide scheme codes and names.
JURISDICTION_SCHEMES: dict[str, tuple[str, str]] = {
    # Europe
    "gb": ("GB-COH", "Companies House"),
    "ie": ("IE-CRO", "Companies Registration Office"),
    "de": ("DE-CR", "Handelsregister"),
    "fr": ("FR-RCS", "Registre du Commerce et des Societes"),
    "nl": ("NL-KVK", "Kamer van Koophandel"),
    "be": ("BE-BCE_KBO", "Banque-Carrefour des Entreprises"),
    "lu": ("LU-RCS", "Registre de Commerce et des Societes"),
    "at": ("AT-FB", "Firmenbuch"),
    "ch": ("CH-FDJP", "Commercial Registry"),
    "it": ("IT-RI", "Registro Imprese"),
    "es": ("ES-RMC", "Registro Mercantil Central"),
    "pt": ("PT-RNPC", "Registo Nacional de Pessoas Colectivas"),
    "dk": ("DK-CVR", "Det Centrale Virksomhedsregister"),
    "se": ("SE-BLV", "Bolagsverket"),
    "no": ("NO-BRC", "Bronnoysundregistrene"),
    "fi": ("FI-PRO", "Patentti- ja rekisterihallitus"),
    "pl": ("PL-KRS", "Krajowy Rejestr Sadowy"),
    "cz": ("CZ-ICO", "Czech Statistical Office"),
    "sk": ("SK-ORSR", "Obchodny register"),
    "hu": ("HU-CRN", "Cegjegyzekszam"),
    "ro": ("RO-CUI", "Registrul Comertului"),
    "bg": ("BG-EIK", "BULSTAT Register"),
    "hr": ("HR-MBS", "Croatian Court Register"),
    "si": ("SI-PRS", "Poslovni register Slovenije"),
    "ee": ("EE-RIK", "Centre of Registers and Information Systems"),
    "lv": ("LV-RE", "Register of Enterprises"),
    "lt": ("LT-RC", "Juridinių asmenų registras"),
    "cy": ("CY-DRCOR", "Department of Registrar of Companies"),
    "mt": ("MT-MBR", "Malta Business Registry"),
    "gr": ("GR-GEMI", "General Electronic Commercial Registry"),
    "li": ("LI-FLR", "Financial Market Authority"),
    "is": ("IS-RSK", "Rikisskattstjori"),
    # Americas
    "us": ("US-EIN", "Internal Revenue Service"),
    "ca": ("CA-BN-CRA", "Canada Revenue Agency"),
    "mx": ("MX-RFC", "Registro Federal de Contribuyentes"),
    "br": ("BR-CNPJ", "Cadastro Nacional de Pessoa Juridica"),
    "ar": ("AR-CUIT", "Administracion Federal de Ingresos Publicos"),
    "co": ("CO-RUE", "Registro Unico Empresarial"),
    "cl": ("CL-RUT", "Servicio de Impuestos Internos"),
    "pe": ("PE-RUC", "Registro Unico de Contribuyentes"),
    # Asia-Pacific
    "au": ("AU-ABN", "Australian Business Number"),
    "nz": ("NZ-NZBN", "New Zealand Business Number"),
    "sg": ("SG-ACRA", "Accounting and Corporate Regulatory Authority"),
    "hk": ("HK-CR", "Companies Registry"),
    "jp": ("JP-JCN", "National Tax Agency"),
    "kr": ("KR-CRN", "Korean Corporate Registration Number"),
    "in": ("IN-MCA", "Ministry of Corporate Affairs"),
    "my": ("MY-SSM", "Suruhanjaya Syarikat Malaysia"),
    "th": ("TH-DBD", "Department of Business Development"),
    "ph": ("PH-SEC", "Securities and Exchange Commission"),
    "id": ("ID-AHU", "Ministry of Law and Human Rights"),
    "cn": ("CN-SAIC", "State Administration for Industry and Commerce"),
    "tw": ("TW-MOEA", "Ministry of Economic Affairs"),
    # Middle East & Africa
    "ae": ("AE-DED", "Department of Economic Development"),
    "sa": ("SA-MC", "Ministry of Commerce"),
    "za": ("ZA-CIPC", "Companies and Intellectual Property Commission"),
    "ng": ("NG-CAC", "Corporate Affairs Commission"),
    "ke": ("KE-RCO", "Registrar of Companies"),
    "mu": ("MU-CR", "Corporate and Business Registration Department"),
    # Offshore/Caribbean
    "ky": ("KY-CR", "Cayman Islands General Registry"),
    "bm": ("BM-ROC", "Registrar of Companies"),
    "vg": ("VG-FSC", "BVI Financial Services Commission"),
    "je": ("JE-JFSC", "Jersey Financial Services Commission"),
    "gg": ("GG-GFSC", "Guernsey Financial Services Commission"),
    "im": ("IM-CR", "Isle of Man Companies Registry"),
    "gi": ("GI-FSC", "Gibraltar Companies House"),
    "pa": ("PA-RPP", "Registro Publico de Panama"),
    "bz": ("BZ-ICS", "International Corporate Services"),
    "sc": ("SC-FSA", "Seychelles Financial Services Authority"),
}


def build_company_identifier(
    jurisdiction: str | None,
    registration_number: str | None,
) -> dict | None:
    """Build a BODS identifier object for a company.

    Returns None if no registration number is available.
    """
    if not registration_number:
        return None

    jur = (jurisdiction or "").strip().lower()
    identifier: dict = {"id": registration_number.strip()}

    if jur in JURISDICTION_SCHEMES:
        scheme_code, scheme_name = JURISDICTION_SCHEMES[jur]
        identifier["scheme"] = scheme_code
        identifier["schemeName"] = scheme_name
    elif jur:
        # Use jurisdiction as a generic scheme indicator
        identifier["schemeName"] = f"Company register ({jur.upper()})"

    return identifier
