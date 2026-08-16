import psycopg2
import os

# ---------- CONFIG ----------
# REPLACE with your real password
DB_URL = os.getenv("DATABASE_URL")
DB_URL = f"{DB_URL}"

print("🔌 Connecting to CockroachDB...")
conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cur = conn.cursor()

# 1. Create the database (if it doesn't exist)
print("📦 Creating database 'devmem_db'...")
cur.execute("CREATE DATABASE IF NOT EXISTS devmem_db;")

# 2. Switch to devmem_db
conn.close()
DB_URL_DEV = DB_URL.replace("defaultdb", "devmem_db")
conn = psycopg2.connect(DB_URL_DEV)
cur = conn.cursor()

# 3. Enable Vector extension
print("🧠 Enabling pgvector...")
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

# 4. Create memories table
print("📋 Creating 'memories' table...")
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

# 5. Create relationships table
print("🔗 Creating 'relationships' table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS relationships (
    memory_id_a UUID REFERENCES memories(id) ON DELETE CASCADE,
    memory_id_b UUID REFERENCES memories(id) ON DELETE CASCADE,
    relation_type TEXT DEFAULT 'related',
    PRIMARY KEY (memory_id_a, memory_id_b)
);
""")

# # 6. Create vector index for fast similarity search
# print("⚡ Creating vector index...")
# cur.execute("""
# CREATE INDEX IF NOT EXISTS idx_memories_embedding 
# ON memories USING ivfflat (embedding vector_cosine_ops) 
# WITH (lists = 100);
# """)

conn.commit()
cur.close()
conn.close()

print("\n✅ ALL DONE! Tables created successfully.")
print(f"   Database: devmem_db")
print("   Tables: memories, relationships")
print("   Index: idx_memories_embedding")