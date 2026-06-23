
# PAN-AI Skills Package
# OpenClaw-compatible skills for PANDAI AI.

# Import all available skills
from . import digital_twin
from . import evaluate_biometrics
from . import generate_quiz
from . import language_tutor_skill
from . import memory_retrieval_skill
from . import feedback_generator_skill
from . import mascot_skill
from . import skill_orchestrator

# Export all skill modules
__all__ = [
    "digital_twin",
    "evaluate_biometrics",
    "generate_quiz",
    "language_tutor_skill",
    "memory_retrieval_skill",
    "feedback_generator_skill",
    "mascot_skill",
    "skill_orchestrator"
]
