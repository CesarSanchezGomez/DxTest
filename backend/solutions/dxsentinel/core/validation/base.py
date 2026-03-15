"""Clases base y contexto de validacion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from .result import Severity, ValidationResult
from .messages import Messages


@dataclass
class ValidationContext:
    """Datos compartidos entre todos los validadores."""

    parsed_model: dict
    processed_data: dict
    columns: list[dict]
    field_catalog: dict
    target_countries: Optional[list[str]] = None
    format_groups: dict = field(default_factory=dict)
    language_code: str = "en-us"
    upload_filename: Optional[str] = None
    upload_size_bytes: Optional[int] = None

    # ── Datos CSV (solo para validacion pre-split) ───────────────────────
    csv_headers: list[str] = field(default_factory=list)
    """IDs de columnas del CSV (fila 1)."""

    csv_rows: list[dict] = field(default_factory=list)
    """Filas de datos del CSV como [{field_id: value}, ...]."""

    mode: str = "generation"
    """Modo de validacion: 'generation' (XML) o 'split' (CSV)."""

    def get_entity_analyzer(self):
        """EntityAnalyzer cacheado para reusar entre validators."""
        if not hasattr(self, "_entity_analyzer"):
            from .content.entity_analyzer import EntityAnalyzer
            self._entity_analyzer = EntityAnalyzer(self.field_catalog)
        return self._entity_analyzer

    def get_empty_entities_global(self) -> set:
        """Entidades vacias globalmente, cacheadas."""
        if not hasattr(self, "_empty_entities_global"):
            analyzer = self.get_entity_analyzer()
            self._empty_entities_global = {
                eid for eid in analyzer.get_entity_fields()
                if analyzer.is_entity_empty_globally(self.csv_rows, eid)
            }
        return self._empty_entities_global


class BaseValidator(ABC):
    """Contrato base con helper para emitir resultados."""

    # Sobreescribir en subclases para restringir el modo
    modes: tuple[str, ...] = ("generation", "split")

    @abstractmethod
    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        """Retorna lista de problemas (vacia si todo OK)."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _emit(
        self,
        severity: Severity,
        code: str,
        *,
        element_id: str | None = None,
        field_id: str | None = None,
        country_code: str | None = None,
        row_index: int | None = None,
        column_name: str | None = None,
        person_id: str | None = None,
        value: str | None = None,
        **msg_kwargs: object,
    ) -> ValidationResult:
        """Crea un ValidationResult usando el catalogo de mensajes."""
        all_kwargs = {
            "element_id": element_id or "",
            "field_id": field_id or "",
            "country_code": country_code or "",
            **msg_kwargs,
        }
        return ValidationResult(
            severity=severity,
            code=code,
            message=Messages.get(code, **all_kwargs),
            element_id=element_id,
            field_id=field_id,
            country_code=country_code,
            validator=self.name,
            row_index=row_index,
            column_name=column_name,
            person_id=person_id,
            value=value[:50] if value else value,
        )
