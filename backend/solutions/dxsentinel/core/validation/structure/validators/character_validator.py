import csv
from io import StringIO
from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ...base_character_validator import BaseCharacterValidator
from ..messages import StructureMessages
from .base_validator import BaseValidator


class CharacterValidator(BaseValidator, BaseCharacterValidator):
    """Valida caracteres inválidos en estructura (filas 1-2: headers y labels)"""

    def validate(self, file_content: str, context: dict) -> List[ValidationError]:
        """Valida solo las primeras 2 filas (headers y labels)"""
        errors = []

        try:
            csv_reader = csv.reader(StringIO(file_content))
            rows = list(csv_reader)
        except Exception:
            return errors

        max_row = min(2, len(rows))

        for row_idx in range(max_row):
            row = rows[row_idx]
            actual_row = row_idx + 1

            for col_idx, cell in enumerate(row, start=1):
                if not cell:
                    continue

                invalid_chars, suspicious_chars = self.detect_problematic_chars(cell)

                if invalid_chars:
                    char_repr = self.format_char_repr(invalid_chars)
                    cell_preview = cell[:30] + '...' if len(cell) > 30 else cell

                    errors.append(ValidationError(
                        code="INVALID_CHARACTERS",
                        message=StructureMessages.invalid_characters_in_cell(
                            char_repr,
                            cell_preview
                        ),
                        severity=ErrorSeverity.FATAL,
                        row_index=actual_row,
                        column_index=col_idx,
                        value=cell_preview
                    ))

                elif suspicious_chars:
                    char_repr = self.format_char_repr(suspicious_chars)
                    cell_preview = cell[:30] + '...' if len(cell) > 30 else cell

                    errors.append(ValidationError(
                        code="SUSPICIOUS_ENCODING",
                        message=StructureMessages.suspicious_encoding_in_cell(
                            char_repr,
                            cell_preview
                        ),
                        severity=ErrorSeverity.FATAL,
                        row_index=actual_row,
                        column_index=col_idx,
                        value=cell_preview
                    ))

        return errors
