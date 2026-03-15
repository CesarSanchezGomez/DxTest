"""Mapeo de codigos de pais ISO 3166-1 alpha-3 al formato de fecha primario esperado.

El validador intenta PRIMERO el formato del pais, luego acepta ISO (YYYY-MM-DD)
como formato universal de respaldo.
"""

from __future__ import annotations

from typing import Optional

# Constantes de formato: (strptime, label)
_DD_MM_YYYY = ("%d/%m/%Y", "DD/MM/YYYY")
_MM_DD_YYYY = ("%m/%d/%Y", "MM/DD/YYYY")
_ISO = ("%Y-%m-%d", "YYYY-MM-DD")
_DD_MM_YYYY_DASH = ("%d-%m-%Y", "DD-MM-YYYY")

# Regex compartido
_SLASH_PATTERN = r"^\d{1,2}/\d{1,2}/\d{4}$"
_ISO_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
_DASH_PATTERN = r"^\d{1,2}-\d{1,2}-\d{4}$"

# Mapeo pais → (strptime, label, regex)
COUNTRY_DATE_FORMAT: dict[str, tuple[str, str, str]] = {
    # America del Norte
    "USA": (*_MM_DD_YYYY, _SLASH_PATTERN),
    "CAN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    # America Latina
    "MEX": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "ARG": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "BRA": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "COL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "CHL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "PER": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "VEN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "ECU": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "BOL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "PRY": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "URY": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "PAN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "CRI": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "GTM": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "HND": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "SLV": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "NIC": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "DOM": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "PRI": (*_DD_MM_YYYY, _SLASH_PATTERN),
    # Europa
    "GBR": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "DEU": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "FRA": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "ESP": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "ITA": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "PRT": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "NLD": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "BEL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "CHE": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "AUT": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "POL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "SWE": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "NOR": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "DNK": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "FIN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "ROU": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "HUN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "CZE": (*_DD_MM_YYYY, _SLASH_PATTERN),
    # Asia-Pacifico (ISO)
    "JPN": (*_ISO, _ISO_PATTERN),
    "CHN": (*_ISO, _ISO_PATTERN),
    "KOR": (*_ISO, _ISO_PATTERN),
    "TWN": (*_ISO, _ISO_PATTERN),
    # Asia-Pacifico (DD/MM)
    "SGP": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "AUS": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "NZL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "IND": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "MYS": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "PHL": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "THA": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "IDN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "VNM": (*_DD_MM_YYYY, _SLASH_PATTERN),
    # Medio Oriente
    "SAU": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "ARE": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "QAT": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "KWT": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "BHR": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "OMN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    # Africa
    "ZAF": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "NGA": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "KEN": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "EGY": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "GHA": (*_DD_MM_YYYY, _SLASH_PATTERN),
    "MAR": (*_DD_MM_YYYY, _SLASH_PATTERN),
}

# Orden de intentos cuando no hay pais conocido
_FALLBACK_PATTERNS: list[tuple[str, str]] = [
    (_SLASH_PATTERN, _DD_MM_YYYY[0]),
    (_ISO_PATTERN, _ISO[0]),
    (_DASH_PATTERN, _DD_MM_YYYY_DASH[0]),
]


def resolve_date_formats(
    country_codes: list[str],
) -> tuple[Optional[str], list[tuple[str, str]]]:
    """Dado un listado de codigos de pais, devuelve (expected_label, [(regex, strptime_fmt), ...])."""
    if not country_codes:
        return None, _FALLBACK_PATTERNS

    primaries: list[tuple[str, str, str]] = []
    for code in country_codes:
        fmt = COUNTRY_DATE_FORMAT.get(code.upper())
        if fmt:
            primaries.append(fmt)

    if not primaries:
        return None, _FALLBACK_PATTERNS

    unique_strf = {p[0] for p in primaries}
    if len(unique_strf) > 1:
        return None, _FALLBACK_PATTERNS

    primary_strf, primary_label, primary_regex = primaries[0]
    patterns: list[tuple[str, str]] = [(primary_regex, primary_strf)]

    if primary_strf != _ISO[0]:
        patterns.append((_ISO_PATTERN, _ISO[0]))

    patterns.append((_DASH_PATTERN, _DD_MM_YYYY_DASH[0]))

    return primary_label, patterns
