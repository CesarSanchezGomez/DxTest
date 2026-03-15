from abc import ABC, abstractmethod
from typing import List, Any, Dict
from ...models.validation_error import ValidationError


class BaseContentValidator(ABC):

    @abstractmethod
    def validate(self, value: Any, context: Dict) -> List[ValidationError]:
        pass
