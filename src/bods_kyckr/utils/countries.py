"""Country and jurisdiction code resolution using pycountry."""

from __future__ import annotations

import logging

import pycountry

logger = logging.getLogger(__name__)

# Common abbreviations not handled by pycountry
COUNTRY_ABBREVIATIONS: dict[str, str] = {
    "uk": "GB",
    "usa": "US",
    "uae": "AE",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "great britain": "GB",
    "korea": "KR",
    "south korea": "KR",
    "north korea": "KP",
    "russia": "RU",
    "iran": "IR",
    "syria": "SY",
    "venezuela": "VE",
    "bolivia": "BO",
    "tanzania": "TZ",
    "vietnam": "VN",
    "laos": "LA",
    "brunei": "BN",
    "ivory coast": "CI",
    "czech republic": "CZ",
    "taiwan": "TW",
    "hong kong": "HK",
    "macau": "MO",
    "palestine": "PS",
    "vatican": "VA",
    "vatican city": "VA",
    "kosovo": "XK",
    "curacao": "CW",
    "sint maarten": "SX",
    "bonaire": "BQ",
}


def resolve_jurisdiction(jurisdiction_code: str | None) -> dict | None:
    """Convert a Kyckr jurisdiction code to a BODS jurisdiction object.

    'GB' -> {"code": "GB", "name": "United Kingdom"}
    'US' -> {"code": "US", "name": "United States"}
    """
    if not jurisdiction_code:
        return None

    code = jurisdiction_code.strip().upper()

    # Direct alpha-2 lookup
    country = pycountry.countries.get(alpha_2=code)
    if country:
        return {"code": code, "name": country.name}

    # Try as alpha-3
    if len(code) == 3:
        country = pycountry.countries.get(alpha_3=code)
        if country:
            return {"code": country.alpha_2, "name": country.name}

    # Check abbreviations
    lower = code.lower()
    if lower in COUNTRY_ABBREVIATIONS:
        alpha2 = COUNTRY_ABBREVIATIONS[lower]
        country = pycountry.countries.get(alpha_2=alpha2)
        if country:
            return {"code": alpha2, "name": country.name}

    # Fuzzy match
    try:
        results = pycountry.countries.search_fuzzy(code)
        if results:
            return {"code": results[0].alpha_2, "name": results[0].name}
    except LookupError:
        pass

    logger.warning("Could not resolve jurisdiction code: %s", jurisdiction_code)
    return None


def resolve_country(country_text: str | None) -> dict | None:
    """Resolve a free-text country name to a BODS country object.

    "United Kingdom" -> {"code": "GB", "name": "United Kingdom"}
    "GB" -> {"code": "GB", "name": "United Kingdom"}
    """
    if not country_text or not country_text.strip():
        return None

    text = country_text.strip()

    # Try as ISO code first
    if len(text) == 2:
        country = pycountry.countries.get(alpha_2=text.upper())
        if country:
            return {"code": country.alpha_2, "name": country.name}

    if len(text) == 3:
        country = pycountry.countries.get(alpha_3=text.upper())
        if country:
            return {"code": country.alpha_2, "name": country.name}

    # Check abbreviations
    lower = text.lower()
    if lower in COUNTRY_ABBREVIATIONS:
        alpha2 = COUNTRY_ABBREVIATIONS[lower]
        country = pycountry.countries.get(alpha_2=alpha2)
        if country:
            return {"code": alpha2, "name": country.name}

    # Try exact name match
    country = pycountry.countries.get(name=text)
    if country:
        return {"code": country.alpha_2, "name": country.name}

    # Fuzzy match
    try:
        results = pycountry.countries.search_fuzzy(text)
        if results:
            return {"code": results[0].alpha_2, "name": results[0].name}
    except LookupError:
        pass

    logger.warning("Could not resolve country: %s", country_text)
    return None


def jurisdiction_to_country_code(jurisdiction_code: str | None) -> str | None:
    """Extract the ISO alpha-2 country code from a jurisdiction code.

    'GB' -> 'GB', 'gb' -> 'GB'
    """
    if not jurisdiction_code:
        return None
    return jurisdiction_code.strip().upper()
