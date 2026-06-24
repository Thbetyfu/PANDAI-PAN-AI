
"""
LLMHandler: Berkomunikasi dengan Ollama untuk generate response AI & koreksi bahasa.
"""
import ctypes
import os
import json
import platform
import requests
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List, Any

LOCAL_LLM_PROFILES: Dict[str, Dict[str, Any]] = {
    "lite": {
        "label": "Lite",
        "model": "qwen2.5:1.5b",
        "min_vram_gb": 4,
        "target_devices": "Laptop entry-mid dengan GPU terbatas",
        "description": "Paling ringan dan cepat untuk chat dasar."
    },
    "balanced": {
        "label": "Balanced",
        "model": "qwen2.5:3b",
        "min_vram_gb": 6,
        "target_devices": "Laptop mid-range dengan GPU dedicated",
        "description": "Default aman untuk kualitas dan kecepatan yang seimbang."
    },
    "quality": {
        "label": "Quality",
        "model": "qwen2.5:7b",
        "min_vram_gb": 8,
        "target_devices": "Laptop high-end atau desktop dengan VRAM lebih lega",
        "description": "Kualitas respons lebih baik untuk tutor yang lebih natural."
    }
}

LAST_LLM_ACTIVITY: Dict[str, Any] = {
    "timestamp": None,
    "provider": None,
    "mode": None,
    "profile": None,
    "model": None,
    "latency_ms": None,
    "success": None,
    "error": None
}

LAST_LOCAL_WARMUP: Dict[str, Any] = {
    "timestamp": None,
    "attempted": False,
    "success": False,
    "model": None,
    "profile": None,
    "message": "Warmup belum dijalankan."
}


