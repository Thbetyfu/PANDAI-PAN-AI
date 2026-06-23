
# PAN-AI/skills/skill_orchestrator.py
# OpenClaw Skill Orchestrator: Automatically determines which skills to execute based on context.

import re
from typing import Dict, Any, List, Optional
from enum import Enum


class SkillCategory(Enum):
    LANGUAGE_TUTOR = "language_tutor"
    FEEDBACK = "feedback"
    MEMORY = "memory"
    MASCOT = "mascot"
    QUIZ = "quiz"
    BIOMETRICS = "biometrics"


class Intent(Enum):
    # Language tutor intents
    CHAT = "chat"
    LEARN_VOCAB = "learn_vocab"
    LEARN_GRAMMAR = "learn_grammar"
    PRACTICE_LANGUAGE = "practice_language"
    GET_LANGUAGE_PROGRESS = "get_language_progress"
    
    # Feedback intents
    GET_ANSWER_FEEDBACK = "get_answer_feedback"
    GET_QUIZ_FEEDBACK = "get_quiz_feedback"
    GET_ENCOURAGEMENT = "get_encouragement"
    
    # Memory intents
    SEARCH_MEMORY = "search_memory"
    GET_MEMORY_SUMMARY = "get_memory_summary"
    GET_LEARNING_PATTERNS = "get_learning_patterns"
    GET_RECOMMENDATIONS = "get_recommendations"
    
    # Mascot intents
    GET_MASCOT = "get_mascot"
    
    # Quiz intents
    GENERATE_QUIZ = "generate_quiz"
    
    # Biometrics intents
    EVALUATE_BIOMETRICS = "evaluate_biometrics"
    
    # Unknown
    UNKNOWN = "unknown"


