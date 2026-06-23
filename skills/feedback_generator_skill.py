
# PAN-AI/skills/feedback_generator_skill.py
# OpenClaw skill for generating personalized educational feedback
# for student answers, quiz results, and learning progress.

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from skills.digital_twin import load_student_memory, update_student_memory
from skills.memory_retrieval_skill import get_memory_summary


def generate_answer_feedback(
    student_id: str,
    question: str,
    student_answer: str,
    correct_answer: Optional[str] = None,
    is_correct: Optional[bool] = None,
    subject: str = "Umum"
) -> Dict[str, Any]:
    """
    OpenClaw skill: Generate personalized feedback for a student's answer.
    
    Args:
        student_id: Unique student identifier
        question: The question asked
        student_answer: The student's answer
        correct_answer: Optional correct answer for reference
        is_correct: Optional flag indicating if answer was correct
        subject: Subject/topic area (default: "Umum")
    
    Returns:
        Dictionary with personalized feedback
    """
    # Load student memory for personalization
    memory = load_student_memory(student_id)
    
    # Determine feedback tone based on correctness
    if is_correct:
        tone = "positif"
        encouragement = [
            "Luar biasa! Jawaban kamu sangat tepat!",
            "Hebat! Kamu memahami konsep ini dengan baik!",
            "Bagus sekali! Pemahamanmu tentang materi ini berkembang!",
            "Keren! Jawabanmu menunjukkan pemahaman yang mendalam!"
        ]
    elif is_correct is False:
        tone = "konstruktif"
        encouragement = [
            "Tidak apa-apa! Mari kita pelajari bersama konsep ini.",
            "Bagus usaha! Mari kita coba lagi dengan penjelasan baru.",
            "Semua orang belajar dari kesalahan, mari kita coba lagi!",
            "Kerja bagus mencoba! Ini adalah kesempatan untuk belajar lebih dalam."
        ]
    else:
        tone = "netral"
        encouragement = ["Mari kita lihat jawabanmu dan diskusikan lebih lanjut!"]
    
    # Select random encouragement
    import random
    feedback = random.choice(encouragement)
    
    # Build detailed feedback
    detailed_feedback = feedback
    if correct_answer and not is_correct:
        detailed_feedback += f" Jawaban yang tepat adalah: {correct_answer}."
    
    # Determine mascot expression (for later integration)
    mascot_expression = "Happy" if is_correct else "Bingung" if is_correct is None else "Idle"
    
    return {
        "success": True,
        "skill": "feedback_generator",
        "action": "answer_feedback",
        "student_id": student_id,
        "question": question,
        "student_answer": student_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "subject": subject,
        "tone": tone,
        "feedback": detailed_feedback,
        "mascot_expression": mascot_expression,
        "timestamp": datetime.now().isoformat()
    }


def generate_quiz_feedback(
    student_id: str,
    quiz_results: List[Dict[str, Any]],
    total_score: float,
    topic: str = "Umum"
) -> Dict[str, Any]:
    """
    OpenClaw skill: Generate comprehensive feedback for a quiz.
    
    Args:
        student_id: Unique student identifier
        quiz_results: List of question results with is_correct flag
        total_score: Total quiz score (0-100)
        topic: Quiz topic (default: "Umum")
    
    Returns:
        Dictionary with comprehensive quiz feedback
    """
    # Calculate statistics
    total_questions = len(quiz_results)
    correct_count = sum(1 for q in quiz_results if q.get("is_correct", False))
    wrong_count = total_questions - correct_count
    
    # Determine performance level and feedback
    if total_score >= 90:
        performance_level = "Luar Biasa"
        summary_feedback = "Pencapaianmu luar biasa! Kamu menguasai materi dengan sangat baik!"
        mascot_expression = "Happy"
    elif total_score >= 75:
        performance_level = "Bagus"
        summary_feedback = "Bagus sekali! Kamu memiliki pemahaman yang solid tentang materi ini!"
        mascot_expression = "Happy"
    elif total_score >= 60:
        performance_level = "Cukup"
        summary_feedback = "Lumayan! Masih ada beberapa konsep yang perlu kita pelajari lebih lanjut."
        mascot_expression = "Idle"
    else:
        performance_level = "Perlu Latihan"
        summary_feedback = "Tidak apa-apa! Mari kita ulangi materi ini dan coba lagi nanti."
        mascot_expression = "Bingung"
    
    # Get wrong questions for focused feedback
    wrong_questions = [
        q for q in quiz_results 
        if not q.get("is_correct", False)
    ]
    
    return {
        "success": True,
        "skill": "feedback_generator",
        "action": "quiz_feedback",
        "student_id": student_id,
        "topic": topic,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "total_score": total_score,
        "performance_level": performance_level,
        "summary_feedback": summary_feedback,
        "wrong_questions": wrong_questions,
        "mascot_expression": mascot_expression,
        "timestamp": datetime.now().isoformat()
    }


