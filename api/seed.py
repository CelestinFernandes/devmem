# api/seed.py
import json
import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
repo = None
model = None

def init_seed(repository, embedding_model):
    global repo, model
    repo = repository
    model = embedding_model

class SeedResponse(BaseModel):
    status: str
    memories_created: int
    relationships_created: int

@router.post("/seed", response_model=SeedResponse)
async def seed_database():
    if not repo or not model:
        raise HTTPException(status_code=500, detail="Seed services not initialized")

    # Path to your generated seed file
    json_path = "output/labeled_clusters.json"
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail=f"Seed file not found at {json_path}")

    # Load the JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    clusters = data.get('clusters', [])
    memories_created = 0
    relationships_created = 0

    for cluster in clusters:
        label = cluster.get('label')
        cluster_mems = cluster.get('memories', [])
        if not cluster_mems:
            continue

        saved_ids = []
        for mem_data in cluster_mems:
            # Generate ID if missing
            if 'id' not in mem_data:
                mem_data['id'] = str(uuid.uuid4())

            # Build embedding text (problem + cause + technologies)
            problem = mem_data.get('problem', '')
            cause = mem_data.get('cause', '')
            techs = ' '.join(mem_data.get('technologies', []))
            embed_text = f"{problem} {cause} {techs}"
            
            # Generate embedding
            embedding = model.encode(embed_text).tolist()

            # Save to database
            repo.save_memory(mem_data, embedding)
            saved_ids.append(mem_data['id'])
            memories_created += 1

        # Create relationships based on cluster label
        if label in ['duplicate', 'related'] and len(saved_ids) > 1:
            primary_id = saved_ids[0]
            for mem_id in saved_ids[1:]:
                rel_type = 'duplicate' if label == 'duplicate' else 'related'
                repo.create_relationship(primary_id, mem_id, rel_type)
                relationships_created += 1

    return SeedResponse(
        status="success",
        memories_created=memories_created,
        relationships_created=relationships_created
    )