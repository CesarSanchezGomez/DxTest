"""Validacion de archivos de upload → FATAL.

Integra las validaciones que se hacian en router.py (file type, size, empty)
como parte del sistema de validacion formal para que queden registradas
en el reporte.
"""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

MAX_XML_UPLOAD_SIZE = 50 * 1024 * 1024   # 50 MB
MAX_CSV_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB


@register_validator
class UploadValidator(BaseValidator):
    """Verifica restricciones del archivo subido → FATAL."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        filename = ctx.upload_filename
        size = ctx.upload_size_bytes

        if not filename:
            return issues

        self._check_file_extension(filename, issues)
        if size is not None:
            self._check_file_size(filename, size, issues)

        return issues

    def _check_file_extension(self, filename: str, issues: list[ValidationResult]) -> None:
        lower = filename.lower()
        if not (lower.endswith(".xml") or lower.endswith(".csv")):
            issues.append(ValidationResult(
                severity=Severity.FATAL,
                code="UPLOAD_001",
                message=f"Tipo de archivo no soportado: '{filename}'. Solo XML y CSV.",
                validator=self.name,
            ))

    def _check_file_size(self, filename: str, size: int, issues: list[ValidationResult]) -> None:
        lower = filename.lower()
        if lower.endswith(".xml") and size > MAX_XML_UPLOAD_SIZE:
            issues.append(ValidationResult(
                severity=Severity.FATAL,
                code="UPLOAD_002",
                message=f"Archivo XML excede limite de 50MB ({size / 1024 / 1024:.1f}MB)",
                validator=self.name,
            ))
        elif lower.endswith(".csv") and size > MAX_CSV_UPLOAD_SIZE:
            issues.append(ValidationResult(
                severity=Severity.FATAL,
                code="UPLOAD_003",
                message=f"Archivo CSV excede limite de 100MB ({size / 1024 / 1024:.1f}MB)",
                validator=self.name,
            ))
