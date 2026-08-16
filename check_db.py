import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Count memories
cur.execute("SELECT COUNT(*) FROM memories")
count = cur.fetchone()
print(f"📊 Total memories in DB: {count['count']}")

# Show recent memories
cur.execute("SELECT id, title, confidence, created_at FROM memories ORDER BY created_at DESC LIMIT 5")
memories = cur.fetchall()
print("\n📝 Recent memories:")
for mem in memories:
    print(f"  - {mem['title'][:50]}... (confidence: {mem['confidence']})")

# Check relationships
cur.execute("SELECT COUNT(*) FROM relationships")
rel_count = cur.fetchone()
print(f"\n🔗 Total relationships in DB: {rel_count['count']}")

if rel_count['count'] > 0:
    cur.execute("SELECT * FROM relationships LIMIT 5")
    rels = cur.fetchall()
    print("   Sample relationships:")
    for r in rels:
        print(f"     {r['memory_id_a'][:8]} -> {r['memory_id_b'][:8]} ({r['relation_type']})")
else:
    print("   ⚠️ No relationships found. The Knowledge Graph will show nothing.")

cur.close()
conn.close()