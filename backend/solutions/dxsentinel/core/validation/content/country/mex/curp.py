"""Validacion completa de CURP (Clave Unica de Registro de Poblacion) → ERROR.

Estructura CURP (18 caracteres):
  Pos 1-4:   Iniciales de nombres y apellidos
  Pos 5-10:  Fecha de nacimiento AAMMDD
  Pos 11:    Sexo (H=hombre, M=mujer)
  Pos 12-13: Entidad federativa (codigo de 2 letras)
  Pos 14-16: Consonantes internas
  Pos 17:    Digito diferenciador homonimia (0-9 o A-Z)
  Pos 18:    Digito verificador (0-9)

Valida contra datos del golden record: nombre, apellidos, fecha de nacimiento,
genero, region de nacimiento, pais de nacimiento.
Usa picklist SAP para estado de nacimiento.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from ....registry import register_validator
from ....result import Severity, ValidationResult
from ....base import BaseValidator, ValidationContext


_CURP_LENGTH = 18
_VOWELS = frozenset("AEIOU")
_COMPOUND_NAME_PREFIXES = frozenset({"JOSE", "MARIA", "MA", "J"})
_NAME_PARTICLES = frozenset({"DE", "DEL", "LA", "LAS", "LOS", "EL", "Y", "E"})
_AP_PAT_PARTICLES = frozenset({"DE", "DEL", "LA", "LAS", "LOS", "MC", "MAC"})

# Picklist oficial SAP 'state_mex' — valores exactos sin modificar
STATE_MEX_PICKLIST: frozenset = frozenset({
    "Aguascalientes",
    "Baja California",
    "Baja California Sur",
    "Campeche",
    "Chiapas",
    "Chihuahua",
    "Ciudad de M\u00e9xico",
    "Ciudad de M\u00e9xico - Federal District (until January 2016)",
    "Coahuila de Zaragoza",
    "Colima",
    "Durango",
    "Guanajuato",
    "Guerrero",
    "Hidalgo",
    "Jalisco",
    "M\u00e9xico",
    "Michoac\u00e1n de Ocampo",
    "Morelos",
    "Nayarit",
    "Nuevo Le\u00f3n",
    "Oaxaca",
    "Puebla",
    "Quer\u00e9taro",
    "Quintana Roo",
    "San Luis Potos\u00ed",
    "Sinaloa",
    "Sonora",
    "Tabasco",
    "Tamaulipas",
    "Tlaxcala",
    "Veracruz de Ignacio de la Llave",
    "Yucat\u00e1n",
    "Zacatecas",
})

# Mapas de genero por idioma
_GENDER_MAP_ES = {"H": "H", "M": "M"}
_GENDER_MAP_EN = {"M": "H", "F": "M"}
_GENDER_PICKLIST_ES = ["H", "M"]
_GENDER_PICKLIST_EN = ["M", "F"]

# Tabla de estados para normalizacion flexible
STATE_TABLE: dict[str, str] = {
    "AGUASCALIENTES": "AS", "AGS": "AS",
    "BAJA CALIFORNIA": "BC", "BAJA CALIFORNIA NORTE": "BC", "BC": "BC",
    "BAJA CALIFORNIA SUR": "BS", "BCS": "BS",
    "CAMPECHE": "CC", "CAMP": "CC",
    "COAHUILA": "CL", "COAHUILA DE ZARAGOZA": "CL", "COAH": "CL",
    "COLIMA": "CM", "COL": "CM",
    "CHIAPAS": "CS", "CHIS": "CS",
    "CHIHUAHUA": "CH", "CHIH": "CH",
    "DISTRITO FEDERAL": "DF", "CIUDAD DE MEXICO": "DF",
    "CIUDAD DE MÉXICO": "DF", "CDMX": "DF", "DF": "DF",
    "D.F.": "DF", "D.F": "DF", "CIUDAD MEXICO": "DF",
    "DURANGO": "DG", "DGO": "DG",
    "GUANAJUATO": "GT", "GTO": "GT",
    "GUERRERO": "GR", "GRO": "GR",
    "HIDALGO": "HG", "HGO": "HG",
    "JALISCO": "JC", "JAL": "JC",
    "MEXICO": "MC", "ESTADO DE MEXICO": "MC",
    "ESTADO DE MÉXICO": "MC", "EDO. DE MEXICO": "MC",
    "EDO. MEX.": "MC", "EDO MEX": "MC", "EDOMEX": "MC", "MEX": "MC",
    "MICHOACAN": "MN", "MICHOACÁN": "MN",
    "MICHOACAN DE OCAMPO": "MN", "MICH": "MN",
    "MORELOS": "MS", "MOR": "MS",
    "NAYARIT": "NT", "NAY": "NT",
    "NUEVO LEON": "NL", "NUEVO LEÓN": "NL", "NL": "NL", "N.L.": "NL",
    "OAXACA": "OC", "OAX": "OC",
    "PUEBLA": "PL", "PUE": "PL",
    "QUERETARO": "QT", "QUERÉTARO": "QT",
    "QUERETARO DE ARTEAGA": "QT", "QRO": "QT",
    "QUINTANA ROO": "QR", "Q. ROO": "QR", "Q.ROO": "QR", "QROO": "QR",
    "SAN LUIS POTOSI": "SP", "SAN LUIS POTOSÍ": "SP", "SLP": "SP",
    "SINALOA": "SL", "SIN": "SL",
    "SONORA": "SR", "SON": "SR",
    "TABASCO": "TC", "TAB": "TC",
    "TAMAULIPAS": "TS", "TAMPS": "TS",
    "TLAXCALA": "TL", "TLAX": "TL",
    "VERACRUZ": "VZ", "VERACRUZ DE IGNACIO DE LA LLAVE": "VZ", "VER": "VZ",
    "YUCATAN": "YN", "YUCATÁN": "YN", "YUC": "YN",
    "ZACATECAS": "ZS", "ZAC": "ZS",
    "NACIDO EN EL EXTRANJERO": "NE", "EXTRANJERO": "NE", "NE": "NE",
}


@register_validator
class CURPValidator(BaseValidator):
    """Valida CURP cruzando contra datos personales del golden record."""

    modes = ("split",)

    # Modo: "picklist" valida contra SAP picklist, "flexible" normaliza y cruza
    STATE_VALIDATION_MODE = "picklist"

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        country_codes = [c.upper() for c in (ctx.target_countries or [])]
        if "MEX" not in country_codes:
            return issues

        lang = (ctx.language_code or "").strip().lower()
        if lang.startswith("en"):
            gender_map = _GENDER_MAP_EN
            gender_picklist = _GENDER_PICKLIST_EN
            language_label = "en-US"
        else:
            gender_map = _GENDER_MAP_ES
            gender_picklist = _GENDER_PICKLIST_ES
            language_label = "es-MX"

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2
            person_id = self._extract_person_id(row)
            curp_value = self._get_field(row, "national-id")
            if not curp_value:
                continue

            row_issues = self._validate_curp_row(
                curp_value, row, row_index, person_id,
                gender_map, gender_picklist, language_label,
            )
            issues.extend(row_issues)

        return issues

    def _validate_curp_row(
        self,
        curp_value: str,
        row: dict,
        row_index: int,
        person_id: str | None,
        gender_map: dict,
        gender_picklist: list,
        language_label: str,
    ) -> list[ValidationResult]:
        errors: list[ValidationResult] = []

        first_name = self._get_field(row, "first-name")
        middle_name = self._get_field(row, "middle-name")
        last_name = self._get_field(row, "last-name")
        second_last_name = self._get_field(row, "second-last-name")
        date_of_birth = self._get_field(row, "date-of-birth")
        gender = self._get_field(row, "gender")
        region = self._get_field(row, "region-of-birth")
        country_of_birth = self._get_field(row, "country-of-birth")

        # Verificar campos requeridos
        required = {
            "first-name": first_name,
            "last-name": last_name,
            "date-of-birth": date_of_birth,
            "gender": gender,
            "region-of-birth": region,
            "country-of-birth": country_of_birth,
        }
        has_empty = False
        for field_name, value in required.items():
            if not value or not str(value).strip():
                errors.append(self._emit(
                    Severity.ERROR, "CURP_EMPTY_FIELD",
                    element_id="nationalIdCard", field_id=field_name,
                    row_index=row_index, person_id=person_id,
                    field_name=field_name,
                ))
                has_empty = True

        if has_empty:
            return errors

        curp = curp_value.strip()
        first_name = str(first_name).strip()
        middle_name = str(middle_name).strip() if middle_name else ""
        last_name = str(last_name).strip()
        second_last_name = str(second_last_name).strip() if second_last_name else ""
        date_of_birth = str(date_of_birth).strip()
        gender = str(gender).strip()
        region = str(region).strip()

        effective_first_name = f"{first_name} {middle_name}".strip() if middle_name else first_name

        if curp != curp.upper():
            errors.append(self._emit(
                Severity.ERROR, "CURP_NOT_UPPERCASE",
                element_id="nationalIdCard", field_id="national-id",
                row_index=row_index, person_id=person_id, value=curp,
            ))

        curp_upper = curp.upper()
        if len(curp_upper) != _CURP_LENGTH:
            errors.append(self._emit(
                Severity.ERROR, "CURP_INVALID_LENGTH",
                element_id="nationalIdCard", field_id="national-id",
                row_index=row_index, person_id=person_id, value=curp,
                actual=len(curp_upper), expected=_CURP_LENGTH,
            ))
            return errors

        # Validar formato de fecha
        date_match = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", date_of_birth)
        if not date_match:
            errors.append(self._emit(
                Severity.ERROR, "CURP_INVALID_DATE_FORMAT",
                element_id="nationalIdCard", field_id="date-of-birth",
                row_index=row_index, person_id=person_id, value=date_of_birth,
            ))
            return errors

        if errors:
            return errors

        # Normalizar para comparaciones
        last_name_n = _normalize(last_name)
        second_last_name_n = _normalize(second_last_name) if second_last_name else ""
        first_name_n = _normalize(effective_first_name)
        region_n = _normalize(region)
        born_in_mexico = _normalize(country_of_birth) == "MEX"
        country_of_birth_raw = str(country_of_birth).strip()

        # Validar iniciales de nombre
        expected_prefixes = _build_expected_prefixes(last_name_n, second_last_name_n, first_name_n)
        if expected_prefixes and curp_upper[0:4] not in expected_prefixes:
            errors.append(self._emit(
                Severity.ERROR, "CURP_NAME_MISMATCH",
                element_id="nationalIdCard", field_id="national-id",
                row_index=row_index, person_id=person_id, value=curp,
            ))

        # Validar fecha en CURP
        day, month, year = date_match.group(1), date_match.group(2), date_match.group(3)
        if year[2:] + month + day != curp_upper[4:10]:
            errors.append(self._emit(
                Severity.ERROR, "CURP_DATE_MISMATCH",
                element_id="nationalIdCard", field_id="date-of-birth",
                row_index=row_index, person_id=person_id, value=curp,
            ))

        # Validar genero
        gender_key = gender.upper()
        if gender_key not in gender_map:
            errors.append(self._emit(
                Severity.ERROR, "CURP_GENDER_INVALID_VALUE",
                element_id="nationalIdCard", field_id="gender",
                row_index=row_index, person_id=person_id, value=gender,
                language_label=language_label,
                picklist=", ".join(gender_picklist),
            ))
        else:
            curp_gender_code = gender_map[gender_key]
            if curp_gender_code != curp_upper[10]:
                errors.append(self._emit(
                    Severity.ERROR, "CURP_GENDER_MISMATCH",
                    element_id="nationalIdCard", field_id="gender",
                    row_index=row_index, person_id=person_id, value=curp,
                    language_label=language_label,
                    picklist=", ".join(gender_picklist),
                ))

        # Validar estado de nacimiento
        curp_state = curp_upper[11:13]
        if self.STATE_VALIDATION_MODE == "picklist":
            errors.extend(self._validate_state_picklist(
                region, born_in_mexico, country_of_birth_raw,
                curp_state, curp, row_index, person_id,
            ))
        else:
            errors.extend(self._validate_state_flexible(
                region_n, born_in_mexico, country_of_birth_raw,
                curp_state, curp, row_index, person_id,
            ))

        return errors

    def _validate_state_picklist(
        self, region: str, born_in_mexico: bool, country_of_birth: str,
        curp_state: str, curp: str, row_index: int, person_id: str | None,
    ) -> list[ValidationResult]:
        errors: list[ValidationResult] = []

        if not born_in_mexico:
            if curp_state != "NE":
                errors.append(self._emit(
                    Severity.ERROR, "CURP_STATE_FOREIGN_NOT_NE",
                    element_id="nationalIdCard", field_id="national-id",
                    row_index=row_index, person_id=person_id, value=curp,
                    country_of_birth=country_of_birth, state_in_curp=curp_state,
                ))
        else:
            if region not in STATE_MEX_PICKLIST:
                errors.append(self._emit(
                    Severity.ERROR, "CURP_STATE_NOT_IN_PICKLIST",
                    element_id="nationalIdCard", field_id="region-of-birth",
                    row_index=row_index, person_id=person_id, value=region,
                    region=region,
                ))

        return errors

    def _validate_state_flexible(
        self, region_n: str, born_in_mexico: bool, country_of_birth: str,
        curp_state: str, curp: str, row_index: int, person_id: str | None,
    ) -> list[ValidationResult]:
        errors: list[ValidationResult] = []

        if not born_in_mexico:
            if curp_state != "NE":
                errors.append(self._emit(
                    Severity.ERROR, "CURP_STATE_FOREIGN_NOT_NE",
                    element_id="nationalIdCard", field_id="national-id",
                    row_index=row_index, person_id=person_id, value=curp,
                    country_of_birth=country_of_birth, state_in_curp=curp_state,
                ))
        else:
            state_code = STATE_TABLE.get(region_n, "NE")
            cdmx_codes = {"DF", "MC"}
            state_valid = curp_state == state_code or (
                state_code in cdmx_codes and curp_state in cdmx_codes
            )
            if not state_valid:
                if curp_state == "NE":
                    errors.append(self._emit(
                        Severity.ERROR, "CURP_STATE_MEXICO_IS_NE",
                        element_id="nationalIdCard", field_id="national-id",
                        row_index=row_index, person_id=person_id, value=curp,
                    ))
                else:
                    errors.append(self._emit(
                        Severity.ERROR, "CURP_STATE_MISMATCH",
                        element_id="nationalIdCard", field_id="region-of-birth",
                        row_index=row_index, person_id=person_id, value=curp,
                    ))

        return errors

    @staticmethod
    def _get_field(row: dict, field_id: str) -> Optional[str]:
        suffix = f"_{field_id}"
        for key, value in row.items():
            if key.endswith(suffix):
                if value is None:
                    return None
                val_str = str(value).strip()
                if "|" in val_str:
                    val_str = val_str.split("|")[0].strip()
                return val_str or None
        return None

    @staticmethod
    def _extract_person_id(row: dict) -> str | None:
        for key in ("personInfo_person-id-external", "personalInfo_person-id-external"):
            if key in row and row[key]:
                val = str(row[key]).strip()
                if "|" in val:
                    val = val.split("|")[0].strip()
                return val
        return None


# ── Funciones auxiliares de normalizacion ──────────────────────────────────

def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.upper())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _strip_trailing_periods(s: str) -> str:
    return s.rstrip(".")


def _first_internal_vowel(word: str) -> str:
    for ch in word[1:]:
        if ch in _VOWELS:
            return ch
    return "X"


def _first_vowel(word: str) -> str:
    for ch in word:
        if ch in _VOWELS:
            return ch
    return "X"


def _effective_word(words: list[str], particles: frozenset) -> str:
    for word in words:
        if _strip_trailing_periods(word) not in particles:
            return word
    return words[-1] if words else ""


def _initial_for_first_name(parts: list[str]) -> str:
    if not parts:
        return "X"

    first_clean = _strip_trailing_periods(parts[0])
    is_prefix = first_clean in _COMPOUND_NAME_PREFIXES

    if is_prefix and len(parts) == 1:
        return first_clean[0]

    remaining = parts[1:] if is_prefix else parts
    for part in remaining:
        part_clean = _strip_trailing_periods(part)
        if part_clean not in _NAME_PARTICLES:
            return part_clean[0] if part_clean else part[0]

    if remaining:
        last_clean = _strip_trailing_periods(remaining[-1])
        return last_clean[0] if last_clean else "X"
    return first_clean[0] if first_clean else "X"


def _build_expected_prefixes(
    last_name_n: str,
    second_last_name_n: str,
    first_name_n: str,
) -> list[str]:
    ap1_words = last_name_n.split() if last_name_n else []
    ap2_words = second_last_name_n.split() if second_last_name_n else []
    first_words = first_name_n.split() if first_name_n else []

    if not ap1_words or not first_words:
        return []

    effective_ap1 = _effective_word(ap1_words, _AP_PAT_PARTICLES)
    p0 = effective_ap1[0]
    p1_primary = _first_internal_vowel(effective_ap1)
    p1_legacy = _first_internal_vowel(ap1_words[0])
    nombre_inicial = _initial_for_first_name(first_words)

    prefixes: set = set()

    for p1 in {p1_primary, p1_legacy}:
        if ap2_words:
            for ap2 in ap2_words:
                prefixes.add(p0 + p1 + ap2[0] + nombre_inicial)
            prefixes.add(p0 + p1 + "X" + nombre_inicial)
        else:
            prefixes.add(p0 + p1 + "X" + nombre_inicial)

            first_clean = _strip_trailing_periods(first_words[0])
            is_name_prefix = first_clean in _COMPOUND_NAME_PREFIXES

            if is_name_prefix and len(first_words) > 1:
                for part in first_words[1:]:
                    part_clean = _strip_trailing_periods(part)
                    if part_clean not in _NAME_PARTICLES:
                        prefixes.add(p0 + p1 + part_clean[0] + _first_vowel(part_clean))
                        break

            elif not is_name_prefix and len(first_words) > 1:
                for part in first_words[1:]:
                    part_clean = _strip_trailing_periods(part)
                    if part_clean not in _NAME_PARTICLES:
                        prefixes.add(p0 + p1 + first_words[0][0] + part_clean[0])
                        break

    prefixes.update({p[0] + "X" + p[2:] for p in prefixes})

    return list(prefixes)
