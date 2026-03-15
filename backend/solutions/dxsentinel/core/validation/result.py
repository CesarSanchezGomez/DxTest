"""Modelos de datos para resultados de validacion."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    """Nivel de severidad de un problema de validacion.

    WARNING  - Permite continuar (split posible).
    ERROR    - No permite continuar con el split.
    FATAL    - Invalida la estructura completa; detiene el pipeline.
    """

    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"

    def __lt__(self, other: Severity) -> bool:
        return _SEVERITY_ORDER[self] < _SEVERITY_ORDER[other]

    def __le__(self, other: Severity) -> bool:
        return _SEVERITY_ORDER[self] <= _SEVERITY_ORDER[other]


_SEVERITY_ORDER = {Severity.WARNING: 0, Severity.ERROR: 1, Severity.FATAL: 2}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Un problema individual detectado por un validador."""

    severity: Severity
    code: str
    message: str
    element_id: Optional[str] = None
    field_id: Optional[str] = None
    country_code: Optional[str] = None
    validator: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "element_id": self.element_id,
            "field_id": self.field_id,
            "country_code": self.country_code,
            "validator": self.validator,
        }


@dataclass
class ValidationReport:
    """Coleccion de resultados de validacion con helpers de consulta."""

    results: list[ValidationResult] = field(default_factory=list)

    # ── Propiedades rapidas ──────────────────────────────────────────────

    @property
    def has_fatal(self) -> bool:
        return any(r.severity == Severity.FATAL for r in self.results)

    @property
    def has_errors(self) -> bool:
        return any(r.severity == Severity.ERROR for r in self.results)

    @property
    def can_continue(self) -> bool:
        """True si no hay fatals (warnings y errors permiten generar)."""
        return not self.has_fatal

    @property
    def can_split(self) -> bool:
        """True si no hay fatals ni errors."""
        return not self.has_fatal and not self.has_errors

    @property
    def count(self) -> int:
        return len(self.results)

    # ── Filtros ──────────────────────────────────────────────────────────

    def by_severity(self, severity: Severity) -> list[ValidationResult]:
        return [r for r in self.results if r.severity == severity]

    def by_element(self, element_id: str) -> list[ValidationResult]:
        return [r for r in self.results if r.element_id == element_id]

    def by_country(self, country_code: str) -> list[ValidationResult]:
        return [r for r in self.results if r.country_code == country_code]

    # ── Mutacion ─────────────────────────────────────────────────────────

    def add(self, result: ValidationResult) -> None:
        self.results.append(result)

    def extend(self, results: list[ValidationResult]) -> None:
        self.results.extend(results)

    def merge(self, other: ValidationReport) -> None:
        self.results.extend(other.results)

    # ── Serialization ────────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "total": self.count,
            "fatal": len(self.by_severity(Severity.FATAL)),
            "error": len(self.by_severity(Severity.ERROR)),
            "warning": len(self.by_severity(Severity.WARNING)),
            "can_continue": self.can_continue,
            "can_split": self.can_split,
        }

    def to_dict(self) -> dict:
        return {
            "summary": self.summary(),
            "issues": [r.to_dict() for r in self.results],
        }
