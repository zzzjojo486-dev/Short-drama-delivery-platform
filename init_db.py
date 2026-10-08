import pymysql
from backend.database import db
import os

def init_db():
    print("Initializing database...")
    conn = db.get_connection()
    if not conn:
        print("Failed to connect to database")
        return

    # Read schema.sql
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()

    # Split by semicolon to execute individual statements
    # This is a simple parser, might fail on complex statements with semicolons in strings
    # but schema.sql looks simple enough.
    statements = schema.split(';')
    
    try:
        with conn.cursor() as cursor:
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        print(f"Executed: {statement[:50]}...")
                    except pymysql.MySQLError as e:
                        # Ignore "Table already exists" errors if any, though IF NOT EXISTS should handle it
                        print(f"Error executing statement: {e}")
        print("Database initialization complete.")
    except Exception as e:
        print(f"Error during initialization: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()

