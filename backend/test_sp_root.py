import os
import requests
from sharepoint_service import get_graph_token

token = get_graph_token()
drive_id = "b!1pkjZ--JYkKXDQ1gOB-vjPwHcbSJJSxCiVkJy3UkKNCSIE3oGKrWTYMQItJIUouB"
headers = {"Authorization": f"Bearer {token}"}
url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"

print(f"Listing ROOT children in drive {drive_id} (TIMEOUT 10s)...")
try:
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        items = resp.json().get('value', [])
        print(f"FOUND {len(items)} ITEMS in ROOT")
    else:
        print(f"FAILURE {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"ERROR: {e}")
