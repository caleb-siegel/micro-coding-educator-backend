from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_lesson(self, topic: str, difficulty: str = "Foundational", duration_minutes: int = 5) -> Dict[str, Any]:
        """Generate a complete structured interactive lesson deck for the given topic, difficulty, and target duration."""
        pass
