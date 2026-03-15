from typing import List
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import StructureMessages
from .base_validator import BaseValidator


class FileValidator(BaseValidator):
    """Valida que el contenido del archivo no esté vacío"""

    def validate(self, data: str, context: dict) -> List[ValidationError]:
        errors = []

        if not data or not data.strip():
            errors.append(ValidationError(
                code="EMPTY_FILE",
                message=StructureMessages.empty_file(),
                severity=ErrorSeverity.FATAL
            ))

        return errors
