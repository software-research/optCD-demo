#!/bin/bash

if [ "$#" -le 3 ]; then
  echo "Usage: run.sh <input_yaml_filename> <output_yaml_filename> <owner> <repo> [output_file]"
  exit 1
fi

python3 -m venv venv > /dev/null 2>&1
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

currentDir=$(pwd)
input_yaml_filename=$1
output_yaml_filename=$2
owner=$3
repo=$4
initial_output_file=$5
fixed_output_file="temp_out.txt"

rm $initial_output_file > /dev/null 2>&1
rm $fixed_output_file > /dev/null 2>&1

path_to_yaml_file=$(echo "$output_yaml_filename" | rev | cut -d'/' -f1-3 | rev)
path_to_local_repo=$(echo "$output_yaml_filename" | rev | cut -d'/' -f4- | rev)
workflow_file=$(echo "$input_yaml_filename" | rev | cut -d'/' -f1 | rev | cut -d'.' -f1)
branch=$(git -C "$path_to_local_repo" rev-parse --abbrev-ref HEAD)

python modify_yaml.py "$input_yaml_filename" "$output_yaml_filename" "$repo"

echo "Finished modifying the original YAML file to find unused directories."
output_workflow_name=$(echo $output_yaml_filename | rev | cut -d'/' -f1 | rev)
bash utils.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" "$workflow_file" "$path_to_local_repo" "$initial_output_file" "$input_yaml_filename"
echo "Finding and testing fixes for unused directories."
python3 fixer/run_gemini_with_confirmation.py "$owner" "$repo" "$path_to_yaml_file" "$branch" "$workflow_file" "$path_to_local_repo" "$fixed_output_file" "$input_yaml_filename" "$output_workflow_name" "$currentDir" "$initial_output_file"

if [ "$initial_output_file" != "" ]; then
  # copy the content of the $fixed_output_file to $initial_output_file , just append at the end of the $initial_output_file
  echo "The output is written to $initial_output_file."
fi
