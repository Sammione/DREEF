# Deployment Entry Point (Robust for Azure/Render)
import sys
import os

# --- CRITICAL: PATCH SQLITE FOR CHROMADB ---
try:
    import pysqlite3 as sqlite3
    sys.modules['sqlite3'] = sqlite3
except ImportError:
    pass

# Ensure backend directory is in sys.path
root_path = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(root_path, 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    # Explicitly import from backend.main
    from main import app
    print("Backend application loaded successfully!")
except ImportError:
    # Try alternate import path
    try:
        from backend.main import app
    except Exception as e:
        print(f"FAILED TO LOAD BACKEND APP: {e}")
        from fastapi import FastAPI
        app = FastAPI(title="DRFEER - Error Fallback")
        @app.get("/")
        async def root(): return {"status": "error", "message": str(e)}
except Exception as e:
    print(f"FAILED TO LOAD BACKEND APP: {e}")
    from fastapi import FastAPI
    app = FastAPI(title="DRFEER - Error Fallback")
    @app.get("/")
    async def root(): return {"status": "error", "message": str(e)}
