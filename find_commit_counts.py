import os
import requests

github_api_key = os.environ["GITHUB_API_KEY"]
headers = {
    "Authorization": "Bearer " + github_api_key,
    "Accept": "Accept: application/vnd.github.v3+json"
}
base_api_url = "https://api.github.com"

with open("repos-with-commit-counts.csv", "w") as res:
    with open("repos.csv", "r") as f:
        for line in f:
            line = line.strip()
            repo_url, owner_repo, yaml_files = line.split(";")
            url = base_api_url + "/repos/" + owner_repo + "/commits?per_page=1&page=1"
            response = requests.get(url, headers=headers)
            commit_count = response.headers["Link"].split("=")[5].split(">")[0]
            res.write(line + ";" + commit_count + "\n")
