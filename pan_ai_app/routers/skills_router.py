from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional

from skills.feedback_generator_skill import (
    generate_answer_feedback,
    generate_encouragement,
    generate_progress_feedback,
    generate_quiz_feedback,
)
from skills.hermes_memory_v2 import get_memory_summary as get_hermes_summary
from skills.language_tutor_skill import (
    clear_chat_history as skill_clear_chat_history,
    get_chat_history as skill_get_chat_history,
    get_student_progress as skill_get_progress,
    increment_lesson_completed as skill_increment_lesson,
    language_chat as openclaw_language_chat,
)
from skills.mascot_skill import get_expression_for_answer, get_mascot_expression, get_random_expression
from skills.memory_retrieval_skill import (
    get_learning_patterns,
    get_memory_summary,
    get_personalized_recommendations,
    search_memory,
)

from ..deps import build_teacher_context_from_hermes_summary
from ..schemas import (
    AnswerFeedbackRequest,
    EncouragementRequest,
    LanguageChatMessagePayload,
    MascotExpressionRequest,
    MemorySearchRequest,
    ProgressFeedbackRequest,
    QuizFeedbackRequest,
)


router = APIRouter()


@router.post("/api/skills/mascot/expression")
async def skill_get_mascot_expression(payload: MascotExpressionRequest):
    result = get_mascot_expression(context=payload.context, state=payload.cognitive_state, feedback_type=payload.feedback_type)
    return result


@router.get("/api/skills/mascot/random")
async def skill_get_random_expression():
    return get_random_expression()


@router.get("/api/skills/mascot/answer/{is_correct}")
async def skill_get_answer_expression(is_correct: bool):
    return get_expression_for_answer(is_correct)


@router.post("/api/skills/feedback/answer")
async def skill_generate_answer_feedback(payload: AnswerFeedbackRequest):
    result = generate_answer_feedback(
        student_id=payload.student_id,
        question=payload.question,
        student_answer=payload.student_answer,
        correct_answer=payload.correct_answer,
        is_correct=payload.is_correct,
        subject=payload.subject,
    )
    return result


@router.post("/api/skills/feedback/quiz")
async def skill_generate_quiz_feedback(payload: QuizFeedbackRequest):
    result = generate_quiz_feedback(
        student_id=payload.student_id,
        quiz_results=payload.quiz_results,
        total_score=payload.total_score,
        topic=payload.topic,
    )
    return result


@router.post("/api/skills/feedback/progress")
async def skill_generate_progress_feedback(payload: ProgressFeedbackRequest):
    result = generate_progress_feedback(
        student_id=payload.student_id,
        progress_summary=payload.progress_summary,
        time_period=payload.time_period,
    )
    return result


@router.post("/api/skills/feedback/encouragement")
async def skill_generate_encouragement(payload: EncouragementRequest):
    result = generate_encouragement(student_id=payload.student_id, context=payload.context, student_state=payload.student_state)
    return result


@router.post("/api/skills/memory/search")
async def skill_search_memory(payload: MemorySearchRequest):
    result = search_memory(
        student_id=payload.student_id,
        query=payload.query,
        limit=payload.limit,
        content_type=payload.content_type,
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error searching memory"))
    return result


@router.get("/api/skills/memory/summary/{student_id}")
async def skill_get_memory_summary(student_id: str):
    result = get_memory_summary(student_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error getting memory summary"))
    return result


@router.get("/api/skills/memory/patterns/{student_id}")
async def skill_get_learning_patterns(student_id: str):
    result = get_learning_patterns(student_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error analyzing patterns"))
    return result


@router.get("/api/skills/memory/recommendations/{student_id}")
async def skill_get_personalized_recommendations(student_id: str):
    result = get_personalized_recommendations(student_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error getting recommendations"))
    return result


@router.post("/api/skills/language-tutor/chat")
async def skill_language_chat_endpoint(payload: LanguageChatMessagePayload):
    teacher_context = ""
    try:
        hermes_summary = get_hermes_summary(payload.student_id)
        if isinstance(hermes_summary, dict) and hermes_summary.get("success"):
            teacher_context = build_teacher_context_from_hermes_summary(hermes_summary)
    except Exception:
        teacher_context = ""

    result = openclaw_language_chat(
        student_id=payload.student_id,
        user_message=payload.content,
        language=payload.language,
        use_llm=True,
        teacher_context=teacher_context or None,
        teacher_persona="strict_warm",
        correction_mode="fluency_first",
        llm_mode=payload.llm_mode or "local",
        llm_profile=payload.llm_profile or "balanced",
        llm_model=payload.llm_model,
    )
    return result


@router.get("/api/skills/language-tutor/progress/{student_id}")
async def skill_get_language_progress(student_id: str):
    return skill_get_progress(student_id)


@router.post("/api/skills/language-tutor/increment-lesson/{student_id}")
async def skill_increment_language_lesson(student_id: str):
    return skill_increment_lesson(student_id)


@router.get("/api/skills/language-tutor/history/{student_id}")
async def skill_get_language_history(student_id: str, limit: Optional[int] = None):
    return skill_get_chat_history(student_id, limit)


@router.delete("/api/skills/language-tutor/history/{student_id}")
async def skill_clear_language_history(student_id: str):
    return skill_clear_chat_history(student_id)

