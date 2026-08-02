import os
import json
import random
import logging
from typing import Dict, Any, List
import requests
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
    "match_pairs"
]

def build_dynamic_prompt(topic: str, difficulty: str, duration_minutes: int, selected_cards: List[str]) -> str:
    card_sequence_instructions = [
        f"Card 1: type 'hook' (headline, body, statBadge: {{label, value}}, simpleExplanation)"
    ]
    for idx, c_type in enumerate(selected_cards):
        card_sequence_instructions.append(f"Card {idx+2}: type '{c_type}'")
    card_sequence_instructions.append(f"Card {len(selected_cards)+2}: type 'takeaway' (oneSentenceSummary, keyInsights [2-3 items])")

    seq_str = "\n".join(card_sequence_instructions)

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
Generate a concise, punchy {len(selected_cards)+2}-card micro-learning deck for software engineers on:
TOPIC: {topic}
DIFFICULTY: {difficulty}
TARGET DURATION: {duration_minutes} Minutes

{difficulty_guidance}

Target Card Sequence ({len(selected_cards)+2} Cards total):
{seq_str}

Schema rules for specific card types:
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

Return ONLY a valid JSON object:
{{
  "id": "lesson-id",
  "title": "Lesson Title",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "durationMinutes": {duration_minutes},
  "subtitle": "Subtitle",
  "cards": [ ...array of {len(selected_cards)+2} cards... ]
}}
No markdown formatting or extra text.
"""

def sanitize_and_normalize_lesson(lesson: Dict[str, Any], topic: str, difficulty: str, duration_minutes: int) -> Dict[str, Any]:
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
        card["id"] = card.get("id") or f"card-{idx+1}"

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
                    {"id": "b3", "label": "Event Stream (Kafka)", "icon": "Cpu"},
                    {"id": "b4", "label": "Persistent DB", "icon": "HardDrive"}
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


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    async def generate_lesson(self, topic: str, difficulty: str = "Foundational", duration_minutes: int = 5) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. Using fallback structured lesson generator.")
            print("[DEBUG Gemini] No API Key provided in .env. Using Fallback Engine.")
            return self._fallback_lesson(topic, difficulty, duration_minutes)

        try:
            if duration_minutes <= 3:
                card_count = 2
            elif duration_minutes <= 5:
                card_count = 4
            else:
                card_count = 5

            selected_cards = random.sample(INTERACTIVE_CARD_POOL, card_count)
            prompt = build_dynamic_prompt(topic, difficulty, duration_minutes, selected_cards)

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
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
                    "temperature": 0.5
                }
            }

            print(f"[DEBUG Gemini] Requesting {len(selected_cards)+2}-card deck ({difficulty} difficulty) for '{topic}'...")
            resp = requests.post(url, json=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                raw_json = json.loads(text)
                normalized_lesson = sanitize_and_normalize_lesson(raw_json, topic, difficulty, duration_minutes)
                print(f"[DEBUG Gemini] Successfully generated {len(normalized_lesson.get('cards', []))}-card deck for '{topic}'.")
                return normalized_lesson
            else:
                print(f"[DEBUG Gemini ERROR] Status Code {resp.status_code}: {resp.text}")
                logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return self._fallback_lesson(topic, difficulty, duration_minutes)

        except Exception as e:
            print(f"[DEBUG Gemini EXCEPTION] {type(e).__name__}: {e}")
            logger.error(f"GeminiProvider exception: {e}")
            return self._fallback_lesson(topic, difficulty, duration_minutes)

    def _fallback_lesson(self, topic: str, difficulty: str, duration_minutes: int = 5) -> Dict[str, Any]:
        t = topic.strip().capitalize()
        return {
            "id": f"gemini-fallback-{t.lower()}",
            "title": f"Mastering {t}",
            "topic": t,
            "difficulty": difficulty,
            "durationMinutes": duration_minutes,
            "subtitle": f"Bite-sized architecture challenge for {t}",
            "cards": [
                {
                    "id": "g-1",
                    "type": "hook",
                    "headline": f"Why {t} is crucial in modern high-throughput software systems.",
                    "body": f"Understanding {t} enables engineers to design reliable, scalable applications that gracefully handle traffic surges.",
                    "statBadge": {"label": "Impact", "value": "100x Scale"},
                    "iconName": "Sparkles",
                    "simpleExplanation": f"{t} simplifies complex software by isolating component dependencies and reducing system latency."
                },
                {
                    "id": "g-2",
                    "type": "multiple_choice",
                    "question": f"What primary problem does {t} solve in software design?",
                    "hint": f"Consider how {t} impacts performance and maintainability.",
                    "simpleExplanation": f"{t} prevents single-point-of-failure bottlenecks by distributing workloads cleanly.",
                    "options": [
                        {
                            "id": "opt-1",
                            "text": f"Decouples service dependencies and optimizes throughput for {t}",
                            "isCorrect": True,
                            "explanation": f"Correct! {t} enables clean separation of concerns and scales under heavy load."
                        },
                        {
                            "id": "opt-2",
                            "text": "Permanently eliminates the need for RAM and CPU hardware",
                            "isCorrect": False,
                            "explanation": "All software execution requires hardware resources."
                        }
                    ]
                },
                {
                    "id": "g-3",
                    "type": "build_the_system",
                    "task": f"Assemble a Resilient {t} Pipeline",
                    "subtitle": "Tap components to place them in correct pipeline order:",
                    "availableBlocks": [
                        {"id": "b1", "label": f"{t} API Gateway", "icon": "Layers"},
                        {"id": "b2", "label": "In-Memory Cache (Redis)", "icon": "Database"},
                        {"id": "b3", "label": "Async Queue (Kafka)", "icon": "Cpu"},
                        {"id": "b4", "label": "Persistent SQL DB", "icon": "HardDrive"}
                    ],
                    "targetSlots": [
                        {"slotId": "s1", "label": "1. API Gateway", "correctBlockId": "b1"},
                        {"slotId": "s2", "label": "2. In-Memory Cache", "correctBlockId": "b2"},
                        {"slotId": "s3", "label": "3. Event Queue", "correctBlockId": "b3"},
                        {"slotId": "s4", "label": "4. Database", "correctBlockId": "b4"}
                    ],
                    "explanation": f"Spot on! Incoming traffic hits the {t} Gateway, checks Redis cache, queues events in Kafka, and persists data."
                },
                {
                    "id": "g-4",
                    "type": "takeaway",
                    "oneSentenceSummary": f"Mastering {t} gives software engineers a critical tool for building resilient, high-scale applications.",
                    "keyInsights": [
                        f"Decouple components using {t} design principles.",
                        "Always benchmark latency and storage trade-offs before deploying to production."
                    ],
                    "suggestedNextTopic": "System Design"
                }
            ]
        }
