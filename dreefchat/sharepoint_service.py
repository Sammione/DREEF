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
def list_all_files_recursively(site_id, drive_id, folder_id, token, logger=None):
    """Recursively list all files and folders in a drive."""
    all_files = []
    
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
    if folder_id == 'root':
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        
    msg = f"Scanning folder: {folder_id}"
    if logger: logger(msg)
    else: print(msg)
    
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if resp.status_code != 200:
        msg = f"Failed to list folder {folder_id}: {resp.status_code}"
        if logger: logger(msg)
        else: print(msg)
        return []
        
    items = resp.json().get('value', [])
    for item in items:
        if 'file' in item:
            all_files.append({
                "name": item['name'],
                "server_relative_url": item['id'],
                "webUrl": item.get('webUrl', "")
            })
        elif 'folder' in item:
            msg = f"Entering folder: {item['name']}"
            if logger: logger(msg)
            else: print(msg)
            sub_files = list_all_files_recursively(site_id, drive_id, item['id'], token, logger=logger)
            all_files.extend(sub_files)
            
    return all_files

def list_files_in_document_library(doc_lib_name="Documents", logger=None):
    """List all files in the specified library using multi-method discovery."""
    token = get_graph_token()
    if not token:
        if logger: logger("Failed to obtain Graph token.")
        return [], None, None
        
    SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
    parsed = urlparse(SHAREPOINT_SITE_URL)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip('/')
    
    # METHOD 1: Hostname:SitePath
    site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    resp = requests.get(site_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    
    site_id = None
    if resp.status_code == 200:
        site_id = resp.json().get('id')
    
    # METHOD 2: Site Search fallback
    if not site_id:
        msg = f"URL resolve failed ({resp.status_code}). Trying site search for name..."
        if logger: logger(msg)
        else: print(msg)
        site_name = site_path.split('/')[-1]
        search_url = f"https://graph.microsoft.com/v1.0/sites?search={site_name}"
        search_resp = requests.get(search_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if search_resp.status_code == 200:
            sites = search_resp.json().get('value', [])
            target = next((s for s in sites if hostname in s.get('webUrl', '')), None)
            if target:
                site_id = target.get('id')

    if not site_id:
        msg = f"Critical Error: Could not resolve site ID for {SHAREPOINT_SITE_URL}"
        if logger: logger(msg)
        else: print(msg)
        return [], None, token

    msg = f"Resolved Site ID: {site_id}"
    if logger: logger(msg)
    else: print(msg)
    
    # List available drives
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    resp = requests.get(drives_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    
    if resp.status_code == 200:
        drives = resp.json().get('value', [])
        target_drive = next((d for d in drives if d['name'].lower() == doc_lib_name.lower()), None)
        
        if not target_drive and drives:
            msg = f"Drive '{doc_lib_name}' not found. Fallback to: {drives[0]['name']}"
            if logger: logger(msg)
            else: print(msg)
            target_drive = drives[0]
            
        if not target_drive:
            if logger: logger("No drives found.")
            return [], None, token
            
        drive_id = target_drive['id']
        msg = f"Using Drive: {target_drive['name']}"
        if logger: logger(msg)
        else: print(msg)
        
        files = list_all_files_recursively(site_id, drive_id, 'root', token, logger=logger)
        return files, drive_id, token
    else:
        if logger: logger(f"Failed to fetch drives: {resp.status_code}")
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
