import requests
import base64

ORG = "parthjade21"
PROJECT = "ProjectTest"
PAT = ""

auth = base64.b64encode(f":{PAT}".encode()).decode()

wiql_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/wit/wiql?api-version=7.0"

query = {
    "query": """
    SELECT [System.Id], [System.Title], [System.WorkItemType]
    FROM WorkItems
    ORDER BY [System.ChangedDate] DESC
    """
}

headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/json"
}

res = requests.post(wiql_url, headers=headers, json=query)

print("Status:", res.status_code)
print(res.json())
