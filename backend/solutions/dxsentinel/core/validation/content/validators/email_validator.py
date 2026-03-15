import re
from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import ContentMessages
from .base_validator import BaseContentValidator


class EmailValidator(BaseContentValidator):
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def validate(self, value: str, context: dict) -> List[ValidationError]:
        errors = []

        if not self._is_valid_email(value):
            errors.append(ValidationError(
                code="INVALID_EMAIL_FORMAT",
                message=ContentMessages.invalid_email(value, context.get('field_id', '')),
                severity=ErrorSeverity.ERROR,
                row_index=context.get('row_index'),
                column_name=context.get('column_name'),
                entity_id=context.get('entity_id'),
                field_id=context.get('field_id'),
                person_id=context.get('person_id'),
                value=value[:50]
            ))

        return errors

    def _is_valid_email(self, email: str) -> bool:
        if not email or not email.strip():
            return False
        return bool(self.EMAIL_PATTERN.match(email.strip()))

    @staticmethod
    def is_email_field(column_name: str) -> bool:
        lower_name = column_name.lower()

        email_suffixes = [
            'email',
            'email-address',
            'email_address',
            'emailaddress',
            '-email',
            '_email'
        ]

        return any(lower_name.endswith(suffix) for suffix in email_suffixes)
