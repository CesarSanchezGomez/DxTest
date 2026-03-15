"""Validacion de completitud de entidades → ERROR.

Regla especial: si una fila de entidad completa esta vacia,
NO se lanza error aunque sus campos sean obligatorios.
Pero si uno de sus campos tiene datos y otro obligatorio falta, SI se lanza.
"""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext
from .entity_analyzer import EntityAnalyzer


@register_validator
class EntityCompletenessValidator(BaseValidator):
    """Verifica completitud de entidades: entidad parcialmente llena con required vacios."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.field_catalog:
            return issues

        analyzer = EntityAnalyzer(ctx.field_catalog)

        # Determinar entidades vacias globalmente
        empty_entities_global: set[str] = set()
        entity_fields = analyzer.get_entity_fields()
        for entity_id in entity_fields:
            if analyzer.is_entity_empty_globally(ctx.csv_rows, entity_id):
                empty_entities_global.add(entity_id)

        # Track columnas validadas para que RequiredFieldsValidator no duplique
        validated_columns: set[str] = set()

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            person_id = _extract_person_id(row)
            row_index = row_idx + 2  # +2: fila 1=headers, 2=labels

            for entity_id, columns in entity_fields.items():
                # Skip entidades vacias globalmente
                if entity_id in empty_entities_global:
                    continue

                # Skip entidades vacias en esta fila
                if analyzer.is_entity_empty_for_row(row, entity_id):
                    continue

                # La entidad tiene al menos un campo con datos → verificar required
                required_fields = analyzer.get_required_fields_for_entity(entity_id)

                filled_fields = []
                missing_fields = []

                for col in columns:
                    value = row.get(col)
                    if not analyzer._is_value_empty(value):
                        field_meta = ctx.field_catalog.get(col, {})
                        filled_fields.append(field_meta.get("field", col))

                for col in required_fields:
                    value = row.get(col)
                    if analyzer._is_value_empty(value):
                        field_meta = ctx.field_catalog.get(col, {})
                        missing_fields.append(field_meta.get("field", ""))

                for col in required_fields:
                    value = row.get(col)
                    if analyzer._is_value_empty(value):
                        field_meta = ctx.field_catalog.get(col, {})
                        field_id = field_meta.get("field", "")

                        filled_display = ", ".join(filled_fields[:3])
                        if len(filled_fields) > 3:
                            filled_display += f" (+{len(filled_fields) - 3})"
                        missing_display = ", ".join(missing_fields)

                        issues.append(self._emit(
                            Severity.ERROR,
                            "INCOMPLETE_ENTITY",
                            element_id=entity_id,
                            field_id=field_id,
                            row_index=row_index,
                            column_name=col,
                            person_id=person_id,
                            filled=filled_display,
                            missing=missing_display,
                        ))

                        validated_columns.add(col)

        # Guardar columnas validadas en el contexto para RequiredFieldsValidator
        ctx._validated_columns = validated_columns

        return issues


def _extract_person_id(row: dict) -> str | None:
    """Extrae person-id-external de la fila."""
    for key in ("personInfo_person-id-external", "personalInfo_person-id-external"):
        if key in row and row[key]:
            val = str(row[key]).strip()
            if "|" in val:
                val = val.split("|")[0].strip()
            return val
    return None
