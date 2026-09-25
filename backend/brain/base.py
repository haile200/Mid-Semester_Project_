from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ToxicityResult:
    allowed: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class GeneratedPost:
    title: str
    body: str


class Brain(ABC):
    """The contract every AI provider implements. Callers depend on this class, never on a provider.

    All text going in and coming out is plain text; callers handle HTML.
    """

    @abstractmethod
    def suggest_correction(self, text: str) -> str:
        """Returns the text with spelling and capitalization fixed."""

    @abstractmethod
    def propose_comments(self, post_title: str, post_body: str) -> List[str]:
        """Returns three short comment ideas for a post."""

    @abstractmethod
    def check_toxicity(self, text: str) -> ToxicityResult:
        """Decides whether the text may be published."""

    @abstractmethod
    def write_post(self, personality: str, seed: int) -> GeneratedPost:
        """Writes a post in the voice of the personality. The caller supplies the randomness via seed."""

    @abstractmethod
    def write_reply(self, personality: str, context: str, seed: int) -> str:
        """Writes a reply to the context text in the voice of the personality."""
