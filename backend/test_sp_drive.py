import os
import requests
from sharepoint_service import get_graph_token
from urllib.parse import urlparse

token = get_graph_token()
site_id = "dreef.sharepoint.com,672399d6-89ef-4262-970d-0d60381faf8c,b47107fc-2589-422c-8959-09cb752428d0"
headers = {"Authorization": f"Bearer {token}"}

target = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
print(f"Listing Drives: {target}")
resp = requests.get(target, headers=headers)
if resp.status_code == 200:
    drives = resp.json().get('value', [])
    print(f"FOUND {len(drives)} DRIVES")
    for d in drives:
        print(f"DRIVE NAME: {d['name']} | ID: {d['id']}")
else:
    print(f"FAILURE {resp.status_code}: {resp.text}")
