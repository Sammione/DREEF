import os
try:
    import pyodbc
except ImportError:
    pyodbc = None
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    # RE-ENABLING FOR AZURE DEPLOYMENT (Ensures goal for memory and history is met)
    connection_string = os.getenv("DB_CONNECTION_STRING")
    if not pyodbc:
        print("pyodbc is not installed/available. Persistent memory will be disabled.")
        return None
    
    if not connection_string:
        print("DB_CONNECTION_STRING not set. Persistent memory will be disabled.")
        return None
        
    try:
        # Added a 5-second timeout to avoid long hangs
        conn = pyodbc.connect(connection_string, timeout=5)
        return conn
    except Exception as e:
        print(f"Error connecting to database (History won't be stored): {e}")
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


def get_all_sessions(user_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        # SQL to get distinct sessions with their most recent timestamp and first user message
        # This is for SQL Server (T-SQL) as suggested by IF NOT EXISTS (SELECT * FROM sysobjects...)
        query = """
            SELECT SessionId, 
                   (SELECT TOP 1 Content FROM ChatHistory WHERE SessionId = c.SessionId AND Role = 'user' ORDER BY Timestamp ASC) as Title,
                   MAX(Timestamp) as LastActive
            FROM ChatHistory c
            WHERE UserId = ?
            GROUP BY SessionId
            ORDER BY LastActive DESC
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        # Return as list of dicts: {"id": "...", "title": "..."}
        return [{"id": row[0], "title": row[1] or "New Chat"} for row in rows]
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return []
    finally:
        if conn:
            conn.close()
