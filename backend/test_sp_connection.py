import os
import requests
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

load_dotenv()

def get_graph_token():
    authority = f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}"
    app = ConfidentialClientApplication(
        os.getenv('SHAREPOINT_CLIENT_ID'), 
        authority=authority, 
        client_credential=os.getenv('SHAREPOINT_CLIENT_SECRET')
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result.get('access_token')

def download_and_save(site_url, sync_dir):
    token = get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    from urllib.parse import urlparse
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip('/')
    
    # Get Site ID
    site_api_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    resp = requests.get(site_api_url, headers=headers)
    site_id = resp.json()['id']
    
    # Get Drive ID
    drives_resp = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives", headers=headers)
    drive_id = drives_resp.json().get('value', [])[0]['id'] # Default first drive
    
    if not os.path.exists(sync_dir):
        os.makedirs(sync_dir)
        
    def download_folder(folder_id, folder_path):
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
        resp = requests.get(url, headers=headers)
        items = resp.json().get('value', [])
        
        for item in items:
            item_path = os.path.join(folder_path, item['name'])
            if 'file' in item:
                print(f"Downloading: {item['name']}")
                content_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item['id']}/content"
                r = requests.get(content_url, headers=headers)
                with open(item_path, "wb") as f:
                    f.write(r.content)
            elif 'folder' in item:
                if not os.path.exists(item_path):
                    os.makedirs(item_path)
                download_folder(item['id'], item_path)

    print(f"Starting SYNC for {site_url}...")
    download_folder('root', sync_dir)
    print("SYNC COMPLETE!")

download_and_save(os.getenv('SHAREPOINT_SITE_URL'), os.path.join(os.getcwd(), 'synced_documents'))
