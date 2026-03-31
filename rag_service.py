import os
import sys

# SQLite fix for ChromaDB on many Linux environments (Render/Vercel)
try:
    if 'sqlite3' in sys.modules:
        del sys.modules['sqlite3']
    import pysqlite3 as sqlite3
    sys.modules['sqlite3'] = sqlite3
except ImportError:
    import sqlite3

import chromadb
from chromadb.utils import embedding_functions
from openai_service import get_embeddings
from dotenv import load_dotenv

load_dotenv()

# Setup ChromaDB for local vector storage
# This will act as our "Knowledge Base"
# Use absolute path to avoid working directory issues on Azure
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(
    name="dreef_kb",
    embedding_function=embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
)

def add_document_to_kb(doc_id, text, metadata=None):
    """Add a document snippet to the vector store."""
    try:
        collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata] if metadata else None
        )
        return True
    except Exception as e:
        print(f"Error adding to KB: {e}")
        return False

def search_kb(query, n_results=5):
    """Search for relevant snippets and include source metadata."""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        # Extract documents and metadatas
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        # Format as numbered snippets with metadata
        formatted_snippets = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            source_name = meta.get('filename') or meta.get('source') or "Internal Document"
            web_url = meta.get('webUrl', None)
            
            snippet_text = (
                f"=== DOCUMENT SNIPPET {i+1} ===\n"
                f"SOURCE: {source_name}\n"
                f"URL: {web_url if web_url else 'No link available'}\n"
                f"CONTENT:\n{doc}\n"
            )
            formatted_snippets.append(snippet_text)
            
        context = "\n\n".join(formatted_snippets)
        return context
    except Exception as e:
        print(f"Error searching KB: {e}")
        return ""

def initialize_mock_kb():
    """Knowledge base initialized empty (no mock data)."""
    # Previously contained sample HR policies. Removed for production.
    pass
