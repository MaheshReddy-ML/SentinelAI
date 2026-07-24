from abc import ABC, abstractmethod

from schemas.decision import Decision


class BaseExplainer(ABC):
    """
    Abstract base class for all explanation engines.
    """

    @abstractmethod
    def explain(
        self,
        decision: Decision,
    ) -> str:
        """
        Generate a human-readable explanation
        for a governance decision.
        """
        pass