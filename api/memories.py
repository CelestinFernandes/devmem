from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor

router = APIRouter()
repo = None  # We'll pass this later

def init_repository(repository):
    global repo
    repo = repository

@router.get("/memories")
async def get_memories():
    if not repo:
        raise HTTPException(status_code=500, detail="Repository not initialized")
    
    with repo._get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, title, problem, confidence, status, created_at, last_used_at
                FROM memories
                ORDER BY created_at DESC
                LIMIT 50
            """)
            results = cur.fetchall()
            return {"memories": results}

@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    if not repo:
        raise HTTPException(status_code=500, detail="Repository not initialized")
    
    with repo._get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get memory details
            cur.execute("SELECT * FROM memories WHERE id = %s", (memory_id,))
            memory = cur.fetchone()
            
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            # Get relationships
            cur.execute("""
                SELECT m.id, m.title, r.relation_type
                FROM relationships r
                JOIN memories m ON m.id = r.memory_id_b
                WHERE r.memory_id_a = %s
                UNION
                SELECT m.id, m.title, r.relation_type
                FROM relationships r
                JOIN memories m ON m.id = r.memory_id_a
                WHERE r.memory_id_b = %s
            """, (memory_id, memory_id))
            
            related = cur.fetchall()
            memory['related_memories'] = related
            
            return memory