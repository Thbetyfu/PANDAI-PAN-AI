# PAN-AI/server.py
# Centralized FastAPI Server for PAN-AI Agent Services.

import os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from skills.digital_twin import load_student_memory, update_student_memory
from skills.evaluate_biometrics import evaluate_student_state
from skills.generate_quiz import generate_educational_quiz

app = FastAPI(
    title="PAN-AI Core Service",
    description="Centralized AI Agent Gateway with OpenClaw skills and Hermes-style memory storage."
)

class TelemetryPayload(BaseModel):
    studentId: str = Field(..., description="Unique ID of the student")
    heartRate: float = Field(..., alias="heart_rate", description="Heart rate in bpm")
    hrv: float = Field(..., description="Heart rate variability in ms")
    ear: float = Field(..., description="Eye aspect ratio")
    gsr: float = Field(..., description="Galvanic Skin Response in uS")
    focusScore: float = Field(..., alias="focus_score", description="Focus score from 0-100")

    class Config:
        populate_by_name = True


class QuizPayload(BaseModel):
    topic: str
    grade: str
    difficulty: str
    numQuestions: int = Field(5, alias="num_questions")
    modelName: str = Field("qwen2.5:7b", alias="model_name")

    class Config:
        populate_by_name = True


@app.post("/api/evaluate-biometrics")
async def evaluate_biometrics(payload: TelemetryPayload):
    """
    Evaluate student biometrics, update their Digital Twin memory, and return intervention states.
    
    Why: Keeps student memory updated on the server dynamically per session, ensuring
    the persistent Hermes memory is synced without client-side database overhead.
    """
    try:
        # Load existing student memory
        student_memory = load_student_memory(payload.studentId)
        
        # Evaluate current cognitive state
        evaluation = evaluate_student_state(
            heart_rate=payload.heartRate,
            hrv=payload.hrv,
            ear=payload.ear,
            gsr=payload.gsr,
            focus_score=payload.focusScore
        )
        
        state = evaluation["state"]
        reason = evaluation["reason"]

        # Update learning log (MEMORY.md) if state is critical
        if state != "NORMAL":
            learning_log = student_memory["learning_log"]
            log_entry = f"\n- [{state}] {reason} (HR: {payload.heartRate}, EAR: {payload.ear}, GSR: {payload.gsr})"
            # Append log entry to the log file content
            new_log = learning_log.strip() + log_entry + "\n"
            
            # Simple threshold counter increments
            if state == "MENGANTUK" and "Fatigue Count:" in new_log:
                # Basic string replacement to increment count for demonstration
                try:
                    for line in new_log.splitlines():
                        if "Fatigue Count:" in line:
                            current_val = int(line.split(":")[-1].strip())
                            new_log = new_log.replace(line, f"- Fatigue Count: {current_val + 1}")
                            break
                except Exception:
                    pass
            elif state == "STRES" and "Stress Count:" in new_log:
                try:
                    for line in new_log.splitlines():
                        if "Stress Count:" in line:
                            current_val = int(line.split(":")[-1].strip())
                            new_log = new_log.replace(line, f"- Stress Count: {current_val + 1}")
                            break
                except Exception:
                    pass
            
            update_student_memory(payload.studentId, learning_log=new_log)

        return {
            "success": True,
            "student_id": payload.studentId,
            "cognitive_state": state,
            "reason": reason,
            "intervention_recommended": state != "NORMAL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal evaluation error: {str(e)}")


@app.post("/api/generate-quiz")
async def generate_quiz(payload: QuizPayload):
    """
    Generate multiple choice questions based on curriculum topics.
    
    Why: Relies on local Ollama engine running Qwen which returns a standardized JSON structure
    guaranteeing quiz compatibility.
    """
    result = generate_educational_quiz(
        topic=payload.topic,
        grade=payload.grade,
        difficulty=payload.difficulty,
        num_questions=payload.numQuestions,
        model_name=payload.modelName
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


if __name__ == "__main__":
    import uvicorn
    # Why: We run on port 3002, which is one of the allowed dev/server ports in global rules.
    uvicorn.run(app, host="0.0.0.0", port=3002)
