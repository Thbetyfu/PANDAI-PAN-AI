
# PAN-AI/skills/language_tutor_skill.py
# OpenClaw skill for Neuro-Language-Tutor: interactive language learning with LLM-powered responses,
# vocabulary lessons, grammar exercises, progress tracking, and speech interaction.

import os
from typing import Dict, Any, Optional
from datetime import datetime

# Import our existing Neuro-Language-Tutor modules
from neuro_language_tutor import (
    LanguageChatHandler,
    LessonGenerator,
    ProgressTracker,
    SpeechHandler
)

# Initialize components
chat_handler = LanguageChatHandler()
lesson_generator = LessonGenerator()
progress_tracker = ProgressTracker()
speech_handler = SpeechHandler()


def language_chat(
    student_id: str,
    user_message: str,
    language: str = "English",
    use_llm: bool = True,
    teacher_context: Optional[str] = None,
    teacher_persona: str = "strict_warm",
    correction_mode: str = "fluency_first",
    llm_mode: str = "auto"
) -> Dict[str, Any]:
    """
    OpenClaw skill: Interactive language chat with AI tutor.
    
    Args:
        student_id: Unique student identifier
        user_message: Student's message in the target language
        language: Target language (default: "English")
        use_llm: Whether to use LLM for responses (fallback to rule-based if False)
    
    Returns:
        Dictionary with assistant response, correction, explanation, and progress updates
    """
    timestamp = datetime.now().isoformat()
    
    # Add user message to history
    chat_handler.add_user_message(student_id, user_message, timestamp)
    
    assistant_msg = chat_handler.generate_assistant_response(
        student_id,
        teacher_context=teacher_context,
        teacher_persona=teacher_persona,
        correction_mode=correction_mode,
        llm_mode=llm_mode
    )
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "chat",
        "assistant_message": assistant_msg.content,
        "correction": assistant_msg.correction,
        "explanation": assistant_msg.explanation,
        "student_id": student_id,
        "language": language,
        "teacher_persona": teacher_persona,
        "correction_mode": correction_mode,
        "llm_mode": llm_mode,
        "timestamp": timestamp
    }


def generate_vocab_lesson(
    student_id: str,
    language: str = "English",
    topic: Optional[str] = None,
    difficulty: str = "beginner",
    count: int = 5
) -> Dict[str, Any]:
    """
    OpenClaw skill: Generate personalized vocabulary lesson.
    
    Args:
        student_id: Unique student identifier
        language: Target language (default: "English")
        topic: Optional topic for vocabulary (e.g., "food", "travel")
        difficulty: Difficulty level (beginner/intermediate/advanced)
        count: Number of vocabulary items to generate
    
    Returns:
        Dictionary with vocabulary lesson
    """
    vocab_items = lesson_generator.generate_vocab_lesson(
        student_id=student_id,
        language=language,
        topic=topic,
        difficulty=difficulty,
        count=count
    )
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "vocab_lesson",
        "student_id": student_id,
        "language": language,
        "topic": topic,
        "difficulty": difficulty,
        "vocabulary": [item.__dict__ for item in vocab_items],
        "timestamp": datetime.now().isoformat()
    }


def generate_grammar_lesson(
    student_id: str,
    language: str = "English",
    difficulty: str = "beginner",
    count: int = 3
) -> Dict[str, Any]:
    """
    OpenClaw skill: Generate personalized grammar lesson.
    
    Args:
        student_id: Unique student identifier
        language: Target language (default: "English")
        difficulty: Difficulty level (beginner/intermediate/advanced)
        count: Number of grammar exercises to generate
    
    Returns:
        Dictionary with grammar lesson
    """
    grammar_items = lesson_generator.generate_grammar_lesson(
        student_id=student_id,
        language=language,
        difficulty=difficulty,
        count=count
    )
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "grammar_lesson",
        "student_id": student_id,
        "language": language,
        "difficulty": difficulty,
        "grammar": [item.__dict__ for item in grammar_items],
        "timestamp": datetime.now().isoformat()
    }


