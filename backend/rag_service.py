import os
import chromadb
from chromadb.utils import embedding_functions
from openai_service import get_embeddings
from dotenv import load_dotenv

load_dotenv()

# Setup ChromaDB for local vector storage
# This will act as our "Knowledge Base"
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="drfeer_kb",
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
            source_name = meta.get('filename') or meta.get('source') or "Unknown Source"
            web_url = meta.get('webUrl', None)
            source_info = f"Source: {source_name}"
            if web_url:
                source_info += f" (Link: {web_url})"
            formatted_snippets.append(f"Snippet [{i+1}]:\nContent: {doc}\n{source_info}")
            
        context = "\n\n---\n\n".join(formatted_snippets)
        return context
    except Exception as e:
        print(f"Error searching KB: {e}")
        return ""

def initialize_mock_kb():
    """Initializes a mock knowledge base if none exists."""
    if collection.count() == 0:
        add_document_to_kb(
            "doc1", 
            "DRFEER Company Policy: Employees are entitled to 25 days of annual leave. Working hours are from 9 AM to 5 PM.",
            {"source": "HR_Policy.pdf"}
        )
        add_document_to_kb(
            "doc2", 
            "Project DRFEER: The goal is to build an AI platform that integrates SharePoint and SQL Databases for company-wide intelligence.",
            {"source": "Project_Drfeer_Overview.docx"}
        )
        print("Mock Knowledge Base initialized with 2 documents.")
