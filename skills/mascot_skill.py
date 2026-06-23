
# PAN-AI/skills/mascot_skill.py
# OpenClaw skill for PANDAI mascot expression mapping and interaction.

import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


# Path to mascot assets
MASCOT_DIR = Path(__file__).parent.parent / "assets" / "mascot" / "siswa"

# Mapping of cognitive states to mascot expressions
COGNITIVE_STATE_TO_MASCOT = {
    "NORMAL": "Happy",
    "MENGANTUK": "Ngantuk",
    "STRES": "Marah",
    "FRUSTRASI": "Nangis",
    "BINGUNG": "Bingung"
}

# Mapping of feedback types to mascot expressions
FEEDBACK_TO_MASCOT = {
    "positive": "Happy",
    "constructive": "Bingung",
    "neutral": "Idle",
    "encouragement": "Menyapa",
    "success": "Happy",
    "failure": "Bingung"
}

# All available mascot expressions
AVAILABLE_EXPRESSIONS = [
    "Happy",
    "Menyapa",
    "Idle",
    "Bingung",
    "Suprise",
    "Ngantuk",
    "Nangis",
    "Marah"
]


def get_mascot_expression(
    context: str,
    state: Optional[str] = None,
    feedback_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    OpenClaw skill: Get appropriate mascot expression based on context.
    
    Args:
        context: General context (e.g., "chat", "quiz", "learning")
        state: Optional student cognitive state (NORMAL/MENGANTUK/STRES/FRUSTRASI)
        feedback_type: Optional feedback type (positive/constructive/neutral)
    
    Returns:
        Dictionary with mascot expression and metadata
    """
    # Determine expression based on priority: state > feedback_type > context
    expression = "Idle"
    
    if state and state in COGNITIVE_STATE_TO_MASCOT:
        expression = COGNITIVE_STATE_TO_MASCOT[state]
    elif feedback_type and feedback_type in FEEDBACK_TO_MASCOT:
        expression = FEEDBACK_TO_MASCOT[feedback_type]
    elif context:
        # Context-based defaults
        if context == "chat":
            expression = "Menyapa"
        elif context == "quiz":
            expression = "Happy"
        elif context == "learning":
            expression = "Happy"
    
    # Validate expression is available
    if expression not in AVAILABLE_EXPRESSIONS:
        expression = "Happy"
    
    # Check if SVG file exists
    svg_path = MASCOT_DIR / f"{expression}.svg"
    file_exists = svg_path.exists()
    
    return {
        "success": True,
        "skill": "mascot",
        "action": "get_expression",
        "mascot_expression": expression,
        "context": context,
        "cognitive_state": state,
        "feedback_type": feedback_type,
        "file_exists": file_exists,
        "available_expressions": AVAILABLE_EXPRESSIONS,
        "timestamp": datetime.now().isoformat()
    }


def get_random_expression() -> Dict[str, Any]:
    """
    OpenClaw skill: Get a random mascot expression.
    
    Returns:
        Dictionary with random expression
    """
    import random
    expression = random.choice(AVAILABLE_EXPRESSIONS)
    
    return {
        "success": True,
        "skill": "mascot",
        "action": "random_expression",
        "mascot_expression": expression,
        "available_expressions": AVAILABLE_EXPRESSIONS,
        "timestamp": datetime.now().isoformat()
    }


def get_expression_for_answer(is_correct: bool) -> Dict[str, Any]:
    """
    OpenClaw skill: Get mascot expression for correct/incorrect answer.
    
    Args:
        is_correct: Whether the student's answer was correct
    
    Returns:
        Dictionary with appropriate expression
    """
    expression = "Happy" if is_correct else "Bingung"
    
    return {
        "success": True,
        "skill": "mascot",
        "action": "answer_expression",
        "mascot_expression": expression,
        "is_correct": is_correct,
        "timestamp": datetime.now().isoformat()
    }
