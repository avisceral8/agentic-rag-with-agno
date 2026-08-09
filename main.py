"""FastAPI app that mounts the Chainlit chat interface."""

from contextlib import asynccontextmanager

from chainlit.utils import mount_chainlit
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    print("Starting Agentic RAG server...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Agentic RAG",
    description="Agentic RAG with Chainlit, Agno, Chonkie, and LanceDB",
    lifespan=lifespan,
)


@app.get("/")
def read_root():
    return {
        "app": "Agentic RAG",
        "status": "running",
        "endpoints": {
            "chat": "/chainlit",
            "health": "/health",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Mount Chainlit at /chainlit
mount_chainlit(app=app, target="src/chainlit_app.py", path="/chainlit")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)