import uuid
import numpy as np

DUPLICATE_THRESHOLD = 0.90
RELATED_THRESHOLD = 0.75

class MemoryService:
    def __init__(self, repository, embedding_service):
        self.repo = repository
        self.embedding_service = embedding_service

    def get_embedding_text(self, memory):
        problem = memory.get('problem', '')
        cause = memory.get('cause', '')
        techs = ' '.join(memory.get('technologies', []))
        return f"{problem} {cause} {techs}"

    def save_memory(self, raw_text, extracted_data):
        if 'title' not in extracted_data or not extracted_data['title']:
            extracted_data['title'] = raw_text[:100] + ('...' if len(raw_text) > 100 else '')

        embed_text = self.get_embedding_text(extracted_data)
        embedding = self.embedding_service.encode(embed_text).tolist()

        if 'id' not in extracted_data:
            extracted_data['id'] = str(uuid.uuid4())
        new_id = extracted_data['id']

        existing = self.repo.vector_search(embedding, limit=5)

        for mem in existing:
            if mem['similarity'] >= DUPLICATE_THRESHOLD:
                self.repo.update_confidence(mem['id'], bump=0.05)
                self.repo.increment_frequency(mem['id'])
                return {
                    "status": "duplicate",
                    "memory_id": mem['id'],
                    "similarity": mem['similarity'],
                    "message": "This learning already exists. Confidence bumped."
                }

        self.repo.save_memory(extracted_data, embedding)

        related_count = 0
        for mem in existing:
            if mem['similarity'] >= RELATED_THRESHOLD:
                self.repo.create_relationship(new_id, mem['id'], "related")
                related_count += 1

        return {
            "status": "new",
            "memory_id": new_id,
            "related_count": related_count,
            "message": f"New memory saved with {related_count} related links."
        }