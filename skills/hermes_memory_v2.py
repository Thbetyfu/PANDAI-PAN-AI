# PAN-AI/skills/hermes_memory_v2.py
# Improved Hermes Memory System with Metadata and Versioning

import os
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
from pathlib import Path

MEMORIES_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memories")))

DEFAULT_USER_PROFILE = {
    "version": "1.0.0",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "learning_style": "Visual",
    "sleep_threshold_hours": 7,
    "baseline_heart_rate": 75,
    "average_attention_span_minutes": 20,
    "student_id": "",
    "personality_traits": [],
    "preferences": {},
    "metadata": {}
}

DEFAULT_LEARNING_LOG = {
    "version": "1.0.0",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "current_chapter": "Chapter 1 Introduction",
    "fatigue_count": 0,
    "stress_count": 0,
    "confusion_highlights": [],
    "retention_rate": 1.0,
    "lesson_history": [],
    "quiz_results": [],
    "biometric_events": [],
    "metadata": {}
}


def get_student_dir(student_id: str) -> Path:
    """Get the absolute path to the student's memory directory."""
    return MEMORIES_DIR / student_id


def get_version_history_path(student_id: str, record_type: str) -> Path:
    """Get path to version history directory for a specific record type."""
    student_dir = get_student_dir(student_id)
    history_dir = student_dir / "history" / record_type
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def save_version(student_id: str, record_type: str, data: Dict[str, Any], version: str) -> str:
    """Save a version of the data with timestamp."""
    history_path = get_version_history_path(student_id, record_type)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v{version}_{timestamp}.json"
    filepath = history_path / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }, f, indent=2, ensure_ascii=False)
    
    return str(filepath)


