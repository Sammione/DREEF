# Deployment Entry Point (Robust for Azure/Render)
import sys
import os

# --- CRITICAL: PATCH SQLITE FOR CHROMADB ---
try:
    import pysqlite3 as sqlite3
    sys.modules['sqlite3'] = sqlite3
except ImportError:
    pass

# Root directory setup
root_path = os.path.dirname(os.path.abspath(__file__))
if root_path not in sys.path:
    sys.path.append(root_path)

try:
    # Now that the backend is in the root, we import directly
    from main import app
    print("Backend application loaded successfully from root!")
except Exception as e:
    print(f"FAILED TO LOAD BACKEND APP: {e}")
    from fastapi import FastAPI
    app = FastAPI(title="DRFEER - Error Fallback")
    @app.get("/")
    async def root(): return {"status": "error", "message": f"Initialization failed: {str(e)}"}
