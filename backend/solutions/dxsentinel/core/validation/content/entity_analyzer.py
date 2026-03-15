"""Analisis de entidades para validacion de completitud.

Determina si una entidad esta vacia por fila o globalmente,
y obtiene los campos required por entidad.
"""

from __future__ import annotations

from collections import defaultdict


class EntityAnalyzer:
    """Analiza entidades del field_catalog para reglas de completitud."""

    def __init__(self, field_catalog: dict):
        self.field_catalog = field_catalog
        self._entity_fields_cache: dict[str, list[str]] | None = None

    def get_entity_fields(self) -> dict[str, list[str]]:
        """Agrupa columnas por entity_id."""
        if self._entity_fields_cache is not None:
            return self._entity_fields_cache

        entity_fields: dict[str, list[str]] = defaultdict(list)
        for column, meta in self.field_catalog.items():
            entity_id = meta.get("element", "")
            if entity_id:
                entity_fields[entity_id].append(column)

        self._entity_fields_cache = dict(entity_fields)
        return self._entity_fields_cache

    def is_entity_empty_for_row(self, row: dict, entity_id: str) -> bool:
        """True si TODOS los campos de la entidad estan vacios en esta fila."""
        columns = self.get_entity_fields().get(entity_id, [])
        if not columns:
            return True
        return all(self._is_value_empty(row.get(col)) for col in columns)

    def is_entity_empty_globally(self, csv_data: list[dict], entity_id: str) -> bool:
        """True si TODOS los campos de la entidad estan vacios en TODAS las filas."""
        columns = self.get_entity_fields().get(entity_id, [])
        if not columns:
            return True
        for row in csv_data:
            for col in columns:
                if not self._is_value_empty(row.get(col)):
                    return False
        return True

    def get_required_fields_for_entity(self, entity_id: str) -> list[str]:
        """Columnas required dentro de una entidad."""
        columns = self.get_entity_fields().get(entity_id, [])
        return [
            col for col in columns
            if self.field_catalog.get(col, {}).get("required", False)
        ]

    @staticmethod
    def _is_value_empty(value) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False
