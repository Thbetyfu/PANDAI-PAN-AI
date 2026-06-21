# PAN-AI/server.py
# Centralized FastAPI Server for PAN-AI Agent Services.

import os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from skills.digital_twin import load_student_memory, update_student_memory
from skills.evaluate_biometrics import evaluate_student_state
from skills.generate_quiz import generate_educational_quiz

# Import Neuro-Memory modules
from neuro_memory import MemoryEngine, EmbeddingStore, ModelTrainer
from pathlib import Path

app = FastAPI(
    title="PAN-AI Core Service",
    description="Centralized AI Agent Gateway with OpenClaw skills and Hermes-style memory storage + Neuro-Memory Foundation Model."
)

# Inisialisasi Neuro-Memory services
memory_engine = MemoryEngine()
embedding_store = EmbeddingStore()
model_trainer = ModelTrainer()

# --- Neuro-Memory Models ---
class MemoryChunkPayload(BaseModel):
    student_id: str
    content_type: str
    content: Dict[str, Any]
    session_id: Optional[str] = None
    timestamp: Optional[str] = None

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


# --- Neuro-Memory Endpoints ---
@app.post("/api/neuro-memory/store")
async def store_memory_chunk(payload: MemoryChunkPayload):
    """Simpan satu unit memory chunk ke Neuro-Memory"""
    try:
        from neuro_memory.memory_engine import MemoryChunk
        from datetime import datetime
        
        chunk = MemoryChunk(
            chunk_id="",
            student_id=payload.student_id,
            session_id=payload.session_id,
            timestamp=payload.timestamp or datetime.now().isoformat(),
            content_type=payload.content_type,
            content=payload.content
        )
        
        chunk_id = memory_engine.store_memory_chunk(chunk)
        
        # Generate and store embedding
        embedding_text = f"{payload.content_type}: {str(payload.content)}"
        embedding = embedding_store.generate_embedding(embedding_text)
        embedding_store.add_vector(
            chunk_id=chunk_id,
            student_id=payload.student_id,
            vector=embedding,
            metadata={"content_type": payload.content_type, "model_used": "all-MiniLM-L6-v2" if embedding_store.model_available else "dummy"}
        )
        
        return {"success": True, "chunk_id": chunk_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan memory: {str(e)}")


@app.get("/api/neuro-memory/profile/{student_id}")
async def get_cognitive_profile(student_id: str):
    """Dapatkan profil kognitif siswa"""
    profile = memory_engine.get_student_profile(student_id)
    if not profile:
        profile = memory_engine.create_initial_profile(student_id)
    return {
        "success": True,
        "student_id": student_id,
        "profile": profile
    }


@app.post("/api/neuro-memory/analyze/{student_id}")
async def analyze_learning_patterns(student_id: str):
    """Analisis pola belajar siswa dari riwayat memori"""
    try:
        analysis = memory_engine.analyze_learning_pattern(student_id)
        return {"success": True, **analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis pola: {str(e)}")


@app.get("/api/neuro-memory/recommendations/{student_id}")
async def get_personalized_recommendations(student_id: str):
    """Dapatkan rekomendasi belajar personalisasi"""
    profile = memory_engine.get_student_profile(student_id) or memory_engine.create_initial_profile(student_id)
    
    recommendations = []
    
    if profile.focus_peak_hours:
        recommendations.append({
            "type": "schedule",
            "title": "Waktu Belajar Optimal",
            "content": f"Puncak fokus kamu pada jam {', '.join(profile.focus_peak_hours)}. Gunakan waktu ini untuk materi sulit!"
        })
    
    # Rekomendasi sederhana berdasarkan durasi fokus
    if profile.typical_focus_duration < 15:
        recommendations.append({
            "type": "technique",
            "title": "Teknik Pomodoro",
            "content": "Coba teknik Pomodoro: 15 menit fokus, 5 menit istirahat."
        })
    
    return {
        "success": True,
        "student_id": student_id,
        "recommendations": recommendations
    }


@app.get("/api/neuro-memory/chunks/{student_id}")
async def get_memory_chunks(student_id: str, limit: int = 100):
    """Dapatkan riwayat memory chunks siswa"""
    chunks = memory_engine.get_memory_chunks(student_id, limit=limit)
    return {
        "success": True,
        "student_id": student_id,
        "chunks": chunks
    }


class TrainModelPayload(BaseModel):
    model_name: str = "pandai_neuro_memory_v1"


@app.post("/api/neuro-memory/train")
async def train_neuro_memory_model(payload: TrainModelPayload = TrainModelPayload()):
    """Latih model Neuro-Memory dengan data yang ada"""
    try:
        # Ambil semua memory chunks dari semua siswa untuk training
        all_chunks = []
        # Kita perlu cara untuk mengambil semua chunks - untuk saat ini, kita gunakan contoh data dummy
        # Di production, kamu bisa query dari database
        
        # Contoh: Generate dummy data untuk testing training (jika tidak ada data nyata)
        from datetime import datetime, timedelta
        import random
        dummy_chunks = []
        for i in range(200):
            chunk = {
                "content_type": "biometric" if i % 2 == 0 else "quiz_result",
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "content": {
                    "focus_score": random.uniform(0.3, 0.95),
                    "eye_aspect_ratio": random.uniform(0.2, 0.4),
                    "blink_rate": random.uniform(5, 25),
                    "head_movement": random.uniform(0, 0.5),
                    "yaw": random.uniform(-0.2, 0.2),
                    "pitch": random.uniform(-0.2, 0.2),
                    "eye_movement": random.uniform(0, 0.6),
                    "score": random.uniform(0.5, 1.0),
                    "duration_seconds": random.uniform(30, 300),
                    "difficulty_level": random.randint(1, 5),
                    "attempt_count": random.randint(1, 3),
                    "correct_answers": random.randint(5, 10),
                    "total_questions": 10,
                    "session_duration_seconds": random.uniform(300, 3600),
                    "learning_effectiveness": random.uniform(0.4, 0.95)
                }
            }
            dummy_chunks.append(chunk)
        
        print(f"[Neuro-Memory] Training dengan {len(dummy_chunks)} dummy samples")
        
        # Prepare training data
        training_data = model_trainer.prepare_training_data(dummy_chunks)
        
        # Train model
        model_package = model_trainer.train_model(training_data)
        
        return {
            "success": True,
            "model_name": payload.model_name,
            "metrics": model_package["metrics"],
            "trained_at": model_package["trained_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal training model: {str(e)}")


class PredictPayload(BaseModel):
    features: List[float]


class ImportDatabasePayload(BaseModel):
    db_path: str = "../Siswa/Neuro-Client-Siswa/db/local_memory.db"
    student_id: Optional[str] = "NEURO_CLIENT_USER"


class ImportArchivePayload(BaseModel):
    archive_path: str
    student_id: Optional[str] = "ARCHIVE_USER"


@app.post("/api/neuro-memory/import-database")
async def import_from_database(payload: ImportDatabasePayload):
    """Impor data dari database Neuro-Client-Siswa"""
    try:
        db_path = Path(payload.db_path)
        count = memory_engine.import_from_neuro_client_database(db_path, payload.student_id)
        
        # Jika ada chunks yang diimpor, generate embedding untuk masing-masing
        if count > 0:
            chunks = memory_engine.get_memory_chunks(payload.student_id, limit=count)
            for chunk in chunks:
                if "neuro_client" in chunk.chunk_id:
                    embedding_text = f"{chunk.content_type}: {str(chunk.content)}"
                    embedding = embedding_store.generate_embedding(embedding_text)
                    embedding_store.add_vector(
                        chunk_id=chunk.chunk_id,
                        student_id=payload.student_id,
                        vector=embedding,
                        metadata={"content_type": chunk.content_type, "source": "neuro_client_import"}
                    )
        
        return {
            "success": True,
            "imported_count": count,
            "student_id": payload.student_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengimpor dari database: {str(e)}")


@app.post("/api/neuro-memory/import-archive")
async def import_from_archive(payload: ImportArchivePayload):
    """Impor data dari arsip Neuro-Client-Siswa (.csv.gz)"""
    try:
        archive_path = Path(payload.archive_path)
        count = memory_engine.import_from_archive(archive_path, payload.student_id)
        
        # Jika ada chunks yang diimpor, generate embedding untuk masing-masing
        if count > 0:
            chunks = memory_engine.get_memory_chunks(payload.student_id, limit=count)
            for chunk in chunks:
                if "archive" in chunk.chunk_id:
                    embedding_text = f"{chunk.content_type}: {str(chunk.content)}"
                    embedding = embedding_store.generate_embedding(embedding_text)
                    embedding_store.add_vector(
                        chunk_id=chunk.chunk_id,
                        student_id=payload.student_id,
                        vector=embedding,
                        metadata={"content_type": chunk.content_type, "source": "archive_import"}
                    )
        
        return {
            "success": True,
            "imported_count": count,
            "student_id": payload.student_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengimpor dari arsip: {str(e)}")


@app.post("/api/neuro-memory/predict")
async def predict_performance(payload: PredictPayload):
    """Prediksi kinerja belajar dengan model Neuro-Memory yang sudah dilatih"""
    try:
        model_package = model_trainer.load_model()
        if not model_package:
            raise HTTPException(status_code=404, detail="Model belum dilatih. Silakan training terlebih dahulu.")
        
        prediction = model_trainer.predict(model_package, payload.features)
        
        return {
            "success": True,
            "predicted_performance": prediction,
            "feature_names": model_package.get("feature_names", []),
            "model_trained_at": model_package.get("trained_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal prediksi: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Why: We run on port 3002, which is one of the allowed dev/server ports in global rules.
    uvicorn.run(app, host="0.0.0.0", port=3002)
