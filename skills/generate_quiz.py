# PAN-AI/skills/generate_quiz.py
# Module for generating structured educational quizzes using PAN-AI's shared LLM router.

import json
from typing import Dict, Any, Optional

from neuro_language_tutor.llm_handler import LLMHandler

def generate_educational_quiz(
    topic: str,
    grade: str,
    difficulty: str,
    num_questions: int = 5,
    model_name: Optional[str] = None,
    llm_mode: str = "local",
    llm_profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate multiple-choice questions (Pilihan Ganda) using PAN-AI's shared LLM router.

    Why: Menyatukan jalur quiz dengan router LLM utama membuat local profile, model
    override, dan fallback policy tetap konsisten di seluruh aplikasi.
    """
    system_prompt = (
        "Anda adalah asisten pembuat soal ujian sekolah yang ahli. "
        "Anda wajib selalu mengembalikan output dalam format JSON yang valid. "
        "Struktur JSON wajib memiliki root object dengan key 'questions' berupa array. "
        "Jangan gunakan markdown, jangan gunakan code fence, jangan tambahkan teks pembuka atau penutup."
    )

    user_prompt = (
        f"Buatlah kuis pilihan ganda tentang '{topic}' untuk kelas '{grade}' dengan tingkat kesulitan '{difficulty}'. "
        f"Buat tepat {num_questions} soal. Setiap soal harus memiliki tepat 4 opsi pilihan (A, B, C, D). "
        "Kembalikan jawaban dalam format JSON terstruktur yang berisi array 'questions'. "
        "Setiap item soal wajib memiliki properti: 'question' (string), 'options' (array berisi 4 string), "
        "'answer' (string berisi A, B, C, atau D), dan 'explanation' (string penjelasan detail). "
        "Tulis semua konten dalam Bahasa Indonesia. "
        "Contoh schema yang wajib diikuti: "
        "{\"questions\":[{\"question\":\"...\",\"options\":[\"A...\",\"B...\",\"C...\",\"D...\"],\"answer\":\"A\",\"explanation\":\"...\"}]}"
    )

    llm = LLMHandler(model=model_name or "qwen2.5:7b")
    try:
        raw_content = llm.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            llm_mode=llm_mode,
            llm_profile=llm_profile,
            json_output=True,
            allow_fallback=True,
            model_override=model_name
        )
        parsed = json.loads(raw_content)
        if not isinstance(parsed, dict):
            raise ValueError("Root JSON harus berupa object.")
        questions = parsed.get("questions")
        if not isinstance(questions, list):
            raise ValueError("Field 'questions' harus berupa array.")
        parsed.setdefault("topic", topic)
        parsed.setdefault("grade", grade)
        parsed.setdefault("difficulty", difficulty)
        return parsed
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"Gagal mengurai respon JSON dari model: {str(e)}"}
    except Exception as e:
        return {"error": f"Gagal menghasilkan quiz via LLM router: {str(e)}"}
