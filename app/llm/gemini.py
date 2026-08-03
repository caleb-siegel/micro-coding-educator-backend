import os
import json
import random
import logging
from typing import Dict, Any, List
import requests
from fastapi import HTTPException
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

INTERACTIVE_CARD_POOL = [
    "multiple_choice",
    "spot_the_mistake",
    "choose_the_tradeoff",
    "build_the_system",
    "predict_what_happens",
    "before_vs_after",
    "guess_the_metric",
    "timeline",
    "drag_to_order",
    "match_pairs",
    "debug_session"
]

def build_cards_prompt(topic: str, difficulty: str, count: int, seen_titles: List[str] = None, include_hook: bool = False) -> str:
    selected_types = random.sample(INTERACTIVE_CARD_POOL, min(count, len(INTERACTIVE_CARD_POOL)))
    card_sequence_instructions = []
    start_idx = 1
    if include_hook:
        card_sequence_instructions.append("Card 1: type 'hook' (headline, body, statBadge: {label, value}, simpleExplanation)")
        start_idx = 2
        interactive_types = selected_types[:count-1]
    else:
        interactive_types = selected_types[:count]

    for idx, c_type in enumerate(interactive_types):
        card_sequence_instructions.append(f"Card {start_idx + idx}: type '{c_type}'")

    seq_str = "\n".join(card_sequence_instructions)

    seen_guidance = ""
    if seen_titles and len(seen_titles) > 0:
        seen_str = "\n".join([f"- {t}" for t in seen_titles[-10:]])
        seen_guidance = f"\nALREADY COVERED TOPICS/QUESTIONS (DO NOT REPEAT OR DUPLICATE THESE CONCEPTS):\n{seen_str}\n"

    difficulty_guidance = ""
    if "foundational" in difficulty.lower() or "intro" in difficulty.lower():
        difficulty_guidance = """
DIFFICULTY LEVEL GUIDANCE — 'Foundational' (🟢 Intro / Junior Developer Level):
- TARGET AUDIENCE: Junior Developers, Bootcamp graduates, or engineers completely new to this topic.
- TONE & PEDAGOGY: Extremely welcoming, intuitive, clear, and friendly.
- NO HEAVY JARGON: Avoid intimidating acronyms without immediate plain-English explanations.
- REAL-WORLD ANALOGIES: Use everyday intuitive ELI5 analogies (e.g. comparing a cache to a sticky note on a desk, a load balancer to a restaurant host, or an API to a menu).
- QUESTIONS: Focus on fundamental "Why do we use this?" and "What is the core benefit?" rather than complex failure modes.
"""
    elif "staff" in difficulty.lower() or "deep" in difficulty.lower():
        difficulty_guidance = """
DIFFICULTY LEVEL GUIDANCE — 'Staff Level' (🔴 Deep / Principal Engineer):
- TARGET AUDIENCE: Senior & Staff Level Architects.
- TONE & PEDAGOGY: Deep internals, edge cases, and high-concurrency failure modes.
- ADVANCED PROBLEMS: Cover cache stampedes, distributed lock contention, split-brain scenarios, and low-level memory/network internals.
"""
    else:
        difficulty_guidance = """
DIFFICULTY LEVEL GUIDANCE — 'Intermediate' (🟡 Mid-Level Developer):
- TARGET AUDIENCE: Mid-level Software Engineers with 2-4 years of experience.
- TONE & PEDAGOGY: Production-focused, trade-off oriented.
- REAL-WORLD SCENARIOS: Focus on real-world engineering trade-offs, code bug spotting, and system architecture metrics.
"""

    return f"""You are an expert Senior Software Engineer and Product Educator.
Generate a concise batch of {count} interactive learning cards for software engineers on:
TOPIC: {topic}
DIFFICULTY: {difficulty}

{difficulty_guidance}
{seen_guidance}

Target Card Sequence ({count} Cards total):
{seq_str}

Schema rules for specific card types:
- type 'hook':
  headline: string, body: string, statBadge: {{ label: string, value: string }}, simpleExplanation: string

- type 'multiple_choice':
  question: string
  options: [ {{ id: "opt-1", text: "...", isCorrect: true, explanation: "..." }}, {{ id: "opt-2", text: "...", isCorrect: false, explanation: "..." }} ]
  hint: string
  simpleExplanation: string

- type 'spot_the_mistake':
  instruction: string
  contextCodeOrDiagram: {{ type: "diagram", content: "...", nodes: [ {{ id: "n1", label: "...", isMistake: true, subtext: "..." }}, {{ id: "n2", label: "...", isMistake: false, subtext: "..." }} ] }}
  explanation: string

- type 'choose_the_tradeoff':
  scenario: string
  options: [ {{ id: "t1", title: "...", pros: ["..."], cons: ["..."], isBestChoice: true, why: "..." }}, {{ id: "t2", title: "...", pros: ["..."], cons: ["..."], isBestChoice: false, why: "..." }} ]

- type 'build_the_system':
  task: string
  availableBlocks: [ {{ id: "b1", label: "...", icon: "Layers" }}, {{ id: "b2", label: "...", icon: "Database" }} ]
  targetSlots: [ {{ slotId: "s1", label: "...", correctBlockId: "b1" }}, {{ slotId: "s2", label: "...", correctBlockId: "b2" }} ]
  explanation: string

- type 'match_pairs':
  instruction: string
  pairs: [ {{ id: "p1", left: "...", right: "..." }}, {{ id: "p2", left: "...", right: "..." }} ]
  explanation: string

- type 'predict_what_happens':
  scenario: string
  metricLabel: string
  minVal: 0, maxVal: 100, unit: "ms"
  outcomes: [ {{ threshold: 50, title: "...", status: "warning", description: "...", diagramState: "..." }} ]
  targetValue: 80
  explanation: string

- type 'before_vs_after':
  question: string
  optionA: {{ id: "a", label: "...", diagramType: "...", metrics: [ {{ label: "...", value: "..." }} ], isBetter: false }}
  optionB: {{ id: "b", label: "...", diagramType: "...", metrics: [ {{ label: "...", value: "..." }} ], isBetter: true }}
  explanation: string

- type 'guess_the_metric':
  metricTitle: string
  chartData: [ {{ time: "00:00", value: 20 }}, {{ time: "01:00", value: 95, spike: true }} ]
  question: string
  choices: [ {{ id: "c1", label: "...", isCorrect: true, explanation: "..." }} ]

- type 'timeline':
  title: string
  instruction: string
  events: [ {{ id: "e1", title: "...", description: "...", correctOrder: 1 }} ]
  explanation: string

- type 'drag_to_order':
  instruction: string
  items: [ {{ id: "d1", label: "...", correctIndex: 0 }} ]
  explanation: string

- type 'debug_session':
  bugTitle: string
  symptom: string
  stackTraceOrLog: string
  codeSnippet: {{ filename: "auth.ts", language: "typescript", lines: [ {{ lineNumber: 1, code: "...", isBuggyLine: false }}, {{ lineNumber: 2, code: "...", isBuggyLine: true }} ] }}
  fixOptions: [ {{ id: "f1", patchCode: "...", isCorrectFix: true, explanation: "..." }}, {{ id: "f2", patchCode: "...", isCorrectFix: false, explanation: "..." }} ]
  explanation: string

Return ONLY a JSON array containing the {count} card objects:
[
  {{ "type": "...", ... }},
  ...
]
No markdown formatting or extra text outside the JSON array.
"""

