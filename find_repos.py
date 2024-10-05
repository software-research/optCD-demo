import os
import base64
import requests

github_api_key = os.environ["GITHUB_API_KEY"]
headers = {
    "Authorization": "Bearer " + github_api_key,
    "Accept": "Accept: application/vnd.github.v3+json"
}
base_api_url = "https://api.github.com"

# https://api.github.com/search/repositories?q=language:java&sort=stars&order=desc&page={1..34}

not_having_pom_xml_count = 0
not_having_github_actions_count = 0
no_mvn_commands_in_all_workflows = 0
has_secrets_in_all_workflows = 0
both_has_secrets_and_no_mvn_commands = 0
count = 0
i = 1

with open("repos.csv", "a") as f:
    while count < 300:
        # get 30 projects at a time
        url = base_api_url + "/search/repositories?q=language:java&sort=stars&order=desc&page=" + str(i)
        response = requests.get(url=url, headers=headers).json()
        try:
            for repository in response["items"]:
                # check if the project has a pom.xml file
                url = base_api_url + "/repos/" + repository["full_name"] + "/contents/pom.xml"
                response = requests.get(url=url, headers=headers)
                print(response, count, repository["html_url"], i)
                if response.status_code != 200:
                    not_having_pom_xml_count += 1
                    continue
                # check if the project uses github actions
                url = base_api_url + "/repos/" + repository["full_name"] + "/contents/.github/workflows"
                response = requests.get(url=url, headers=headers)
                if response.status_code != 200:
                    not_having_github_actions_count += 1
                    continue
                response = response.json()
                workflow_files = []
                uses_secrets = False
                does_not_have_mvn_commands = False
                for workflow_file in response:
                    # skip folders and other non yml files
                    if not workflow_file["name"].endswith(".yml") and not workflow_file["name"].endswith(".yaml"):
                        continue
                    # check if the workflow is passing
                    url = base_api_url + "/repos/" + repository["full_name"] + "/actions/workflows/" + workflow_file["name"] + "/runs"
                    print("Workflow file name:", workflow_file["name"])
                    response = requests.get(url=url, headers=headers).json()
                    k = 0
                    failing = False
                    success = False
                    while k < len(response["workflow_runs"]):
                        # skip in progress or cancelled ones
                        if response["workflow_runs"][k]["status"] != "completed" or response["workflow_runs"][k]["conclusion"] == "cancelled":
                            k += 1
                            continue
                        if response["workflow_runs"][k]["conclusion"] == "failure":
                            failing = True
                        if response["workflow_runs"][k]["conclusion"] == "success":
                            success = True
                        break
                    if failing:
                        print(workflow_file["name"], "status: failing")
                        continue
                    if not success:
                        print(workflow_file["name"], "status: not success (never run?)")
                        continue
                    # check if the workflow file has mvn in it and doesn't have secrets in it
                    url = base_api_url + "/repos/" + repository["full_name"] + "/contents/" + workflow_file["path"]
                    response = requests.get(url=url, headers=headers).json()
                    workflow_file_content = base64.b64decode(response["content"]).decode("utf-8")
                    if "mvn" not in workflow_file_content:
                        does_not_have_mvn_commands = True
                        continue
                    if "secrets." in workflow_file_content:
                        uses_secrets = True
                        continue
                    workflow_files.append(workflow_file["name"])
                if len(workflow_files) > 0:
                    f.write(repository["html_url"] + ";" + repository["full_name"] + ";" + ','.join(workflow_files) + "\n")
                    count += 1
                    continue
                if does_not_have_mvn_commands and uses_secrets:
                    both_has_secrets_and_no_mvn_commands += 1
                    continue
                if does_not_have_mvn_commands:
                    no_mvn_commands_in_all_workflows += 1
                    continue
                if uses_secrets:
                    has_secrets_in_all_workflows += 1
            i += 1
        except:
            break

print("Projects that does not have pom.xml:", not_having_pom_xml_count)
print("Projects that does not use github actions:", not_having_github_actions_count)
print("Projects that has no mvn commands in all workflows:", no_mvn_commands_in_all_workflows)
print("Projects with secrets in all workflows:", has_secrets_in_all_workflows)
print("Projects with both secrets and no mvn commands in all workflows:", both_has_secrets_and_no_mvn_commands)
print("Found repos:", count)

"""
Total projects inspected: 1020
Projects that does not have pom.xml: 661
Projects that does not use github actions: 145
Projects that has no mvn commands in all workflows: 27
Projects with secrets in all workflows: 19
Projects with both secrets and no mvn commands in all workflows: 31
Projects with all workflows failing or never run: 27
Found repos: 110
"""
