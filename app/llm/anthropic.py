import os
import json
import logging
import re
from typing import Dict, Any, List
import requests
from fastapi import HTTPException
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

def format_sharp_summary(text: str, max_sentences: int = 3) -> str:
    text = text.strip()
    if not text:
        return ""

    lines = [l for l in text.split("\n") if not l.strip().lower().startswith(("rule", "constraint", "* constraint", "**rule", "format rule", "system instruction", "instruction:"))]
    cleaned_text = " ".join(lines).strip()

    sentence_pattern = re.compile(r'([^.!?]+[.!?])', re.DOTALL)
    matches = sentence_pattern.findall(cleaned_text)

    if matches:
        selected = matches[:max_sentences]
        return " ".join([s.strip() for s in selected])
    return cleaned_text


class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    async def generate_lesson(self, topic: str, difficulty: str = "Foundational", duration_minutes: int = 5) -> Dict[str, Any]:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY is not configured in backend/.env. Lesson generation data is currently unavailable."
            )

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
                raise HTTPException(
                    status_code=resp.status_code if 400 <= resp.status_code < 600 else 500,
                    detail=f"Anthropic API returned error ({resp.status_code}): {resp.text}"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AnthropicProvider exception: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate lesson via Anthropic API: {str(e)}"
            )

    async def ask_card_question(self, lesson_topic: str, difficulty: str, card_context: Dict[str, Any], messages: List[Dict[str, str]], user_prompt: str) -> str:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY is not configured in backend/.env. AI Chat assistance is currently unavailable."
            )

        system_instruction = f"""You are an expert Senior Software Engineer tutoring a developer on an interactive coding card.
LESSON TOPIC: {lesson_topic} ({difficulty} Level)
CARD CONTEXT: {json.dumps(card_context)}

INSTRUCTION: Answer the student's question directly in a single friendly paragraph (2 to 4 sentences). Keep your answer brief, high-level, and easy to digest. Never output headers, bullet lists, rule quotes, or meta-commentary. If the concept needs more technical detail, end your paragraph with: "Feel free to ask if you'd like more details!"
"""

        claude_messages = []
        for msg in (messages or []):
            role = "user" if msg.get("role") == "user" else "assistant"
            claude_messages.append({"role": role, "content": msg.get("content", "")})

        claude_messages.append({"role": "user", "content": user_prompt})

        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": self.model,
                "max_tokens": 800,
                "system": system_instruction,
                "messages": claude_messages
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["content"][0]["text"].strip()
                return format_sharp_summary(raw_text, max_sentences=3)
            else:
                logger.error(f"Anthropic Chat API returned status {resp.status_code}: {resp.text}")
                raise HTTPException(
                    status_code=resp.status_code if 400 <= resp.status_code < 600 else 500,
                    detail=f"Anthropic API error ({resp.status_code}): {resp.text}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Anthropic ask_card_question exception: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with Anthropic API: {str(e)}"
            )

    async def generate_cards(self, topic: str, difficulty: str = "Foundational", count: int = 2, seen_titles: List[str] = None, include_hook: bool = False) -> List[Dict[str, Any]]:
        lesson = await self.generate_lesson(topic, difficulty, 5)
        return lesson.get("cards", [])[:count]