def sanitize_and_normalize_lesson(lesson: Dict[str, Any], topic: str, difficulty: str, duration_minutes: int = 5) -> Dict[str, Any]:
    if not isinstance(lesson, dict):
        lesson = {}

    lesson["id"] = lesson.get("id") or f"gemini-gen-{random.randint(1000, 9999)}"
    lesson["title"] = lesson.get("title") or f"Mastering {topic}"
    lesson["topic"] = lesson.get("topic") or topic
    lesson["difficulty"] = lesson.get("difficulty") or difficulty
    lesson["durationMinutes"] = lesson.get("durationMinutes") or duration_minutes
    lesson["subtitle"] = lesson.get("subtitle") or f"Interactive challenge for {topic}"

    raw_cards = lesson.get("cards")
    if not isinstance(raw_cards, list) or len(raw_cards) == 0:
        return lesson

    normalized_cards = []
    for idx, card in enumerate(raw_cards):
        if not isinstance(card, dict):
            continue

        c_type = card.get("type", "multiple_choice")
        card["id"] = card.get("id") or f"card-{random.randint(10000, 99999)}-{idx+1}"

        if c_type == "multiple_choice":
            raw_options = card.get("options") or card.get("choices")
            if not isinstance(raw_options, list) or len(raw_options) == 0:
                card["options"] = [
                    {
                        "id": "opt-1",
                        "text": f"Decouples architecture and optimizes performance for {topic}",
                        "isCorrect": True,
                        "explanation": f"Correct! This is the fundamental trade-off for {topic}."
                    },
                    {
                        "id": "opt-2",
                        "text": "Permanently eliminates CPU and RAM overhead",
                        "isCorrect": False,
                        "explanation": "All software requires compute resources."
                    }
                ]
            else:
                formatted_opts = []
                has_correct = False
                for o_idx, opt in enumerate(raw_options):
                    if isinstance(opt, str):
                        opt_obj = {
                            "id": f"opt-{o_idx+1}",
                            "text": opt,
                            "isCorrect": (o_idx == 0),
                            "explanation": "Valid architecture choice."
                        }
                    elif isinstance(opt, dict):
                        opt_obj = {
                            "id": str(opt.get("id") or f"opt-{o_idx+1}"),
                            "text": str(opt.get("text") or opt.get("label") or f"Option {o_idx+1}"),
                            "isCorrect": bool(opt.get("isCorrect") or opt.get("correct") or False),
                            "explanation": str(opt.get("explanation") or "Architecture impact explanation.")
                        }
                    else:
                        continue

                    if opt_obj["isCorrect"]:
                        has_correct = True
                    formatted_opts.append(opt_obj)

                if not has_correct and len(formatted_opts) > 0:
                    formatted_opts[0]["isCorrect"] = True

                card["options"] = formatted_opts

        elif c_type == "spot_the_mistake":
            context = card.get("contextCodeOrDiagram")
            if not isinstance(context, dict):
                card["contextCodeOrDiagram"] = {
                    "type": "diagram",
                    "content": f"{topic} Traffic -> Uncached DB Node (Bottleneck)",
                    "nodes": [
                        {"id": "n1", "label": "API Gateway", "isMistake": False, "subtext": "Rate limited"},
                        {"id": "n2", "label": "Direct Uncached DB Read", "isMistake": True, "subtext": "Lock contention!"}
                    ]
                }

        elif c_type == "build_the_system":
            blocks = card.get("availableBlocks")
            slots = card.get("targetSlots")
            if not isinstance(blocks, list) or len(blocks) == 0:
                card["availableBlocks"] = [
                    {"id": "b1", "label": f"{topic} Ingress", "icon": "Layers"},
                    {"id": "b2", "label": "RAM Cache (Redis)", "icon": "Database"},
                    {"id": "b3", "label": "Async Queue (Kafka)", "icon": "Cpu"},
                    {"id": "b4", "label": "Persistent SQL DB", "icon": "HardDrive"}
                ]
            if not isinstance(slots, list) or len(slots) == 0:
                card["targetSlots"] = [
                    {"slotId": "s1", "label": "1. Ingress Layer", "correctBlockId": "b1"},
                    {"slotId": "s2", "label": "2. Caching Layer", "correctBlockId": "b2"},
                    {"slotId": "s3", "label": "3. Async Queue", "correctBlockId": "b3"},
                    {"slotId": "s4", "label": "4. Storage", "correctBlockId": "b4"}
                ]

        normalized_cards.append(card)

    lesson["cards"] = normalized_cards
    return lesson


