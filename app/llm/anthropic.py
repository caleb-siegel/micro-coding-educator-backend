import os
import json
import logging
from typing import Dict, Any
import requests
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

CLAUDE_PROMPT = """You are an expert Senior Software Engineer and Product Educator.
Generate a high-quality interactive learning deck for software engineers on TOPIC and DIFFICULTY.

If DIFFICULTY is 'Foundational' (🟢 Intro):
- Tailor content specifically for Junior Developers and beginners.
- Use friendly, welcoming tone with zero gatekeeping jargon.
- Use intuitive, everyday real-world analogies (e.g. comparing a cache to a sticky note, a load balancer to a restaurant host, or an API to a menu).
- Focus on "Why do we use this?" and core benefits.

Return ONLY valid JSON matching this schema:
{
  "id": "lesson-id",
  "title": "Short Lesson Title",
  "topic": "Topic Name",
  "difficulty": "Foundational",
  "durationMinutes": 5,
  "subtitle": "Short Subtitle",
  "cards": [
    { "type": "hook", "headline": "...", "body": "...", "statBadge": {"label": "...", "value": "..."}, "simpleExplanation": "..." },
    { "type": "multiple_choice", "question": "...", "options": [{"id": "1", "text": "...", "isCorrect": true, "explanation": "..."}], "hint": "...", "simpleExplanation": "..." },
    { "type": "build_the_system", "task": "...", "availableBlocks": [{"id": "b1", "label": "...", "icon": "Layers"}], "targetSlots": [{"slotId": "s1", "label": "...", "correctBlockId": "b1"}], "explanation": "..." },
    { "type": "takeaway", "oneSentenceSummary": "...", "keyInsights": ["..."], "suggestedNextTopic": "System Design" }
  ]
}
No markdown wrappers around the JSON.
"""

class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    async def generate_lesson(self, topic: str, difficulty: str = "Foundational", duration_minutes: int = 5) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found. Using Anthropic fallback generator.")
            return self._fallback_lesson(topic, difficulty, duration_minutes)

        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": self.model,
                "max_tokens": 1500,
                "system": CLAUDE_PROMPT,
                "messages": [
                    {"role": "user", "content": f"TOPIC: {topic}\nDIFFICULTY: {difficulty}\nDURATION: {duration_minutes} minutes"}
                ]
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                text = data["content"][0]["text"]
                return json.loads(text)
            else:
                logger.error(f"Anthropic API returned status {resp.status_code}: {resp.text}")
                return self._fallback_lesson(topic, difficulty, duration_minutes)

        except Exception as e:
            logger.error(f"AnthropicProvider exception: {e}")
            return self._fallback_lesson(topic, difficulty, duration_minutes)

    def _fallback_lesson(self, topic: str, difficulty: str, duration_minutes: int = 5) -> Dict[str, Any]:
        t = topic.strip().capitalize()
        return {
            "id": f"claude-fallback-{t.lower()}",
            "title": f"Claude Analysis: {t}",
            "topic": t,
            "difficulty": difficulty,
            "durationMinutes": duration_minutes,
            "subtitle": f"Anthropic-style micro-challenge for {t}",
            "cards": [
                {
                    "id": "c-1",
                    "type": "hook",
                    "headline": f"Understanding {t} at a fundamental architectural level.",
                    "body": f"Mastering {t} helps engineers avoid unexpected production outages and optimize latency.",
                    "statBadge": {"label": "Claude AI", "value": "Optimized"},
                    "iconName": "Sparkles",
                    "simpleExplanation": f"{t} organizes system components so that data flows cleanly with minimal overhead."
                },
                {
                    "id": "c-2",
                    "type": "multiple_choice",
                    "question": f"What is the key trade-off when adopting {t}?",
                    "hint": f"Think about initial complexity vs long-term scalability of {t}.",
                    "simpleExplanation": f"{t} exchanges a small amount of upfront setup complexity for massive long-term reliability.",
                    "options": [
                        {
                            "id": "co-1",
                            "text": f"Higher initial modularity for scalable throughput in {t}",
                            "isCorrect": True,
                            "explanation": f"Correct! {t} pays upfront design cost to achieve high resilience under traffic spikes."
                        },
                        {
                            "id": "co-2",
                            "text": "Requires shutting down all database servers permanently",
                            "isCorrect": False,
                            "explanation": "Databases remain essential for state storage."
                        }
                    ]
                },
                {
                    "id": "c-3",
                    "type": "takeaway",
                    "oneSentenceSummary": f"Claude Recommendation: Leverage {t} to design bulletproof software systems.",
                    "keyInsights": [
                        f"Implement {t} with clear component boundaries.",
                        "Benchmark key metrics under realistic synthetic traffic before deploying."
                    ],
                    "suggestedNextTopic": "Security"
                }
            ]
        }
