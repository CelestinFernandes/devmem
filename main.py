from dotenv import load_dotenv
load_dotenv()
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Services
from repositories.cockroach_repository import CockroachRepository
from services.memory_service import MemoryService
from services.extraction_service import ExtractionService
from services.synthesis_service import SynthesisService
from services.embedding_service import EmbeddingService

# API routers
from api.capture import router as capture_router, init_services as init_capture
from api.memories import router as memories_router, init_repository as init_mem_repo
from api.ask import router as ask_router, init_services as init_ask
from api.seed import router as seed_router, init_seed

# ---------- CONFIG ----------
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL not set in environment")

# ---------- INIT ----------
print("Initializing DevMeM backend...")

# 1. Repository
repo = CockroachRepository(DB_URL)

# 2. Embedding service (uses HF API)
embedding_service = EmbeddingService()

# 3. Memory service
memory_service = MemoryService(repo, embedding_service)

# 4. AI Services (use Hugging Face API)
extraction_service = ExtractionService(use_bedrock=False)
synthesis_service = SynthesisService(use_bedrock=False)

# 5. FastAPI app
app = FastAPI(title="DevMeM - Living Memory System")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Static files ----------
app.mount("/static", StaticFiles(directory="frontend", html=True), name="static")

# ---------- Inject dependencies ----------
init_capture(memory_service, extraction_service)
init_mem_repo(repo)
init_ask(memory_service, synthesis_service)
init_seed(repo, embedding_service)   # Note: seed.py expects embedding model, we'll adapt

# ---------- Include routers ----------
app.include_router(capture_router)
app.include_router(memories_router)
app.include_router(ask_router)
app.include_router(seed_router)

# ---------- Root ----------
@app.get("/")
async def root():
    return {"status": "ok", "service": "DevMeM", "frontend": "/static/index.html"}

# Lambda handler
_mangum_handler = Mangum(app, api_gateway_base_path="/default")

def handler(event, context):
    print("=== API GATEWAY EVENT ===")
    print(event)
    print("=== END API GATEWAY EVENT ===")
    return _mangum_handler(event, context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)