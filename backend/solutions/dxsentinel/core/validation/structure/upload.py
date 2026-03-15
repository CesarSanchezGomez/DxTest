"""Validacion de archivos de upload → FATAL."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

MAX_XML_UPLOAD_SIZE = 50 * 1024 * 1024   # 50 MB
MAX_CSV_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB


@register_validator
class UploadValidator(BaseValidator):
    """Verifica restricciones del archivo subido (FATAL)."""

    modes = ("generation",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []
        filename = ctx.upload_filename
        size = ctx.upload_size_bytes

        if not filename:
            return issues

        lower = filename.lower()
        if not (lower.endswith(".xml") or lower.endswith(".csv")):
            issues.append(self._emit(Severity.FATAL, "UPLOAD_001", filename=filename))

        if size is not None:
            if lower.endswith(".xml") and size > MAX_XML_UPLOAD_SIZE:
                issues.append(self._emit(Severity.FATAL, "UPLOAD_002", size_mb=size / 1024 / 1024))
            elif lower.endswith(".csv") and size > MAX_CSV_UPLOAD_SIZE:
                issues.append(self._emit(Severity.FATAL, "UPLOAD_003", size_mb=size / 1024 / 1024))

        return issues
