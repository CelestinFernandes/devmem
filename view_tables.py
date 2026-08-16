import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://mochineko:Ck6bEvX-aSy5BJX0qUNZEg@jagged-otter-31419.j77.aws-ap-south-1.cockroachlabs.cloud:26257/devmem_db?sslmode=require"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Show all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = cur.fetchall()
print("📋 Tables in devmem_db:")
for t in tables:
    print(f"  - {t['table_name']}")

# Show memories
cur.execute("SELECT id, title, confidence, status, created_at FROM memories ORDER BY created_at DESC;")
memories = cur.fetchall()
print(f"\n🧠 Memories ({len(memories)} total):")
for m in memories:
    print(f"  - {m['title'][:40]}... (conf: {m['confidence']}, status: {m['status']})")

# Show relationships
cur.execute("SELECT memory_id_a, memory_id_b, relation_type FROM relationships;")
rels = cur.fetchall()
print(f"\n🔗 Relationships ({len(rels)} total):")
for r in rels:
    print(f"  - {r['memory_id_a'][:8]}... ↔ {r['memory_id_b'][:8]}... ({r['relation_type']})")

cur.close()
conn.close()