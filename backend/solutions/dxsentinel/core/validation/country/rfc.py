"""Validacion de RFC (Registro Federal de Contribuyentes) → ERROR.

Estructura RFC:
  Persona fisica (13 chars): 4 letras + 6 digitos (AAMMDD) + 3 alfanum (homoclave)
  Persona moral (12 chars):  3 letras + 6 digitos (AAMMDD) + 3 alfanum (homoclave)
"""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

# RFC persona fisica: 4 letras (incluye &, Ñ) + 6 digitos + 3 alfanum
_RFC_FISICA = re.compile(r"^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$", re.IGNORECASE)

# RFC persona moral: 3 letras + 6 digitos + 3 alfanum
_RFC_MORAL = re.compile(r"^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$", re.IGNORECASE)

# Tablas para digito verificador RFC
_RFC_CHAR_VALUES: dict[str, int] = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "A": 10, "B": 11, "C": 12, "D": 13, "E": 14,
    "F": 15, "G": 16, "H": 17, "I": 18, "J": 19, "K": 20, "L": 21,
    "M": 22, "N": 23, "&": 24, "O": 25, "P": 26, "Q": 27, "R": 28,
    "S": 29, "T": 30, "U": 31, "V": 32, "W": 33, "X": 34, "Y": 35,
    "Z": 36, " ": 37, "Ñ": 38,
}


def _verify_rfc_check_digit(rfc: str) -> bool:
    """Verifica el digito verificador del RFC."""
    rfc = rfc.upper().strip()
    # Pad a 13 si es persona moral (12 chars → agregar espacio al inicio)
    if len(rfc) == 12:
        rfc = " " + rfc

    if len(rfc) != 13:
        return False

    total = 0
    for i in range(12):
        char = rfc[i]
        value = _RFC_CHAR_VALUES.get(char, 0)
        total += value * (13 - i)

    remainder = total % 11
    if remainder == 0:
        expected = "0"
    elif remainder == 1:
        expected = "A"  # algunos usan 10 → A
    else:
        expected = str(11 - remainder)

    return rfc[12] == expected


def validate_rfc(rfc: str) -> tuple[bool, str | None]:
    """Valida un RFC completo."""
    if not rfc:
        return False, "RFC vacio"

    rfc = rfc.strip().upper()

    if len(rfc) == 13:
        if not _RFC_FISICA.match(rfc):
            return False, "Formato invalido para RFC persona fisica"
    elif len(rfc) == 12:
        if not _RFC_MORAL.match(rfc):
            return False, "Formato invalido para RFC persona moral"
    else:
        return False, f"Longitud {len(rfc)}, esperada 12 o 13"

    # Verificar fecha
    yy = int(rfc[-9:-7]) if len(rfc) == 13 else int(rfc[-9:-7])
    mm = int(rfc[-7:-5]) if len(rfc) == 13 else int(rfc[-7:-5])
    dd = int(rfc[-5:-3]) if len(rfc) == 13 else int(rfc[-5:-3])

    if mm < 1 or mm > 12:
        return False, f"Mes invalido: {mm:02d}"
    if dd < 1 or dd > 31:
        return False, f"Dia invalido: {dd:02d}"

    if not _verify_rfc_check_digit(rfc):
        return False, "Digito verificador incorrecto"

    return True, None


@register_validator
class RFCValidator(BaseValidator):
    """Valida formato RFC en datos CSV (ERROR)."""

    modes = ("split",)

    _RFC_CARD_TYPES = {"RFC", "RX"}

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        # Buscar en nationalIdCard o workPermitInfo
        nid_col = None
        card_type_col = None
        country_col = None

        for prefix in ("nationalIdCard", "workPermitInfo"):
            for h in ctx.csv_headers:
                if h == f"{prefix}_national-id" or h == f"{prefix}_document-number":
                    nid_col = h
                if h == f"{prefix}_card-type" or h == f"{prefix}_document-type":
                    card_type_col = h
                if h == f"{prefix}_country":
                    country_col = h
            if nid_col:
                break

        if not nid_col:
            return issues

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            nid_val = row.get(nid_col, "")
            country_val = row.get(country_col, "") if country_col else ""
            card_type_val = row.get(card_type_col, "") if card_type_col else ""

            if not nid_val:
                continue

            nid_values = [v.strip() for v in nid_val.split("|")]
            countries = [v.strip() for v in country_val.split("|")] if country_val else [""]
            card_types = [v.strip() for v in card_type_val.split("|")] if card_type_val else [""]

            for i, nid in enumerate(nid_values):
                country = countries[i] if i < len(countries) else countries[-1] if countries else ""
                card_type = card_types[i] if i < len(card_types) else card_types[-1] if card_types else ""

                if country.upper().strip() not in ("MEX", "MX", "MEXICO"):
                    continue

                # Detectar si es RFC por card_type
                ct_upper = card_type.upper().strip()
                is_rfc_type = any(rfc_t in ct_upper for rfc_t in self._RFC_CARD_TYPES)
                # Tambien detectar por el label/description del card_type
                is_rfc_desc = "RFC" in ct_upper or "Registro Federal" in card_type

                if not is_rfc_type and not is_rfc_desc:
                    continue

                valid, reason = validate_rfc(nid)
                if not valid:
                    issues.append(self._emit(
                        Severity.ERROR,
                        "RFC_001",
                        element_id="nationalIdCard",
                        field_id=nid_col,
                        country_code="MX",
                        row=row_idx,
                        value=nid[:20],
                        reason=reason,
                    ))

        return issues
