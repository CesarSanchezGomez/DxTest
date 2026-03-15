from abc import ABC, abstractmethod
from typing import List, Any
from ...models.validation_error import ValidationError


class BaseValidator(ABC):

    @abstractmethod
    def validate(self, data: Any, context: dict) -> List[ValidationError]:
        pass
