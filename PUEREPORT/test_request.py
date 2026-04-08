
import requests

url = "http://localhost:8000/generate_report"
files = {'file': open('sheet 1.xlsx', 'rb')}

try:
    response = requests.post(url, files=files)
    if response.status_code == 200:
        with open('test_result.docx', 'wb') as f:
            f.write(response.content)
        print("Success: test_result.docx created")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")