import re

def format_sharp_summary(text: str, max_sentences: int = 3) -> str:
    text = text.strip()
    if not text:
        return ""

    lines = [l for l in text.split("\n") if not l.strip().lower().startswith(("rule", "constraint", "* constraint", "**rule", "format rule", "system instruction", "instruction:"))]
    cleaned_text = " ".join(lines).strip()

    # Extract complete sentences ending in . ! or ?
    sentence_pattern = re.compile(r'([^.!?]+[.!?])', re.DOTALL)
    matches = sentence_pattern.findall(cleaned_text)

    if matches:
        selected = matches[:max_sentences]
        return " ".join([s.strip() for s in selected])
    return cleaned_text


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        raw_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
        self.model = raw_model.replace("models/", "").strip('"').strip("'")

    async def generate_cards(self, topic: str, difficulty: str = "Foundational", count: int = 2, seen_titles: List[str] = None, include_hook: bool = False) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="GEMINI_API_KEY is not configured in backend/.env."
            )

        try:
            prompt = build_cards_prompt(topic, difficulty, count, seen_titles, include_hook)
            clean_model = self.model.replace("models/", "").strip('"').strip("'")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.6
                }
            }

            print(f"[DEBUG Gemini] Requesting {count} cards for '{topic}' ({difficulty}) with model '{clean_model}'...")
            resp = requests.post(url, json=payload, timeout=25)

            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                raw_cards = json.loads(text)
                if isinstance(raw_cards, dict) and "cards" in raw_cards:
                    raw_cards = raw_cards["cards"]
                if not isinstance(raw_cards, list):
                    raw_cards = []

                dummy_lesson = {"cards": raw_cards}
                normalized = sanitize_and_normalize_lesson(dummy_lesson, topic, difficulty)
                cards = normalized.get("cards", [])
                print(f"[DEBUG Gemini] Successfully generated {len(cards)} cards for '{topic}'.")
                return cards
            else:
                logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                raise HTTPException(
                    status_code=resp.status_code if 400 <= resp.status_code < 600 else 500,
                    detail=f"Gemini API error ({resp.status_code}): {resp.text}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Gemini generate_cards exception: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate cards via Gemini API: {str(e)}"
            )

    async def generate_lesson(self, topic: str, difficulty: str = "Foundational", duration_minutes: int = 5) -> Dict[str, Any]:
        cards = await self.generate_cards(topic=topic, difficulty=difficulty, count=3, include_hook=True)
        return {
            "id": f"gemini-session-{random.randint(1000, 9999)}",
            "title": f"Mastering {topic}",
            "topic": topic,
            "difficulty": difficulty,
            "subtitle": f"Interactive practice for {topic}",
            "cards": cards
        }

    async def ask_card_question(self, lesson_topic: str, difficulty: str, card_context: Dict[str, Any], messages: List[Dict[str, str]], user_prompt: str) -> str:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="GEMINI_API_KEY is not configured in backend/.env."
            )

        system_instruction = f"""You are an expert Senior Software Engineer tutoring a developer on an interactive coding card.
LESSON TOPIC: {lesson_topic} ({difficulty} Level)
CARD CONTEXT: {json.dumps(card_context)}

INSTRUCTION: Answer the student's question directly in a crisp, high-level summary of 2 to 3 sentences. Keep your response clear and easy to digest. If you feel the concept requires deeper technical detail, end your response with: "Feel free to ask if you'd like more details!"
"""

        contents = []
        for msg in (messages or []):
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        contents.append({"role": "user", "parts": [{"text": user_prompt}]})

        clean_model = self.model.replace("models/", "").strip('"').strip("'")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 800
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return format_sharp_summary(raw_text, max_sentences=3)
            else:
                logger.error(f"Gemini Chat API returned status {resp.status_code}: {resp.text}")
                raise HTTPException(
                    status_code=resp.status_code if 400 <= resp.status_code < 600 else 500,
                    detail=f"Gemini API error ({resp.status_code}): {resp.text}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Gemini ask_card_question exception: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with Gemini API: {str(e)}"
            )
