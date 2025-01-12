#!/bin/bash

echo "From utils.sh ************, $(pwd)"

    owner="$1"
    repo="$2"
    path_to_yaml_file="$3"
    branch="$4"
    workflow_file="$5"
    path_to_local_repo="$6"
    output_file="$7"
    input_yaml_filename="$8"

    git -C "$path_to_local_repo" fetch
    git -C "$path_to_local_repo" rebase origin/"$branch"
    git -C "$path_to_local_repo" push origin "$branch"
    git -C "$path_to_local_repo" add "$path_to_yaml_file"
    git -C "$path_to_local_repo" commit -m "add modified YAML file"
    git -C "$path_to_local_repo" push --set-upstream origin "$branch"
    
    echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Pushed the modified YAML file to remote repository."
    gh workflow list --repo "$owner"/"$repo"
    run_id=$(gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId')
    echo "[INFO] got the run id for the original YAML workflow: $run_id"
    
    while true; do
      echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Waiting until modified YAML workflow starts."
      echo "gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId'"
      temp_run_id=$(gh run list --repo "$owner"/"$repo" --workflow "$path_to_yaml_file" --limit 1 --json databaseId --jq '.[0].databaseId')
      echo "run_id =$run_id", "temp_run_id= $temp_run_id" 
      if [ "$run_id" != "$temp_run_id" ]; then
        echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Modified YAML workflow started."
        run_id=$temp_run_id
        break
      fi
      sleep 10
    done
    
    rm $repo"-"$workflow_file".txt"
    echo "$run_id" > "$repo"-"$workflow_file".txt
    
    echo "**** run_id is saved $repo"-"$workflow_file.txt "
    # wait until modified yaml workflow finishes
    while true; do
      run_status=$(gh run view "$run_id" --repo "$owner"/"$repo" --json status -q '.status')
      if [ "$run_status" = "completed" ]; then
        echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Modified YAML workflow completed."
        break
      fi
      echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Waiting until modified YAML workflow is completed."
      echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Run status of current workflow (run_id: $run_id) is: $run_status"
      sleep 50
    done
    
    # get job ids inside of modified yaml workflow run
    job_ids=$(gh run view "$run_id" --repo "$owner"/"$repo" --json jobs --jq '.jobs.[] | (.databaseId | tostring) + " " + .name')
    
    while IFS=' ' read -r job_id name; do
      rm -rf "$repo"/inotifywait-"$name"
    done <<< "$job_ids"
    
    rm -rf "$output_file"
    
    mkdir -p "$repo"-"$workflow_file"
    mkdir -p "$repo"
    # download inotifywait log to "$repo"/inotifywait-${{ job_name }}/inotifywait-log-${{ job_name }}.csv
    echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Downloaded the inotifywait log artifacts."
    gh run download "$run_id" --repo "$owner"/"$repo" -D "$repo"-"$workflow_file"
    
    echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Finding unused directories and their responsible plugins."
    
    while IFS=' ' read -r job_id name; do
      # fetch workflow run logs to "$repo"/workflow-run-log.txt
      echo "downloading logs: using command"
      echo "curl -s -H \"Accept: application/vnd.github+json\" -H \"Authorization: Bearer $GITHUB_API_TOKEN\" -H \"X-GitHub-Api-Version: 2022-11-28\" -L \"https://api.github.com/repos/$owner/$repo/actions/jobs/$job_id/logs\" -o \"$repo\"/workflow-run-log-\"$name\"-\"$workflow_file\".txt"
    
      echo $job_id
      curl -s -H "Accept: application/vnd.github+json" \
           -H "Authorization: Bearer $GITHUB_API_TOKEN" \
           -H "X-GitHub-Api-Version: 2022-11-28" \
           -L "https://api.github.com/repos/$owner/$repo/actions/jobs/$job_id/logs" \
           -o "$repo"/workflow-run-log-"$name"-"$workflow_file".txt
    
      echo "[INFO] downloading the inotifywait log for $name into $repo/inotifywait-$name/inotifywait-log-$name.csv"
    
    
      if [ "$output_file" != "" ]; then
        echo "Unused directories and their responsible plugins in $name:" >> "$output_file"
      else
        echo "Unused directories and their responsible plugins in $name:"
      fi
      echo "path to inotifywait log is: $repo"-"$workflow_file"/inotifywait-"$name"/inotifywait-log-"$name".csv"
      echo "path to workflow run log is: $repo"/workflow-run-log-"$name"-"$workflow_file".txt"
    
      python find_plugins.py "$repo"-"$workflow_file"/inotifywait-"$name"/inotifywait-log-"$name".csv "$repo"/workflow-run-log-"$name"-"$workflow_file".txt "$output_file" "$input_yaml_filename" "$name"
    
      ret_val=$?
      if [ $ret_val -eq 1 ]; then
        continue
      fi
    done <<< "$job_ids"
#}
