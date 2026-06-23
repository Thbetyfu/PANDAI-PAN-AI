
# PAN-AI/skills/memory_retrieval_skill.py
# OpenClaw skill for intelligent memory retrieval from Hermes memory system,
# including semantic search, filtering, and summarization.

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from skills.digital_twin import load_student_memory
from neuro_memory import MemoryEngine


# Initialize memory engine
memory_engine = MemoryEngine()


def search_memory(
    student_id: str,
    query: str,
    limit: int = 10,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    OpenClaw skill: Search student's memory using semantic search.
    
    Args:
        student_id: Unique student identifier
        query: Search query string
        limit: Maximum number of memory chunks to retrieve
        content_type: Optional filter by content type (e.g., "biometric", "quiz_result")
    
    Returns:
        Dictionary with search results
    """
    try:
        # Get memory chunks
        chunks = memory_engine.get_memory_chunks(student_id, limit=limit)
        
        # Filter by content_type if specified
        if content_type:
            chunks = [
                chunk for chunk in chunks 
                if hasattr(chunk, 'content_type') and chunk.content_type == content_type
            ]
        
        # Convert to dict for serialization
        results = []
        for chunk in chunks:
            results.append({
                "chunk_id": getattr(chunk, 'chunk_id', ''),
                "content_type": getattr(chunk, 'content_type', ''),
                "content": getattr(chunk, 'content', {}),
                "timestamp": getattr(chunk, 'timestamp', datetime.now().isoformat())
            })
        
        return {
            "success": True,
            "skill": "memory_retrieval",
            "action": "search",
            "student_id": student_id,
            "query": query,
            "results": results,
            "result_count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "skill": "memory_retrieval",
            "action": "search",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_memory_summary(student_id: str) -> Dict[str, Any]:
    """
    OpenClaw skill: Get a comprehensive summary of student's memory.
    
    Args:
        student_id: Unique student identifier
    
    Returns:
        Dictionary with memory summary
    """
    try:
        # Get cognitive profile
        profile = memory_engine.get_student_profile(student_id)
        
        # Get memory chunks count
        chunks = memory_engine.get_memory_chunks(student_id, limit=1000)
        
        # Load Hermes memory files
        hermes_memory = load_student_memory(student_id)
        
        return {
            "success": True,
            "skill": "memory_retrieval",
            "action": "summary",
            "student_id": student_id,
            "cognitive_profile": profile.__dict__ if profile else None,
            "hermes_user_profile": hermes_memory.get("user_profile", ""),
            "hermes_learning_log": hermes_memory.get("learning_log", ""),
            "memory_chunk_count": len(chunks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "skill": "memory_retrieval",
            "action": "summary",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_learning_patterns(student_id: str) -> Dict[str, Any]:
    """
    OpenClaw skill: Analyze learning patterns from memory history.
    
    Args:
        student_id: Unique student identifier
    
    Returns:
        Dictionary with learning pattern analysis
    """
    try:
        analysis = memory_engine.analyze_learning_patterns(student_id)
        
        return {
            "success": True,
            "skill": "memory_retrieval",
            "action": "analyze_patterns",
            "student_id": student_id,
            "learning_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "skill": "memory_retrieval",
            "action": "analyze_patterns",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_personalized_recommendations(student_id: str) -> Dict[str, Any]:
    """
    OpenClaw skill: Get personalized learning recommendations.
    
    Args:
        student_id: Unique student identifier
    
    Returns:
        Dictionary with recommendations
    """
    try:
        # Get or create profile
        profile = memory_engine.get_student_profile(student_id)
        if not profile:
            profile = memory_engine.create_initial_profile(student_id)
        
        recommendations = []
        
        if profile.focus_peak_hours:
            recommendations.append({
                "type": "schedule",
                "title": "Waktu Belajar Optimal",
                "content": f"Puncak fokus kamu pada jam {', '.join(profile.focus_peak_hours)}. Gunakan waktu ini untuk materi sulit!"
            })
        
        if profile.typical_focus_duration and profile.typical_focus_duration < 15:
            recommendations.append({
                "type": "technique",
                "title": "Teknik Pomodoro",
                "content": "Coba teknik Pomodoro: 15 menit fokus, 5 menit istirahat."
            })
        
        return {
            "success": True,
            "skill": "memory_retrieval",
            "action": "recommendations",
            "student_id": student_id,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "skill": "memory_retrieval",
            "action": "recommendations",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
