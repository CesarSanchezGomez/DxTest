import re
from datetime import datetime
from typing import List, Optional
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import ContentMessages
from ..country_date_formats import resolve_date_formats
from .base_validator import BaseContentValidator


class TypeValidator(BaseContentValidator):

    def validate(self, value: str, context: dict) -> List[ValidationError]:
        errors = []
        expected_type = context.get('expected_type')
        field_id = context.get('field_id')

        if expected_type == 'date':
            error = self._validate_date(value, field_id, context)
        elif expected_type == 'integer':
            error = self._validate_integer(value, field_id, context)
        elif expected_type == 'decimal':
            error = self._validate_decimal(value, field_id, context)
        elif expected_type == 'boolean':
            error = self._validate_boolean(value, field_id, context)
        else:
            return errors

        if error:
            errors.append(error)

        return errors

    def _validate_date(self, value: str, field_id: str, context: dict) -> Optional[ValidationError]:
        country_codes = context.get('country_codes') or []
        expected_label, patterns = resolve_date_formats(country_codes)

        for regex, fmt in patterns:
            if re.match(regex, value):
                try:
                    datetime.strptime(value, fmt)
                    return None
                except ValueError:
                    continue

        return ValidationError(
            code="INVALID_DATE_FORMAT",
            message=ContentMessages.invalid_date(value, field_id, expected_label, country_codes),
            severity=ErrorSeverity.ERROR,
            row_index=context.get('row_index'),
            column_name=context.get('column_name'),
            entity_id=context.get('entity_id'),
            field_id=field_id,
            person_id=context.get('person_id'),
            value=value[:50]
        )

    def _validate_integer(self, value: str, field_id: str, context: dict) -> Optional[ValidationError]:
        cleaned = re.sub(r'[,\s]', '', value)
        if re.match(r'^-?\d+$', cleaned):
            return None

        return ValidationError(
            code="INVALID_INTEGER",
            message=ContentMessages.invalid_integer(value, field_id),
            severity=ErrorSeverity.ERROR,
            row_index=context.get('row_index'),
            column_name=context.get('column_name'),
            entity_id=context.get('entity_id'),
            field_id=field_id,
            person_id=context.get('person_id'),
            value=value[:50]
        )

    def _validate_decimal(self, value: str, field_id: str, context: dict) -> Optional[ValidationError]:
        cleaned = re.sub(r'[,\s]', '', value)
        if re.match(r'^-?\d+(\.\d+)?$', cleaned):
            return None

        return ValidationError(
            code="INVALID_DECIMAL",
            message=ContentMessages.invalid_decimal(value, field_id),
            severity=ErrorSeverity.ERROR,
            row_index=context.get('row_index'),
            column_name=context.get('column_name'),
            entity_id=context.get('entity_id'),
            field_id=field_id,
            person_id=context.get('person_id'),
            value=value[:50]
        )

    def _validate_boolean(self, value: str, field_id: str, context: dict) -> Optional[ValidationError]:
        valid_booleans = {
            "yes", "no", "true", "false",
            "1", "0", "y", "n", "si", "sí"
        }

        if value.lower().strip() in valid_booleans:
            return None

        return ValidationError(
            code="INVALID_BOOLEAN",
            message=ContentMessages.invalid_boolean(value, field_id),
            severity=ErrorSeverity.WARNING,
            row_index=context.get('row_index'),
            column_name=context.get('column_name'),
            entity_id=context.get('entity_id'),
            field_id=field_id,
            person_id=context.get('person_id'),
            value=value[:50]
        )
