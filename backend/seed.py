import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database_from_sql():
    # Connect to MySQL server
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cursor = conn.cursor()

    # Read and execute the SQL file
    try:
        with open('init.sql', 'r') as file:
            sql_script = file.read()
            
        # Execute each statement separated by a semicolon
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        print("Database schema created successfully from init.sql.")
    except Exception as e:
        print(f"Error reading or executing init.sql: {e}")

    # ---------------------------------------------------------
    # Add your data seeding logic here
    # Example: Insert dummy users, posts, etc.
    # ---------------------------------------------------------
    # cursor.execute("INSERT INTO users (name, email...) VALUES ...")
    # conn.commit()

    cursor.close()
    conn.close()

if __name__ == '__main__':
    setup_database_from_sql()