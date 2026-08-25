from fastapi import FastAPI

from app.core.agent import agent
from app.api.ai import router as ai_router
from app.api.documents import router as documents_router
from app.api.generator import router as generator_router
from app.api.project_processor import router as project_processor_router


app = FastAPI(
    title="ID-Agent",
    version="0.5.7"
)


app.include_router(ai_router)
app.include_router(documents_router)
app.include_router(generator_router)
app.include_router(project_processor_router)


@app.get("/")
def home():
    return {
        "program": "ID-Agent",
        "version": "0.5.7",
        "status": "Работает"
    }


@app.get("/agent")
def agent_status():
    return agent.status()