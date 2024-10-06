import os
import time
import requests


github_api_key = os.environ["GITHUB_API_KEY"]
headers = {
    "Authorization": "Bearer " + github_api_key,
    "Accept": "Accept: application/vnd.github.v3+json"
}
base_api_url = "https://api.github.com"

with open("repos-with-commit-counts.csv", "r") as repos:
    i = -1
    for line in repos:
        i += 1
        line = line.strip()
        project_url, owner_repo, yaml_files, commit_count = line.split(";")
        yaml_files = yaml_files.split(",")
        owner, repo = owner_repo.split("/")
        modified_workflow_ids = set()
        for yaml_file in yaml_files:
            f = yaml_file.split(".")[0]
            os.system(f"./run.sh ../{repo}/.github/workflows/{yaml_file} ../{repo}/.github/workflows/opt-{yaml_file} ogul1 {repo} {github_api_key} table_results/{owner}_{repo}_{f}_result.txt &")
            time.sleep(15)
            while True:
                try:
                    with open(f"{repo}-{f}.txt", "r") as run_id_file:
                        modified_workflow_id = int(run_id_file.read().strip())
                        modified_workflow_ids.add(modified_workflow_id)
                        url = base_api_url + "/repos/ogul1/" + repo + "/actions/runs"
                        response = requests.get(url, headers=headers).json()
                        for workflow_run in response["workflow_runs"]:
                            if workflow_run["id"] not in modified_workflow_ids:
                                url = base_api_url + "/repos/ogul1/" + repo + "/actions/runs/" + str(workflow_run["id"]) + "/cancel"
                                requests.post(url, headers=headers)
                    break
                except:
                    print("Run id file not loaded yet.")
                    time.sleep(10)
                    continue
