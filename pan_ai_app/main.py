from __future__ import annotations

import os
import time

from fastapi import FastAPI

from .deps import llm_runtime
from .routers.biometrics_router import router as biometrics_router
from .routers.hermes_router import router as hermes_router
from .routers.language_tutor_router import router as language_tutor_router
from .routers.mascot_router import router as mascot_router
from .routers.neuro_memory_router import router as neuro_memory_router
from .routers.orchestrator_router import router as orchestrator_router
from .routers.quiz_router import router as quiz_router
from .routers.skills_router import router as skills_router
from .routers.status_router import router as status_router
from .routers.ui_router import router as ui_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PAN-AI Core Service",
        description="Centralized AI Agent Gateway with OpenClaw skills and Hermes-style memory storage + Neuro-Memory Foundation Model.",
    )

    app.state.local_llm_warmup = {
        "timestamp": None,
        "attempted": False,
        "success": False,
        "model": None,
        "profile": None,
        "message": "Warmup belum dijalankan.",
    }

    @app.on_event("startup")
    async def startup_local_llm_warmup():
        should_warmup = os.getenv("PANDAI_LOCAL_WARMUP", "1").strip().lower() not in {"0", "false", "no"}
        if not should_warmup:
            app.state.local_llm_warmup = {
                "timestamp": None,
                "attempted": False,
                "success": False,
                "model": None,
                "profile": None,
                "message": "Warmup dinonaktifkan oleh konfigurasi.",
            }
            return

        started = time.perf_counter()
        warmup_status = llm_runtime.warmup_local_model()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        warmup_status["startup_elapsed_ms"] = elapsed_ms
        app.state.local_llm_warmup = warmup_status

    app.include_router(ui_router)
    app.include_router(biometrics_router)
    app.include_router(hermes_router)
    app.include_router(quiz_router)
    app.include_router(neuro_memory_router)
    app.include_router(language_tutor_router)
    app.include_router(mascot_router)
    app.include_router(skills_router)
    app.include_router(orchestrator_router)
    app.include_router(status_router)

    return app

