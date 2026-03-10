class GoldenRecordError(Exception):
    """Error base para generación de Golden Record."""
    pass


class ElementNotFoundError(GoldenRecordError):
    """Error cuando no se encuentran elementos esperados."""
    pass


class FieldFilterError(GoldenRecordError):
    """Error en el filtrado de campos."""
    pass
