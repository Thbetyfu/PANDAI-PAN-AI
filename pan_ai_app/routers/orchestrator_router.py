from __future__ import annotations

from fastapi import APIRouter, HTTPException

from skills.feedback_generator_skill import generate_encouragement
from skills.hermes_memory_v2 import get_memory_summary as get_hermes_summary
from skills.language_tutor_skill import language_chat as openclaw_language_chat
from skills.mascot_skill import get_mascot_expression
from skills.skill_orchestrator import Intent, orchestrator

from ..deps import build_teacher_context_from_hermes_summary
from ..schemas import OrchestratorRequest


router = APIRouter()


@router.post("/api/orchestrator/recognize-intent")
async def orchestrator_recognize_intent(payload: OrchestratorRequest):
    intent = orchestrator.recognize_intent(payload.user_input)
    return {"success": True, "user_input": payload.user_input, "intent": intent.value}


@router.post("/api/orchestrator/orchestrate")
async def orchestrator_orchestrate(payload: OrchestratorRequest):
    result = orchestrator.orchestrate(payload.user_input, payload.student_id)
    return result


@router.post("/api/orchestrator/execute")
async def orchestrator_execute(payload: OrchestratorRequest):
    intent = orchestrator.recognize_intent(payload.user_input)

    teacher_context = ""
    try:
        hermes_summary = get_hermes_summary(payload.student_id)
        if isinstance(hermes_summary, dict) and hermes_summary.get("success"):
            teacher_context = build_teacher_context_from_hermes_summary(hermes_summary)
    except Exception:
        hermes_summary = {"success": False}
        teacher_context = ""

    tutor_result = openclaw_language_chat(
        student_id=payload.student_id,
        user_message=payload.user_input,
        language=payload.language,
        use_llm=True,
        teacher_context=teacher_context or None,
        teacher_persona="strict_warm",
        correction_mode="fluency_first",
        llm_mode=payload.llm_mode or "local",
        llm_profile=payload.llm_profile or "balanced",
        llm_model=payload.llm_model,
    )

    feedback_type = "constructive" if tutor_result.get("correction") else "positive"
    mascot_result = get_mascot_expression(context="chat", feedback_type=feedback_type)

    encouragement_context = "kesulitan" if tutor_result.get("correction") else "keberhasilan"
    feedback_result = generate_encouragement(
        student_id=payload.student_id,
        context=encouragement_context,
        student_state=None,
    )

    return {
        "success": True,
        "intent": intent.value,
        "student_id": payload.student_id,
        "language": payload.language,
        "teacher_persona": "strict_warm",
        "correction_mode": "fluency_first",
        "llm_mode": payload.llm_mode or "local",
        "llm_profile": payload.llm_profile or "balanced",
        "llm_model": payload.llm_model or "auto",
        "teacher_context_used": bool(teacher_context),
        "hermes_summary_ok": bool(isinstance(hermes_summary, dict) and hermes_summary.get("success")),
        "tutor": tutor_result,
        "mascot": mascot_result,
        "feedback": feedback_result,
    }


@router.post("/api/orchestrator/get-skills-for-intent")
async def orchestrator_get_skills(intent: str = "chat"):
    try:
        intent_enum = Intent(intent)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid intent: {intent}")

    skills = orchestrator.get_skills_for_intent(intent_enum)
    return {"success": True, "intent": intent, "recommended_skills": skills, "total_skills": len(skills)}

