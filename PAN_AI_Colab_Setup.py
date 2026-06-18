# PAN-AI/PAN_AI_Colab_Setup.py
# Script to run PAN-AI FastAPI Server in Google Colab and tunnel it to local Express backend.

import os
import sys

def install_dependencies():
    """
    Install required packages for running PAN-AI on Google Colab.
    
    Why: Google Colab environments have pre-installed libraries, but we need
    specific packages like pyngrok and fastapi for API routing and tunneling.
    """
    print("[PAN-AI] Installing dependencies...")
    os.system("pip install fastapi uvicorn pydantic requests pyyaml pyngrok paho-mqtt")

def setup_directory_structure():
    """
    Create temporary directory structure for skills and memories in Colab.
    
    Why: Ensures the server script finds the modules in the expected relative paths.
    """
    print("[PAN-AI] Setting up directories...")
    os.makedirs("skills", exist_ok=True)
    os.makedirs("memories", exist_ok=True)

def write_temp_skills():
    """
    Write skill modules directly into the Colab environment.
    
    Why: Keeps the script self-contained so the user only needs to run one file
    in Colab to boot the entire gateway.
    """
    print("[PAN-AI] Creating skill modules...")
    
    # 1. digital_twin.py
    with open("skills/digital_twin.py", "w", encoding="utf-8") as f:
        f.write('''import os
from typing import Dict, Optional
MEMORIES_DIR = "memories"
DEFAULT_USER_TEMPLATE = "# Student Profile\\n- Learning Style: Visual\\n- Baseline Heart Rate: 75 bpm\\n"
DEFAULT_MEMORY_TEMPLATE = "# Learning Log\\n- Current Chapter: Chapter 1\\n- Fatigue Count: 0\\n"

def load_student_memory(student_id: str) -> Dict[str, str]:
    student_dir = os.path.join(MEMORIES_DIR, student_id)
    os.makedirs(student_dir, exist_ok=True)
    u_path = os.path.join(student_dir, "USER.md")
    m_path = os.path.join(student_dir, "MEMORY.md")
    if not os.path.exists(u_path):
        with open(u_path, "w") as f: f.write(DEFAULT_USER_TEMPLATE)
    if not os.path.exists(m_path):
        with open(m_path, "w") as f: f.write(DEFAULT_MEMORY_TEMPLATE)
    with open(u_path, "r") as f: u_c = f.read()
    with open(m_path, "r") as f: m_c = f.read()
    return {"user_profile": u_c, "learning_log": m_c}

def update_student_memory(student_id: str, user_profile: Optional[str] = None, learning_log: Optional[str] = None) -> bool:
    student_dir = os.path.join(MEMORIES_DIR, student_id)
    os.makedirs(student_dir, exist_ok=True)
    if user_profile:
        with open(os.path.join(student_dir, "USER.md"), "w") as f: f.write(user_profile)
    if learning_log:
        with open(os.path.join(student_dir, "MEMORY.md"), "w") as f: f.write(learning_log)
    return True
''')

    # 2. evaluate_biometrics.py
    with open("skills/evaluate_biometrics.py", "w", encoding="utf-8") as f:
        f.write('''def evaluate_student_state(heart_rate: float, hrv: float, ear: float, gsr: float, focus_score: float):
    state = "NORMAL"
    reason = "Kondisi stabil."
    if ear < 0.20 or focus_score < 40:
        state = "MENGANTUK"
        reason = "Deteksi kedipan mata lambat."
    elif heart_rate > 95.0 or hrv < 40.0:
        state = "STRES"
        reason = "Detak jantung tinggi."
    return {
        "state": state,
        "reason": reason,
        "biometrics_snapshot": {"heart_rate": heart_rate, "hrv": hrv, "ear": ear, "gsr": gsr, "focus_score": focus_score}
    }
''')

    # 3. generate_quiz.py
    with open("skills/generate_quiz.py", "w", encoding="utf-8") as f:
        f.write('''import requests
import json
def generate_educational_quiz(topic: str, grade: str, difficulty: str, num_questions: int = 5, api_key: str = ""):
    if not api_key:
        return {"error": "API Key is required."}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"Create a quiz about {topic} for grade {grade} with difficulty {difficulty}. Generate {num_questions} questions in JSON."
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "questions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "question": {"type": "STRING"},
                                "options": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "answer": {"type": "STRING"},
                                "explanation": {"type": "STRING"}
                            },
                            "required": ["question", "options", "answer", "explanation"]
                        }
                    }
                },
                "required": ["questions"]
            }
        }
    }
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}
''')

def write_server_code():
    """
    Write the FastAPI server entrypoint.
    
    Why: Decouples the server routing logic from local path dependencies.
    """
    print("[PAN-AI] Writing server entrypoint...")
    with open("server_app.py", "w", encoding="utf-8") as f:
        f.write('''import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from skills.digital_twin import load_student_memory, update_student_memory
from skills.evaluate_biometrics import evaluate_student_state
from skills.generate_quiz import generate_educational_quiz

app = FastAPI()

class TelemetryPayload(BaseModel):
    studentId: str
    heart_rate: float
    hrv: float
    ear: float
    gsr: float
    focus_score: float

class QuizPayload(BaseModel):
    topic: str
    grade: str
    difficulty: str
    num_questions: int = 5

@app.post("/api/evaluate-biometrics")
def evaluate_biometrics(payload: TelemetryPayload):
    try:
        mem = load_student_memory(payload.studentId)
        eval_res = evaluate_student_state(
            payload.heart_rate, payload.hrv, payload.ear, payload.gsr, payload.focus_score
        )
        state = eval_res["state"]
        if state != "NORMAL":
            new_log = mem["learning_log"].strip() + f"\\n- [{state}] {eval_res['reason']}"
            update_student_memory(payload.studentId, learning_log=new_log)
        return {
            "success": True,
            "student_id": payload.studentId,
            "cognitive_state": state,
            "reason": eval_res["reason"],
            "intervention_recommended": state != "NORMAL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-quiz")
def generate_quiz(payload: QuizPayload):
    key = os.environ.get("GEMINI_API_KEY", "")
    res = generate_educational_quiz(payload.topic, payload.grade, payload.difficulty, payload.num_questions, key)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res
''')

def start_tunnel(ngrok_token: str):
    """
    Initiate the ngrok tunnel to expose local port 3002 to the public internet.
    
    Why: Google Colab runs on remote Google VMs. We need a secure public tunnel
    so the local Express server on the user's PC can call the Colab backend.
    """
    from pyngrok import ngrok
    print("[PAN-AI] Setting up ngrok tunnel...")
    ngrok.set_auth_token(ngrok_token)
    public_url = ngrok.connect(3002, "http")
    print(f"\\n[PAN-AI] SUCCESS! Your public Colab AI URL is: {public_url.public_url}\\n")
    print("Use this URL in your Express backend (.env) as process.env.PAN_AI_URL")
    return public_url.public_url

if __name__ == "__main__":
    # If run in Google Colab
    if len(sys.argv) < 2:
        token = input("Enter your Ngrok Authtoken: ").strip()
    else:
        token = sys.argv[1]

    install_dependencies()
    setup_directory_structure()
    write_temp_skills()
    write_server_code()
    
    # Run uvicorn server in background and start tunnel
    import uvicorn
    import threading
    
    public_address = start_tunnel(token)
    
    # Set mock Gemini Key for testing
    gemini_key = input("Enter your Gemini API Key (optional): ").strip()
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key

    from server_app import app
    print("[PAN-AI] Launching FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=3002)
