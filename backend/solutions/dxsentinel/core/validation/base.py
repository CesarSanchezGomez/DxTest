"""Clases base y contexto de validacion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from .result import ValidationResult


@dataclass
class ValidationContext:
    """Datos compartidos entre todos los validadores.

    Se construye una sola vez y se pasa a cada validador para evitar
    recalcular o duplicar acceso a datos.
    """

    parsed_model: dict
    """Modelo XML normalizado (output del parser)."""

    processed_data: dict
    """Output de ElementProcessor.process_model()."""

    columns: list[dict]
    """Columnas consolidadas del CSV."""

    field_catalog: dict
    """Catalogo de campos (output de MetadataGenerator)."""

    target_countries: Optional[list[str]] = None
    """Paises objetivo (None = todos)."""

    format_groups: dict = field(default_factory=dict)
    """Reglas de formato por pais (country_code -> groups)."""

    language_code: str = "en-us"
    """Idioma solicitado para labels."""

    upload_filename: Optional[str] = None
    """Nombre del archivo subido (para validaciones de upload)."""

    upload_size_bytes: Optional[int] = None
    """Tamano del archivo subido en bytes."""


class BaseValidator(ABC):
    """Contrato que todo validador debe cumplir."""

    @abstractmethod
    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        """Ejecuta las validaciones y retorna problemas encontrados.

        Retorna lista vacia si todo esta OK.
        """

    @property
    def name(self) -> str:
        return self.__class__.__name__
