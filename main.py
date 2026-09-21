from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.agent import agent
from app.api.ai import router as ai_router
from app.api.documents import router as documents_router
from app.api.generator import router as generator_router
from app.api.knowledge import router as knowledge_router
from app.api.project_processor import router as project_processor_router
from app.services.project_service import ProjectStateCorruptionError


app = FastAPI(
    title="ID-Agent",
    version="0.5.7"
)


app.include_router(ai_router)
app.include_router(documents_router)
app.include_router(generator_router)
app.include_router(knowledge_router)
app.include_router(project_processor_router)


@app.exception_handler(ProjectStateCorruptionError)
async def project_state_corruption_handler(
    _request: Request,
    error: ProjectStateCorruptionError,
):
    return JSONResponse(
        status_code=409,
        content={"detail": str(error)},
    )


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