def load_user_profile(student_id: str) -> Dict[str, Any]:
    """
    Load user profile from HERMES_USER.json. Creates default if missing.
    Includes metadata and versioning.
    """
    student_dir = get_student_dir(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    
    profile_path = student_dir / "HERMES_USER.json"
    
    if not profile_path.exists():
        profile = DEFAULT_USER_PROFILE.copy()
        profile["student_id"] = student_id
        profile["created_at"] = datetime.now().isoformat()
        profile["updated_at"] = datetime.now().isoformat()
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return profile
    
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_user_profile(student_id: str, profile: Dict[str, Any], increment_version: bool = True) -> bool:
    """Save user profile with automatic versioning."""
    student_dir = get_student_dir(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    
    profile_path = student_dir / "HERMES_USER.json"
    
    # Get current version for history
    if profile_path.exists():
        with open(profile_path, "r", encoding="utf-8") as f:
            current_profile = json.load(f)
        current_version = current_profile.get("version", "1.0.0")
        save_version(student_id, "user", current_profile, current_version)
    
    # Update metadata
    if increment_version:
        version_parts = profile.get("version", "1.0.0").split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        profile["version"] = ".".join(version_parts)
    
    profile["updated_at"] = datetime.now().isoformat()
    profile["student_id"] = student_id
    
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    return True


def load_learning_log(student_id: str) -> Dict[str, Any]:
    """
    Load learning log from HERMES_LEARNING.json. Creates default if missing.
    Includes metadata and versioning.
    """
    student_dir = get_student_dir(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = student_dir / "HERMES_LEARNING.json"
    
    if not log_path.exists():
        log = DEFAULT_LEARNING_LOG.copy()
        log["created_at"] = datetime.now().isoformat()
        log["updated_at"] = datetime.now().isoformat()
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        return log
    
    with open(log_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_learning_log(student_id: str, log: Dict[str, Any], increment_version: bool = True) -> bool:
    """Save learning log with automatic versioning."""
    student_dir = get_student_dir(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = student_dir / "HERMES_LEARNING.json"
    
    # Get current version for history
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            current_log = json.load(f)
        current_version = current_log.get("version", "1.0.0")
        save_version(student_id, "learning", current_log, current_version)
    
    # Update metadata
    if increment_version:
        version_parts = log.get("version", "1.0.0").split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        log["version"] = ".".join(version_parts)
    
    log["updated_at"] = datetime.now().isoformat()
    
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    
    return True


def add_lesson_event(student_id: str, lesson_title: str, duration_minutes: int, 
                     focus_score: Optional[float] = None, notes: Optional[str] = None) -> bool:
    """Add a lesson event to learning log."""
    log = load_learning_log(student_id)
    
    event = {
        "id": f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": lesson_title,
        "duration_minutes": duration_minutes,
        "focus_score": focus_score,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    }
    
    log["lesson_history"].insert(0, event)
    log["lesson_history"] = log["lesson_history"][:1000]  # Keep last 1000 lessons
    return save_learning_log(student_id, log)


def add_quiz_result(student_id: str, quiz_title: str, score: float, 
                    total_questions: int, topic: Optional[str] = None) -> bool:
    """Add a quiz result to learning log."""
    log = load_learning_log(student_id)
    
    result = {
        "id": f"quiz_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": quiz_title,
        "score": score,
        "total_questions": total_questions,
        "topic": topic,
        "timestamp": datetime.now().isoformat()
    }
    
    log["quiz_results"].insert(0, result)
    log["quiz_results"] = log["quiz_results"][:1000]  # Keep last 1000 results
    return save_learning_log(student_id, log)


def add_biometric_event(student_id: str, event_type: str, metrics: Dict[str, Any],
                        reason: Optional[str] = None) -> bool:
    """Add a biometric event to learning log."""
    log = load_learning_log(student_id)
    
    event = {
        "id": f"bio_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": event_type,
        "metrics": metrics,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    
    log["biometric_events"].insert(0, event)
    log["biometric_events"] = log["biometric_events"][:1000]  # Keep last 1000 events
    
    # Update counters
    if event_type == "FATIGUE":
        log["fatigue_count"] = log.get("fatigue_count", 0) + 1
    elif event_type == "STRESS":
        log["stress_count"] = log.get("stress_count", 0) + 1
    
    return save_learning_log(student_id, log)


def get_memory_summary(student_id: str) -> Dict[str, Any]:
    """Get comprehensive summary of all student memory data."""
    profile = load_user_profile(student_id)
    log = load_learning_log(student_id)
    
    return {
        "success": True,
        "student_id": student_id,
        "user_profile": {
            "version": profile.get("version"),
            "learning_style": profile.get("learning_style"),
            "sleep_threshold_hours": profile.get("sleep_threshold_hours"),
            "baseline_heart_rate": profile.get("baseline_heart_rate"),
            "average_attention_span_minutes": profile.get("average_attention_span_minutes"),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at")
        },
        "learning_log": {
            "version": log.get("version"),
            "current_chapter": log.get("current_chapter"),
            "fatigue_count": log.get("fatigue_count"),
            "stress_count": log.get("stress_count"),
            "retention_rate": log.get("retention_rate"),
            "lesson_count": len(log.get("lesson_history", [])),
            "quiz_count": len(log.get("quiz_results", [])),
            "biometric_event_count": len(log.get("biometric_events", [])),
            "created_at": log.get("created_at"),
            "updated_at": log.get("updated_at")
        }
    }


# Backward compatibility functions
def load_student_memory(student_id: str) -> Dict[str, str]:
    """Load memory in old format for backward compatibility."""
    profile = load_user_profile(student_id)
    log = load_learning_log(student_id)
    
    # Convert to old string format for compatibility
    user_profile_str = f"""# Student Profile
- Learning Style: {profile.get('learning_style', 'Visual')}
- Sleep Threshold: {profile.get('sleep_threshold_hours', 7)} hours
- Baseline Heart Rate: {profile.get('baseline_heart_rate', 75)} bpm
- Average Attention Span: {profile.get('average_attention_span_minutes', 20)} minutes
"""
    
    learning_log_str = f"""# Learning Log
- Current Chapter: {log.get('current_chapter', 'Chapter 1 Introduction')}
- Fatigue Count: {log.get('fatigue_count', 0)}
- Stress Count: {log.get('stress_count', 0)}
- Confusion Highlights: {', '.join(log.get('confusion_highlights', ['None']))}
- Retention Rate: {log.get('retention_rate', 1.0)}
"""
    
    return {
        "user_profile": user_profile_str,
        "learning_log": learning_log_str
    }


def update_student_memory(student_id: str, user_profile: Optional[str] = None,
                         learning_log: Optional[str] = None) -> bool:
    """Update memory from old string format for backward compatibility."""
    if user_profile is not None:
        profile = load_user_profile(student_id)
        # Try to parse old format
        if "Learning Style:" in user_profile:
            for line in user_profile.split("\n"):
                line = line.strip()
                if line.startswith("- Learning Style:"):
                    profile["learning_style"] = line.split(":")[1].strip()
                elif line.startswith("- Sleep Threshold:"):
                    try:
                        profile["sleep_threshold_hours"] = int(line.split(":")[1].strip().split()[0])
                    except:
                        pass
                elif line.startswith("- Baseline Heart Rate:"):
                    try:
                        profile["baseline_heart_rate"] = int(line.split(":")[1].strip().split()[0])
                    except:
                        pass
                elif line.startswith("- Average Attention Span:"):
                    try:
                        profile["average_attention_span_minutes"] = int(line.split(":")[1].strip().split()[0])
                    except:
                        pass
        save_user_profile(student_id, profile)
    
    if learning_log is not None:
        log = load_learning_log(student_id)
        # Try to parse old format
        if "Current Chapter:" in learning_log:
            for line in learning_log.split("\n"):
                line = line.strip()
                if line.startswith("- Current Chapter:"):
                    log["current_chapter"] = line.split(":")[1].strip()
                elif line.startswith("- Fatigue Count:"):
                    try:
                        log["fatigue_count"] = int(line.split(":")[1].strip())
                    except:
                        pass
                elif line.startswith("- Stress Count:"):
                    try:
                        log["stress_count"] = int(line.split(":")[1].strip())
                    except:
                        pass
                elif line.startswith("- Retention Rate:"):
                    try:
                        log["retention_rate"] = float(line.split(":")[1].strip())
                    except:
                        pass
        save_learning_log(student_id, log)
    
    return True
