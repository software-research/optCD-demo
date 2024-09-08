import requests
from dateutil import parser
from collections import defaultdict
from bisect import bisect_right
import os

"""
owner = os.environ['GITHUB_REPOSITORY'].split(os.sep)[0]
repo = os.environ['GITHUB_REPOSITORY'].split(os.sep)[1]
token = os.environ['GITHUB_TOKEN']
base_api_url = "https://api.github.com"
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28"
}


def get_raw_logs(workflow_run_id: int) -> list[str]:
    url = f"{base_api_url}/repos/{owner}/{repo}/actions/runs/{workflow_run_id}/jobs"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.text)
    raw_logs = []
    response = response.json()["jobs"]
    for job in response:
        job_id = job["id"]
        url = f"{base_api_url}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(resp.text)
        raw_logs.append(resp.text)

    return raw_logs
"""

def get_responsible_plugins(log: str, unused_dirs: list[str], timestamps: defaultdict[str, str]) -> list[tuple[str, str]]:
    plugin_timestamps = []
    plugin_names = []
    responsible_plugins = []
    for line in log.splitlines():
        tokens = line.split(" ")
        if len(tokens) != 8 or tokens[1] != "[INFO]" or tokens[2] != "---":
            continue
        timestamp = parser.isoparse(tokens[0])
        name = ' '.join(tokens[3:7])
        plugin_timestamps.append(timestamp)
        plugin_names.append(name)

    for unused_dir in unused_dirs:
        if unused_dir not in timestamps:
            responsible_plugins.append((unused_dir, "Not responsible by any plugin"))
            continue
        timestamp = parser.isoparse(timestamps[unused_dir])
        i = bisect_right(plugin_timestamps, timestamp)
        if i == 0:
            responsible_plugins.append((unused_dir, "Not responsible by any plugin"))
        else:
            responsible_plugins.append((unused_dir, plugin_names[i - 1]))

    return responsible_plugins
