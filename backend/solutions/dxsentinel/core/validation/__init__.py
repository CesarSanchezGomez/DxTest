"""Sistema de validacion de DxSentinel.

Estructura:
    validation/
        structure/      → FATAL (xml_structure, character, upload)
        content/        → ERROR/WARNING (field_rules, field_filter, label, format_group)
        country/        → ERROR por pais (mx, ...)

Uso:
    from .validation import validate, ValidationEngine, ValidationContext
    from .validation.result import Severity, ValidationReport
"""

from .engine import ValidationEngine
from .result import Severity, ValidationReport, ValidationResult
from .base import ValidationContext

__all__ = [
    "ValidationEngine",
    "ValidationContext",
    "ValidationReport",
    "ValidationResult",
    "Severity",
    "validate",
    "validate_csv",
]


def validate(
    parsed_model: dict,
    processed_data: dict,
    columns: list[dict],
    field_catalog: dict,
    target_countries: list[str] | None = None,
    format_groups: dict | None = None,
    language_code: str = "en-us",
    upload_filename: str | None = None,
    upload_size_bytes: int | None = None,
) -> ValidationReport:
    """Atajo para ejecutar todas las validaciones (modo generation)."""
    ctx = ValidationContext(
        parsed_model=parsed_model,
        processed_data=processed_data,
        columns=columns,
        field_catalog=field_catalog,
        target_countries=target_countries,
        format_groups=format_groups or {},
        language_code=language_code,
        upload_filename=upload_filename,
        upload_size_bytes=upload_size_bytes,
        mode="generation",
    )
    return ValidationEngine().validate(ctx)


def validate_csv(
    csv_headers: list[str],
    csv_rows: list[dict],
    field_catalog: dict,
    target_countries: list[str] | None = None,
    format_groups: dict | None = None,
    language_code: str = "en-us",
) -> ValidationReport:
    """Atajo para validar datos CSV antes del split (modo split)."""
    ctx = ValidationContext(
        parsed_model={},
        processed_data={},
        columns=[],
        field_catalog=field_catalog,
        target_countries=target_countries,
        format_groups=format_groups or {},
        language_code=language_code,
        csv_headers=csv_headers,
        csv_rows=csv_rows,
        mode="split",
    )
    return ValidationEngine().validate(ctx)