class LLMHandler:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen2.5:3b"):
        """
        Inisialisasi LLM Handler.
        
        Args:
            base_url: URL Ollama server
            model: Nama model yang akan digunakan (default: qwen2.5:3b)
        """
        self.base_url = os.getenv("OLLAMA_BASE_URL", base_url)
        self.default_model = model
        self.default_local_profile = os.getenv("PANDAI_LOCAL_LLM_PROFILE", "balanced").strip().lower() or "balanced"
        self.model = os.getenv("OLLAMA_MODEL", self.default_model)
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

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_activity(
        self,
        provider: str,
        mode: str,
        profile: Optional[str],
        model: Optional[str],
        latency_ms: Optional[float],
        success: bool,
        error: Optional[str] = None
    ) -> None:
        LAST_LLM_ACTIVITY.update({
            "timestamp": self._utc_now(),
            "provider": provider,
            "mode": mode,
            "profile": profile,
            "model": model,
            "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
            "success": success,
            "error": error
        })

    def get_last_activity(self) -> Dict[str, Any]:
        return dict(LAST_LLM_ACTIVITY)

    def get_last_warmup(self) -> Dict[str, Any]:
        return dict(LAST_LOCAL_WARMUP)

    def _get_total_ram_gb(self) -> Optional[float]:
        try:
            if platform.system().lower() == "windows":
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                memory_status = MEMORYSTATUSEX()
                memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
                return round(memory_status.ullTotalPhys / (1024 ** 3), 1)

            if hasattr(os, "sysconf"):
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                return round((pages * page_size) / (1024 ** 3), 1)
        except Exception:
            return None
        return None

    def _detect_gpu_names(self) -> List[str]:
        env_gpu = os.getenv("PANDAI_GPU_NAMES", "").strip()
        if env_gpu:
            return [part.strip() for part in env_gpu.split(",") if part.strip()]

        if platform.system().lower() != "windows":
            return []

        try:
            command = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=4, check=False)
            if result.returncode != 0:
                return []
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception:
            return []

    def get_device_recommendation(self) -> Dict[str, Any]:
        override_tier = os.getenv("PANDAI_DEVICE_TIER", "").strip().lower()
        ram_gb = self._get_total_ram_gb()
        gpu_names = self._detect_gpu_names()
        gpu_blob = " ".join(gpu_names).lower()

        if override_tier in ("entry", "mid", "high"):
            tier = override_tier
            reason = "Menggunakan override dari PANDAI_DEVICE_TIER."
        elif any(keyword in gpu_blob for keyword in ("4090", "4080", "4070", "3090", "3080", "3070", "7900", "7800", "6900", "6800")):
            tier = "high"
            reason = "GPU terdeteksi pada kelas performa tinggi."
        elif any(keyword in gpu_blob for keyword in ("1660", "2060", "2070", "3050", "3060", "4060", "6600", "6650", "7600")):
            tier = "mid"
            reason = "GPU terdeteksi pada kelas laptop menengah sampai menengah-atas."
        elif (ram_gb or 0) >= 32:
            tier = "mid"
            reason = "RAM besar terdeteksi meskipun kelas GPU tidak terbaca jelas."
        else:
            tier = "entry"
            reason = "Spesifikasi lokal terbaca konservatif, memakai tier aman."

        if tier == "high":
            recommended_profile = "quality"
        elif tier == "mid":
            recommended_profile = "balanced"
        else:
            recommended_profile = "lite"

        return {
            "device_tier": tier,
            "reason": reason,
            "total_ram_gb": ram_gb,
            "gpu_names": gpu_names,
            "recommended_profile": recommended_profile
        }

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

    def get_local_profiles(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                **profile,
                "name": name
            }
            for name, profile in LOCAL_LLM_PROFILES.items()
        }

    def resolve_local_profile(self, llm_profile: Optional[str] = None) -> Dict[str, Any]:
        requested_profile = (llm_profile or self.default_local_profile or "balanced").strip().lower()
        profile_name = requested_profile if requested_profile in LOCAL_LLM_PROFILES else "balanced"
        profile = LOCAL_LLM_PROFILES[profile_name]
        return {
            "name": profile_name,
            **profile
        }

    def resolve_local_model(self, llm_profile: Optional[str] = None, model_override: Optional[str] = None) -> str:
        override = (model_override or "").strip()
        if override and override.lower() not in {"auto", "default"}:
            return override
        env_model = os.getenv("OLLAMA_MODEL", "").strip()
        if env_model:
            return env_model
        return self.resolve_local_profile(llm_profile)["model"]

    def resolve_provider_order(self, llm_mode: str = "auto") -> List[str]:
        mode = (llm_mode or "auto").strip().lower()
        if mode in ("local", "gpu", "ollama", "local_gpu"):
            return ["ollama", "fallback"]
        if mode in ("api", "cloud", "openai"):
            return ["openai", "fallback"]
        return self.provider_order

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

    def list_ollama_models(self) -> List[Dict[str, Any]]:
        for base in self._candidate_ollama_base_urls():
            try:
                response = requests.get(f"{base}/api/tags", timeout=4)
                if response.status_code != 200:
                    continue
                self.base_url = base
                payload = response.json()
                models = payload.get("models") or []
                normalized: List[Dict[str, Any]] = []
                for item in models:
                    name = item.get("name")
                    if not name:
                        continue
                    normalized.append({
                        "name": name,
                        "size": item.get("size"),
                        "modified_at": item.get("modified_at"),
                        "digest": item.get("digest")
                    })
                return normalized
            except Exception:
                continue
        return []

    def get_model_catalog(self) -> Dict[str, Any]:
        installed_models = self.list_ollama_models()
        installed_names = {item["name"] for item in installed_models}
        recommended_profiles = self.get_local_profiles()
        recommended_models = []
        for name, profile in recommended_profiles.items():
            model_name = profile["model"]
            recommended_models.append({
                "profile": name,
                "model": model_name,
                "installed": model_name in installed_names,
                "suggested_pull_command": f"ollama pull {model_name}"
            })
        return {
            "installed_models": installed_models,
            "installed_model_names": sorted(installed_names),
            "recommended_models": recommended_models
        }

    def get_local_status(self, llm_profile: Optional[str] = None, model_override: Optional[str] = None) -> Dict[str, Any]:
        recommendation = self.get_device_recommendation()
        effective_profile = llm_profile or recommendation["recommended_profile"]
        active_profile = self.resolve_local_profile(effective_profile)
        active_model = self.resolve_local_model(effective_profile, model_override=model_override)
        ollama_available = self.is_ollama_available()
        catalog = self.get_model_catalog()
        return {
            "available": ollama_available,
            "base_url": self.base_url,
            "candidate_base_urls": self._candidate_ollama_base_urls(),
            "active_profile": active_profile,
            "active_model": active_model,
            "active_model_installed": active_model in set(catalog["installed_model_names"]),
            "fallback_enabled": "fallback" in self.provider_order,
            "device_recommendation": recommendation,
            "last_activity": self.get_last_activity(),
            "last_warmup": self.get_last_warmup(),
            "model_catalog": catalog
        }

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

    def _generate_via_ollama(self, prompt: str, model_name: str) -> Tuple[str, Optional[str], Optional[str]]:
        if not self.is_ollama_available():
            return (
                "Aku belum bisa akses Ollama lokal. Pastikan Ollama berjalan lalu coba lagi.",
                None,
                None
            )
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model_name,
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

    def _chat_via_ollama(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        json_output: bool = False
    ) -> str:
        if not self.is_ollama_available():
            raise RuntimeError("Ollama lokal tidak tersedia.")

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }
        if json_output:
            payload["format"] = "json"

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        content = (data.get("message") or {}).get("content", "")
        if not content:
            raise RuntimeError("Respon Ollama kosong.")
        return content

    def _chat_via_openai(
        self,
        messages: List[Dict[str, str]],
        json_output: bool = False
    ) -> str:
        if not self.is_openai_available():
            raise RuntimeError("Provider API cloud belum siap.")

        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": self.openai_model,
            "messages": messages,
            "temperature": 0.3
        }
        if json_output:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        if not content:
            raise RuntimeError("Respon API cloud kosong.")
        return content

    def warmup_local_model(self, llm_profile: Optional[str] = None, model_override: Optional[str] = None) -> Dict[str, Any]:
        profile_name = (llm_profile or self.get_device_recommendation()["recommended_profile"]).strip().lower()
        model_name = self.resolve_local_model(profile_name, model_override=model_override)

        LAST_LOCAL_WARMUP.update({
            "timestamp": self._utc_now(),
            "attempted": True,
            "success": False,
            "model": model_name,
            "profile": profile_name,
            "message": "Warmup sedang dicoba."
        })

        if not self.is_ollama_available():
            LAST_LOCAL_WARMUP["message"] = "Warmup dilewati karena Ollama belum aktif."
            return self.get_last_warmup()

        try:
            start = time.perf_counter()
            self._chat_via_ollama(
                messages=[
                    {"role": "system", "content": "Anda hanya perlu menjawab READY."},
                    {"role": "user", "content": "READY"}
                ],
                model_name=model_name,
                json_output=False
            )
            latency_ms = (time.perf_counter() - start) * 1000
            LAST_LOCAL_WARMUP.update({
                "timestamp": self._utc_now(),
                "attempted": True,
                "success": True,
                "model": model_name,
                "profile": profile_name,
                "message": f"Warmup berhasil ({round(latency_ms, 2)} ms)."
            })
            return self.get_last_warmup()
        except Exception as e:
            LAST_LOCAL_WARMUP.update({
                "timestamp": self._utc_now(),
                "attempted": True,
                "success": False,
                "model": model_name,
                "profile": profile_name,
                "message": f"Warmup gagal: {str(e)}"
            })
            return self.get_last_warmup()

    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        llm_mode: str = "auto",
        llm_profile: Optional[str] = None,
        json_output: bool = False,
        allow_fallback: bool = True,
        model_override: Optional[str] = None
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]
        provider_order = self.resolve_provider_order(llm_mode)
        local_model = self.resolve_local_model(llm_profile, model_override=model_override)
        effective_profile = llm_profile or self.get_device_recommendation()["recommended_profile"]
        last_error: Optional[Exception] = None

        for provider in provider_order:
            try:
                if provider == "ollama":
                    if self.is_ollama_available():
                        started = time.perf_counter()
                        content = self._chat_via_ollama(messages, local_model, json_output=json_output)
                        self._record_activity(
                            provider="ollama",
                            mode=llm_mode,
                            profile=effective_profile,
                            model=local_model,
                            latency_ms=(time.perf_counter() - started) * 1000,
                            success=True
                        )
                        return content
                    continue

                if provider == "openai":
                    if self.is_openai_available():
                        started = time.perf_counter()
                        content = self._chat_via_openai(messages, json_output=json_output)
                        self._record_activity(
                            provider="openai",
                            mode=llm_mode,
                            profile=effective_profile,
                            model=self.openai_model,
                            latency_ms=(time.perf_counter() - started) * 1000,
                            success=True
                        )
                        return content
                    continue

                if provider == "fallback" and allow_fallback:
                    if json_output:
                        fallback_json = json.dumps({
                            "questions": [],
                            "warning": "LLM tidak tersedia, fallback quiz kosong digunakan.",
                            "fallback_used": True
                        })
                        self._record_activity(
                            provider="fallback",
                            mode=llm_mode,
                            profile=effective_profile,
                            model=None,
                            latency_ms=0.0,
                            success=False,
                            error="LLM unavailable"
                        )
                        return fallback_json
                    self._record_activity(
                        provider="fallback",
                        mode=llm_mode,
                        profile=effective_profile,
                        model=None,
                        latency_ms=0.0,
                        success=False,
                        error="LLM unavailable"
                    )
                    return "LLM tidak tersedia, menggunakan fallback."
            except Exception as e:
                last_error = e
                self._record_activity(
                    provider=provider,
                    mode=llm_mode,
                    profile=effective_profile,
                    model=local_model if provider == "ollama" else self.openai_model,
                    latency_ms=None,
                    success=False,
                    error=str(e)
                )
                continue

        if last_error:
            raise RuntimeError(str(last_error))
        raise RuntimeError("Tidak ada provider LLM yang tersedia.")

    def generate_response(
        self, 
        user_message: str, 
        conversation_history: Optional[list] = None,
        teacher_context: Optional[str] = None,
        teacher_persona: str = "strict_warm",
        correction_mode: str = "fluency_first",
        llm_mode: str = "auto",
        llm_profile: Optional[str] = None,
        llm_model: Optional[str] = None
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

        provider_order = self.resolve_provider_order(llm_mode)
        local_model = self.resolve_local_model(llm_profile, model_override=llm_model)
        effective_profile = llm_profile or self.get_device_recommendation()["recommended_profile"]
        last_error: Optional[Exception] = None
        for provider in provider_order:
            try:
                if provider == "ollama":
                    if self.is_ollama_available():
                        started = time.perf_counter()
                        result = self._generate_via_ollama(prompt, local_model)
                        self._record_activity(
                            provider="ollama",
                            mode=llm_mode,
                            profile=effective_profile,
                            model=local_model,
                            latency_ms=(time.perf_counter() - started) * 1000,
                            success=True
                        )
                        return result
                    continue

                if provider == "openai":
                    if self.is_openai_available():
                        started = time.perf_counter()
                        result = self._generate_via_openai(prompt)
                        self._record_activity(
                            provider="openai",
                            mode=llm_mode,
                            profile=effective_profile,
                            model=self.openai_model,
                            latency_ms=(time.perf_counter() - started) * 1000,
                            success=True
                        )
                        return result
                    continue

                if provider == "fallback":
                    self._record_activity(
                        provider="fallback",
                        mode=llm_mode,
                        profile=effective_profile,
                        model=None,
                        latency_ms=0.0,
                        success=False,
                        error="LLM unavailable"
                    )
                    return (
                        f"Hello! You said: '{user_message}'. I'm your English tutor! (No LLM configured, using fallback)",
                        None,
                        None
                    )
            except Exception as e:
                last_error = e
                self._record_activity(
                    provider=provider,
                    mode=llm_mode,
                    profile=effective_profile,
                    model=local_model if provider == "ollama" else self.openai_model,
                    latency_ms=None,
                    success=False,
                    error=str(e)
                )
                continue

        if last_error:
            print(f"[LLMHandler] Error: {last_error}")
        return (
            f"Hello! You said: '{user_message}'. I'm your English tutor! (LLM unavailable, using fallback)",
            None,
            None
        )
