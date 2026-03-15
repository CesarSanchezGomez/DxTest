from typing import List, Dict, Set, Tuple
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import ContentMessages
from .base_validator import BaseContentValidator
from .entity_analyzer import EntityAnalyzer


class EntityCompletenessValidator(BaseContentValidator):

    def __init__(self, entity_analyzer: EntityAnalyzer, field_catalog: Dict):
        self.entity_analyzer = entity_analyzer
        self.field_catalog = field_catalog

    def validate(self, row: Dict, context: dict) -> Tuple[List[ValidationError], Set[str]]:
        errors = []
        validated_columns = set()

        entity_fields = self.entity_analyzer.get_entity_fields()
        empty_entities_global = context.get('empty_entities_global', set())

        for entity_id, columns in entity_fields.items():
            if entity_id in empty_entities_global:
                continue

            if self.entity_analyzer.is_entity_empty_for_row(row, entity_id):
                continue

            required_fields = self.entity_analyzer.get_required_fields_for_entity(entity_id)
            missing_fields = []
            filled_fields = []

            for col in columns:
                value = row.get(col)
                if not self.entity_analyzer._is_value_empty(value):
                    field_meta = self.field_catalog.get(col, {})
                    filled_fields.append(field_meta.get("field", col))

            for col in required_fields:
                value = row.get(col)
                if self.entity_analyzer._is_value_empty(value):
                    field_meta = self.field_catalog.get(col, {})
                    field_id = field_meta.get("field", "")
                    missing_fields.append(field_id)

            for col in required_fields:
                value = row.get(col)
                if self.entity_analyzer._is_value_empty(value):
                    field_meta = self.field_catalog.get(col, {})
                    field_id = field_meta.get("field", "")

                    errors.append(ValidationError(
                        code="INCOMPLETE_ENTITY",
                        message=ContentMessages.incomplete_entity(
                            entity_id,
                            field_id,
                            filled_fields,
                            missing_fields
                        ),
                        severity=ErrorSeverity.ERROR,
                        row_index=context.get('row_index'),
                        column_name=col,
                        entity_id=entity_id,
                        field_id=field_id,
                        person_id=context.get('person_id')
                    ))

                    validated_columns.add(col)

        return errors, validated_columns
