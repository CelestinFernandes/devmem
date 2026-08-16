import psycopg2

# PASTE YOUR CONNECTION STRING WITH THE REAL PASSWORD HERE
DATABASE_URL = "postgresql://mochineko:Ck6bEvX-aSy5BJX0qUNZEg@jagged-otter-31419.j77.aws-ap-south-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Try to count how many memories are already in there
    cur.execute("SELECT COUNT(*) FROM memories;")
    count = cur.fetchone()[0]
    
    print(f"✅ Connection successful! There are {count} memories already in the database.")
    print("🎉 Your teammate already set up the tables. You are ready to go!")
    
    cur.close()
    conn.close()

except Exception as e:
    print("❌ Something went wrong:")
    print(e)
    print("\nIf the error says 'relation memories does not exist', that means he DID NOT create the tables yet. Run my big setup script from before.")