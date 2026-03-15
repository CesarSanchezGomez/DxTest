"""Validacion de campos required vacios en CSV → ERROR.

Solo valida campos required que NO estan ya cubiertos por
EntityCompletenessValidator (que maneja la regla de entidad parcial).
Respeta la regla: si la entidad completa esta vacia en la fila, no lanza error.
"""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext
from .entity_analyzer import EntityAnalyzer


@register_validator
class RequiredFieldsValidator(BaseValidator):
    """Verifica que campos required tengan valor, respetando regla de entidad vacia."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.field_catalog:
            return issues

        analyzer = EntityAnalyzer(ctx.field_catalog)

        # Determinar entidades vacias globalmente
        empty_entities_global: set[str] = set()
        for entity_id in analyzer.get_entity_fields():
            if analyzer.is_entity_empty_globally(ctx.csv_rows, entity_id):
                empty_entities_global.add(entity_id)

        # Campos required del catalogo que estan en el CSV
        required_fields = {
            fid for fid, entry in ctx.field_catalog.items()
            if entry.get("required") and fid in ctx.csv_headers
        }

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2
            person_id = _extract_person_id(row)

            for col in required_fields:
                meta = ctx.field_catalog.get(col, {})
                entity_id = meta.get("element", "")

                # Skip entidades vacias globalmente
                if entity_id in empty_entities_global:
                    continue

                # Skip entidades vacias en esta fila (la regla especial)
                if analyzer.is_entity_empty_for_row(row, entity_id):
                    continue

                # Si llegamos aqui, la entidad tiene datos en esta fila
                # EntityCompletenessValidator ya cubre los required dentro de
                # entidades parcialmente llenas. Este validator cubre el caso
                # donde la entidad NO esta parcialmente llena pero el campo
                # required esta vacio (edge case que no deberia ocurrir si
                # EntityCompleteness ya lo cubrio, pero por seguridad).
                value = row.get(col)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    issues.append(self._emit(
                        Severity.ERROR,
                        "REQUIRED_FIELD_EMPTY",
                        element_id=entity_id,
                        field_id=meta.get("field", ""),
                        row_index=row_index,
                        column_name=col,
                        person_id=person_id,
                    ))

        return issues


def _extract_person_id(row: dict) -> str | None:
    for key in ("personInfo_person-id-external", "personalInfo_person-id-external"):
        if key in row and row[key]:
            val = str(row[key]).strip()
            if "|" in val:
                val = val.split("|")[0].strip()
            return val
    return None
