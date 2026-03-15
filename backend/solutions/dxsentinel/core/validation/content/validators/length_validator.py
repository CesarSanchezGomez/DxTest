from typing import List, Optional
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import ContentMessages
from .base_validator import BaseContentValidator


class LengthValidator(BaseContentValidator):

    def validate(self, value: str, context: dict) -> List[ValidationError]:
        errors = []
        max_length = context.get('max_length')

        if not max_length:
            return errors

        if max_length == 1 and self._is_boolean_value(value):
            return errors

        actual_length = len(value)

        if actual_length > max_length:
            errors.append(ValidationError(
                code="MAX_LENGTH_EXCEEDED",
                message=ContentMessages.max_length_exceeded(
                    value,
                    context.get('field_id', ''),
                    max_length,
                    actual_length
                ),
                severity=ErrorSeverity.ERROR,
                row_index=context.get('row_index'),
                column_name=context.get('column_name'),
                entity_id=context.get('entity_id'),
                field_id=context.get('field_id'),
                person_id=context.get('person_id'),
                value=value[:50] + "..." if len(value) > 50 else value
            ))

        return errors

    def _is_boolean_value(self, value: str) -> bool:
        valid_booleans = {
            "yes", "no", "true", "false",
            "1", "0", "y", "n", "si", "sí"
        }
        return value.lower().strip() in valid_booleans
