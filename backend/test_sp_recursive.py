import os
import requests
from sharepoint_service import get_graph_token, list_all_files_recursively

token = get_graph_token()
site_id = "dreef.sharepoint.com,672399d6-89ef-4262-970d-0d60381faf8c,b47107fc-2589-422c-8959-09cb752428d0"
drive_id = "b!1pkjZ--JYkKXDQ1gOB-vjPwHcbSJJSxCiVkJy3UkKNCSIE3oGKrWTYMQItJIUouB"

print(f"Listing files recursively from ROOT in drive {drive_id}...")
files = list_all_files_recursively(site_id, drive_id, 'root', token)
print(f"TOTAL FILES FOUND: {len(files)}")
for f in files[:10]:
    print(f"FILE: {f['name']}")
