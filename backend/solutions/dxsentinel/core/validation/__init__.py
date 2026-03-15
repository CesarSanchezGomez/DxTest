"""Sistema de validacion de DxSentinel.

Uso:
    from .validation import validate, ValidationEngine, ValidationContext
    from .validation.result import Severity, ValidationReport
"""

from .engine import ValidationEngine
from .result import Severity, ValidationReport, ValidationResult
from .validators.base import ValidationContext

__all__ = [
    "ValidationEngine",
    "ValidationContext",
    "ValidationReport",
    "ValidationResult",
    "Severity",
    "validate",
]


def validate(
    parsed_model: dict,
    processed_data: dict,
    columns: list[dict],
    field_catalog: dict,
    target_countries: list[str] | None = None,
    format_groups: dict | None = None,
    language_code: str = "en-us",
) -> ValidationReport:
    """Atajo para ejecutar todas las validaciones."""
    ctx = ValidationContext(
        parsed_model=parsed_model,
        processed_data=processed_data,
        columns=columns,
        field_catalog=field_catalog,
        target_countries=target_countries,
        format_groups=format_groups or {},
        language_code=language_code,
    )
    return ValidationEngine().validate(ctx)
