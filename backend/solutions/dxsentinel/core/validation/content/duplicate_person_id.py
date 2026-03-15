"""Validacion de person-id-external duplicados → FATAL.

Valida que no existan registros duplicados en el Golden Record,
usando personInfo_person-id-external como clave unica.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext


_PERSON_ID_CANDIDATES = [
    "personInfo_person-id-external",
    "personalInfo_person-id-external",
]
_PERSON_ID_FIELD_SUFFIX = "person-id-external"


def _resolve_person_id_column(headers: list[str]) -> Optional[str]:
    """Devuelve el nombre real de la columna person-id-external en este CSV."""
    for candidate in _PERSON_ID_CANDIDATES:
        if candidate in headers:
            return candidate
    for header in headers:
        if header.endswith(_PERSON_ID_FIELD_SUFFIX):
            return header
    return None


def _extract_id(raw_value) -> Optional[str]:
    """Extrae el primer valor de una celda (ignora multi-valor con |)."""
    if raw_value is None:
        return None
    val = str(raw_value).strip()
    if not val:
        return None
    if "|" in val:
        val = val.split("|")[0].strip()
    return val or None


@register_validator
class DuplicatePersonIdValidator(BaseValidator):
    """Detecta person-id-external duplicados entre filas (FATAL)."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        column = _resolve_person_id_column(ctx.csv_headers)
        if column is None:
            return issues

        entity_id, _, field_id = column.partition("_")

        # Agrupar row_indices por person-id-external
        seen: dict[str, list[int]] = defaultdict(list)
        for row_idx, row in enumerate(ctx.csv_rows):
            pid = _extract_id(row.get(column))
            if pid:
                seen[pid].append(row_idx + 3)  # +3: fila 1=headers, 2=labels

        for person_id, row_indices in seen.items():
            if len(row_indices) < 2:
                continue
            rows_display = ", ".join(str(r) for r in row_indices)
            for row_index in row_indices:
                issues.append(self._emit(
                    Severity.FATAL,
                    "DUPLICATE_PERSON_ID",
                    element_id=entity_id,
                    field_id=field_id,
                    row_index=row_index,
                    column_name=column,
                    person_id=person_id,
                    value=person_id,
                    rows=rows_display,
                ))

        return issues