def update_vocab_progress(
    student_id: str,
    word: str,
    is_correct: bool
) -> Dict[str, Any]:
    """
    OpenClaw skill: Update vocabulary progress for a student.
    
    Args:
        student_id: Unique student identifier
        word: The vocabulary word practiced
        is_correct: Whether the student answered correctly
    
    Returns:
        Dictionary with updated progress summary
    """
    progress_tracker.update_vocab_progress(
        student_id=student_id,
        word=word,
        is_correct=is_correct
    )
    
    summary = progress_tracker.get_student_summary(student_id)
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "update_progress",
        "student_id": student_id,
        "word_practiced": word,
        "is_correct": is_correct,
        "progress_summary": summary,
        "timestamp": datetime.now().isoformat()
    }


def increment_lesson_completed(student_id: str) -> Dict[str, Any]:
    """
    OpenClaw skill: Increment lesson completed count for a student.
    
    Args:
        student_id: Unique student identifier
    
    Returns:
        Dictionary with updated progress summary
    """
    progress_tracker.increment_lesson_completed(student_id)
    summary = progress_tracker.get_student_summary(student_id)
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "lesson_completed",
        "student_id": student_id,
        "progress_summary": summary,
        "timestamp": datetime.now().isoformat()
    }


def get_student_progress(student_id: str) -> Dict[str, Any]:
    """
    OpenClaw skill: Get complete progress summary for a student.
    
    Args:
        student_id: Unique student identifier
    
    Returns:
        Dictionary with complete progress summary
    """
    summary = progress_tracker.get_student_summary(student_id)
    if not summary:
        progress_tracker.get_or_create_student_progress(student_id)
        summary = progress_tracker.get_student_summary(student_id)
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "get_progress",
        "student_id": student_id,
        "progress_summary": summary,
        "timestamp": datetime.now().isoformat()
    }


def text_to_speech(text: str, language: str = "en", tts_mode: str = "local") -> Dict[str, Any]:
    """
    OpenClaw skill: Convert text to speech audio file.
    
    Args:
        text: Text to convert to speech
        language: Language code (default: "en")
    
    Returns:
        Dictionary with path to generated audio file
    """
    audio_path = speech_handler.text_to_speech(
        text=text,
        language=language,
        tts_mode=tts_mode
    )
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "text_to_speech",
        "text": text,
        "language": language,
        "tts_mode": tts_mode,
        "audio_path": str(audio_path) if audio_path else None,
        "timestamp": datetime.now().isoformat()
    }


def speech_to_text(
    audio_filepath: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    OpenClaw skill: Convert speech audio file to text.
    
    Args:
        audio_filepath: Path to audio file
        language: Language code (default: "en")
    
    Returns:
        Dictionary with transcribed text
    """
    transcribed_text = speech_handler.speech_to_text(
        audio_filepath=audio_filepath,
        language=language
    )
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "speech_to_text",
        "transcribed_text": transcribed_text,
        "language": language,
        "timestamp": datetime.now().isoformat()
    }


def get_chat_history(student_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    OpenClaw skill: Get chat conversation history for a student.
    
    Args:
        student_id: Unique student identifier
        limit: Optional limit on number of messages to retrieve
    
    Returns:
        Dictionary with chat history
    """
    history = chat_handler.get_conversation_history(student_id, limit=limit)
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "get_history",
        "student_id": student_id,
        "chat_history": [msg.__dict__ for msg in history],
        "timestamp": datetime.now().isoformat()
    }


def clear_chat_history(student_id: str) -> Dict[str, Any]:
    """
    OpenClaw skill: Clear chat conversation history for a student.
    
    Args:
        student_id: Unique student identifier
    
    Returns:
        Confirmation dictionary
    """
    chat_handler.clear_conversation(student_id)
    
    return {
        "success": True,
        "skill": "language_tutor",
        "action": "clear_history",
        "student_id": student_id,
        "message": "Chat history cleared successfully.",
        "timestamp": datetime.now().isoformat()
    }
