# Deployment Trigger: Secret added
import sys
import os

# 1. Add the backend directory to sys.path so its modules can be found
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_path)

# 2. Change the current working directory to the backend folder
# This ensures relative paths (for database, synced_documents, etc.) work correctly
os.chdir(backend_path)

# 3. Import the FastAPI app instance from main.py
from main import app
