import os
import psycopg2


DB_URL = os.getenv("DATABASE_URL")
# PASTE YOUR CONNECTION STRING WITH THE REAL PASSWORD HERE
DATABASE_URL = "DB_URL"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Try to count how many memories are already in there
    cur.execute("SELECT COUNT(*) FROM memories;")
    count = cur.fetchone()[0]
    
    print(f" Connection successful! There are {count} memories already in the database.")
    print(" already set up the tables. You are ready to go!")
    
    cur.close()
    conn.close()

except Exception as e:
    print(" Something went wrong:")
    print(e)
    print("\nIf the error says 'relation memories does not exist', that must create the tables.")