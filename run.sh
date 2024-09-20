#!/bin/bash

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

yaml_filename=$1
output_filename=$2
owner=$3
repo=$4
github_api_token=$5

python modify_yaml.py "$yaml_filename" "$output_filename" "$repo"

echo "Modified the original yaml file."

path_to_yaml_file=$(echo "$output_filename" | rev | cut -d'/' -f1-3 | rev)
path_to_local_repo=$(echo "$output_filename" | rev | cut -d'/' -f4- | rev)

run_id=$(gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId')

# push and run the modified yaml
git -C "$path_to_local_repo" add "$path_to_yaml_file"
git -C "$path_to_local_repo" commit -m "add modified yaml file"
git -C "$path_to_local_repo" push

while true; do
  echo "Waiting until modified yaml workflow starts."
  temp_run_id=$(gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId')
  if [ "$run_id" != "$temp_run_id" ]; then
    echo "Modified yaml workflow started."
    run_id=$temp_run_id
    break
  fi
  sleep 5
done

# wait until modified yaml workflow finishes
while true; do
  echo "Waiting until modified yaml workflow completes."
  run_status=$(gh run view "$run_id" --repo "$owner"/"$repo" --json status -q '.status')
  echo "gh run view $run_id --repo $owner/$repo --json status -q '.status'"
  echo "Run status of $run_id is: $run_status"
  if [ "$run_status" = "completed" ]; then
    echo "Modified yaml workflow completed."
    break
  fi
  sleep 10
done

# download inotifywait log to inotifywait-${{ job_name }}/inotifywait-log-${{ job_name }}.txt
gh run download "$run_id" --repo "$owner"/"$repo"

# get job ids inside of modified yaml workflow run
job_ids=$(gh run view "$run_id" --repo "$owner"/"$repo" --json jobs --jq '.jobs.[] | (.databaseId | tostring) + " " + .name')

while IFS=' ' read -r job_id name; do
  # get workflow run logs to workflow-run-log.txt
  curl -s -H "Accept: application/vnd.github+json" \
       -H "Authorization: Bearer $github_api_token" \
       -H "X-GitHub-Api-Version: 2022-11-28" \
       -L "https://api.github.com/repos/$owner/$repo/actions/jobs/$job_id/logs" \
       -o workflow-run-log.txt

  echo "Unused directories and their responsible plugins in $name:"
  python find_plugins.py inotifywait-"$name"/inotifywait-log-"$name".csv workflow-run-log.txt
  echo "-------------------------------------------------"

done <<< "$job_ids"
