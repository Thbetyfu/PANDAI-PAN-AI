# PAN-AI/server.py
# Centralized FastAPI Server for PAN-AI Agent Services.

import os
from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from skills.hermes_memory_v2 import (
    load_user_profile, save_user_profile,
    load_learning_log, save_learning_log,
    add_lesson_event, add_quiz_result, add_biometric_event,
    get_memory_summary as get_hermes_summary,
    load_student_memory, update_student_memory
)
from skills.evaluate_biometrics import evaluate_student_state
from skills.generate_quiz import generate_educational_quiz
from skills.language_tutor_skill import (
    language_chat as openclaw_language_chat,
    generate_vocab_lesson as skill_vocab_lesson,
    generate_grammar_lesson as skill_grammar_lesson,
    update_vocab_progress as skill_update_progress,
    increment_lesson_completed as skill_increment_lesson,
    get_student_progress as skill_get_progress,
    text_to_speech as skill_tts,
    speech_to_text as skill_stt,
    get_chat_history as skill_get_chat_history,
    clear_chat_history as skill_clear_chat_history
)
from skills.memory_retrieval_skill import (
    search_memory,
    get_memory_summary,
    get_learning_patterns,
    get_personalized_recommendations
)
from skills.feedback_generator_skill import (
    generate_answer_feedback,
    generate_quiz_feedback,
    generate_progress_feedback,
    generate_encouragement
)
from skills.mascot_skill import (
    get_mascot_expression,
    get_random_expression,
    get_expression_for_answer
)
from skills.skill_orchestrator import orchestrator

# Import Neuro-Memory modules
from neuro_memory import MemoryEngine, EmbeddingStore, ModelTrainer
from pathlib import Path

# Import Neuro-Language-Tutor modules
from neuro_language_tutor import LanguageChatHandler, LessonGenerator, ProgressTracker, SpeechHandler
from neuro_language_tutor.llm_handler import LLMHandler

app = FastAPI(
    title="PAN-AI Core Service",
    description="Centralized AI Agent Gateway with OpenClaw skills and Hermes-style memory storage + Neuro-Memory Foundation Model."
)

def _build_teacher_context_from_hermes_summary(summary: Dict[str, Any]) -> str:
    user_profile = summary.get("user_profile") or {}
    learning_log = summary.get("learning_log") or {}

    learning_style = user_profile.get("learning_style")
    attention_span = user_profile.get("average_attention_span_minutes")
    current_chapter = learning_log.get("current_chapter")
    retention_rate = learning_log.get("retention_rate")
    fatigue_count = learning_log.get("fatigue_count")
    stress_count = learning_log.get("stress_count")

    lines: List[str] = []
    if learning_style:
        lines.append(f"Learning style: {learning_style}")
    if attention_span is not None:
        lines.append(f"Typical attention span: {attention_span} minutes")
    if current_chapter:
        lines.append(f"Current chapter: {current_chapter}")
    if retention_rate is not None:
        lines.append(f"Retention rate (self-tracked): {retention_rate}")
    if fatigue_count is not None:
        lines.append(f"Fatigue events count: {fatigue_count}")
    if stress_count is not None:
        lines.append(f"Stress events count: {stress_count}")

    if not lines:
        return ""

    context = "\n".join(lines).strip()
    return context[:1500]


@app.get("/")
async def root_ui():
    ui_path = Path(__file__).parent / "ui.html"
    if ui_path.exists():
        return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))
    return {"success": True, "message": "UI file not found. Open /docs for API documentation."}


@app.get("/ui")
async def ui():
    ui_path = Path(__file__).parent / "ui.html"
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="UI file not found.")
    return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))

# Inisialisasi Neuro-Memory services
memory_engine = MemoryEngine()
embedding_store = EmbeddingStore()
model_trainer = ModelTrainer()

