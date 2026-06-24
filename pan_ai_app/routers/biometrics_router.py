from __future__ import annotations

from fastapi import APIRouter, HTTPException

from skills.evaluate_biometrics import evaluate_student_state
from skills.hermes_memory_v2 import add_biometric_event

from ..schemas import TelemetryPayload


router = APIRouter()


@router.post("/api/evaluate-biometrics")
async def evaluate_biometrics(payload: TelemetryPayload):
    try:
        evaluation = evaluate_student_state(
            heart_rate=payload.heartRate,
            hrv=payload.hrv,
            ear=payload.ear,
            gsr=payload.gsr,
            focus_score=payload.focusScore,
        )

        state = evaluation["state"]
        reason = evaluation["reason"]

        if state != "NORMAL":
            add_biometric_event(
                student_id=payload.studentId,
                event_type=state,
                metrics={
                    "heart_rate": payload.heartRate,
                    "hrv": payload.hrv,
                    "ear": payload.ear,
                    "gsr": payload.gsr,
                    "focus_score": payload.focusScore,
                },
                reason=reason,
            )

        return {
            "success": True,
            "student_id": payload.studentId,
            "cognitive_state": state,
            "reason": reason,
            "intervention_recommended": state != "NORMAL",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal evaluation error: {str(e)}")

