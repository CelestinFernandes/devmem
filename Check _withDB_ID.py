import os
import psycopg2
from psycopg2.extras import RealDictCursor
DB_URL = os.getenv("DATABASE_URL")
DB_URL = f"{DB_URL}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Pick any memory ID from the previous step
memory_id = "7d5163e9-b238-4e2e-a96c-a63d706fc822"  # replace with actual ID

cur.execute("SELECT id, title, problem, cause, fix, lesson FROM memories WHERE id = %s", (memory_id,))
mem = cur.fetchone()
if mem:
    print(f"Title: {mem['title']}")
    print(f"Problem: {mem['problem']}")
    print(f"Cause: {mem['cause']}")
    print(f"Fix: {mem['fix']}")
    print(f"Lesson: {mem['lesson']}")
else:
    print("Memory not found")
cur.close()
conn.close()