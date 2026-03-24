# Deployment Trigger: Secret added (Robust Application Layer)
import sys
import os
import logging

# Ensure root directory is in sys.path
root_path = os.path.dirname(os.path.abspath(__file__))
if root_path not in sys.path:
    sys.path.append(root_path)

# Add the backend directory to sys.path
backend_path = os.path.join(root_path, 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    # Import the FastAPI app instance from backend.main
    from main import app
    print("Backend application loaded successfully!")
except Exception as e:
    print(f"FAILED TO LOAD BACKEND APP: {e}")
    # Create a fallback FastAPI app to show the error
    from fastapi import FastAPI
    app = FastAPI(title="DRFEER - Deployment Fallback")
    @app.get("/")
    async def root():
        return {
            "status": "error", 
            "message": "The backend failed to load. Check logs for details.",
            "error": str(e)
        }
