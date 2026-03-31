import os
import requests
from urllib.parse import urlparse
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from dotenv import load_dotenv

load_dotenv()

# SharePoint Configuration
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
SHAREPOINT_CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
SHAREPOINT_CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
SHAREPOINT_DOC_LIB = os.getenv("SHAREPOINT_DOC_LIB", "Shared Documents")

from msal import ConfidentialClientApplication

def get_graph_token():
    """
    Acquire access token for Microsoft Graph.
    """
    if not SHAREPOINT_CLIENT_ID or not SHAREPOINT_CLIENT_SECRET or not AZURE_TENANT_ID:
        print("SharePoint configuration is incomplete.")
        return None
    
    authority = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    app = ConfidentialClientApplication(
        SHAREPOINT_CLIENT_ID, 
        authority=authority, 
        client_credential=SHAREPOINT_CLIENT_SECRET
    )
    
    # Scope for Microsoft Graph
    scopes = ["https://graph.microsoft.com/.default"]
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" in result:
        return result['access_token']
    else:
        print(f"Failed to acquire Graph token: {result.get('error')}")
        return None

def list_all_files_recursively(site_id, drive_id, folder_id='root', token=None):
    """
    Recursively list all files in a drive.
    """
    if not token:
        token = get_graph_token()
    
    headers = {"Authorization": f"Bearer {token}"}
    if folder_id == 'root':
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
    else:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
    
    all_files = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        items = resp.json().get('value', [])
        print(f"Items in folder {folder_id}: {len(items)}")
        
        for item in items:
            if 'file' in item:
                all_files.append({
                    "name": item['name'],
                    "server_relative_url": item['id'], # Graph Item ID
                    "parent_id": folder_id,
                    "webUrl": item.get('webUrl', '') # For citations
                })
            elif 'folder' in item:
                # Recurse into folders
                print(f"Entering folder: {item['name']}")
                sub_files = list_all_files_recursively(site_id, drive_id, item['id'], token)
                all_files.extend(sub_files)
        
        return all_files
    except Exception as e:
        print(f"Error listing items in folder {folder_id}: {e}")
        return []

def list_files_in_document_library(doc_lib_name="Documents"):
    """List all files in the specified library using multi-method discovery."""
    token = get_graph_token()
    if not token:
        return [], None, None
        
    SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
    parsed = urlparse(SHAREPOINT_SITE_URL)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip('/')
    
    # METHOD 1: Hostname:SitePath (Fastest)
    site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    resp = requests.get(site_url, headers={"Authorization": f"Bearer {token}"})
    
    site_id = None
    if resp.status_code == 200:
        site_id = resp.json().get('id')
    
    # METHOD 2: Site Search fallback (If SitePath resolver fails)
    if not site_id:
        print(f"Method 1 (Path) failed for {site_path}. Trying Method 2 (Search)...")
        site_name = site_path.split('/')[-1]
        search_url = f"https://graph.microsoft.com/v1.0/sites?search={site_name}"
        search_resp = requests.get(search_url, headers={"Authorization": f"Bearer {token}"})
        if search_resp.status_code == 200:
            sites = search_resp.json().get('value', [])
            # Find the site that matches our hostname
            target = next((s for s in sites if hostname in s.get('webUrl', '')), None)
            if target:
                site_id = target.get('id')

    if not site_id:
        print(f"Could not resolve site ID for {SHAREPOINT_SITE_URL}")
        return [], None, token

    print(f"Resolved Site ID: {site_id}")
    
    # List available drives
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    resp = requests.get(drives_url, headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code == 200:
        drives = resp.json().get('value', [])
        
        # Try to find the drive by name (case insensitive)
        target_drive = next((d for d in drives if d['name'].lower() == doc_lib_name.lower()), None)
        
        # Fallback 1: First available drive
        if not target_drive and drives:
            print(f"Target '{doc_lib_name}' not found. Fallback to: {drives[0]['name']}")
            target_drive = drives[0]
            
        if not target_drive:
            print("No drives found on site.")
            return [], None, token
            
        drive_id = target_drive['id']
        print(f"Using Drive: {target_drive['name']} ({drive_id})")
        
        files = list_all_files_recursively(site_id, drive_id, 'root', token)
        return files, drive_id, token
    else:
        print(f"Failed to fetch drives: {resp.status_code} - {resp.text}")
        return [], None, token

def download_file_content(file_id, drive_id=None, token=None):
    """
    Download file content using file ID via Microsoft Graph API.
    If drive_id and token are provided, it skips redundant resolution.
    """
    if not token:
        token = get_graph_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # If drive_id is not provided, we have to resolve it (slow but fallback)
        if not drive_id:
            from urllib.parse import urlparse
            parsed = urlparse(SHAREPOINT_SITE_URL)
            site_url = f"https://graph.microsoft.com/v1.0/sites/{parsed.netloc}:{parsed.path.rstrip('/')}"
            site_resp = requests.get(site_url, headers=headers, timeout=10)
            site_id = site_resp.json()['id']
            drive_resp = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive", headers=headers, timeout=10)
            drive_id = drive_resp.json()['id']
        
        download_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{file_id}/content"
        resp = requests.get(download_url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"Error downloading via Graph: {e}")
        return None

from io import BytesIO
import PyPDF2
from docx import Document

def chunk_text(text, chunk_size=2000, overlap=200):
    """
    Split text into overlapping chunks for better RAG performance.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        
    return chunks

def extract_text_from_binary(content, file_name):
    """
    Extract text from binary content using appropriate libraries.
    """
    ext = file_name.split('.')[-1].lower()
    
    try:
        text = ""
        if ext in ['txt', 'md', 'csv']:
            text = content.decode('utf-8', errors='ignore')
        
        elif ext == 'pdf':
            pdf_file = BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
        elif ext == 'docx':
            docx_file = BytesIO(content)
            doc = Document(docx_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            
        else:
            return []
            
        # Return chunks instead of full text
        return chunk_text(text)
    except Exception as e:
        print(f"Error extracting text from {file_name}: {e}")
        return []
