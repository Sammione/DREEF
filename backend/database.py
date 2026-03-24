import os
try:
    import pyodbc
except ImportError:
    pyodbc = None
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    # TEMPORARILY DISABLED SQL PERSISTENCE TO AVOID 30s TIMEOUTS
    return None
    
    connection_string = os.getenv("DB_CONNECTION_STRING")
    if not pyodbc:
        print("pyodbc is not installed/available.")
        return None
        
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def store_chat_history(user_id, session_id, role, content):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        # Ensure table exists (Simplified schema)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ChatHistory' AND xtype='U')
            CREATE TABLE ChatHistory (
                Id INT IDENTITY(1,1) PRIMARY KEY,
                UserId NVARCHAR(255),
                SessionId NVARCHAR(255),
                Role NVARCHAR(50),
                Content NVARCHAR(MAX),
                Timestamp DATETIME DEFAULT GETDATE()
            )
        """)
        cursor.execute(
            "INSERT INTO ChatHistory (UserId, SessionId, Role, Content) VALUES (?, ?, ?, ?)",
            (user_id, session_id, role, content)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing chat history: {e}")
        return False
    finally:
        conn.close()

def get_chat_history(user_id, session_id, limit=10):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Role, Content FROM ChatHistory WHERE UserId = ? AND SessionId = ? ORDER BY Timestamp ASC",
            (user_id, session_id)
        )
        rows = cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []
    finally:
        conn.close()
