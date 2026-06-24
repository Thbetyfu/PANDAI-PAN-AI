from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Request

from neuro_language_tutor.llm_handler import LLMHandler

from ..deps import speech_handler


router = APIRouter()


@router.get("/api/config/llm")
async def get_llm_config(request: Request):
    llm = LLMHandler()
    tts = speech_handler.get_tts_config()
    local_status = llm.get_local_status()
    recommended_profile = local_status["device_recommendation"]["recommended_profile"]
    active_profile = llm.resolve_local_profile(recommended_profile)
    return {
        "success": True,
        "recommended_default": "local",
        "recommended_local_profile": recommended_profile,
        "provider_order": os.getenv("PANDAI_LLM_ORDER", "ollama,openai,fallback"),
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            "model": local_status["active_model"],
            "available": local_status["available"],
            "active_profile": active_profile,
            "active_model_installed": local_status["active_model_installed"],
        },
        "local_profiles": llm.get_local_profiles(),
        "device_recommendation": local_status["device_recommendation"],
        "last_activity": local_status["last_activity"],
        "last_warmup": request.app.state.local_llm_warmup,
        "model_catalog": local_status["model_catalog"],
        "openai_compatible": {
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "has_api_key": bool(os.getenv("OPENAI_API_KEY")),
        },
        "api_template_env": [
            "OPENAI_API_KEY=YOUR_KEY_HERE",
            "OPENAI_BASE_URL=https://api.openai.com/v1",
            "OPENAI_MODEL=gpt-4o-mini",
            "PANDAI_LLM_ORDER=ollama,openai,fallback",
            "PANDAI_LOCAL_LLM_PROFILE=balanced",
            "OLLAMA_MODEL=qwen2.5:3b",
        ],
        "tts": tts,
    }


@router.get("/api/status/local-llm")
async def get_local_llm_status(request: Request, llm_profile: str = "balanced", model_name: Optional[str] = None):
    llm = LLMHandler()
    status = llm.get_local_status(llm_profile=llm_profile, model_override=model_name)
    return {
        "success": True,
        "runtime": "ollama",
        "status": "ready" if status["available"] else "unavailable",
        "local_llm": status,
        "startup_warmup": request.app.state.local_llm_warmup,
    }


@router.get("/api/local-llm/models")
async def get_local_llm_models():
    llm = LLMHandler()
    catalog = llm.get_model_catalog()
    recommendation = llm.get_device_recommendation()
    return {"success": True, "device_recommendation": recommendation, "model_catalog": catalog}