def generate_progress_feedback(
    student_id: str,
    progress_summary: Dict[str, Any],
    time_period: str = "Minggu Ini"
) -> Dict[str, Any]:
    """
    OpenClaw skill: Generate feedback about learning progress.
    
    Args:
        student_id: Unique student identifier
        progress_summary: Progress summary data
        time_period: Period of time for feedback (default: "Minggu Ini")
    
    Returns:
        Dictionary with progress feedback
    """
    # Extract progress metrics
    lessons_completed = progress_summary.get("lessons_completed", 0)
    streak = progress_summary.get("streak", 0)
    vocab_mastered = progress_summary.get("vocab_mastered", 0)
    
    # Build feedback based on metrics
    feedback_parts = []
    
    if streak >= 7:
        feedback_parts.append(f"Wow! Kamu memiliki streak {streak} hari berturut-turut! Luar biasa!")
        mascot_expression = "Happy"
    elif streak >= 3:
        feedback_parts.append(f"Bagus! Streak kamu {streak} hari, teruskan semangat!")
        mascot_expression = "Happy"
    else:
        feedback_parts.append("Mari kita mulai streak baru hari ini!")
        mascot_expression = "Menyapa"
    
    if lessons_completed > 0:
        feedback_parts.append(f"Kamu telah menyelesaikan {lessons_completed} pelajaran.")
    
    if vocab_mastered > 0:
        feedback_parts.append(f"Kamu telah menguasai {vocab_mastered} kata-kata baru!")
    
    full_feedback = " ".join(feedback_parts)
    
    return {
        "success": True,
        "skill": "feedback_generator",
        "action": "progress_feedback",
        "student_id": student_id,
        "time_period": time_period,
        "progress_summary": progress_summary,
        "feedback": full_feedback,
        "mascot_expression": mascot_expression,
        "timestamp": datetime.now().isoformat()
    }


def generate_encouragement(
    student_id: str,
    context: str = "umum",
    student_state: Optional[str] = None
) -> Dict[str, Any]:
    """
    OpenClaw skill: Generate encouragement message based on context.
    
    Args:
        student_id: Unique student identifier
        context: Context for encouragement (default: "umum")
        student_state: Optional student cognitive state (e.g., "MENGANTUK", "STRES")
    
    Returns:
        Dictionary with encouragement message and mascot expression
    """
    import random
    
    # Encouragement bank by context
    encouragement_bank = {
        "umum": [
            "Kamu bisa melakukannya! Percaya pada dirimu sendiri!",
            "Setiap langkah kecil adalah kemajuan. Tetap semangat!",
            "Belajar adalah perjalanan, nikmati prosesnya!",
            "Kamu memiliki potensi yang luar biasa!"
        ],
        "kesulitan": [
            "Tidak apa-apa merasa kesulitan. Itu tandanya kamu sedang belajar!",
            "Rintangan adalah kesempatan untuk tumbuh lebih kuat.",
            "Setiap ahli dulunya pemula. Tetap berusaha!"
        ],
        "keberhasilan": [
            "Luar biasa! Kamu layak bangga dengan pencapaianmu!",
            "Kerja kerasmu membuahkan hasil! Tetap semangat!",
            "Wow! Kamu hebat sekali!"
        ],
        "lelah": [
            "Istirahat sejenak, lalu kembali dengan semangat baru!",
            "Tidak apa-apa untuk beristirahat. Kesehatanmu lebih penting!",
            "Rehat sejenak, kamu sudah berusaha keras hari ini!"
        ]
    }
    
    # Select context
    if student_state == "MENGANTUK" or student_state == "STRES":
        context = "lelah"
    elif student_state == "NORMAL":
        context = "umum"
    
    # Get encouragement messages
    messages = encouragement_bank.get(context, encouragement_bank["umum"])
    encouragement_msg = random.choice(messages)
    
    # Determine mascot expression
    if student_state == "MENGANTUK":
        mascot_expression = "Ngantuk"
    elif student_state == "STRES":
        mascot_expression = "Marah"
    elif student_state == "FRUSTRASI":
        mascot_expression = "Nangis"
    elif context == "keberhasilan":
        mascot_expression = "Happy"
    else:
        mascot_expression = "Menyapa"
    
    return {
        "success": True,
        "skill": "feedback_generator",
        "action": "encouragement",
        "student_id": student_id,
        "context": context,
        "student_state": student_state,
        "encouragement": encouragement_msg,
        "mascot_expression": mascot_expression,
        "timestamp": datetime.now().isoformat()
    }
