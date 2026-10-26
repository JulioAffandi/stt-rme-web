from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, dictation, encounters, health, master, patients, pipeline_logs
from app.core.config import get_settings
from app.core.errors import AppError
from app.nlp.stt_whisper import init_whisper_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inisialisasi model Whisper (Fase 3)
    init_whisper_engine()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(patients.router, prefix=settings.api_v1_prefix)
    app.include_router(encounters.router, prefix=settings.api_v1_prefix)
    app.include_router(dictation.router, prefix=settings.api_v1_prefix)
    app.include_router(pipeline_logs.router, prefix=settings.api_v1_prefix)
    app.include_router(master.router, prefix=settings.api_v1_prefix)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            content = exc.detail
        else:
            content = {"detail": exc.detail, "code": f"HTTP_{exc.status_code}"}
        return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validasi input gagal",
                "code": "VALIDATION_ERROR",
                "errors": [
                    {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
                    for err in exc.errors()
                ],
            },
        )

    return app


app = create_app()
