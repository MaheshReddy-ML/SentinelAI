from abc import ABC, abstractmethod

from schemas.enums import ExpertType
from schemas.request import FinancialRequest
from schemas.expert_output import ExpertOutput


class BaseExpert(ABC):
    """
    Abstract base class for all governance experts.
    Every expert must inherit from this class.
    """

    @property
    @abstractmethod
    def expert_type(self) -> ExpertType:
        """
        Returns the type of the expert.
        """
        pass

    @abstractmethod
    def evaluate(
        self,
        request: FinancialRequest,
    ) -> ExpertOutput:
        """
        Evaluates a financial request and returns an ExpertOutput.
        """
        pass