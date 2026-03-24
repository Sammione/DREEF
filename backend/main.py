import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from database import store_chat_history, get_chat_history
from openai_service import generate_chat_response
from rag_service import search_kb, initialize_mock_kb, add_document_to_kb
from sharepoint_service import list_files_in_document_library, download_file_content, extract_text_from_binary

load_dotenv()

# Starting API without mock data

app = FastAPI(title="DRFEER ChatGPT-like API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

@app.get("/")
async def root():
    return {"message": "DRFEER ChatGPT-like API is running"}

@app.get("/health")
async def health():
    """Diagnostic check to see reachability and check config presence."""
    return {
        "status": "online",
        "service": "DRFEER AI Backend",
        "configuration": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "sharepoint_site": bool(os.getenv("SHAREPOINT_SITE_URL")),
            "sharepoint_client_id": bool(os.getenv("SHAREPOINT_CLIENT_ID")),
            "database_connected": os.getenv("DB_CONNECTION_STRING") is not None,
            "pyodbc_available": True # If it's running, it's True
        }
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 1. Fetch history from DB (Memory)
        history = get_chat_history(request.user_id, request.session_id)
        
        # 2. RAG Logic (Search Knowledge Base)
        knowledge_context = search_kb(request.message)
        
        if not knowledge_context:
            knowledge_context = "No specific documents found in the Knowledge Base for this query."
        
        # 3. Prepare strict system prompt
        system_msg = {
            "role": "system", 
            "content": (
                "You are DRFEER AI, a professional corporate assistant. Your primary task is to answer "
                "questions based strictly on the provided Knowledge Base context. \n\n"
                "RULES:\n"
                "1. If the answer is not in the context, say: 'I cannot find the response from the knowledge base.'\n"
                "2. Do NOT hallucinate or use outside information for business-specific facts.\n"
                "3. Always cite your sources at the end of your response using [Filename](URL) format if a link is provided.\n"
                "4. You MUST still respond naturally to greetings (e.g., 'Hello', 'Hi', 'Who are you?'). \n\n"
                f"CONTEXT FROM KNOWLEDGE BASE:\n{knowledge_context}"
            )
        }
        
        # Prepare OpenAI history format
        openai_messages = [system_msg] + history + [{"role": "user", "content": request.message}]
        
        # 4. Generate response
        ai_response_text = generate_chat_response(openai_messages)
        
        # 5. Store in persistent history (Memory)
        store_chat_history(request.user_id, request.session_id, "user", request.message)
        store_chat_history(request.user_id, request.session_id, "assistant", ai_response_text)
        
        return {"response": ai_response_text}
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_sharepoint_docs():
    """
    Trigger ingestion of documents from the configured SharePoint library.
    Also saves a physical copy to the 'synced_documents' folder.
    """
    try:
        print("Starting SharePoint ingestion...")
        files = list_files_in_document_library()
        if not files:
            print("No files found in SharePoint or connection failed.")
            return {"message": "No files found in SharePoint or connection failed."}
        
        print(f"Found {len(files)} files to process.")
        
        # Create a local folder for synced files
        sync_dir = os.path.join(os.path.dirname(__file__), "synced_documents")
        if not os.path.exists(sync_dir):
            os.makedirs(sync_dir)
            
        ingested_count = 0
        for file_info in files:
            file_name = file_info["name"]
            print(f"Processing: {file_name}")
            
            # 1. Download Content
            content = download_file_content(file_info["server_relative_url"])
            if content:
                # 2. Save physical copy locally
                file_path = os.path.join(sync_dir, file_name)
                # Ensure parent dirs exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # 3. Process for Knowledge Base
                if any(file_name.lower().endswith(ext) for ext in ['.txt', '.md', '.pdf', '.docx']):
                    print(f"Extracting & chunking: {file_name}")
                    chunks = extract_text_from_binary(content, file_name)
                    print(f"Generated {len(chunks)} chunks.")
                    
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
                print(f"Successfully processed: {file_name}")
        
        return {
            "message": f"Ingestion complete. {ingested_count} files synced and saved locally.",
            "storage_path": sync_dir,
            "total_files_found": len(files)
        }
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

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
            if meta and 'filename' in meta:
                fname = meta['filename']
                if fname not in seen:
                    files.append({"name": fname, "source": meta.get('source', 'Unknown')})
                    seen.add(fname)
        return {"files": files}
    except Exception as e:
        print(f"Error fetching files: {e}")
        return {"files": []}

@app.get("/history")
async def get_history(user_id: str, session_id: str):
    history = get_chat_history(user_id, session_id)
    # Correct key name for openai history items is 'assistant', not 'ai'
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
