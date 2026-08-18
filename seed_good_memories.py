
import os
import psycopg2
import uuid
from sentence_transformers import SentenceTransformer

DB_URL = os.getenv("DATABASE_URL")
DB_URL = f"{DB_URL}"

print(" Loading MiniLM...")
model = SentenceTransformer('all-MiniLM-L6-v2')

good_memories = [
    {
        "title": "React app performance optimization with memoization",
        "problem": "React app was slow due to excessive re-renders",
        "cause": "Components re-rendered unnecessarily without memoization",
        "fix": "Added React.memo and useCallback to prevent unnecessary re-renders",
        "lesson": "Always use React.memo for expensive components and useCallback for event handlers",
        "technologies": ["react", "javascript"]
    },
    {
        "title": "Kubernetes pod OOMKilled resolved by increasing memory",
        "problem": "Kubernetes pod crashed with OOMKilled error",
        "cause": "Memory limit was set too low for the application",
        "fix": "Increased memory limit from 512Mi to 1Gi in deployment.yaml",
        "lesson": "Monitor actual resource usage before setting limits",
        "technologies": ["kubernetes", "docker"]
    },
    {
        "title": "PostgreSQL connection pool optimization",
        "problem": "PostgreSQL connection latency was high",
        "cause": "Connection pool was not properly configured",
        "fix": "Set max_connections to 50 in connection pool configuration",
        "lesson": "Always tune connection pool size based on workload",
        "technologies": ["postgres", "python"]
    }
]

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

for mem in good_memories:
    # Generate embedding
    embed_text = f"{mem['problem']} {mem['cause']} {' '.join(mem['technologies'])}"
    embedding = model.encode(embed_text).tolist()
    
    # Generate ID
    mem_id = str(uuid.uuid4())
    
    # Insert
    cur.execute("""
        INSERT INTO memories 
        (id, title, problem, cause, fix, lesson, technologies, embedding, confidence, status, frequency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        mem_id,
        mem['title'],
        mem['problem'],
        mem['cause'],
        mem['fix'],
        mem['lesson'],
        '{' + ','.join(mem['technologies']) + '}',
        embedding,
        0.9,
        'ACTIVE',
        1
    ))
    print(f" Inserted: {mem['title']}")

conn.commit()
cur.close()
conn.close()
print(" All good memories inserted!")