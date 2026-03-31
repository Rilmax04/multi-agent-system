import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import ControllerAgent
from agent.providers import ProviderManager
from api.routes import ask, market, suggest, system
from settings import settings

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

controller = None
provider = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global controller, provider
    logging.info("Запуск...")
    controller = ControllerAgent()
    provider = ProviderManager()
    logging.info("Готово ✓")
    yield
    logging.info("Остановка...")


def create_app() -> FastAPI:
    app = FastAPI(title="RAG Crypto Analysis API", version="2.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.include_router(ask.router, prefix="/ask", tags=["Анализ"])
    app.include_router(suggest.router, prefix="/suggest", tags=["Анализ"])
    app.include_router(market.router, prefix="/market", tags=["Рынок"])
    app.include_router(system.router, prefix="/system", tags=["Система"])

    @app.get("/", tags=["Система"])
    def root():
        return {"name": "RAG Crypto Analysis API", "version": "2.0", "docs": "/docs"}

    return app