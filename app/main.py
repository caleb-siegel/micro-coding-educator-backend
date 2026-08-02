import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .schemas import GenerateLessonRequest
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
