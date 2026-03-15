"""Validacion completa de CURP (Clave Unica de Registro de Poblacion) → ERROR.

Estructura CURP (18 caracteres):
  Pos 1-4:   Primera letra apellido paterno + primera vocal interna apellido
             paterno + primera letra apellido materno + primera letra nombre
  Pos 5-10:  Fecha de nacimiento AAMMDD
  Pos 11:    Sexo (H=hombre, M=mujer)
  Pos 12-13: Entidad federativa (codigo de 2 letras)
  Pos 14-16: Primera consonante interna apellido paterno + primera consonante
             interna apellido materno + primera consonante interna nombre
  Pos 17:    Digito diferenciador homonimia (0-9 o A-Z)
  Pos 18:    Digito verificador (0-9)
"""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

# Patron basico: 4 letras + 6 digitos + H/M + 2 letras + 3 consonantes + alfanum + digito
_CURP_PATTERN = re.compile(
    r"^[A-Z]{4}\d{6}[HM][A-Z]{2}[BCDFGHJKLMNPQRSTVWXYZ]{3}[A-Z0-9]\d$"
)

# Entidades federativas validas
_VALID_STATES: set[str] = {
    "AS",  # Aguascalientes
    "BC",  # Baja California
    "BS",  # Baja California Sur
    "CC",  # Campeche
    "CL",  # Coahuila
    "CM",  # Colima
    "CS",  # Chiapas
    "CH",  # Chihuahua
    "DF",  # Ciudad de Mexico (Distrito Federal)
    "DG",  # Durango
    "GT",  # Guanajuato
    "GR",  # Guerrero
    "HG",  # Hidalgo
    "JC",  # Jalisco
    "MC",  # Estado de Mexico
    "MN",  # Michoacan
    "MS",  # Morelos
    "NT",  # Nayarit
    "NL",  # Nuevo Leon
    "OC",  # Oaxaca
    "PL",  # Puebla
    "QT",  # Queretaro
    "QR",  # Quintana Roo
    "SP",  # San Luis Potosi
    "SL",  # Sinaloa
    "SR",  # Sonora
    "TC",  # Tabasco
    "TS",  # Tamaulipas
    "TL",  # Tlaxcala
    "VZ",  # Veracruz
    "YN",  # Yucatan
    "ZS",  # Zacatecas
    "NE",  # Nacido en el extranjero
}

# Palabras inconvenientes que el SAT/RENAPO sustituyen
_INCONVENIENT_WORDS: set[str] = {
    "BACA", "BAKA", "BUEI", "BUEY", "CACA", "CACO", "CAGA", "CAGO",
    "CAKA", "CAKO", "COGE", "COGI", "COJA", "COJE", "COJI", "COJO",
    "COLA", "CULO", "FALO", "FETO", "GETA", "GUEI", "GUEY", "JETA",
    "JOTO", "KACA", "KACO", "KAGA", "KAGO", "KAKA", "KAKO", "KOGE",
    "KOGI", "KOJA", "KOJE", "KOJI", "KOJO", "KOLA", "KULO", "LELO",
    "LOCA", "LOCO", "LOKA", "LOKO", "MAME", "MAMO", "MEAR", "MEAS",
    "MEON", "MIAR", "MION", "MOCO", "MOKO", "MULA", "MULO", "NACA",
    "NACO", "PEDA", "PEDO", "PENE", "PIPI", "PITO", "POPO", "PUTA",
    "PUTO", "QULO", "RATA", "ROBA", "ROBE", "ROBO", "RUIN", "SENO",
    "TETA", "VACA", "VAGA", "VAGO", "VAKA", "VUEI", "VUEY", "WUEI",
    "WUEY",
}


def _char_value(c: str) -> int:
    """Valor numerico de un caracter para el calculo del digito verificador."""
    if c.isdigit():
        return int(c)
    return ord(c) - ord("A") + 10


def verify_check_digit(curp: str) -> bool:
    """Verifica el digito verificador (posicion 18) de una CURP."""
    if len(curp) != 18:
        return False

    total = 0
    for i in range(17):
        total += _char_value(curp[i]) * (18 - i)

    remainder = total % 10
    expected = (10 - remainder) % 10

    return int(curp[17]) == expected


