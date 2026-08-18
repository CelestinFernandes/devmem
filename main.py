from dotenv import load_dotenv
load_dotenv()
import os

DB_URL = os.getenv("DATABASE_URL")
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from sentence_transformers import SentenceTransformer

# Services
from repositories.cockroach_repository import CockroachRepository
from services.memory_service import MemoryService
from services.extraction_service import ExtractionService
from services.synthesis_service import SynthesisService

# API routers
from api.capture import router as capture_router, init_services as init_capture
from api.memories import router as memories_router, init_repository as init_mem_repo
from api.ask import router as ask_router, init_services as init_ask
from api.seed import router as seed_router, init_seed

# ---------- CONFIG ----------
DB_URL = os.getenv("DATABASE_URL")
# ---------- INIT ----------
print("🚀 Initializing DevMeM backend...")

# 1. Repository
repo = CockroachRepository(DB_URL)

# 2. Embedding model
print(" Loading MiniLM...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# 3. Memory service
memory_service = MemoryService(repo, model)

# 4. AI Services with Qwen3 Coder 30B (cheaper and more reliable)
print("🤖 Initializing AI Services with Qwen3 Coder 30B...")
extraction_service = ExtractionService(use_bedrock=False, region='ap-south-1')
synthesis_service = SynthesisService(use_bedrock=False, region='ap-south-1')

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
init_seed(repo, model)

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
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)