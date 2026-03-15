"""Sistema de validacion de DxSentinel.

Estructura:
    validation/
        structure/              → FATAL (csv_structure_validator + sub-validators)
        content/                → ERROR/WARNING (golden_record_validator + sub-validators)
            country/
                mex/            → Mexico: curp, work_permit (RFC/NSS)

Uso:
    from .validation import validate_csv
    from .validation.result import Severity, ValidationReport
"""

from .result import Severity, ValidationReport, ValidationResult
from .models.error_severity import ErrorSeverity
from .structure.csv_structure_validator import CsvStructureValidator
from .content.golden_record_validator import GoldenRecordValidator

__all__ = [
    "ValidationReport",
    "ValidationResult",
    "Severity",
    "validate_csv",
]

# Mapeo ErrorSeverity (interno) → Severity (API)
_SEVERITY_MAP = {
    ErrorSeverity.FATAL: Severity.FATAL,
    ErrorSeverity.ERROR: Severity.ERROR,
    ErrorSeverity.WARNING: Severity.WARNING,
}


def _convert_error(err) -> ValidationResult:
    """Convierte un ValidationError interno a ValidationResult para la API."""
    return ValidationResult(
        severity=_SEVERITY_MAP[err.severity],
        code=err.code,
        message=err.message,
        element_id=err.entity_id,
        field_id=err.field_id,
        row_index=err.row_index,
        column_name=err.column_name,
        person_id=err.person_id,
        value=err.value,
    )


def validate_csv(
    csv_headers: list[str],
    csv_rows: list[dict],
    field_catalog: dict,
    target_countries: list[str] | None = None,
    format_groups: dict | None = None,
    language_code: str = "en-us",
) -> ValidationReport:
    """Valida datos CSV antes del split.

    Ejecuta validacion de contenido sobre los datos ya parseados
    (headers como list[str], rows como list[dict]).
    """
    report = ValidationReport()

    metadata = {
        "field_catalog": field_catalog,
        "country_codes": target_countries or [],
        "format_groups": format_groups or {},
        "language_code": language_code,
    }

    # ── Validacion de contenido ───────────────────────────────────────
    content_validator = GoldenRecordValidator(metadata)
    content_errors = content_validator.validate(csv_rows, csv_headers)
    report.extend([_convert_error(e) for e in content_errors])

    return report


def validate_csv_file(
    file_content: str,
    field_catalog: dict,
    target_countries: list[str] | None = None,
    format_groups: dict | None = None,
    language_code: str = "en-us",
) -> ValidationReport:
    """Valida un archivo CSV completo (estructura + contenido).

    Recibe el contenido raw del CSV como string.
    Ejecuta primero validacion de estructura y luego de contenido.
    """
    import csv
    import io

    report = ValidationReport()

    metadata = {
        "field_catalog": field_catalog,
        "country_codes": target_countries or [],
        "format_groups": format_groups or {},
        "language_code": language_code,
    }

    # ── Fase 1: Validacion de estructura ──────────────────────────────
    structure_validator = CsvStructureValidator(metadata)
    is_valid, structure_errors = structure_validator.validate_structure(file_content)
    report.extend([_convert_error(e) for e in structure_errors])

    if not is_valid:
        return report

    # ── Fase 2: Parsear CSV ───────────────────────────────────────────
    normalized = file_content.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.strip().split("\n")

    if len(lines) < 3:
        return report

    headers_line = lines[0]
    data_lines = lines[2:]  # Skip labels row
    csv_content = "\n".join([headers_line] + data_lines)

    reader = csv.DictReader(io.StringIO(csv_content))
    csv_headers = reader.fieldnames or []
    csv_rows = [
        row for row in reader
        if any(v and str(v).strip() for v in row.values())
    ]

    if not csv_headers:
        return report

    # ── Fase 3: Validacion de contenido ───────────────────────────────
    content_validator = GoldenRecordValidator(metadata)
    content_errors = content_validator.validate(csv_rows, csv_headers)
    report.extend([_convert_error(e) for e in content_errors])

    return report
