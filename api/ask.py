# api/ask.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

# These will be injected
router = APIRouter()
memory_service = None
synthesis_service = None

class AskRequest(BaseModel):
    question: str

class Source(BaseModel):
    id: str
    title: str
    similarity: float

class AskResponse(BaseModel):
    answer: str
    sources: List[Source]

def init_services(mem_service, synth_service):
    global memory_service, synthesis_service
    memory_service = mem_service
    synthesis_service = synth_service

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    if not memory_service or not synthesis_service:
        raise HTTPException(status_code=500, detail="Services not initialized")

    # 1. Generate embedding for the question
    question_embedding = memory_service.model.encode(request.question).tolist()

    # 2. Vector search (top 3)
    results = memory_service.repo.vector_search(question_embedding, limit=3)

    if not results:
        return AskResponse(
            answer="I don't have any relevant learnings yet. Please capture some learnings first!",
            sources=[]
        )

    # 3. Synthesize answer
    synthesis_result = synthesis_service.synthesize(request.question, results)

    return AskResponse(
        answer=synthesis_result["answer"],
        sources=[
            Source(id=s['id'], title=s['title'], similarity=s['similarity'])
            for s in synthesis_result["sources"]
        ]
    )