def validate_curp(curp: str) -> tuple[bool, str | None]:
    """Valida una CURP completa. Retorna (valida, razon_error)."""
    if not curp:
        return False, "CURP vacia"

    curp = curp.strip().upper()

    if len(curp) != 18:
        return False, f"Longitud {len(curp)}, esperada 18"

    if not _CURP_PATTERN.match(curp):
        return False, "Formato invalido (no cumple patron CURP)"

    # Verificar entidad federativa (posiciones 12-13)
    state = curp[11:13]
    if state not in _VALID_STATES:
        return False, f"Entidad federativa invalida: '{state}'"

    # Verificar fecha de nacimiento (posiciones 5-10: AAMMDD)
    yy = int(curp[4:6])
    mm = int(curp[6:8])
    dd = int(curp[8:10])

    if mm < 1 or mm > 12:
        return False, f"Mes invalido: {mm:02d}"
    if dd < 1 or dd > 31:
        return False, f"Dia invalido: {dd:02d}"

    # Meses con 30 dias
    if mm in (4, 6, 9, 11) and dd > 30:
        return False, f"Dia {dd} invalido para mes {mm:02d}"
    # Febrero (simplificado: max 29 por bisiesto)
    if mm == 2 and dd > 29:
        return False, f"Dia {dd} invalido para febrero"

    # Verificar digito verificador
    if not verify_check_digit(curp):
        return False, "Digito verificador incorrecto"

    # Verificar palabra inconveniente (pos 1-4)
    first_four = curp[:4]
    if first_four in _INCONVENIENT_WORDS:
        # No es error fatal, RENAPO sustituye la segunda letra por X
        # pero si el usuario lo mando tal cual, advertir
        return True, None  # Aceptar, pero podria ser warning

    return True, None


@register_validator
class CURPValidator(BaseValidator):
    """Valida formato CURP en campos nationalIdCard (ERROR)."""

    modes = ("split",)

    # Campos donde puede estar la CURP
    _CURP_FIELD_IDS = {"national-id", "nationalId", "national-id-number"}
    _CARD_TYPE_FIELD = "card-type"
    _COUNTRY_FIELD = "country"
    _CURP_CARD_TYPES = {"PR", "CURP"}

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        # Buscar columnas relevantes de nationalIdCard
        nid_columns = [h for h in ctx.csv_headers if h.startswith("nationalIdCard_")]
        if not nid_columns:
            return issues

        # Identificar field IDs
        country_col = f"nationalIdCard_{self._COUNTRY_FIELD}"
        card_type_col = f"nationalIdCard_{self._CARD_TYPE_FIELD}"
        nid_col = None
        for fid in self._CURP_FIELD_IDS:
            candidate = f"nationalIdCard_{fid}"
            if candidate in ctx.csv_headers:
                nid_col = candidate
                break

        if not nid_col:
            return issues

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            country_val = row.get(country_col, "")
            card_type_val = row.get(card_type_col, "")
            nid_val = row.get(nid_col, "")

            if not nid_val:
                continue

            # Manejar valores multi-pais (pipe-separated)
            countries = [c.strip() for c in country_val.split("|")] if country_val else [""]
            card_types = [c.strip() for c in card_type_val.split("|")] if card_type_val else [""]
            nid_values = [c.strip() for c in nid_val.split("|")] if nid_val else [""]

            for i, nid in enumerate(nid_values):
                country = countries[i] if i < len(countries) else countries[-1] if countries else ""
                card_type = card_types[i] if i < len(card_types) else card_types[-1] if card_types else ""

                # Solo validar CURP si es Mexico y tipo PR/CURP
                if country.upper().strip() not in ("MEX", "MX", "MEXICO"):
                    continue
                if card_type.upper().strip() not in self._CURP_CARD_TYPES:
                    continue

                valid, reason = validate_curp(nid)
                if not valid:
                    issues.append(self._emit(
                        Severity.ERROR,
                        "CURP_001",
                        element_id="nationalIdCard",
                        field_id=nid_col,
                        country_code="MX",
                        row=row_idx,
                        value=nid[:20],
                        reason=reason,
                    ))

        return issues
