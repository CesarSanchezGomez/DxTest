from collections import defaultdict
from typing import List, Dict, Optional
from ...models.validation_error import ValidationError
from ...models.error_severity import ErrorSeverity
from ..messages import ContentMessages

# Posibles nombres de la columna de ID de persona (orden de prioridad)
_PERSON_ID_CANDIDATES = [
    "personInfo_person-id-external",
    "personalInfo_person-id-external",
]
_PERSON_ID_FIELD_SUFFIX = "person-id-external"
_MULTI_VALUE_DELIMITER = "|"


def _resolve_person_id_column(headers: List[str]) -> Optional[str]:
    """Devuelve el nombre real de la columna person-id-external en este CSV."""
    for candidate in _PERSON_ID_CANDIDATES:
        if candidate in headers:
            return candidate
    # Búsqueda flexible: cualquier columna que termine con el sufijo esperado
    for header in headers:
        if header.endswith(_PERSON_ID_FIELD_SUFFIX):
            return header
    return None


def _extract_id(raw_value) -> Optional[str]:
    """Extrae el primer valor de una celda (ignora multi-valor con |)."""
    if raw_value is None:
        return None
    val = str(raw_value).strip()
    if not val:
        return None
    if _MULTI_VALUE_DELIMITER in val:
        val = val.split(_MULTI_VALUE_DELIMITER)[0].strip()
    return val or None


class DuplicatePersonIdValidator:
    """
    Valida que no existan registros duplicados en el Golden Record,
    usando personInfo_person-id-external como clave única.

    Opera sobre todas las filas a la vez (validación cross-row).
    Devuelve un error FATAL por cada fila donde aparezca el ID duplicado.
    """

    def validate(self, rows: List[Dict], headers: List[str]) -> List[ValidationError]:
        column = _resolve_person_id_column(headers)

        if column is None:
            # Si no existe la columna, no hay nada que validar
            return []

        entity_id, _, field_id = column.partition("_")

        # Paso 1: agrupar row_indices por person-id-external
        seen: Dict[str, List[int]] = defaultdict(list)
        for row_idx, row in enumerate(rows):
            pid = _extract_id(row.get(column))
            if pid:
                seen[pid].append(row_idx + 3)  # +3: fila 1=headers, 2=labels

        # Paso 2: generar un error FATAL por cada fila de cada ID duplicado
        errors: List[ValidationError] = []
        for person_id, row_indices in seen.items():
            if len(row_indices) < 2:
                continue
            for row_index in row_indices:
                errors.append(ValidationError(
                    code="DUPLICATE_PERSON_ID",
                    message=ContentMessages.duplicate_person_id(person_id, row_indices),
                    severity=ErrorSeverity.FATAL,
                    row_index=row_index,
                    column_name=column,
                    entity_id=entity_id,
                    field_id=field_id,
                    person_id=person_id,
                    value=person_id
                ))

        return errors
