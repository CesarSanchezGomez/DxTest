import re
import unicodedata
from typing import Dict, List, Optional

from ....models.error_severity import ErrorSeverity
from ....models.validation_error import ValidationError
from ...messages import ContentMessages


class CURPValidator:

    TARGET_COUNTRY = "MEX"
    CURP_LENGTH = 18
    VOWELS: frozenset = frozenset("AEIOU")
    COMPOUND_NAME_PREFIXES: frozenset = frozenset({"JOSE", "MARIA", "MA", "J"})
    NAME_PARTICLES: frozenset = frozenset({"DE", "DEL", "LA", "LAS", "LOS", "EL", "Y", "E"})
    AP_PAT_PARTICLES: frozenset = frozenset({"DE", "DEL", "LA", "LAS", "LOS", "MC", "MAC"})

    STATE_VALIDATION_MODE: str = "picklist"

    STATE_MEX_PICKLIST: frozenset = frozenset({
        "Aguascalientes",
        "Baja California",
        "Baja California Sur",
        "Campeche",
        "Chiapas",
        "Chihuahua",
        "Ciudad de México",
        "Ciudad de México - Federal District (until January 2016)",
        "Coahuila de Zaragoza",
        "Colima",
        "Durango",
        "Guanajuato",
        "Guerrero",
        "Hidalgo",
        "Jalisco",
        "México",
        "Michoacán de Ocampo",
        "Morelos",
        "Nayarit",
        "Nuevo León",
        "Oaxaca",
        "Puebla",
        "Querétaro",
        "Quintana Roo",
        "San Luis Potosí",
        "Sinaloa",
        "Sonora",
        "Tabasco",
        "Tamaulipas",
        "Tlaxcala",
        "Veracruz de Ignacio de la Llave",
        "Yucatán",
        "Zacatecas",
    })

    GENDER_MAP_ES: Dict[str, str] = {
        "H": "H",
        "M": "M",
    }
    GENDER_MAP_EN: Dict[str, str] = {
        "M": "H",
        "F": "M",
    }

    GENDER_PICKLIST_ES: List[str] = ["H", "M"]
    GENDER_PICKLIST_EN: List[str] = ["M", "F"]

    STATE_TABLE: Dict[str, str] = {
        "AGUASCALIENTES": "AS",
        "AGS": "AS",
        "BAJA CALIFORNIA": "BC",
        "BAJA CALIFORNIA NORTE": "BC",
        "BC": "BC",
        "BAJA CALIFORNIA SUR": "BS",
        "BCS": "BS",
        "CAMPECHE": "CC",
        "CAMP": "CC",
        "COAHUILA": "CL",
        "COAHUILA DE ZARAGOZA": "CL",
        "COAH": "CL",
        "COLIMA": "CM",
        "COL": "CM",
        "CHIAPAS": "CS",
        "CHIS": "CS",
        "CHIHUAHUA": "CH",
        "CHIH": "CH",
        "DISTRITO FEDERAL": "DF",
        "CIUDAD DE MEXICO": "DF",
        "CIUDAD DE MÉXICO": "DF",
        "CDMX": "DF",
        "DF": "DF",
        "D.F.": "DF",
        "D.F": "DF",
        "CIUDAD MEXICO": "DF",
        "DURANGO": "DG",
        "DGO": "DG",
        "GUANAJUATO": "GT",
        "GTO": "GT",
        "GUERRERO": "GR",
        "GRO": "GR",
        "HIDALGO": "HG",
        "HGO": "HG",
        "JALISCO": "JC",
        "JAL": "JC",
        "MEXICO": "MC",
        "ESTADO DE MEXICO": "MC",
        "ESTADO DE MÉXICO": "MC",
        "EDO. DE MEXICO": "MC",
        "EDO. MEX.": "MC",
        "EDO MEX": "MC",
        "EDOMEX": "MC",
        "MEX": "MC",
        "MICHOACAN": "MN",
        "MICHOACÁN": "MN",
        "MICHOACAN DE OCAMPO": "MN",
        "MICH": "MN",
        "MORELOS": "MS",
        "MOR": "MS",
        "NAYARIT": "NT",
        "NAY": "NT",
        "NUEVO LEON": "NL",
        "NUEVO LEÓN": "NL",
        "NL": "NL",
        "N.L.": "NL",
        "OAXACA": "OC",
        "OAX": "OC",
        "PUEBLA": "PL",
        "PUE": "PL",
        "QUERETARO": "QT",
        "QUERÉTARO": "QT",
        "QUERETARO DE ARTEAGA": "QT",
        "QRO": "QT",
        "QUINTANA ROO": "QR",
        "Q. ROO": "QR",
        "Q.ROO": "QR",
        "QROO": "QR",
        "SAN LUIS POTOSI": "SP",
        "SAN LUIS POTOSÍ": "SP",
        "SLP": "SP",
        "SINALOA": "SL",
        "SIN": "SL",
        "SONORA": "SR",
        "SON": "SR",
        "TABASCO": "TC",
        "TAB": "TC",
        "TAMAULIPAS": "TS",
        "TAMPS": "TS",
        "TLAXCALA": "TL",
        "TLAX": "TL",
        "VERACRUZ": "VZ",
        "VERACRUZ DE IGNACIO DE LA LLAVE": "VZ",
        "VER": "VZ",
        "YUCATAN": "YN",
        "YUCATÁN": "YN",
        "YUC": "YN",
        "ZACATECAS": "ZS",
        "ZAC": "ZS",
        "NACIDO EN EL EXTRANJERO": "NE",
        "EXTRANJERO": "NE",
        "NE": "NE",
    }

    def __init__(self, country_codes: List[str], language_code: str = ""):
        self.active = self.TARGET_COUNTRY in [c.upper() for c in (country_codes or [])]
        lang = (language_code or "").strip().lower()
        if lang.startswith("en"):
            self.gender_map = self.GENDER_MAP_EN
            self.gender_picklist = self.GENDER_PICKLIST_EN
            self.language_label = "en-US"
        else:
            self.gender_map = self.GENDER_MAP_ES
            self.gender_picklist = self.GENDER_PICKLIST_ES
            self.language_label = "es-MX"

    def is_active(self) -> bool:
        return self.active

    def validate_row(self, curp_value: str, row: Dict, context: Dict) -> List[ValidationError]:
        errors: List[ValidationError] = []

        first_name = self._get_field(row, "first-name")
        middle_name = self._get_field(row, "middle-name")
        last_name = self._get_field(row, "last-name")
        second_last_name = self._get_field(row, "second-last-name")
        date_of_birth = self._get_field(row, "date-of-birth")
        gender = self._get_field(row, "gender")
        region = self._get_field(row, "region-of-birth")
        country_of_birth = self._get_field(row, "country-of-birth")

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
                errors.append(self._err(
                    "CURP_EMPTY_FIELD",
                    ContentMessages.curp_empty_field(field_name),
                    context,
                    field_id=field_name,
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
            errors.append(self._err(
                "CURP_NOT_UPPERCASE",
                ContentMessages.curp_not_uppercase(),
                context,
                value=curp,
            ))

        curp_upper = curp.upper()
        if len(curp_upper) != self.CURP_LENGTH:
            errors.append(self._err(
                "CURP_INVALID_LENGTH",
                ContentMessages.curp_invalid_length(len(curp_upper), self.CURP_LENGTH),
                context,
                value=curp,
            ))
            return errors

        date_match = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", date_of_birth)
        if not date_match:
            errors.append(self._err(
                "CURP_INVALID_DATE_FORMAT",
                ContentMessages.curp_invalid_date_format(),
                context,
                field_id="date-of-birth",
                value=date_of_birth,
            ))
            return errors

        if errors:
            return errors

        last_name_n = self._normalize(last_name)
        second_last_name_n = self._normalize(second_last_name) if second_last_name else ""
        first_name_n = self._normalize(effective_first_name)
        region_n = self._normalize(region)
        born_in_mexico: bool = self._normalize(country_of_birth) == "MEX"
        country_of_birth = str(country_of_birth).strip()

        expected_prefixes = self._build_expected_prefixes(last_name_n, second_last_name_n, first_name_n)
        if expected_prefixes and curp_upper[0:4] not in expected_prefixes:
            errors.append(self._err(
                "CURP_NAME_MISMATCH",
                ContentMessages.curp_field_mismatch("iniciales de nombre y apellidos"),
                context,
                value=curp,
            ))

        day, month, year = date_match.group(1), date_match.group(2), date_match.group(3)
        if year[2:] + month + day != curp_upper[4:10]:
            errors.append(self._err(
                "CURP_DATE_MISMATCH",
                ContentMessages.curp_field_mismatch("fecha de nacimiento"),
                context,
                field_id="date-of-birth",
                value=curp,
            ))

        gender_key = gender.upper()
        if gender_key not in self.gender_map:
            errors.append(self._err(
                "CURP_GENDER_INVALID_VALUE",
                ContentMessages.curp_gender_invalid_value(self.language_label, self.gender_picklist),
                context,
                field_id="gender",
                value=gender,
            ))
        else:
            curp_gender_code = self.gender_map[gender_key]
            if curp_gender_code != curp_upper[10]:
                errors.append(self._err(
                    "CURP_GENDER_MISMATCH",
                    ContentMessages.curp_gender_mismatch(self.language_label, self.gender_picklist),
                    context,
                    field_id="gender",
                    value=curp,
                ))

        curp_state = curp_upper[11:13]

        if self.STATE_VALIDATION_MODE == "picklist":
            errors.extend(self._validate_state_picklist(
                region, born_in_mexico, country_of_birth, curp_state, curp, context
            ))
        else:
            errors.extend(self._validate_state_flexible(
                region_n, born_in_mexico, country_of_birth, curp_state, curp, context
            ))

        return errors

    def _validate_state_picklist(
        self,
        region: str,
        born_in_mexico: bool,
        country_of_birth: str,
        curp_state: str,
        curp: str,
        context: Dict,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []

        if not born_in_mexico:
            if curp_state != "NE":
                errors.append(self._err(
                    "CURP_STATE_FOREIGN_NOT_NE",
                    ContentMessages.curp_state_picklist_foreign_mismatch(country_of_birth, curp_state),
                    context,
                    field_id="national-id",
                    value=curp,
                ))
        else:
            if region not in self.STATE_MEX_PICKLIST:
                errors.append(self._err(
                    "CURP_STATE_NOT_IN_PICKLIST",
                    ContentMessages.curp_state_not_in_picklist(region),
                    context,
                    field_id="region-of-birth",
                    value=region,
                ))

        return errors

    def _validate_state_flexible(
        self,
        region_n: str,
        born_in_mexico: bool,
        country_of_birth: str,
        curp_state: str,
        curp: str,
        context: Dict,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []

        if not born_in_mexico:
            if curp_state != "NE":
                errors.append(self._err(
                    "CURP_STATE_FOREIGN_NOT_NE",
                    ContentMessages.curp_state_foreign_not_ne(country_of_birth, curp_state),
                    context,
                    field_id="national-id",
                    value=curp,
                ))
        else:
            state_code = self.STATE_TABLE.get(region_n, "NE")
            cdmx_codes = {"DF", "MC"}
            state_valid = curp_state == state_code or (state_code in cdmx_codes and curp_state in cdmx_codes)
            if not state_valid:
                if curp_state == "NE":
                    errors.append(self._err(
                        "CURP_STATE_MEXICO_IS_NE",
                        ContentMessages.curp_state_mexico_is_ne(),
                        context,
                        field_id="national-id",
                        value=curp,
                    ))
                else:
                    errors.append(self._err(
                        "CURP_STATE_MISMATCH",
                        ContentMessages.curp_field_mismatch("lugar de nacimiento"),
                        context,
                        field_id="region-of-birth",
                        value=curp,
                    ))

        return errors

    def _get_field(self, row: Dict, field_id: str) -> Optional[str]:
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
    def _normalize(text: str) -> str:
        nfkd = unicodedata.normalize("NFKD", text.upper())
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    @staticmethod
    def _strip_trailing_periods(s: str) -> str:
        return s.rstrip(".")

    def _first_internal_vowel(self, word: str) -> str:
        for ch in word[1:]:
            if ch in self.VOWELS:
                return ch
        return "X"

    def _first_vowel(self, word: str) -> str:
        for ch in word:
            if ch in self.VOWELS:
                return ch
        return "X"

    def _effective_word(self, words: List[str], particles: frozenset) -> str:
        for word in words:
            if self._strip_trailing_periods(word) not in particles:
                return word
        return words[-1] if words else ""

    def _initial_for_first_name(self, parts: List[str]) -> str:
        if not parts:
            return "X"

        first_clean = self._strip_trailing_periods(parts[0])
        is_prefix = first_clean in self.COMPOUND_NAME_PREFIXES

        if is_prefix and len(parts) == 1:
            return first_clean[0]

        remaining = parts[1:] if is_prefix else parts
        for part in remaining:
            part_clean = self._strip_trailing_periods(part)
            if part_clean not in self.NAME_PARTICLES:
                return part_clean[0] if part_clean else part[0]

        if remaining:
            last_clean = self._strip_trailing_periods(remaining[-1])
            return last_clean[0] if last_clean else "X"
        return first_clean[0] if first_clean else "X"

    def _build_expected_prefixes(
        self,
        last_name_n: str,
        second_last_name_n: str,
        first_name_n: str,
    ) -> List[str]:
        ap1_words = last_name_n.split() if last_name_n else []
        ap2_words = second_last_name_n.split() if second_last_name_n else []
        first_words = first_name_n.split() if first_name_n else []

        if not ap1_words or not first_words:
            return []

        effective_ap1 = self._effective_word(ap1_words, self.AP_PAT_PARTICLES)
        p0 = effective_ap1[0]
        p1_primary = self._first_internal_vowel(effective_ap1)
        p1_legacy = self._first_internal_vowel(ap1_words[0])
        nombre_inicial = self._initial_for_first_name(first_words)

        prefixes: set = set()

        for p1 in {p1_primary, p1_legacy}:
            if ap2_words:
                for ap2 in ap2_words:
                    prefixes.add(p0 + p1 + ap2[0] + nombre_inicial)
                prefixes.add(p0 + p1 + "X" + nombre_inicial)
            else:
                prefixes.add(p0 + p1 + "X" + nombre_inicial)

                first_clean = self._strip_trailing_periods(first_words[0])
                is_name_prefix = first_clean in self.COMPOUND_NAME_PREFIXES

                if is_name_prefix and len(first_words) > 1:
                    for part in first_words[1:]:
                        part_clean = self._strip_trailing_periods(part)
                        if part_clean not in self.NAME_PARTICLES:
                            prefixes.add(p0 + p1 + part_clean[0] + self._first_vowel(part_clean))
                            break

                elif not is_name_prefix and len(first_words) > 1:
                    for part in first_words[1:]:
                        part_clean = self._strip_trailing_periods(part)
                        if part_clean not in self.NAME_PARTICLES:
                            prefixes.add(p0 + p1 + first_words[0][0] + part_clean[0])
                            break

        prefixes.update({p[0] + "X" + p[2:] for p in prefixes})

        return list(prefixes)

    def _err(
        self,
        code: str,
        message: str,
        context: Dict,
        field_id: str = "national-id",
        value: Optional[str] = None,
    ) -> ValidationError:
        return ValidationError(
            code=code,
            message=message,
            severity=ErrorSeverity.ERROR,
            row_index=context.get("row_index"),
            column_name=None,
            entity_id="nationalIdCard",
            field_id=field_id,
            person_id=context.get("person_id"),
            value=value[:50] if value else None,
        )