# Inisialisasi Neuro-Language-Tutor services
chat_handler = LanguageChatHandler()
lesson_generator = LessonGenerator()
progress_tracker = ProgressTracker()
speech_handler = SpeechHandler()

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

        # Update Hermes Memory v2 with biometric event
        if state != "NORMAL":
            add_biometric_event(
                student_id=payload.studentId,
                event_type=state,
                metrics={
                    "heart_rate": payload.heartRate,
                    "hrv": payload.hrv,
                    "ear": payload.ear,
                    "gsr": payload.gsr,
                    "focus_score": payload.focusScore
                },
                reason=reason
            )

        return {
            "success": True,
            "student_id": payload.studentId,
            "cognitive_state": state,
            "reason": reason,
            "intervention_recommended": state != "NORMAL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal evaluation error: {str(e)}")


# --- Hermes Memory v2 Endpoints ---
class UpdateUserProfileRequest(BaseModel):
    learning_style: Optional[str] = None
    sleep_threshold_hours: Optional[int] = None
    baseline_heart_rate: Optional[int] = None
    average_attention_span_minutes: Optional[int] = None
    personality_traits: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class AddLessonEventRequest(BaseModel):
    lesson_title: str
    duration_minutes: int
    focus_score: Optional[float] = None
    notes: Optional[str] = None


class AddQuizResultRequest(BaseModel):
    quiz_title: str
    score: float
    total_questions: int
    topic: Optional[str] = None


@app.get("/api/hermes/v2/profile/{student_id}")
async def hermes_get_profile(student_id: str):
    """Get student's Hermes profile (v2)."""
    profile = load_user_profile(student_id)
    return {"success": True, "student_id": student_id, "profile": profile}


@app.put("/api/hermes/v2/profile/{student_id}")
async def hermes_update_profile(student_id: str, payload: UpdateUserProfileRequest):
    """Update student's Hermes profile (v2)."""
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


@app.get("/api/hermes/v2/learning-log/{student_id}")
async def hermes_get_learning_log(student_id: str):
    """Get student's Hermes learning log (v2)."""
    log = load_learning_log(student_id)
    return {"success": True, "student_id": student_id, "learning_log": log}


@app.post("/api/hermes/v2/learning-log/{student_id}/lesson")
async def hermes_add_lesson_event(student_id: str, payload: AddLessonEventRequest):
    """Add lesson event to Hermes learning log (v2)."""
    add_lesson_event(
        student_id=student_id,
        lesson_title=payload.lesson_title,
        duration_minutes=payload.duration_minutes,
        focus_score=payload.focus_score,
        notes=payload.notes
    )
    return {"success": True, "student_id": student_id, "message": "Lesson event added"}


@app.post("/api/hermes/v2/learning-log/{student_id}/quiz")
async def hermes_add_quiz_result(student_id: str, payload: AddQuizResultRequest):
    """Add quiz result to Hermes learning log (v2)."""
    add_quiz_result(
        student_id=student_id,
        quiz_title=payload.quiz_title,
        score=payload.score,
        total_questions=payload.total_questions,
        topic=payload.topic
    )
    return {"success": True, "student_id": student_id, "message": "Quiz result added"}


@app.get("/api/hermes/v2/summary/{student_id}")
async def hermes_get_summary(student_id: str):
    """Get comprehensive summary of student's Hermes memory (v2)."""
    summary = get_hermes_summary(student_id)
    return summary


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


# --- Neuro-Language-Tutor Models ---
class LanguageChatMessagePayload(BaseModel):
    student_id: str
    content: str
    timestamp: Optional[str] = None
    language: str = "English"
    llm_mode: str = "local"


class LanguageChatResponse(BaseModel):
    success: bool
    assistant_message: str
    correction: Optional[str] = None
    explanation: Optional[str] = None


class VocabLessonPayload(BaseModel):
    student_id: str
    language: str = "English"
    topic: Optional[str] = None
    difficulty: str = "beginner"
    count: int = 5


class GrammarLessonPayload(BaseModel):
    student_id: str
    language: str = "English"
    difficulty: str = "beginner"
    count: int = 3


class UpdateVocabProgressPayload(BaseModel):
    student_id: str
    word: str
    is_correct: bool


