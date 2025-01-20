#!/bin/bash

if [ "$#" -le 3 ]; then
  echo "Usage: run.sh <input_yaml_filename> <output_yaml_filename> <owner> <repo> [output_file]"
  exit 1
fi

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

currentDir=$(pwd)
input_yaml_filename=$1
output_yaml_filename=$2
owner=$3
repo=$4
initial_output_file=$5
fixed_output_file=$6

path_to_yaml_file=$(echo "$output_yaml_filename" | rev | cut -d'/' -f1-3 | rev)
path_to_local_repo=$(echo "$output_yaml_filename" | rev | cut -d'/' -f4- | rev)
workflow_file=$(echo "$input_yaml_filename" | rev | cut -d'/' -f1 | rev | cut -d'.' -f1)
branch=$(git -C "$path_to_local_repo" rev-parse --abbrev-ref HEAD)

echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Started modifying the original YAML file."

python modify_yaml.py "$input_yaml_filename" "$output_yaml_filename" "$repo"

echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Finished modifying the original YAML file."
output_workflow_name=$(echo $output_yaml_filename | rev | cut -d'/' -f1 | rev)
echo $output_filename
echo "utils.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $initial_output_file $input_yaml_filename"
bash utils.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $initial_output_file $input_yaml_filename
rm -rf $repo"-"$workflow_file

echo "python3 fixer/run_gemini_with_confirmation.py "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $fixed_output_file $input_yaml_filename $output_workflow_name $currentDir" 
python3 fixer/run_gemini_with_confirmation.py "$owner" "$repo" "$path_to_yaml_file" "$branch" "$workflow_file" "$path_to_local_repo" "$fixed_output_file" "$input_yaml_filename" "$output_workflow_name" "$currentDir"

if [ "$output_file" != "" ]; then
  echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | The output is written to $output_file."
fi
