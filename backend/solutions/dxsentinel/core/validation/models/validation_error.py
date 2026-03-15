from dataclasses import dataclass
from typing import Optional
from .error_severity import ErrorSeverity


@dataclass
class ValidationError:
    code: str
    message: str
    severity: ErrorSeverity
    row_index: Optional[int] = None
    column_index: Optional[int] = None
    column_name: Optional[str] = None
    entity_id: Optional[str] = None
    field_id: Optional[str] = None
    person_id: Optional[str] = None
    value: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "row_index": self.row_index,
            "column_index": self.column_index,
            "column_name": self.column_name,
            "entity": self.entity_id,
            "field": self.column_name or self.field_id,
            "person_id": self.person_id,
            "value": self.value
        }
