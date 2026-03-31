import sys
import os

# --- CRITICAL: MUST BE AT THE VERY TOP TO PATCH SQLITE FOR CHROMADB ---
try:
    import pysqlite3 as sqlite3
    sys.modules['sqlite3'] = sqlite3
    print("SQLite successfully patched with pysqlite3-binary.")
except ImportError:
    try:
        import sqlite3
        print("Using standard sqlite3.")
    except Exception as e:
        print(f"Warning: Could not load sqlite3 or pysqlite3: {e}")

from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from database import store_chat_history, get_chat_history, get_all_sessions
from openai_service import generate_chat_response
from rag_service import search_kb, initialize_mock_kb, add_document_to_kb
from sharepoint_service import list_files_in_document_library, download_file_content, extract_text_from_binary

load_dotenv()

# Starting API
app = FastAPI(title="DREEF ChatGPT-like API")

# Global history of logs for diagnostics (accessible via /logs)
GLOBAL_LOGS = []

def log_event(message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    GLOBAL_LOGS.append(entry)
    if len(GLOBAL_LOGS) > 100:
        GLOBAL_LOGS.pop(0)

@app.on_event("startup")
async def startup_event():
    log_event("Application Startup initiated.")
    try:
        initialize_mock_kb()
        log_event("Mock Knowledge Base ensured/initialized.")
    except Exception as e:
        log_event(f"Error initializing mock KB: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

@app.get("/")
async def root():
    return {"message": "DREEF ChatGPT-like API is running"}

@app.get("/health")
async def health():
    """Diagnostic check to see reachability and check config presence."""
    import psutil # Ensure this is in requirements!
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_stats = {
            "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
            "vms_mb": round(mem_info.vms / (1024 * 1024), 2),
        }
    except:
        mem_stats = "unavailable"
    
    return {
        "status": "online",
        "service": "DREEF AI Backend",
        "memory": mem_stats,
        "configuration": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "sharepoint_site": bool(os.getenv("SHAREPOINT_SITE_URL")),
            "sharepoint_client_id": bool(os.getenv("SHAREPOINT_CLIENT_ID")),
            "database_connected": os.getenv("DB_CONNECTION_STRING") is not None,
            "pyodbc_available": True 
        }
    }

@app.get("/logs")
async def get_logs():
    """Access runtime diagnostic logs."""
    return {"logs": GLOBAL_LOGS}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        log_event(f">>> Processing /CHAT | User: {request.user_id} | Msg: {request.message[:50]}...")
        
        # 1. Fetch history from DB (Memory)
        log_event("Fetching history...")
        history = get_chat_history(request.user_id, request.session_id)
        
        # 2. RAG Logic (Search Knowledge Base)
        log_event("Searching knowledge base (Chromadb)...")
        try:
            knowledge_context = search_kb(request.message)
            log_event(f"KB Search Complete. Context size: {len(knowledge_context)} chars.")
        except Exception as e:
            log_event(f"ERROR in KB Search: {e}")
            knowledge_context = "Error retrieving from knowledge base."
        
        if not knowledge_context or "No specific documents found" in knowledge_context:
            log_event("No relevant KB documents found.")
            knowledge_context = "No specific documents found in the Knowledge Base for this query."
        
        
        log_event("Calling OpenAI Chat Completion...")
        system_msg = {
            "role": "system", 
            "content": (
                "You are the DREEF Intelligent Consultant, a highly sophisticated AI expert trained to analyze corporate data. "
                "Your objective is to provide professional, synthesized, and conversational responses based on SharePoint documents. \n\n"
                "GUIDELINES:\n"
                "1. NEVER just copy and paste text. Always rephrase and explain information in your own professional words.\n"
                "2. If the answer is in the documents, summarize clearly. If not available, state that you don't have that specific information in your repository.\n"
                "3. GREETINGS: For greetings (Hello, Hi, etc.), simply respond: 'How can I assist you today?' (Do not add long data-related suffixes).\n"
                "4. CITATIONS: List used sources at the end: 'Sources: [Filename](URL)'.\n"
                "5. PERSONALITY: Helpful, sharp, and corporate-toned.\n\n"
                "KNOWLEDGE BASE CONTEXT:\n"
                "--------------------\n"
                f"{knowledge_context}\n"
                "--------------------"
            )
        }
        openai_messages = [system_msg] + history + [{"role": "user", "content": request.message}]
        
        # 4. Generate response
        ai_response_text = generate_chat_response(openai_messages)
        log_event("OpenAI generation successful.")
        
        # 5. Store history
        log_event("Storing chat history...")
        store_chat_history(request.user_id, request.session_id, "user", request.message)
        store_chat_history(request.user_id, request.session_id, "assistant", ai_response_text)
        
        log_event("<<< /CHAT SUCCESSFUL")
        return {"response": ai_response_text}
    except Exception as e:
        log_event(f"!!! CRITICAL FAIL in /chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def run_ingestion():
    """Background task for ingestion."""
    from rag_service import collection
    try:
        log_event("Starting SharePoint background ingestion...")
        
        # CLEAR EXISTING DATA BEFORE SYNC
        log_event("Clearing existing Knowledge Base documents for a clean sync...")
        try:
            results = collection.get()
            if results['ids']:
                collection.delete(ids=results['ids'])
            log_event("Existing Knowledge Base cleared.")
        except Exception as e:
            log_event(f"Note: Could not clear KB (it might already be empty): {e}")

        doc_lib = os.getenv("SHAREPOINT_DOC_LIB", "Shared Documents")
        files, drive_id, token = list_files_in_document_library(doc_lib)
        
        if not files:
            log_event("No files found or connection failed during background sync.")
            return

        log_event(f"Found {len(files)} files. Starting processing...")
        sync_dir = os.path.join(os.path.dirname(__file__), "synced_documents")
        if not os.path.exists(sync_dir):
            os.makedirs(sync_dir)

        ingested_count = 0
        for file_info in files:
            file_name = file_info["name"]
            log_event(f"BG Processing: {file_name}")
            
            content = download_file_content(file_info["server_relative_url"], drive_id, token)
            if content:
                file_path = os.path.join(sync_dir, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(content)
                
                if any(file_name.lower().endswith(ext) for ext in ['.txt', '.md', '.pdf', '.docx']):
                    chunks = extract_text_from_binary(content, file_name)
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"sp_{file_name.replace(' ', '_')}_v{i}"
                        metadata = {
                            "source": "SharePoint", 
                            "filename": file_name, 
                            "webUrl": file_info.get("webUrl", ""),
                            "chunk_index": i
                        }
                        add_document_to_kb(chunk_id, chunk, metadata)
                
                ingested_count += 1
        log_event(f"Background ingestion complete. {ingested_count} files processed.")
    except Exception as e:
        log_event(f"Error in background ingestion: {e}")

@app.post("/ingest")
async def ingest_sharepoint_docs(background_tasks: BackgroundTasks):
    """Trigger background ingestion."""
    background_tasks.add_task(run_ingestion)
    return {"message": "Ingestion started in the background (Existing data cleared). Please check /logs for progress."}

@app.get("/files")
async def get_synced_files():
    """
    Get the list of files currently in the Knowledge Base.
    """
    from rag_service import collection
    try:
        results = collection.get()
        # Extract unique filenames from metadata
        files = []
        seen = set()
        for meta in results.get('metadatas', []):
            if not meta: continue
            fname = meta.get('filename') or meta.get('source')
            if fname and fname not in seen:
                files.append({"name": fname, "source": meta.get('source', 'SharePoint')})
                seen.add(fname)
        return {"files": files}
    except Exception as e:
        print(f"Error fetching files: {e}")
        return {"files": []}

@app.get("/history")
async def get_history(user_id: str, session_id: str):
    """Get chat history for a specific session."""
    history = get_chat_history(user_id, session_id)
    return {"history": history}

@app.get("/sessions")
async def get_sessions(user_id: str):
    """Get list of previous session IDs for a user."""
    sessions = get_all_sessions(user_id)
    return {"sessions": sessions}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
