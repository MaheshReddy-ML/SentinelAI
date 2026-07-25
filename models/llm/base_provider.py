from abc import ABC, abstractmethod

from schemas.request import FinancialRequest


class RequestProvider(ABC):
    """Converts natural-language input into a validated request, never a decision."""

    @abstractmethod
    def generate_request(self, prompt: str) -> FinancialRequest:
        """Return a validated request or raise a structured provider error."""
