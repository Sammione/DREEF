import os
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./chroma_db")
try:
    collection = client.get_collection(name="drfeer_kb")
    count = collection.count()
    print(f"TOTAL_DOCS_IN_KB: {count}")
    if count > 0:
        results = collection.get()
        for i, doc in enumerate(results['documents'][:5]):
            print(f"DOC {i+1}: {doc[:100]}...")
except Exception as e:
    print(f"ERROR CHECKING KB: {e}")
