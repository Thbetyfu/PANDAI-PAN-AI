
"""
LLMHandler: Berkomunikasi dengan Ollama untuk generate response AI & koreksi bahasa.
"""
import os
import requests
import json
from typing import Dict, Optional, Tuple, List, Any


class LLMHandler:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen2.5:0.5b"):
        """
        Inisialisasi LLM Handler.
        
        Args:
            base_url: URL Ollama server
            model: Nama model yang akan digunakan (default: qwen2.5:0.5b)
        """
        self.base_url = os.getenv("OLLAMA_BASE_URL", base_url)
        self.model = os.getenv("OLLAMA_MODEL", model)
        self.api_url = f"{self.base_url}/api/generate"
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.provider_order = self._parse_provider_order(os.getenv("PANDAI_LLM_ORDER", "ollama,openai"))
        
        self.base_system_prompt = """
You are a strict-but-warm private language teacher for a student.

Core rules:
1) Prioritize fluency first: respond naturally and keep the conversation going.
2) Correction comes second: only correct if it helps learning (clear error or repeated pattern). Keep correction short.
3) Be supportive but firm: clear goals, clear next step, no harsh tone.
4) Prefer Indonesian for explanations if the student seems Indonesian.

Always structure your response as:
- First: Natural response (1–4 sentences), friendly and encouraging.
- Second: CORRECTION: ... (or "No corrections needed!")
- Third: EXPLANATION: ... (only if there were corrections; 1–3 short sentences)
- Fourth: NEXT: one short micro-task (one sentence) to practice immediately.
        """.strip()

    def _parse_provider_order(self, raw: str) -> List[str]:
        parts = [p.strip().lower() for p in (raw or "").split(",") if p.strip()]
        if not parts:
            return ["ollama", "openai"]
        seen = set()
        ordered: List[str] = []
        for p in parts:
            if p in seen:
                continue
            if p in ("ollama", "openai", "fallback"):
                ordered.append(p)
                seen.add(p)
        if "fallback" not in seen:
            ordered.append("fallback")
        return ordered

    def _parse_structured_response(self, full_response: str) -> Tuple[str, Optional[str], Optional[str]]:
        assistant_response = (full_response or "").strip()
        correction = None
        explanation = None

        if "CORRECTION:" in assistant_response:
            parts = assistant_response.split("CORRECTION:", 1)
            assistant_response = parts[0].strip()
            correction_part = parts[1].strip()
            if "EXPLANATION:" in correction_part:
                corr_parts = correction_part.split("EXPLANATION:", 1)
                correction = corr_parts[0].strip() or None
                explanation = corr_parts[1].strip() or None
            else:
                correction = correction_part or None
        return assistant_response, correction, explanation

    def is_ollama_available(self) -> bool:
        """Cek apakah Ollama server berjalan."""
        for base in self._candidate_ollama_base_urls():
            try:
                response = requests.get(f"{base}/api/tags", timeout=3)
                if response.status_code == 200:
                    self.base_url = base
                    self.api_url = f"{self.base_url}/api/generate"
                    return True
            except Exception:
                continue
        return False

    def _candidate_ollama_base_urls(self) -> List[str]:
        candidates: List[str] = []
        raw = (self.base_url or "").strip().rstrip("/")
        if raw:
            candidates.append(raw)
        if "localhost" in raw:
            candidates.append(raw.replace("localhost", "127.0.0.1"))
        if "127.0.0.1" in raw:
            candidates.append(raw.replace("127.0.0.1", "localhost"))
        candidates.append("http://127.0.0.1:11434")
        candidates.append("http://localhost:11434")

        seen = set()
        ordered: List[str] = []
        for c in candidates:
            if c in seen:
                continue
            ordered.append(c)
            seen.add(c)
        return ordered

    def is_openai_available(self) -> bool:
        return bool(self.openai_api_key and self.openai_base_url)

    def _build_prompt(
        self,
        user_message: str,
        conversation_history: Optional[list] = None,
        teacher_context: Optional[str] = None,
        teacher_persona: str = "strict_warm",
        correction_mode: str = "fluency_first"
    ) -> str:
        history_lines: List[str] = []
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
                if not role or not content:
                    continue
                if role == "user":
                    history_lines.append(f"User: {content}")
                elif role == "assistant":
                    history_lines.append(f"Assistant: {content}")
        system_prompt = self.base_system_prompt
        if teacher_persona and teacher_persona != "strict_warm":
            system_prompt = f"{system_prompt}\n\nTeacher persona override: {teacher_persona}".strip()
        if correction_mode and correction_mode != "fluency_first":
            system_prompt = f"{system_prompt}\n\nCorrection mode override: {correction_mode}".strip()

        context_block = ""
        if teacher_context:
            context_block = f"STUDENT CONTEXT (Hermes summary):\n{teacher_context.strip()}\n"

        history_block = "\n".join(history_lines)
        if history_block:
            return f"{system_prompt}\n\n{context_block}\n{history_block}\nUser: {user_message}\nAssistant:"
        return f"{system_prompt}\n\n{context_block}\nUser: {user_message}\nAssistant:"

    def _generate_via_ollama(self, prompt: str) -> Tuple[str, Optional[str], Optional[str]]:
        if not self.is_ollama_available():
            return (
                "Aku belum bisa akses Ollama lokal. Pastikan Ollama berjalan lalu coba lagi.",
                None,
                None
            )
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            full_response = result.get("response", "")
            return self._parse_structured_response(full_response)

        return (
            "Hello! Thanks for your message. Let's practice English together!",
            None,
            None
        )

    def _generate_via_openai(self, prompt: str) -> Tuple[str, Optional[str], Optional[str]]:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        user_content = prompt
        payload: Dict[str, Any] = {
            "model": self.openai_model,
            "messages": [
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            content = (
                (data.get("choices") or [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return self._parse_structured_response(content)

        if response.status_code in (401, 403):
            return (
                "Aku tidak bisa mengakses LLM cloud karena API key tidak valid/ditolak. Coba cek konfigurasi OPENAI_API_KEY.",
                None,
                None
            )

        if response.status_code == 429:
            return (
                "Aku kena rate limit/quota dari provider LLM cloud. Coba tunggu sebentar atau pindah ke Ollama lokal.",
                None,
                None
            )

        return (
            "Aku gagal memanggil LLM cloud. Kita bisa coba lagi atau gunakan Ollama lokal.",
            None,
            None
        )

    def generate_response(
        self, 
        user_message: str, 
        conversation_history: Optional[list] = None,
        teacher_context: Optional[str] = None,
        teacher_persona: str = "strict_warm",
        correction_mode: str = "fluency_first",
        llm_mode: str = "auto"
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Generate response AI beserta koreksi dan penjelasan.
        
        Args:
            user_message: Pesan dari user
            conversation_history: Riwayat percakapan (opsional)
            
        Returns:
            Tuple: (assistant_response, correction, explanation)
        """
        prompt = self._build_prompt(
            user_message=user_message,
            conversation_history=conversation_history,
            teacher_context=teacher_context,
            teacher_persona=teacher_persona,
            correction_mode=correction_mode
        )

        mode = (llm_mode or "auto").strip().lower()
        if mode in ("local", "gpu", "ollama", "local_gpu"):
            provider_order = ["ollama", "fallback"]
        elif mode in ("api", "cloud", "openai"):
            provider_order = ["openai", "fallback"]
        else:
            provider_order = self.provider_order

        last_error: Optional[Exception] = None
        for provider in provider_order:
            try:
                if provider == "ollama":
                    if self.is_ollama_available():
                        return self._generate_via_ollama(prompt)
                    continue

                if provider == "openai":
                    if self.is_openai_available():
                        return self._generate_via_openai(prompt)
                    continue

                if provider == "fallback":
                    return (
                        f"Hello! You said: '{user_message}'. I'm your English tutor! (No LLM configured, using fallback)",
                        None,
                        None
                    )
            except Exception as e:
                last_error = e
                continue

        if last_error:
            print(f"[LLMHandler] Error: {last_error}")
        return (
            f"Hello! You said: '{user_message}'. I'm your English tutor! (LLM unavailable, using fallback)",
            None,
            None
        )
