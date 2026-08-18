import os
import os
import psycopg2
DB_URL = os.getenv("DATABASE_URL")
DATABASE_URL = "DB_URL"

print("Connecting to the cloud database...")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

cur.execute("CREATE DATABASE IF NOT EXISTS devmem_db;")
print(" Database 'devmem_db' created (or already exists)")

# 3. Switch to that new database
conn.close()
DB_URL = DB_URL.replace("defaultdb", "devmem_db")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# 4. Turn on Vector Search (this is mandatory for your AI)
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
print(" Vector extension enabled")

# 5. Create the "memories" table
cur.execute("""
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    problem TEXT,
    cause TEXT,
    fix TEXT,
    lesson TEXT,
    technologies TEXT[],
    embedding vector(384),
    confidence FLOAT DEFAULT 0.8,
    needs_review BOOLEAN DEFAULT FALSE,
    importance FLOAT DEFAULT 0.5,
    frequency INT DEFAULT 1,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT now(),
    last_used_at TIMESTAMP DEFAULT now()
);
""")
print(" Table 'memories' created")

# 6. Create the "relationships" table
cur.execute("""
CREATE TABLE IF NOT EXISTS relationships (
    memory_id_a UUID REFERENCES memories(id) ON DELETE CASCADE,
    memory_id_b UUID REFERENCES memories(id) ON DELETE CASCADE,
    relation_type TEXT DEFAULT 'related',
    PRIMARY KEY (memory_id_a, memory_id_b)
);
""")
print(" Table 'relationships' created")
print(" Table 'relationships' created")

conn.commit()
cur.close()
conn.close()
print(" ALL DONE! Your database is ready.")
print(" ALL DONE! Your database is ready.")