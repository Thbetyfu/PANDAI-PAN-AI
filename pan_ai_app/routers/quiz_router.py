from __future__ import annotations

from fastapi import APIRouter, HTTPException

from skills.generate_quiz import generate_educational_quiz

from ..schemas import QuizPayload


router = APIRouter()


@router.post("/api/generate-quiz")
async def generate_quiz(payload: QuizPayload):
    result = generate_educational_quiz(
        topic=payload.topic,
        grade=payload.grade,
        difficulty=payload.difficulty,
        num_questions=payload.numQuestions,
        model_name=payload.modelName,
        llm_mode=payload.llmMode,
        llm_profile=payload.llmProfile,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

