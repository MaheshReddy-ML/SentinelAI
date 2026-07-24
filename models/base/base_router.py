from abc import ABC, abstractmethod

from schemas.request import FinancialRequest

from models.base.base_expert import BaseExpert


class BaseRouter(ABC):
    """
    Abstract base class for all routing strategies.
    """

    @abstractmethod
    def route(
        self,
        request: FinancialRequest,
    ) -> list[BaseExpert]:
        """
        Select and return the experts that should
        evaluate the given request.
        """
        pass