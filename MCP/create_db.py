import sqlite3

def create_database(db_path: str, sql_file: str):
    # Connect (or create) the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read SQL commands from file
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_script = f.read()

    # Execute SQL script
    cursor.executescript(sql_script)

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print(f"Database created at {db_path}")

if __name__ == "__main__":
    create_database("test.sqlite", "test.sql")
