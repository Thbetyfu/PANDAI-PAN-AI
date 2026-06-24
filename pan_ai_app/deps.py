from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from neuro_memory import MemoryEngine, EmbeddingStore, ModelTrainer
from neuro_language_tutor import LanguageChatHandler, LessonGenerator, ProgressTracker, SpeechHandler
from neuro_language_tutor.llm_handler import LLMHandler


PROJECT_ROOT = Path(__file__).resolve().parents[1]


memory_engine = MemoryEngine()
embedding_store = EmbeddingStore()
model_trainer = ModelTrainer()

chat_handler = LanguageChatHandler()
lesson_generator = LessonGenerator()
progress_tracker = ProgressTracker()
speech_handler = SpeechHandler()
llm_runtime = LLMHandler()


def get_ui_path() -> Path:
    return PROJECT_ROOT / "ui.html"


def get_mascot_dir() -> Path:
    return PROJECT_ROOT / "assets" / "mascot" / "siswa"


def get_temp_audio_dir() -> Path:
    base = os.getenv("PANDAI_DATA_DIR", "").strip()
    if base:
        return Path(base) / "temp_audio"
    return PROJECT_ROOT / "neuro_memory_storage" / "temp_audio"


def build_teacher_context_from_hermes_summary(summary: Dict[str, Any]) -> str:
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

