# PAN-AI/skills/digital_twin.py
# Module for managing student's cognitive Digital Twin using Hermes-style memory profiles.

import os
from typing import Dict, Optional

MEMORIES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memories"))

DEFAULT_USER_TEMPLATE = """# Student Profile
- Learning Style: Visual
- Sleep Threshold: 7 hours
- Baseline Heart Rate: 75 bpm
- Average Attention Span: 20 minutes
"""

DEFAULT_MEMORY_TEMPLATE = """# Learning Log
- Current Chapter: Chapter 1 Introduction
- Fatigue Count: 0
- Stress Count: 0
- Confusion Highlights: None
- Retention Rate: 1.0
"""


def get_student_dir(student_id: str) -> str:
    """
    Get the absolute path to the student's memory directory.
    
    Why: Keeps student files strictly separated by ID to prevent cross-contamination
    of biometric profiles and ensure privacy compliance.
    """
    return os.path.join(MEMORIES_DIR, student_id)


def load_student_memory(student_id: str) -> Dict[str, str]:
    """
    Load USER.md and MEMORY.md for a given student ID. Creates defaults if missing.
    
    Why: Initiating profiles dynamically allows seamless onboarding of new students
    without manual pre-registration steps in the AI system.
    """
    student_dir = get_student_dir(student_id)
    os.makedirs(student_dir, exist_ok=True)

    user_path = os.path.join(student_dir, "USER.md")
    memory_path = os.path.join(student_dir, "MEMORY.md")

    # Write default if USER.md doesn't exist
    if not os.path.exists(user_path):
        with open(user_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_USER_TEMPLATE)

    # Write default if MEMORY.md doesn't exist
    if not os.path.exists(memory_path):
        with open(memory_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_MEMORY_TEMPLATE)

    with open(user_path, "r", encoding="utf-8") as f:
        user_content = f.read()

    with open(memory_path, "r", encoding="utf-8") as f:
        memory_content = f.read()

    return {
        "user_profile": user_content,
        "learning_log": memory_content
    }


def update_student_memory(
    student_id: str,
    user_profile: Optional[str] = None,
    learning_log: Optional[str] = None
) -> bool:
    """
    Overwrite or update the student's profile or learning log files.
    
    Why: Digital Twins must reflect real-time changes in cognitive load and
    spaced repetition metrics immediately after each learning session to remain accurate.
    """
    student_dir = get_student_dir(student_id)
    os.makedirs(student_dir, exist_ok=True)

    if user_profile is not None:
        user_path = os.path.join(student_dir, "USER.md")
        with open(user_path, "w", encoding="utf-8") as f:
            f.write(user_profile)

    if learning_log is not None:
        memory_path = os.path.join(student_dir, "MEMORY.md")
        with open(memory_path, "w", encoding="utf-8") as f:
            f.write(learning_log)

    return True
