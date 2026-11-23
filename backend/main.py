from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.repositories import router as repositories_router
from api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("RepoSage backend initializing...")
    yield
    # Shutdown actions
    print("RepoSage backend shutting down...")


app = FastAPI(
    title="RepoSage API",
    description="AI-Powered Codebase Intelligence using RAG with Hybrid Search, Citations and Interactive Code Viewing",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(repositories_router)
app.include_router(chat_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RepoSage API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
