"""Validacion de workPermitInfo: RFC y NSS para Mexico → ERROR.

Valida workPermitInfo_document-type y workPermitInfo_document-number.
Tipos soportados:
    Federal Taxpayer Registration / Registro Federal de Contribuyentes → RFC
    IMSS Instituto Mexicano del Seguro Social → NSS (11 digitos)

Separador de valores multiples: '|'
"""

from __future__ import annotations

import re
from typing import Optional

from ....registry import register_validator
from ....result import Severity, ValidationResult
from ....base import BaseValidator, ValidationContext
from ...entity_analyzer import EntityAnalyzer

_TARGET_ENTITY = "workPermitInfo"

_KEYWORD_RFC = "FEDERAL TAXPAYER REGISTRATION"
_KEYWORD_RFC_ES = "REGISTRO FEDERAL DE CONTRIBUYENTES"
_KEYWORD_IMSS = "IMSS"

_RFC_FISICA_RE = re.compile(r"^[A-Z\xd1&]{4}\d{6}[A-Z0-9]{3}$")
_RFC_MORAL_RE = re.compile(r"^[A-Z\xd1&]{3}\d{6}[A-Z0-9]{3}$")
_NSS_RE = re.compile(r"^\d{11}$")


@register_validator
class WorkPermitValidator(BaseValidator):
    """Valida RFC y NSS en workPermitInfo para Mexico."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        country_codes = [c.upper() for c in (ctx.target_countries or [])]
        if "MEX" not in country_codes:
            return issues

        analyzer = EntityAnalyzer(ctx.field_catalog)

        # Verificar si la entidad esta vacia globalmente
        if analyzer.is_entity_empty_globally(ctx.csv_rows, _TARGET_ENTITY):
            return issues

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2

            # Skip si entidad vacia en esta fila
            if analyzer.is_entity_empty_for_row(row, _TARGET_ENTITY):
                continue

            person_id = self._extract_person_id(row)
            row_issues = self._validate_row(row, row_index, person_id)
            issues.extend(row_issues)

        return issues

    def _validate_row(
        self, row: dict, row_index: int, person_id: str | None,
    ) -> list[ValidationResult]:
        errors: list[ValidationResult] = []

        doc_types_raw = self._get_field(row, "document-type")
        doc_numbers_raw = self._get_field(row, "document-number")

        types_empty = not doc_types_raw
        numbers_empty = not doc_numbers_raw

        if types_empty and numbers_empty:
            return errors

        if types_empty or numbers_empty:
            errors.append(self._emit(
                Severity.ERROR, "WORK_PERMIT_INCOMPLETE",
                element_id=_TARGET_ENTITY, field_id="document-type",
                row_index=row_index, person_id=person_id,
            ))
            return errors

        types = [t.strip() for t in str(doc_types_raw).split("|")]
        numbers = [n.strip() for n in str(doc_numbers_raw).split("|")]

        if len(types) != len(numbers):
            errors.append(self._emit(
                Severity.ERROR, "WORK_PERMIT_COUNT_MISMATCH",
                element_id=_TARGET_ENTITY, field_id="document-type",
                row_index=row_index, person_id=person_id,
                types_count=len(types), numbers_count=len(numbers),
            ))
            return errors

        for i, (doc_type, doc_number) in enumerate(zip(types, numbers)):
            position = i + 1
            doc_type_upper = doc_type.upper()

            if _KEYWORD_RFC in doc_type_upper or _KEYWORD_RFC_ES in doc_type_upper:
                if not (_RFC_FISICA_RE.match(doc_number) or _RFC_MORAL_RE.match(doc_number)):
                    errors.append(self._emit(
                        Severity.ERROR, "WORK_PERMIT_RFC_INVALID",
                        element_id=_TARGET_ENTITY, field_id="document-number",
                        row_index=row_index, person_id=person_id,
                        value=doc_number, position=position,
                    ))

            elif _KEYWORD_IMSS in doc_type_upper:
                if not _NSS_RE.match(doc_number):
                    errors.append(self._emit(
                        Severity.ERROR, "WORK_PERMIT_NSS_INVALID",
                        element_id=_TARGET_ENTITY, field_id="document-number",
                        row_index=row_index, person_id=person_id,
                        value=doc_number, position=position,
                    ))

            else:
                errors.append(self._emit(
                    Severity.ERROR, "WORK_PERMIT_UNKNOWN_TYPE",
                    element_id=_TARGET_ENTITY, field_id="document-type",
                    row_index=row_index, person_id=person_id,
                    value=doc_type, position=position, doc_type=doc_type,
                ))

        return errors

    @staticmethod
    def _get_field(row: dict, field_id: str) -> Optional[str]:
        suffix = f"_{field_id}"
        for key, value in row.items():
            if _TARGET_ENTITY in key and key.endswith(suffix):
                if value is None:
                    return None
                val_str = str(value).strip()
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
