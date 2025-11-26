import sqlite3

DB_FILE = "data.db"
TABLE_NAME = "main"

try:
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_FILE)
    # This allows accessing columns by name (like a dictionary)
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()

    print(f"Successfully connected to {DB_FILE}")

    cursor.execute(f"SELECT name FROM sqlite_master;")

    rows = cursor.fetchall()
    print("Existing tables in the database:")
    print(rows)

    # Execute the query on the 'mained' table
    print(f"Executing query: SELECT * FROM {TABLE_NAME}")
    cursor.execute(f"SELECT * FROM {TABLE_NAME}")
    
    # Fetch all results
    rows = cursor.fetchall()
    result = ""
    # Convert each row object to a standard dictionary
    for row in rows:
        result += row['question'] + ";"

    print(result)

except sqlite3.Error as e:
    # Handle potential SQL errors, like "no such table"
    print(f"\nAn error occurred: {e}")

finally:
    # Ensure the connection is closed even if an error occurs
    if 'conn' in locals() and conn:
        conn.close()
        print("\nDatabase connection closed.")