class SkillOrchestrator:
    """
    Skill Orchestrator that analyzes user input and determines which skills to execute.
    
    Key features:
    - Intent recognition using keyword matching (easily extendable to LLM-based)
    - Skill chaining recommendations
    - Context-aware decision making
    """
    
    def __init__(self):
        # Keyword patterns for intent recognition
        self.intent_patterns = {
            # Language tutor
            Intent.CHAT: [
                r"\b(chat|talk|bicar|berbicara|berkomunikasi)\b",
                r"\b(hello|hi|hai|halo)\b",
                r"\b(bagaimana|how)\b.*\b(kabar|anda|kamu|you)\b"
            ],
            Intent.LEARN_VOCAB: [
                r"\b(vocab|vocabulary|kosa kata|kata kata)\b",
                r"\b(learn|pelajari|belajar)\b.*\b(kata|kata-kata|word)\b"
            ],
            Intent.LEARN_GRAMMAR: [
                r"\b(grammar|tata bahasa|bahasa)\b",
                r"\b(learn|pelajari|belajar)\b.*\b(tata bahasa|grammar)\b"
            ],
            Intent.GET_LANGUAGE_PROGRESS: [
                r"\b(progress|kemajuan|kemampuan)\b.*\b(bahasa|language)\b",
                r"\b(berapa|how)\b.*\b(kemajuan|progress)\b"
            ],
            Intent.PRACTICE_LANGUAGE: [
                r"\b(practice|latih|berlatih)\b",
                r"\b(quiz|kuis)\b.*\b(bahasa|language)\b"
            ],
            
            # Feedback
            Intent.GET_ANSWER_FEEDBACK: [
                r"\b(answer|jawaban)\b.*\b(feedback|koreksi|cek)\b",
                r"\b(benar|salah|correct|wrong)\b.*\b(jawaban|answer)\b"
            ],
            Intent.GET_QUIZ_FEEDBACK: [
                r"\b(quiz|kuis)\b.*\b(feedback|hasil|result)\b",
                r"\b(berapa|how much)\b.*\b(nilai|score)\b"
            ],
            Intent.GET_ENCOURAGEMENT: [
                r"\b(lelah|tired|capek)\b",
                r"\b(sulit|difficult|hard)\b",
                r"\b(motivasi|motivation|semangat)\b"
            ],
            
            # Memory
            Intent.SEARCH_MEMORY: [
                r"\b(remember|ingat|kenang)\b",
                r"\b(cari|search|find)\b.*\b(memory|memori)\b"
            ],
            Intent.GET_MEMORY_SUMMARY: [
                r"\b(summary|ringkasan)\b.*\b(memory|memori)\b",
                r"\b(profile|profil)\b.*\b(saya|me|aku)\b"
            ],
            Intent.GET_LEARNING_PATTERNS: [
                r"\b(pola|pattern)\b.*\b(belajar|learning)\b",
                r"\b(analisis|analyze)\b.*\b(belajar|learning)\b"
            ],
            Intent.GET_RECOMMENDATIONS: [
                r"\b(rekomendasi|recommendation)\b",
                r"\b(saran|advice)\b.*\b(belajar|learning)\b"
            ],
            
            # Mascot
            Intent.GET_MASCOT: [
                r"\b(mascot|maskot)\b",
                r"\b(gambar|picture)\b.*\b(panda|maskot)\b"
            ],
            
            # Quiz
            Intent.GENERATE_QUIZ: [
                r"\b(generate|buat)\b.*\b(quiz|kuis)\b",
                r"\b(soal|pertanyaan)\b.*\b(baru|new)\b"
            ],
            
            # Biometrics
            Intent.EVALUATE_BIOMETRICS: [
                r"\b(stres|stress)\b",
                r"\b(lelah|tired)\b",
                r"\b(heart rate|denyut jantung|hrv)\b"
            ]
        }
    
    def recognize_intent(self, user_input: str) -> Intent:
        """
        Recognize user's intent based on their input text.
        
        Args:
            user_input: The user's text input
            
        Returns:
            Intent: The recognized intent
        """
        if not user_input or not isinstance(user_input, str):
            return Intent.UNKNOWN
        
        input_lower = user_input.lower()
        
        # Check each intent's patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    return intent
        
        # Default fallback
        return Intent.UNKNOWN
    
    def get_skills_for_intent(self, intent: Intent) -> List[Dict[str, Any]]:
        """
        Get the recommended skills to execute for a given intent.
        
        Args:
            intent: The recognized intent
            
        Returns:
            List of recommended skills with metadata
        """
        skill_recommendations = {
            # Language tutor
            Intent.CHAT: [
                {"skill": "language_tutor", "method": "language_chat", "priority": 1, "description": "Chat with AI tutor"},
                {"skill": "mascot", "method": "get_mascot_expression", "priority": 2, "description": "Get appropriate mascot expression"}
            ],
            Intent.LEARN_VOCAB: [
                {"skill": "language_tutor", "method": "generate_vocab_lesson", "priority": 1, "description": "Generate vocabulary lesson"},
                {"skill": "mascot", "method": "get_expression_for_answer", "priority": 2, "description": "Get mascot expression"}
            ],
            Intent.LEARN_GRAMMAR: [
                {"skill": "language_tutor", "method": "generate_grammar_lesson", "priority": 1, "description": "Generate grammar lesson"},
                {"skill": "mascot", "method": "get_expression_for_answer", "priority": 2, "description": "Get mascot expression"}
            ],
            Intent.GET_LANGUAGE_PROGRESS: [
                {"skill": "language_tutor", "method": "get_student_progress", "priority": 1, "description": "Get student's progress"},
                {"skill": "feedback_generator", "method": "generate_progress_feedback", "priority": 2, "description": "Generate progress feedback"},
                {"skill": "mascot", "method": "get_expression_for_answer", "priority": 3, "description": "Get mascot expression"}
            ],
            
            # Feedback
            Intent.GET_ENCOURAGEMENT: [
                {"skill": "feedback_generator", "method": "generate_encouragement", "priority": 1, "description": "Generate encouragement"},
                {"skill": "mascot", "method": "get_mascot_expression", "priority": 2, "description": "Get supportive mascot expression"}
            ],
            
            # Memory
            Intent.GET_MEMORY_SUMMARY: [
                {"skill": "memory_retrieval", "method": "get_memory_summary", "priority": 1, "description": "Get memory summary"},
                {"skill": "mascot", "method": "get_mascot_expression", "priority": 2, "description": "Get mascot expression"}
            ],
            Intent.GET_RECOMMENDATIONS: [
                {"skill": "memory_retrieval", "method": "get_personalized_recommendations", "priority": 1, "description": "Get recommendations"},
                {"skill": "mascot", "method": "get_mascot_expression", "priority": 2, "description": "Get mascot expression"}
            ],
            
            # Quiz
            Intent.GENERATE_QUIZ: [
                {"skill": "generate_quiz", "method": "generate_educational_quiz", "priority": 1, "description": "Generate quiz"},
                {"skill": "mascot", "method": "get_expression_for_answer", "priority": 2, "description": "Get mascot expression"}
            ],
            
            # Mascot
            Intent.GET_MASCOT: [
                {"skill": "mascot", "method": "get_random_expression", "priority": 1, "description": "Get random mascot"}
            ]
        }
        
        return skill_recommendations.get(intent, [])
    
    def orchestrate(
        self,
        user_input: str,
        student_id: str = "default_student"
    ) -> Dict[str, Any]:
        """
        Main orchestration method: analyzes input and returns recommended skills.
        
        Args:
            user_input: User's text input
            student_id: Student's unique identifier
            
        Returns:
            Orchestration result with intent and recommended skills
        """
        intent = self.recognize_intent(user_input)
        skills = self.get_skills_for_intent(intent)
        
        return {
            "success": True,
            "intent": intent.value,
            "student_id": student_id,
            "user_input": user_input,
            "recommended_skills": skills,
            "total_skills": len(skills)
        }


# Singleton instance for easy import
orchestrator = SkillOrchestrator()
