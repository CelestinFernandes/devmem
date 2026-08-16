import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid

class CockroachRepository:
    def __init__(self, db_url):
        self.db_url = db_url

    def _get_conn(self):
        return psycopg2.connect(self.db_url)

    def save_memory(self, memory_dto, embedding):
        """Save a memory with its embedding vector"""
        # Prepare technologies array for PostgreSQL
        techs = memory_dto.get('technologies', [])
        if isinstance(techs, str):
            # if it's a string, split by comma
            techs = [t.strip() for t in techs.split(',') if t.strip()]
        elif not isinstance(techs, list):
            techs = []
        # Convert to PostgreSQL array literal: {item1,item2,item3}
        techs_array = '{' + ','.join(techs) + '}' if techs else '{}'

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memories 
                    (id, title, problem, cause, fix, lesson, technologies, 
                     embedding, confidence, needs_review, importance, frequency, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    memory_dto['id'],
                    memory_dto['title'],
                    memory_dto['problem'],
                    memory_dto['cause'],
                    memory_dto['fix'],
                    memory_dto['lesson'],
                    techs_array,  # <-- now a properly formatted array literal
                    embedding,
                    memory_dto.get('confidence', 0.8),
                    memory_dto.get('needs_review', False),
                    memory_dto.get('importance', 0.5),
                    1,
                    'ACTIVE'
                ))
                return memory_dto['id']

    def vector_search(self, query_embedding, limit=5):
        """Find top-K most similar memories"""
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, title, problem, cause, fix, lesson, technologies,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM memories
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                return cur.fetchall()

    def update_confidence(self, memory_id, bump=0.05):
        """Increase confidence when memory is reused"""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE memories 
                    SET confidence = LEAST(confidence + %s, 1.0),
                        last_used_at = now()
                    WHERE id = %s
                """, (bump, memory_id))

    def increment_frequency(self, memory_id):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE memories 
                    SET frequency = frequency + 1,
                        last_used_at = now()
                    WHERE id = %s
                """, (memory_id,))

    def create_relationship(self, id_a, id_b, rel_type="related"):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO relationships (memory_id_a, memory_id_b, relation_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (memory_id_a, memory_id_b) DO NOTHING
                """, (id_a, id_b, rel_type))