# --- Neuro-Language-Tutor Endpoints ---
@app.post("/api/language-tutor/chat", response_model=LanguageChatResponse)
async def language_chat(payload: LanguageChatMessagePayload):
    """
    Endpoint chat bahasa: Kirim pesan user, dapatkan balasan AI + koreksi otomatis.
    """
    from datetime import datetime
    timestamp = payload.timestamp or datetime.now().isoformat()
    
    # Tambahkan pesan user ke riwayat
    chat_handler.add_user_message(payload.student_id, payload.content, timestamp)
    
    # Generate response AI menggunakan LLM
    assistant_msg = chat_handler.generate_assistant_response(payload.student_id)
    
    return LanguageChatResponse(
        success=True,
        assistant_message=assistant_msg.content,
        correction=assistant_msg.correction,
        explanation=assistant_msg.explanation
    )


@app.get("/api/language-tutor/chat-history/{student_id}")
async def get_chat_history(student_id: str, limit: Optional[int] = None):
    """Dapatkan riwayat chat bahasa siswa."""
    history = chat_handler.get_conversation_history(student_id, limit=limit)
    return {
        "success": True,
        "student_id": student_id,
        "history": [msg.__dict__ for msg in history]
    }


@app.delete("/api/language-tutor/chat-history/{student_id}")
async def clear_chat_history(student_id: str):
    """Hapus riwayat chat bahasa siswa."""
    chat_handler.clear_conversation(student_id)
    return {"success": True, "student_id": student_id, "message": "Chat history cleared."}


# --- Lesson Generator Endpoints ---
@app.post("/api/language-tutor/generate-vocab-lesson")
async def generate_vocab_lesson(payload: VocabLessonPayload):
    """Generate latihan kosa kata personal."""
    vocab_items = lesson_generator.generate_vocab_lesson(
        student_id=payload.student_id,
        language=payload.language,
        topic=payload.topic,
        difficulty=payload.difficulty,
        count=payload.count
    )
    return {
        "success": True,
        "student_id": payload.student_id,
        "language": payload.language,
        "vocabulary": [item.__dict__ for item in vocab_items]
    }


@app.post("/api/language-tutor/generate-grammar-lesson")
async def generate_grammar_lesson(payload: GrammarLessonPayload):
    """Generate latihan tata bahasa personal."""
    grammar_items = lesson_generator.generate_grammar_lesson(
        student_id=payload.student_id,
        language=payload.language,
        difficulty=payload.difficulty,
        count=payload.count
    )
    return {
        "success": True,
        "student_id": payload.student_id,
        "language": payload.language,
        "grammar": [item.__dict__ for item in grammar_items]
    }


# --- Progress Tracker Endpoints ---
@app.get("/api/language-tutor/progress/{student_id}")
async def get_student_progress(student_id: str):
    """Dapatkan ringkasan progress belajar siswa."""
    summary = progress_tracker.get_student_summary(student_id)
    if not summary:
        # Buat progress baru jika tidak ada
        progress_tracker.get_or_create_student_progress(student_id)
        summary = progress_tracker.get_student_summary(student_id)
    return {"success": True, "student_id": student_id, "progress": summary}


@app.post("/api/language-tutor/update-vocab-progress")
async def update_vocab_progress(payload: UpdateVocabProgressPayload):
    """Update progress kosa kata siswa (ketika jawaban benar/salah)."""
    progress_tracker.update_vocab_progress(
        student_id=payload.student_id,
        word=payload.word,
        is_correct=payload.is_correct
    )
    return {
        "success": True,
        "student_id": payload.student_id,
        "word": payload.word,
        "is_correct": payload.is_correct
    }


@app.post("/api/language-tutor/increment-lesson-completed/{student_id}")
async def increment_lesson_completed(student_id: str):
    """Tambahkan jumlah lesson yang selesai."""
    progress_tracker.increment_lesson_completed(student_id)
    return {"success": True, "student_id": student_id, "message": "Lesson completed count incremented."}


# --- Speech Endpoints ---
class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    tts_mode: str = "local"

