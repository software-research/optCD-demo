#!/bin/bash

if [ "$#" -le 1 ]; then
  echo "Usage: run.sh <input_yaml_filename> <output_yaml_filename>"
  exit 1
fi

python3 -m venv venv > /dev/null 2>&1
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

currentDir=$(pwd)
input_yaml_filename=$1
output_yaml_filename=$2

# go to the input_yaml_filename directory, and find out owner and repo for pushing the modified YAML file
project_dir=$(dirname "$input_yaml_filename")
cd "$project_dir"
if [ $? -ne 0 ]; then
  echo "Error: Unable to change directory to $project_dir"
  exit 1
fi
url=$(git config --get remote.origin.url)

if [[ $url =~ github.com[:/](.*)/(.*)(\.git)?$ ]]; then
  owner="${BASH_REMATCH[1]}"
  repo="${BASH_REMATCH[2]}" # repo name contains the .git extension
  # remove the .git extension if exists
  if [[ $repo == *.git ]]; then
    repo="${repo%.git}"
  fi
else
  echo "Could not parse owner and repo from URL: $url"
  exit 1
fi

cd "$currentDir"
if [ $? -ne 0 ]; then
  echo "Error: Unable to change directory back to $currentDir"
  exit 1
fi

# if $3 and $4 are not empty, then use them as owner and repo
# if [ -n "$3" ] && [ -n "$4" ]; then
#   owner=$3
#   repo=$4
# fi

# owner=$3
# repo=$4
initial_output_file="out.txt"
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
