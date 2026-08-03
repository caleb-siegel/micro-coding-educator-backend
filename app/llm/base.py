from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_lesson(self, topic: str, difficulty: str = "Foundational", duration_minutes: int = 5) -> Dict[str, Any]:
        """Generate a complete structured interactive lesson deck for the given topic, difficulty, and target duration."""
        pass

    @abstractmethod
    async def ask_card_question(self, lesson_topic: str, difficulty: str, card_context: Dict[str, Any], messages: List[Dict[str, str]], user_prompt: str) -> str:
        """Answer a user question specific to the given card context and conversation thread."""
        pass

    @abstractmethod
    async def generate_cards(self, topic: str, difficulty: str = "Foundational", count: int = 2, seen_titles: List[str] = None, include_hook: bool = False) -> List[Dict[str, Any]]:
        """Generate a batch of interactive cards for a topic and difficulty."""
        pass


