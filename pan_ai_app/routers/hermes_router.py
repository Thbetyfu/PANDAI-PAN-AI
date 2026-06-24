from __future__ import annotations

from fastapi import APIRouter

from skills.hermes_memory_v2 import (
    add_lesson_event,
    add_quiz_result,
    get_memory_summary as get_hermes_summary,
    load_learning_log,
    load_user_profile,
    save_user_profile,
)

from ..schemas import AddLessonEventRequest, AddQuizResultRequest, UpdateUserProfileRequest


router = APIRouter()


@router.get("/api/hermes/v2/profile/{student_id}")
async def hermes_get_profile(student_id: str):
    profile = load_user_profile(student_id)
    return {"success": True, "student_id": student_id, "profile": profile}


@router.put("/api/hermes/v2/profile/{student_id}")
async def hermes_update_profile(student_id: str, payload: UpdateUserProfileRequest):
    profile = load_user_profile(student_id)
    if payload.learning_style is not None:
        profile["learning_style"] = payload.learning_style
    if payload.sleep_threshold_hours is not None:
        profile["sleep_threshold_hours"] = payload.sleep_threshold_hours
    if payload.baseline_heart_rate is not None:
        profile["baseline_heart_rate"] = payload.baseline_heart_rate
    if payload.average_attention_span_minutes is not None:
        profile["average_attention_span_minutes"] = payload.average_attention_span_minutes
    if payload.personality_traits is not None:
        profile["personality_traits"] = payload.personality_traits
    if payload.preferences is not None:
        profile["preferences"] = {**profile.get("preferences", {}), **payload.preferences}
    save_user_profile(student_id, profile)
    return {"success": True, "student_id": student_id, "profile": profile}


@router.get("/api/hermes/v2/learning-log/{student_id}")
async def hermes_get_learning_log(student_id: str):
    log = load_learning_log(student_id)
    return {"success": True, "student_id": student_id, "learning_log": log}


@router.post("/api/hermes/v2/learning-log/{student_id}/lesson")
async def hermes_add_lesson_event(student_id: str, payload: AddLessonEventRequest):
    add_lesson_event(
        student_id=student_id,
        lesson_title=payload.lesson_title,
        duration_minutes=payload.duration_minutes,
        focus_score=payload.focus_score,
        notes=payload.notes,
    )
    return {"success": True, "student_id": student_id, "message": "Lesson event added"}


@router.post("/api/hermes/v2/learning-log/{student_id}/quiz")
async def hermes_add_quiz_result(student_id: str, payload: AddQuizResultRequest):
    add_quiz_result(
        student_id=student_id,
        quiz_title=payload.quiz_title,
        score=payload.score,
        total_questions=payload.total_questions,
        topic=payload.topic,
    )
    return {"success": True, "student_id": student_id, "message": "Quiz result added"}


@router.get("/api/hermes/v2/summary/{student_id}")
async def hermes_get_summary(student_id: str):
    summary = get_hermes_summary(student_id)
    return summary

