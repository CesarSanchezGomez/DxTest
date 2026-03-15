from typing import List, Tuple, Dict
import csv
from io import StringIO

from ..models.validation_error import ValidationError
from ..models.error_severity import ErrorSeverity
from .messages import StructureMessages
from .validators.file_validator import FileValidator
from .validators.header_validator import HeaderValidator
from .validators.label_validator import LabelValidator
from .validators.column_validator import ColumnValidator
from .validators.row_validator import RowValidator
from .validators.character_validator import CharacterValidator


class CsvStructureValidator:

    def __init__(self, metadata: Dict):
        self.metadata = metadata
        self.field_catalog = metadata.get("field_catalog", {})
        self.expected_columns = set(self.field_catalog.keys())

        self.file_validator = FileValidator()
        self.character_validator = CharacterValidator()
        self.header_validator = HeaderValidator()
        self.label_validator = LabelValidator()
        self.column_validator = ColumnValidator(self.expected_columns)
        self.row_validator = RowValidator()

    def validate_structure(self, file_content: str) -> Tuple[bool, List[ValidationError]]:
        errors = []

        file_errors = self.file_validator.validate(file_content, {})
        if file_errors:
            return False, file_errors

        char_errors = self.character_validator.validate(file_content, {})
        if char_errors:
            errors.extend(char_errors)
            return False, errors

        try:
            csv_reader = csv.reader(StringIO(file_content))
            rows = list(csv_reader)
        except Exception as e:
            errors.append(ValidationError(
                code="CSV_PARSE_ERROR",
                message=StructureMessages.csv_parse_error(str(e)),
                severity=ErrorSeverity.FATAL
            ))
            return False, errors

        first_non_empty = next((i for i, row in enumerate(rows) if any(c.strip() for c in row)), None)

        if first_non_empty is None:
            errors.append(ValidationError(
                code="EMPTY_FILE",
                message=StructureMessages.empty_file(),
                severity=ErrorSeverity.FATAL
            ))
            return False, errors

        headers = rows[0]
        labels = rows[1] if len(rows) > 1 else []
        data_rows = RowValidator.filter_empty_rows(rows[2:]) if len(rows) > 2 else []

        header_errors = self.header_validator.validate(headers, {'labels': labels, 'empty_rows_before': first_non_empty})
        errors.extend(header_errors)

        context = {'expected_column_count': len(headers), 'headers': headers}
        label_errors = self.label_validator.validate(labels, context)
        errors.extend(label_errors)

        column_errors = self.column_validator.validate(headers, {})
        errors.extend(column_errors)

        if data_rows:
            row_errors = self.row_validator.validate(data_rows, context)
            errors.extend(row_errors)

        is_valid = not any(err.severity == ErrorSeverity.FATAL for err in errors)

        return is_valid, errors
