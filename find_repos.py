import os
import base64
import requests

github_api_key = os.environ["GITHUB_API_KEY"]
headers = {
    "Authorization": "Bearer " + github_api_key,
    "Accept": "Accept: application/vnd.github.v3+json"
}
base_api_url = "https://api.github.com"


with open("repos.csv", "a") as f:
    count = 0
    i = 1
    while count < 300:
        url = base_api_url + "/search/repositories?q=language:java&sort=stars&order=desc&page=" + str(i)
        response = requests.get(url=url, headers=headers).json()
        for repository in response["items"]:
            url = base_api_url + "/repos/" + repository["full_name"] + "/contents/pom.xml"
            response = requests.get(url=url, headers=headers)
            print(response, count, repository["html_url"], i)
            if response.status_code != 200:
                continue

            url = base_api_url + "/repos/" + repository["full_name"] + "/contents/.github/workflows"
            response = requests.get(url=url, headers=headers)
            if response.status_code != 200:
                continue
            response = response.json()
            workflow_files = []
            for workflow_file in response:
                if not workflow_file["name"].endswith(".yml") and not workflow_file["name"].endswith(".yaml"):
                    continue
                url = base_api_url + "/repos/" + repository["full_name"] + "/contents/" + workflow_file["path"]
                response = requests.get(url=url, headers=headers).json()
                workflow_file_content = base64.b64decode(response["content"]).decode("utf-8")
                if "mvn" in workflow_file_content and "secrets." not in workflow_file_content:
                    workflow_files.append(workflow_file["name"])
            if len(workflow_files) > 0:
                f.write(repository["html_url"] + ";" + repository["full_name"] + ";" + ','.join(workflow_files) + "\n")
                count += 1
        i += 1
