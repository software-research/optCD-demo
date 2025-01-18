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
#source utils.sh
path_to_yaml_file=$(echo "$output_yaml_filename" | rev | cut -d'/' -f1-3 | rev)
path_to_local_repo=$(echo "$output_yaml_filename" | rev | cut -d'/' -f4- | rev)
workflow_file=$(echo "$input_yaml_filename" | rev | cut -d'/' -f1 | rev | cut -d'.' -f1)
#
branch=$(git -C "$path_to_local_repo" rev-parse --abbrev-ref HEAD)

echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Started modifying the original YAML file."

python modify_yaml.py "$input_yaml_filename" "$output_yaml_filename" "$repo"

echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | Finished modifying the original YAML file."
#echo "$path_to_yaml_file"
output_workflow_name=$(echo $output_yaml_filename | rev | cut -d'/' -f1 | rev)
echo $output_filename
echo "utils.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $initial_output_file $input_yaml_filename"
#exit
bash utils.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $initial_output_file $input_yaml_filename
rm -rf $repo"-"$workflow_file
#exit

#Fixer

#csv_path="job-based-results.csv"
#skip_header=1
#postfix="maven_only"
#json_path_base="maven_only_results"
#while IFS=';' read -r owner repo yaml_filename job all_unused maven_unused
#do
#  if [ "$skip_header" -eq 1 ]; then
#    # Skip the first iteration
#    skip_header=0
#    continue
#  fi
#  #echo "Processing job: $job from repository: $repo"
#  #$owner, $repo, 
#  clone_directory="../$repo"
#  repo_url="https://github.com/$owner/$repo"
#  json_filename="$owner_$repo_$yaml_file_in_filename_$job_$postfix.json"
#  numner_of_unused_dirs=$maven_unused
#
#  old_commands=""
#  fix_suggestion_str=""
#  
#  if numner_of_unused_dirs == "0":
#      temp_df_out['fix_suggestion'] = ["No unused directories found"]
#         continue
#
#    full_json_path=$json_path_base/$json_filename"
#
#done <$csv_path

#bash utils.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $initial_output_file $input_yaml_filename
echo "python3 fixer/run_gemini_with_confirmation.py "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $fixed_output_file $input_yaml_filename $output_workflow_name $currentDir" 
python3 fixer/run_gemini_with_confirmation.py "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $fixed_output_file $input_yaml_filename $output_workflow_name $currentDir
#/Users/shantorahman/Documents/Research/optcd/optCD-demo/utils.sh butterfly-lab jsoup .github/workflows/modified-build.yml master build build ../jsoup Output-with-fixer.txt
#python3 fixer/run_gemini_with_confirmation_from_my_another_dir.py
#process_yaml_workflow "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $fixed_output_file $input_yaml_filename
#path_to_yaml_file=".github/workflows/modified-build_1.yml"
#echo "bash x.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $output_file $input_yaml_filename"
#bash x.sh "$owner" "$repo" "$path_to_yaml_file" "$branch" $workflow_file $path_to_local_repo $output_file $input_yaml_filename
#
if [ "$output_file" != "" ]; then
  echo "[INFO] $(date +"%Y-%m-%d %H:%M:%S") | The output is written to $output_file."
fi
