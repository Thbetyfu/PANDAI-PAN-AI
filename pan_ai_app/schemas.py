from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


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
    llmMode: str = Field("local", alias="llm_mode")
    llmProfile: str = Field("balanced", alias="llm_profile")

    class Config:
        populate_by_name = True


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


class TrainModelPayload(BaseModel):
    model_name: str = "pandai_neuro_memory_v1"


class PredictPayload(BaseModel):
    features: List[float]


class ImportDatabasePayload(BaseModel):
    db_path: str = "../Siswa/Neuro-Client-Siswa/db/local_memory.db"
    student_id: Optional[str] = "NEURO_CLIENT_USER"


class ImportArchivePayload(BaseModel):
    archive_path: str
    student_id: Optional[str] = "ARCHIVE_USER"


class LanguageChatMessagePayload(BaseModel):
    student_id: str
    content: str
    timestamp: Optional[str] = None
    language: str = "English"
    llm_mode: str = "local"
    llm_profile: str = "balanced"
    llm_model: Optional[str] = None


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


class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    tts_mode: str = "local"


class MascotExpressionRequest(BaseModel):
    context: str = "chat"
    cognitive_state: Optional[str] = None
    feedback_type: Optional[str] = None


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


class MemorySearchRequest(BaseModel):
    student_id: str
    query: str
    limit: int = 10
    content_type: Optional[str] = None


class OrchestratorRequest(BaseModel):
    user_input: str
    student_id: str = "default_student"
    language: str = "English"
    llm_mode: str = "local"
    llm_profile: str = "balanced"
    llm_model: Optional[str] = None

