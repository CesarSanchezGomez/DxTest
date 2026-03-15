from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import StructureMessages
from .base_validator import BaseValidator


class RowValidator(BaseValidator):

    def validate(self, data: List[List[str]], context: dict) -> List[ValidationError]:
        errors = []
        expected_count = context.get('expected_column_count')

        if not expected_count:
            return errors

        for idx, row in enumerate(data, start=3):
            actual_count = len(row)

            if actual_count != expected_count:
                errors.append(ValidationError(
                    code="ROW_COLUMN_COUNT_MISMATCH",
                    message=StructureMessages.row_column_mismatch(idx, expected_count, actual_count),
                    severity=ErrorSeverity.ERROR,
                    row_index=idx
                ))

        return errors

    @staticmethod
    def detect_empty_rows(lines: List[str]) -> tuple[int, List[int]]:
        first_non_empty_idx = 0
        empty_positions = []

        for idx, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                empty_positions.append(idx + 1)
                continue

            if stripped == ',' or all(c == ',' for c in stripped):
                empty_positions.append(idx + 1)
                continue

            if first_non_empty_idx == 0:
                first_non_empty_idx = idx

        return first_non_empty_idx, empty_positions

    @staticmethod
    def filter_empty_rows(rows: List[List[str]]) -> List[List[str]]:
        non_empty_rows = []

        for row in rows:
            if row and any(cell.strip() for cell in row):
                non_empty_rows.append(row)

        return non_empty_rows
