# PAN-AI/skills/generate_quiz.py
# Module for generating structured educational quizzes using locally-hosted Qwen model via Ollama.

import json
import requests
from typing import Dict, Any

def generate_educational_quiz(
    topic: str,
    grade: str,
    difficulty: str,
    num_questions: int = 5,
    model_name: str = "qwen2.5:7b"
) -> Dict[str, Any]:
    """
    Generate multiple-choice questions (Pilihan Ganda) in structured JSON format via local Ollama API.
    
    Why: Relies on a local Qwen model running inside the Google Colab GPU runtime,
    bypassing the need for Gemini or any other commercial API keys. Ollama's native
    JSON format constraint ensures valid parseable JSON output.
    """
    url = "http://localhost:11434/api/chat"
    
    prompt = (
        f"Buatlah kuis pilihan ganda tentang '{topic}' untuk kelas '{grade}' dengan tingkat kesulitan '{difficulty}'. "
        f"Buat tepat {num_questions} soal. Setiap soal harus memiliki tepat 4 opsi pilihan (A, B, C, D). "
        "Kembalikan jawaban dalam format JSON terstruktur yang berisi array 'questions'. "
        "Setiap item soal wajib memiliki properti: 'question' (string), 'options' (array berisi 4 string), "
        "'answer' (string berisi A, B, C, atau D), dan 'explanation' (string penjelasan detail). "
        "Tulis semua konten dalam Bahasa Indonesia."
    )

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "Anda adalah asisten pembuat soal ujian sekolah yang ahli. Anda wajib selalu mengembalikan output dalam format JSON yang valid."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "format": "json",
        "stream": False
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result_json = response.json()
        
        # Extract response text
        message_content = result_json.get("message", {}).get("content", "")
        if not message_content:
            return {"error": "Respon kosong dari Ollama."}
            
        return json.loads(message_content)
    except requests.exceptions.RequestException as e:
        return {"error": f"Gagal menghubungi Ollama local API: {str(e)}"}
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return {"error": f"Gagal mengurai respon JSON dari model: {str(e)}"}
