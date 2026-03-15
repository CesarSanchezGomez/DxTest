from typing import List


class StructureMessages:

    @staticmethod
    def invalid_file_extension(filename: str) -> str:
        return f"Debe ser .csv (recibido: {filename})"

    @staticmethod
    def empty_file() -> str:
        return "El archivo está vacío"

    @staticmethod
    def empty_rows_before_headers(count: int) -> str:
        return f"{count} {'fila vacía' if count == 1 else 'filas vacías'} antes de los headers"

    @staticmethod
    def csv_parse_error(detail: str) -> str:
        return f"Error al parsear CSV: {detail}"

    @staticmethod
    def empty_column_id(position: int) -> str:
        return f"Columna {position} sin id"

    @staticmethod
    def empty_label_name(position: int) -> str:
        return f"Columna {position} sin etiqueta"

    @staticmethod
    def invalid_column_format(column_name: str, position: int) -> str:
        return f"Formato inválido. Debe ser: entidad_campo (ej: personInfo_first-name)"

    @staticmethod
    def duplicate_column(column_name: str, positions: List[int]) -> str:
        pos_str = ', '.join(map(str, positions))
        return f"Columnas duplicadas: {pos_str}"

    @staticmethod
    def missing_columns(entity: str, columns: List[str], count: int) -> str:
        cols_display = ', '.join(columns[:5])
        if count > 5:
            cols_display += f'... (+{count - 5})'
        return f"Faltan {count}: {cols_display}"

    @staticmethod
    def unexpected_columns(columns: List[str], count: int) -> str:
        cols_display = ', '.join(columns[:3])
        if count > 3:
            cols_display += f'... (+{count - 3})'
        return f"No están en metadata: {cols_display}"

    @staticmethod
    def label_column_mismatch(expected: int, actual: int) -> str:
        return f"Labels tiene {actual} columnas, esperadas {expected}"

    @staticmethod
    def missing_label_row() -> str:
        return "No se encontró la fila de etiquetas (fila 2) o existe una fila vacía entre los headers y las etiquetas."

    @staticmethod
    def row_column_mismatch(row: int, expected: int, actual: int) -> str:
        return f"Tiene {actual} columnas, esperadas {expected}"

    @staticmethod
    def encoding_error() -> str:
        return "Codificación no soportada. Guarda como UTF-8"

    @staticmethod
    def insufficient_rows(found: int) -> str:
        return f"Solo {found} {'fila' if found == 1 else 'filas'}. Mínimo requerido: 2 (headers + labels)"

    @staticmethod
    def invalid_characters_in_cell(chars: str, cell_preview: str) -> str:
        return f"Caracteres inválidos {chars} en: '{cell_preview}'. Problema de encoding"

    @staticmethod
    def suspicious_encoding_in_cell(chars: str, cell_preview: str) -> str:
        return f"Caracteres sospechosos {chars} en: '{cell_preview}'. Posible problema de encoding"
