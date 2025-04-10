#!/bin/bash
owner="$1"
repo="$2"
path_to_yaml_file="$3"
branch="$4"
workflow_file="$5"
path_to_local_repo="$6"
output_file="$7"
input_yaml_filename="$8"

cancel_runs () {
  owner=$1
  repo=$2
  run_id_to_keep=$3
  slug="$owner"/"$repo"

  queued_run_ids=$(gh run list --repo "$slug" --status queued --json databaseId --jq '.[].databaseId')
  in_progress_run_ids=$(gh run list --repo "$slug" --status in_progress --json databaseId --jq '.[].databaseId')

  for queued_run_id in $queued_run_ids; do
    if [ "$queued_run_id" != "$run_id_to_keep" ]; then
      gh run cancel "$queued_run_id" --repo "$slug" > /dev/null 2>&1
    fi
  done

  for in_progress_run_id in $in_progress_run_ids; do
    if [ "$in_progress_run_id" != "$run_id_to_keep" ]; then
      gh run cancel "$in_progress_run_id" --repo "$slug" > /dev/null 2>&1
    fi
  done
}

rm -rf $repo"-"$workflow_file

git -C "$path_to_local_repo" fetch > /dev/null 2>&1
git -C "$path_to_local_repo" rebase origin/"$branch" > /dev/null 2>&1
git -C "$path_to_local_repo" push origin "$branch" > /dev/null 2>&1
git -C "$path_to_local_repo" add "$path_to_yaml_file" > /dev/null 2>&1
git -C "$path_to_local_repo" commit -m "add modified YAML file" > /dev/null 2>&1
git -C "$path_to_local_repo" push --set-upstream origin "$branch" > /dev/null 2>&1

echo "Pushed the modified YAML file to remote repository."
run_id=$(gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId')

echo "Waiting until modified YAML workflow starts."
while true; do
  temp_run_id=$(gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId')
  if [ "$run_id" != "$temp_run_id" ]; then
    echo "Modified YAML workflow started with run_id: $temp_run_id"
    run_id=$temp_run_id
    break
  fi
  sleep 10
done

cancel_runs "$owner" "$repo" "$run_id"

echo "$run_id" > "$repo"-"$workflow_file".txt
echo "Waiting until modified YAML workflow is completed."
while true; do
  run_status=$(gh run view "$run_id" --repo "$owner"/"$repo" --json status -q '.status')
  if [ "$run_status" = "completed" ]; then
    echo "Modified YAML workflow completed."
    break
  fi
  if [ "$last_run_status" != "$run_status" ]; then
    echo "Run status of modified workflow (run_id: $run_id) is: $run_status"
  fi
  last_run_status=$run_status
  sleep 10
done

# get job ids inside of modified yaml workflow run
job_ids=$(gh run view "$run_id" --repo "$owner"/"$repo" --json jobs --jq '.jobs.[] | (.databaseId | tostring) + " " + .name')

while IFS=' ' read -r job_id name; do
  rm -rf "$repo"/inotifywait-"$name"
done <<< "$job_ids"

# rm -rf "$output_file"

echo "[]" > "responsible_plugins.json"

mkdir -p "$repo"-"$workflow_file"
mkdir -p "$repo"
gh run download "$run_id" --repo "$owner"/"$repo" -D "$repo"-"$workflow_file"

echo "Finding unused directories and their responsible plugins."

while IFS=' ' read -r job_id name; do
  curl -s -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $GITHUB_API_TOKEN" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        -L "https://api.github.com/repos/$owner/$repo/actions/jobs/$job_id/logs" \
        -o "$repo"/workflow-run-log-"$name"-"$workflow_file".txt

  # echo name of job into the output_file
  # echo "Result for job $name" >> "$output_file" if name does not has windows or mac in it, then write it
  if [[ "$name" == *"windows"* || "$name" == *"mac"* ]]; then
    echo "Skipped incompatible job $name" >> "$output_file"
  else
    echo "Result for job $name" >> "$output_file"
  fi

  python find_plugins.py "$repo"-"$workflow_file"/inotifywait-"$name"/inotifywait-log-"$name".csv "$repo"/workflow-run-log-"$name"-"$workflow_file".txt "$output_file" "$input_yaml_filename" "$name"

  ret_val=$?
  if [ $ret_val -eq 1 ]; then
    continue
  fi
done <<< "$job_ids"
