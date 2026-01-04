"""
FastAPI server for Nexus Ray.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from src.api.routes import workflows, agents, llm, metrics, collaboration, guardrails, reference_agents, hitl


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    print("🚀 Starting Nexus Ray API...")
    yield
    # Shutdown
    print("👋 Shutting down Nexus Ray API...")


# Create FastAPI app
app = FastAPI(
    title="Nexus Ray API",
    description="Enterprise AI Agent Workflow Orchestration System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["Collaboration"])
app.include_router(guardrails.router, prefix="/api/guardrails", tags=["Guardrails"])
app.include_router(hitl.router, prefix="/api/hitl", tags=["HITL"])
app.include_router(reference_agents.router, prefix="/api/reference", tags=["Reference Agents"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Nexus Ray API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


from fastapi import WebSocket, WebSocketDisconnect
from src.api.websockets import manager

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "llm": "up",
            "kafka": "unknown",
            "database": "unknown"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
