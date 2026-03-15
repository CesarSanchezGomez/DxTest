from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import StructureMessages
from .base_validator import BaseValidator


class LabelValidator(BaseValidator):

    def validate(self, data: List[str], context: dict) -> List[ValidationError]:
        errors = []
        expected_count = context.get('expected_column_count')
        headers = context.get('headers', [])

        if not expected_count:
            return errors

        if not data or not any(cell.strip() for cell in data):
            errors.append(ValidationError(
                code="MISSING_LABEL_ROW",
                message=StructureMessages.missing_label_row(),
                severity=ErrorSeverity.FATAL,
                row_index=2
            ))
            return errors

        actual_count = len(data)
        if actual_count != expected_count:
            errors.append(ValidationError(
                code="LABEL_COLUMN_MISMATCH",
                message=StructureMessages.label_column_mismatch(expected_count, actual_count),
                severity=ErrorSeverity.ERROR,
                row_index=2
            ))

        for col_idx in range(max(len(headers), len(data))):
            header = headers[col_idx].strip() if col_idx < len(headers) else ''
            label = data[col_idx].strip() if col_idx < len(data) else ''

            if header and not label:
                errors.append(ValidationError(
                    code="EMPTY_LABEL_NAME",
                    message=StructureMessages.empty_label_name(col_idx + 1),
                    severity=ErrorSeverity.WARNING,
                    row_index=2,
                    column_index=col_idx + 1,
                    value=header
                ))

        return errors
