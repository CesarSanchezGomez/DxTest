from typing import Optional
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import ContentMessages
from .base_validator import BaseContentValidator
from .entity_analyzer import EntityAnalyzer


class RequiredValidator(BaseContentValidator):

    def __init__(self, entity_analyzer: EntityAnalyzer):
        self.entity_analyzer = entity_analyzer

    def validate(self, value, context: dict) -> Optional[ValidationError]:
        if self.entity_analyzer._is_value_empty(value):
            return ValidationError(
                code="REQUIRED_FIELD_EMPTY",
                message=ContentMessages.required_field_empty(context.get('field_id', '')),
                severity=ErrorSeverity.ERROR,
                row_index=context.get('row_index'),
                column_name=context.get('column_name'),
                entity_id=context.get('entity_id'),
                field_id=context.get('field_id'),
                person_id=context.get('person_id')
            )
        return None
