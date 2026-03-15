from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ...base_character_validator import BaseCharacterValidator
from ..messages import ContentMessages
from .base_validator import BaseContentValidator


class CharacterValidator(BaseContentValidator, BaseCharacterValidator):
    """Valida caracteres inválidos en datos (filas 3+)"""

    def validate(self, value: str, context: dict) -> List[ValidationError]:
        """Valida una celda individual"""
        errors = []

        if not value:
            return errors

        invalid_chars, suspicious_chars = self.detect_problematic_chars(value)

        column_name = context.get('column_name', '')
        entity_id = context.get('entity_id', '')
        field_id = context.get('field_id', '')
        row_index = context.get('row_index', 0)
        person_id = context.get('person_id', '')

        if invalid_chars:
            char_repr = self.format_char_repr(invalid_chars)
            value_preview = value[:30] + '...' if len(value) > 30 else value

            errors.append(ValidationError(
                code="INVALID_CHARACTERS",
                message=ContentMessages.invalid_characters_in_data(
                    char_repr,
                    value_preview
                ),
                severity=ErrorSeverity.ERROR,
                row_index=row_index,
                column_name=column_name,
                entity_id=entity_id,
                field_id=field_id,
                person_id=person_id,
                value=value_preview
            ))

        elif suspicious_chars:
            char_repr = self.format_char_repr(suspicious_chars)
            value_preview = value[:30] + '...' if len(value) > 30 else value

            errors.append(ValidationError(
                code="SUSPICIOUS_ENCODING",
                message=ContentMessages.suspicious_encoding_in_data(
                    char_repr,
                    value_preview
                ),
                severity=ErrorSeverity.ERROR,
                row_index=row_index,
                column_name=column_name,
                entity_id=entity_id,
                field_id=field_id,
                person_id=person_id,
                value=value_preview
            ))

        return errors
