import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .schemas import GenerateLessonRequest, StartSessionRequest, GenerateCardsRequest, CardChatRequest, CardChatResponse
from .llm.factory import get_llm_provider

app = FastAPI(
    title="NYT Games for Software Engineers API",
    description="Modular AI Lesson Generator for interactive engineering challenges.",
    version="1.0.0"
)

# Enable CORS for local dev and Vercel frontend deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
    return {
        "status": "healthy",
        "active_provider": provider_name
    }

@app.post("/api/start-session")
async def start_session(req: StartSessionRequest):
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")

    provider = get_llm_provider()
    count = req.count or 3
    cards = await provider.generate_cards(
        topic=req.topic.strip(),
        difficulty=req.difficulty or "Foundational",
        count=count,
        include_hook=True
    )
    return {
        "id": f"session-{os.urandom(4).hex()}",
        "title": f"Mastering {req.topic.strip()}",
        "topic": req.topic.strip(),
        "difficulty": req.difficulty or "Foundational",
        "subtitle": f"Interactive practice for {req.topic.strip()}",
        "cards": cards
    }

@app.post("/api/generate-cards")
async def generate_cards(req: GenerateCardsRequest):
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")

    provider = get_llm_provider()
    count = req.count or 2
    cards = await provider.generate_cards(
        topic=req.topic.strip(),
        difficulty=req.difficulty or "Foundational",
        count=count,
        seen_titles=req.seenTitles or [],
        include_hook=False
    )
    return {"cards": cards}

@app.post("/api/generate-lesson")
async def generate_lesson(req: GenerateLessonRequest):
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")

    provider = get_llm_provider()
    lesson_data = await provider.generate_lesson(
        topic=req.topic.strip(),
        difficulty=req.difficulty or "Foundational",
        duration_minutes=req.durationMinutes or 5
    )
    return lesson_data

@app.post("/api/card-chat", response_model=CardChatResponse)
async def card_chat(req: CardChatRequest):
    if not req.userPrompt or not req.userPrompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required.")

    provider = get_llm_provider()
    messages_dict = [m.model_dump() for m in req.messages] if req.messages else []

    reply_text = await provider.ask_card_question(
        lesson_topic=req.lessonTopic,
        difficulty=req.difficulty or "Foundational",
        card_context=req.cardContext,
        messages=messages_dict,
        user_prompt=req.userPrompt.strip()
    )

    return CardChatResponse(reply=reply_text)