@app.post("/api/language-tutor/text-to-speech")
async def text_to_speech_endpoint(request: TTSRequest):
    """Convert text ke speech dan return file audio."""
    try:
        audio_path = speech_handler.text_to_speech(
            text=request.text,
            language=request.language,
            tts_mode=request.tts_mode
        )
        
        if not audio_path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate audio")

        suffix = audio_path.suffix.lower()
        media_type = "audio/mpeg"
        if suffix == ".wav":
            media_type = "audio/wav"
        elif suffix == ".ogg":
            media_type = "audio/ogg"
        
        return FileResponse(
            path=str(audio_path),
            media_type=media_type,
            filename=audio_path.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

@app.post("/api/language-tutor/speech-to-text")
async def speech_to_text_endpoint(
    file: UploadFile = File(...),
    language: str = "en"
):
    """Upload file audio dan convert ke text."""
    try:
        # Simpan file temporary
        temp_path = Path("neuro_memory_storage") / "temp_audio"
        temp_path.mkdir(parents=True, exist_ok=True)
        
        file_location = temp_path / file.filename
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Convert speech to text
        text = speech_handler.speech_to_text(
            audio_filepath=str(file_location),
            language=language
        )
        
        # Hapus file temporary
        try:
            os.remove(file_location)
        except:
            pass
        
        return {"success": True, "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT Error: {str(e)}")


# --- Mascot Endpoints ---
@app.get("/api/mascot/siswa/expressions")
async def get_siswa_mascot_expressions():
    """Dapatkan daftar semua ekspresi maskot Siswa yang tersedia."""
    mascot_dir = Path("assets/mascot/siswa")
    expressions = []
    for svg_file in mascot_dir.glob("*.svg"):
        expressions.append(svg_file.stem)
    
    return {"success": True, "expressions": sorted(expressions)}


@app.get("/api/mascot/siswa/{expression}")
async def get_siswa_mascot(expression: str):
    """Dapatkan SVG maskot Siswa dengan ekspresi tertentu.
    
    Ekspresi yang tersedia: Happy, Menyapa, Idle, Bingung, Suprise, Ngantuk, Nangis, Marah
    """
    mascot_dir = Path("assets/mascot/siswa")
    svg_file = mascot_dir / f"{expression}.svg"
    
    if not svg_file.exists():
        # Fallback ke Happy jika ekspresi tidak ditemukan
        svg_file = mascot_dir / "Happy.svg"
        if not svg_file.exists():
            raise HTTPException(status_code=404, detail=f"Mascot dengan ekspresi '{expression}' tidak ditemukan.")
    
    return FileResponse(
        path=str(svg_file),
        media_type="image/svg+xml",
        filename=f"pandai-siswa-{expression.lower()}.svg"
    )


# --- OpenClaw Skill Endpoints ---

# Mascot Skill Endpoints
class MascotExpressionRequest(BaseModel):
    context: str = "chat"
    cognitive_state: Optional[str] = None
    feedback_type: Optional[str] = None


@app.post("/api/skills/mascot/expression")
async def skill_get_mascot_expression(payload: MascotExpressionRequest):
    """Dapatkan ekspresi maskot berdasarkan konteks, state kognitif, atau tipe feedback."""
    result = get_mascot_expression(
        context=payload.context,
        state=payload.cognitive_state,
        feedback_type=payload.feedback_type
    )
    return result


@app.get("/api/skills/mascot/random")
async def skill_get_random_expression():
    """Dapatkan ekspresi maskot acak."""
    return get_random_expression()


@app.get("/api/skills/mascot/answer/{is_correct}")
async def skill_get_answer_expression(is_correct: bool):
    """Dapatkan ekspresi maskot untuk jawaban benar/salah."""
    return get_expression_for_answer(is_correct)


# Feedback Generator Skill Endpoints
class AnswerFeedbackRequest(BaseModel):
    student_id: str
    question: str
    student_answer: str
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    subject: str = "Umum"


class QuizFeedbackRequest(BaseModel):
    student_id: str
    quiz_results: List[Dict[str, Any]]
    total_score: float
    topic: str = "Umum"


class ProgressFeedbackRequest(BaseModel):
    student_id: str
    progress_summary: Dict[str, Any]
    time_period: str = "Minggu Ini"


class EncouragementRequest(BaseModel):
    student_id: str
    context: str = "umum"
    student_state: Optional[str] = None


@app.post("/api/skills/feedback/answer")
async def skill_generate_answer_feedback(payload: AnswerFeedbackRequest):
    """Generate feedback personal untuk jawaban siswa."""
    result = generate_answer_feedback(
        student_id=payload.student_id,
        question=payload.question,
        student_answer=payload.student_answer,
        correct_answer=payload.correct_answer,
        is_correct=payload.is_correct,
        subject=payload.subject
    )
    return result


@app.post("/api/skills/feedback/quiz")
async def skill_generate_quiz_feedback(payload: QuizFeedbackRequest):
    """Generate feedback komprehensif untuk kuis."""
    result = generate_quiz_feedback(
        student_id=payload.student_id,
        quiz_results=payload.quiz_results,
        total_score=payload.total_score,
        topic=payload.topic
    )
    return result


@app.post("/api/skills/feedback/progress")
async def skill_generate_progress_feedback(payload: ProgressFeedbackRequest):
    """Generate feedback tentang progress belajar siswa."""
    result = generate_progress_feedback(
        student_id=payload.student_id,
        progress_summary=payload.progress_summary,
        time_period=payload.time_period
    )
    return result


@app.post("/api/skills/feedback/encouragement")
async def skill_generate_encouragement(payload: EncouragementRequest):
    """Generate pesan dorongan untuk siswa."""
    result = generate_encouragement(
        student_id=payload.student_id,
        context=payload.context,
        student_state=payload.student_state
    )
    return result


# Memory Retrieval Skill Endpoints
class MemorySearchRequest(BaseModel):
    student_id: str
    query: str
    limit: int = 10
    content_type: Optional[str] = None


@app.post("/api/skills/memory/search")
async def skill_search_memory(payload: MemorySearchRequest):
    """Cari memory siswa berdasarkan query."""
    result = search_memory(
        student_id=payload.student_id,
        query=payload.query,
        limit=payload.limit,
        content_type=payload.content_type
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error searching memory"))
    return result


@app.get("/api/skills/memory/summary/{student_id}")
async def skill_get_memory_summary(student_id: str):
    """Dapatkan ringkasan memory siswa."""
    result = get_memory_summary(student_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error getting memory summary"))
    return result


@app.get("/api/skills/memory/patterns/{student_id}")
async def skill_get_learning_patterns(student_id: str):
    """Analisis pola belajar siswa."""
    result = get_learning_patterns(student_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error analyzing patterns"))
    return result


@app.get("/api/skills/memory/recommendations/{student_id}")
async def skill_get_personalized_recommendations(student_id: str):
    """Dapatkan rekomendasi belajar personalisasi."""
    result = get_personalized_recommendations(student_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error getting recommendations"))
    return result


# Language Tutor Skill Endpoints
@app.post("/api/skills/language-tutor/chat")
async def skill_language_chat_endpoint(payload: LanguageChatMessagePayload):
    """Chat bahasa dengan AI tutor via OpenClaw skill."""
    teacher_context = ""
    try:
        hermes_summary = get_hermes_summary(payload.student_id)
        if isinstance(hermes_summary, dict) and hermes_summary.get("success"):
            teacher_context = _build_teacher_context_from_hermes_summary(hermes_summary)
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
        llm_mode=payload.llm_mode or "local"
    )
    return result


@app.get("/api/skills/language-tutor/progress/{student_id}")
async def skill_get_language_progress(student_id: str):
    """Dapatkan progress bahasa siswa via OpenClaw skill."""
    return skill_get_progress(student_id)


@app.post("/api/skills/language-tutor/increment-lesson/{student_id}")
async def skill_increment_language_lesson(student_id: str):
    """Tambahkan lesson yang selesai via OpenClaw skill."""
    return skill_increment_lesson(student_id)


@app.get("/api/skills/language-tutor/history/{student_id}")
async def skill_get_language_history(student_id: str, limit: Optional[int] = None):
    """Dapatkan riwayat chat bahasa via OpenClaw skill."""
    return skill_get_chat_history(student_id, limit)


@app.delete("/api/skills/language-tutor/history/{student_id}")
async def skill_clear_language_history(student_id: str):
    """Hapus riwayat chat bahasa via OpenClaw skill."""
    return skill_clear_chat_history(student_id)


# Skill Orchestrator Endpoints
class OrchestratorRequest(BaseModel):
    user_input: str
    student_id: str = "default_student"
    language: str = "English"
    llm_mode: str = "local"


@app.post("/api/orchestrator/recognize-intent")
async def orchestrator_recognize_intent(payload: OrchestratorRequest):
    """Recognize user's intent using Skill Orchestrator."""
    intent = orchestrator.recognize_intent(payload.user_input)
    return {
        "success": True,
        "user_input": payload.user_input,
        "intent": intent.value
    }


@app.post("/api/orchestrator/orchestrate")
async def orchestrator_orchestrate(payload: OrchestratorRequest):
    """Main orchestration endpoint: analyzes input and returns recommended skills."""
    result = orchestrator.orchestrate(payload.user_input, payload.student_id)
    return result


@app.post("/api/orchestrator/execute")
async def orchestrator_execute(payload: OrchestratorRequest):
    intent = orchestrator.recognize_intent(payload.user_input)

    teacher_context = ""
    try:
        hermes_summary = get_hermes_summary(payload.student_id)
        if isinstance(hermes_summary, dict) and hermes_summary.get("success"):
            teacher_context = _build_teacher_context_from_hermes_summary(hermes_summary)
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
        llm_mode=payload.llm_mode or "local"
    )

    feedback_type = "constructive" if tutor_result.get("correction") else "positive"
    mascot_result = get_mascot_expression(context="chat", feedback_type=feedback_type)

    encouragement_context = "kesulitan" if tutor_result.get("correction") else "keberhasilan"
    feedback_result = generate_encouragement(
        student_id=payload.student_id,
        context=encouragement_context,
        student_state=None
    )

    return {
        "success": True,
        "intent": intent.value,
        "student_id": payload.student_id,
        "language": payload.language,
        "teacher_persona": "strict_warm",
        "correction_mode": "fluency_first",
        "llm_mode": payload.llm_mode or "local",
        "teacher_context_used": bool(teacher_context),
        "hermes_summary_ok": bool(isinstance(hermes_summary, dict) and hermes_summary.get("success")),
        "tutor": tutor_result,
        "mascot": mascot_result,
        "feedback": feedback_result
    }


@app.get("/api/config/llm")
async def get_llm_config():
    llm = LLMHandler()
    tts = speech_handler.get_tts_config()
    return {
        "success": True,
        "recommended_default": "local",
        "provider_order": os.getenv("PANDAI_LLM_ORDER", "ollama,openai,fallback"),
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            "model": os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"),
            "available": llm.is_ollama_available()
        },
        "openai_compatible": {
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "has_api_key": bool(os.getenv("OPENAI_API_KEY"))
        },
        "api_template_env": [
            "OPENAI_API_KEY=YOUR_KEY_HERE",
            "OPENAI_BASE_URL=https://api.openai.com/v1",
            "OPENAI_MODEL=gpt-4o-mini",
            "PANDAI_LLM_ORDER=ollama,openai,fallback"
        ],
        "tts": tts
    }


@app.post("/api/orchestrator/get-skills-for-intent")
async def orchestrator_get_skills(intent: str = "chat"):
    """Get recommended skills for a specific intent."""
    from skills.skill_orchestrator import Intent
    try:
        intent_enum = Intent(intent)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid intent: {intent}")
    
    skills = orchestrator.get_skills_for_intent(intent_enum)
    return {
        "success": True,
        "intent": intent,
        "recommended_skills": skills,
        "total_skills": len(skills)
    }


if __name__ == "__main__":
    import uvicorn
    # Why: We run on port 3004, avoiding conflicts with LMS ports 30001 and 3002.
    uvicorn.run(app, host="0.0.0.0", port=3004)
