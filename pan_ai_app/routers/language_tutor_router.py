from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..deps import chat_handler, get_temp_audio_dir, lesson_generator, progress_tracker, speech_handler
from ..schemas import (
    GrammarLessonPayload,
    LanguageChatMessagePayload,
    LanguageChatResponse,
    TTSRequest,
    UpdateVocabProgressPayload,
    VocabLessonPayload,
)


router = APIRouter()


@router.post("/api/language-tutor/chat", response_model=LanguageChatResponse)
async def language_chat(payload: LanguageChatMessagePayload):
    timestamp = payload.timestamp or datetime.now().isoformat()

    chat_handler.add_user_message(payload.student_id, payload.content, timestamp)

    assistant_msg = chat_handler.generate_assistant_response(
        payload.student_id,
        llm_mode=payload.llm_mode or "local",
        llm_profile=payload.llm_profile or "balanced",
        llm_model=payload.llm_model,
    )

    return LanguageChatResponse(
        success=True,
        assistant_message=assistant_msg.content,
        correction=assistant_msg.correction,
        explanation=assistant_msg.explanation,
    )


@router.get("/api/language-tutor/chat-history/{student_id}")
async def get_chat_history(student_id: str, limit: Optional[int] = None):
    history = chat_handler.get_conversation_history(student_id, limit=limit)
    return {"success": True, "student_id": student_id, "history": [msg.__dict__ for msg in history]}


@router.delete("/api/language-tutor/chat-history/{student_id}")
async def clear_chat_history(student_id: str):
    chat_handler.clear_conversation(student_id)
    return {"success": True, "student_id": student_id, "message": "Chat history cleared."}


@router.post("/api/language-tutor/generate-vocab-lesson")
async def generate_vocab_lesson(payload: VocabLessonPayload):
    vocab_items = lesson_generator.generate_vocab_lesson(
        student_id=payload.student_id,
        language=payload.language,
        topic=payload.topic,
        difficulty=payload.difficulty,
        count=payload.count,
    )
    return {
        "success": True,
        "student_id": payload.student_id,
        "language": payload.language,
        "vocabulary": [item.__dict__ for item in vocab_items],
    }


@router.post("/api/language-tutor/generate-grammar-lesson")
async def generate_grammar_lesson(payload: GrammarLessonPayload):
    grammar_items = lesson_generator.generate_grammar_lesson(
        student_id=payload.student_id,
        language=payload.language,
        difficulty=payload.difficulty,
        count=payload.count,
    )
    return {
        "success": True,
        "student_id": payload.student_id,
        "language": payload.language,
        "grammar": [item.__dict__ for item in grammar_items],
    }


@router.get("/api/language-tutor/progress/{student_id}")
async def get_student_progress(student_id: str):
    summary = progress_tracker.get_student_summary(student_id)
    if not summary:
        progress_tracker.get_or_create_student_progress(student_id)
        summary = progress_tracker.get_student_summary(student_id)
    return {"success": True, "student_id": student_id, "progress": summary}


@router.post("/api/language-tutor/update-vocab-progress")
async def update_vocab_progress(payload: UpdateVocabProgressPayload):
    progress_tracker.update_vocab_progress(
        student_id=payload.student_id,
        word=payload.word,
        is_correct=payload.is_correct,
    )
    return {"success": True, "student_id": payload.student_id, "word": payload.word, "is_correct": payload.is_correct}


@router.post("/api/language-tutor/increment-lesson-completed/{student_id}")
async def increment_lesson_completed(student_id: str):
    progress_tracker.increment_lesson_completed(student_id)
    return {"success": True, "student_id": student_id, "message": "Lesson completed count incremented."}


@router.post("/api/language-tutor/text-to-speech")
async def text_to_speech_endpoint(request: TTSRequest):
    try:
        audio_path = speech_handler.text_to_speech(
            text=request.text,
            language=request.language,
            tts_mode=request.tts_mode,
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
            filename=audio_path.name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")


@router.post("/api/language-tutor/speech-to-text")
async def speech_to_text_endpoint(file: UploadFile = File(...), language: str = "en"):
    try:
        temp_path = get_temp_audio_dir()
        temp_path.mkdir(parents=True, exist_ok=True)

        file_location = temp_path / (file.filename or "upload.wav")
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)

        text = speech_handler.speech_to_text(audio_filepath=str(file_location), language=language)

        try:
            os.remove(file_location)
        except Exception:
            pass

        return {"success": True, "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT Error: {str(e)}")

