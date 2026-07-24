from abc import ABC, abstractmethod

from schemas.decision import Decision
from schemas.expert_output import ExpertOutput


class BaseAggregator(ABC):
    """
    Abstract base class for all aggregation strategies.
    """

    @abstractmethod
    def aggregate(
        self,
        expert_outputs: list[ExpertOutput],
    ) -> Decision:
        """
        Aggregate multiple expert outputs into
        a final governance decision.
        """
        pass