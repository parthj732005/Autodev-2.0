import base64
import requests


class AzureDevOpsClient:
    def __init__(self, org: str, project: str, pat: str):
        self.org = org
        self.project = project
        self.base_url = f"https://dev.azure.com/{org}"
        self.headers = self._auth_headers(pat)

    def _auth_headers(self, pat: str):
        token = base64.b64encode(f":{pat}".encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }

    def get_work_items(self):
        wiql_url = (
            f"{self.base_url}/{self.project}/_apis/wit/wiql"
            f"?api-version=7.0"
        )

        wiql = {
            "query": f"""
                SELECT [System.Id], [System.Title], [System.WorkItemType]
                FROM WorkItems
                WHERE [System.TeamProject] = '{self.project}'
                ORDER BY [System.ChangedDate] DESC
            """
        }

        r = requests.post(wiql_url, headers=self.headers, json=wiql)
        r.raise_for_status()

        ids = [item["id"] for item in r.json().get("workItems", [])]
        if not ids:
            return []

        ids_str = ",".join(map(str, ids))
        details_url = (
            f"{self.base_url}/_apis/wit/workitems"
            f"?ids={ids_str}&api-version=7.0"
        )

        r2 = requests.get(details_url, headers=self.headers)
        r2.raise_for_status()
        return r2.json()["value"]
