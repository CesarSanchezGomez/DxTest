from typing import List, Dict, Set
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import StructureMessages
from .base_validator import BaseValidator
from collections import defaultdict


class ColumnValidator(BaseValidator):

    def __init__(self, expected_columns: Set[str]):
        self.expected_columns = expected_columns

    def validate(self, data: List[str], context: dict) -> List[ValidationError]:
        errors = []

        errors.extend(self._validate_duplicates(data))
        errors.extend(self._validate_expected_columns(data))
        errors.extend(self._validate_extra_columns(data))

        return errors

    def _validate_duplicates(self, headers: List[str]) -> List[ValidationError]:
        errors = []
        seen = defaultdict(list)

        for col_idx, column_name in enumerate(headers):
            column_name = column_name.strip()
            if not column_name:
                continue

            seen[column_name].append(col_idx + 1)

        for column_name, positions in seen.items():
            if len(positions) > 1:
                errors.append(ValidationError(
                    code="DUPLICATED_COLUMN",
                    message=StructureMessages.duplicate_column(column_name, positions),
                    severity=ErrorSeverity.FATAL,
                    row_index=1,
                    column_index=positions[-1],
                    value=column_name
                ))

        return errors

    def _validate_expected_columns(self, headers: List[str]) -> List[ValidationError]:
        errors = []
        actual_columns = {col.strip() for col in headers if col.strip()}
        missing_columns = self.expected_columns - actual_columns

        if not missing_columns:
            return errors

        missing_by_entity = self._group_by_entity(missing_columns)

        for entity, cols in missing_by_entity.items():
            errors.append(ValidationError(
                code="MISSING_EXPECTED_COLUMNS",
                message=StructureMessages.missing_columns(entity, cols, len(cols)),
                severity=ErrorSeverity.FATAL,
                row_index=1
            ))

        return errors

    def _validate_extra_columns(self, headers: List[str]) -> List[ValidationError]:
        errors = []

        for col_idx, column_name in enumerate(headers):
            col_stripped = column_name.strip()
            if not col_stripped:
                continue

            if col_stripped not in self.expected_columns:
                errors.append(ValidationError(
                    code="UNEXPECTED_COLUMNS",
                    message=StructureMessages.unexpected_columns([col_stripped], 1),
                    severity=ErrorSeverity.FATAL,
                    row_index=1,
                    column_index=col_idx + 1,
                    value=col_stripped
                ))

        return errors

    def _group_by_entity(self, columns: Set[str]) -> Dict[str, List[str]]:
        grouped = defaultdict(list)

        for col in columns:
            if '_' in col:
                entity = col.split('_')[0]
                grouped[entity].append(col)
            else:
                grouped['unknown'].append(col)

        return dict(grouped)
