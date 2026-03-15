import re
from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import StructureMessages
from .base_validator import BaseValidator


class HeaderValidator(BaseValidator):
    COLUMN_ID_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*_[a-zA-Z0-9_-]+$')

    def validate(self, data: List[str], context: dict) -> List[ValidationError]:
        errors = []

        empty_rows_before = context.get('empty_rows_before', 0)
        if empty_rows_before > 0:
            errors.append(ValidationError(
                code="EMPTY_ROWS_BEFORE_HEADERS",
                message=StructureMessages.empty_rows_before_headers(empty_rows_before),
                severity=ErrorSeverity.FATAL,
                row_index=1
            ))
            return errors

        if not data:
            return errors

        labels = context.get('labels', [])

        for col_idx, column_name in enumerate(data):
            label = labels[col_idx].strip() if col_idx < len(labels) else ''
            is_header_empty = not column_name or not column_name.strip()

            if is_header_empty:
                if not label:
                    continue

                errors.append(ValidationError(
                    code="EMPTY_COLUMN_NAME",
                    message=StructureMessages.empty_column_id(col_idx + 1),
                    severity=ErrorSeverity.FATAL,
                    row_index=1,
                    column_index=col_idx + 1,
                    value=column_name
                ))
                continue

            if not self.COLUMN_ID_PATTERN.match(column_name.strip()):
                errors.append(ValidationError(
                    code="INVALID_COLUMN_IDENTIFIER",
                    message=StructureMessages.invalid_column_format(column_name, col_idx + 1),
                    severity=ErrorSeverity.FATAL,
                    row_index=1,
                    column_index=col_idx + 1,
                    value=column_name
                ))

        return errors
