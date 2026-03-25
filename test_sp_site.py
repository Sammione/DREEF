import os
import requests
from sharepoint_service import get_graph_token
from urllib.parse import urlparse

token = get_graph_token()
site_url = os.getenv("SHAREPOINT_SITE_URL")
parsed = urlparse(site_url)
hostname = parsed.netloc
site_path = parsed.path.rstrip('/')

target = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
print(f"Resolving: {target}")
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(target, headers=headers)
if resp.status_code == 200:
    print(f"SUCCESS SITE_ID: {resp.json().get('id')}")
else:
    print(f"FAILURE {resp.status_code}: {resp.text}")
