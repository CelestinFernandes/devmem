from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter()

# These will be injected from main.py
memory_service = None
extraction_service = None

class CaptureRequest(BaseModel):
    raw_text: str

class CaptureResponse(BaseModel):
    status: str
    memory_id: str
    duplicate: bool
    related_count: int
    message: str

def init_services(mem_service, ext_service):
    """Inject dependencies from main.py"""
    global memory_service, extraction_service
    memory_service = mem_service
    extraction_service = ext_service

@router.post("/capture", response_model=CaptureResponse)
async def capture_learning(request: CaptureRequest):
    if not memory_service or not extraction_service:
        raise HTTPException(status_code=500, detail="Services not initialized")

    # 1. Extract using Bedrock (or mock fallback)
    extracted = extraction_service.extract(request.raw_text)

    # 2. Ensure an ID
    if 'id' not in extracted:
        extracted['id'] = str(uuid.uuid4())

    # 3. Save via memory service
    result = memory_service.save_memory(request.raw_text, extracted)

    return CaptureResponse(
        status=result['status'],
        memory_id=result['memory_id'],
        duplicate=(result['status'] == 'duplicate'),
        related_count=result.get('related_count', 0),
        message=result.get('message', '')
    )