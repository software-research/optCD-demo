import json
import google.generativeai as genai
import os
from jinja2 import Template
import xml.etree.ElementTree as ET
import time
from collections import defaultdict
import sys
import pandas as pd
import os
import subprocess
import shutil
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PlainScalarString

class GeminiAPI:
    def __init__(self):
        api_key = os.environ["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask_prompt(self, prompt):
        response = self.model.generate_content(prompt)
        aio_response = ""

        for part in response.parts:
            aio_response += part.text
        
        aio_response = aio_response.replace("```", "").replace("\n", "")
        return aio_response


def update_mvn_commands_in_yml(new_mvn_command, repo, old_command, path_to_local_repo):
    file_path = f"{path_to_local_repo}/.github/workflows/{output_workflow_name}"
    modified_yml_file_path = f"{path_to_local_repo}/.github/workflows/{output_workflow_name}"

    yaml = YAML()
    yaml.preserve_quotes = True  # Preserve quotes in the original YAML file
    yaml.indent(mapping=2, sequence=4, offset=2)  # Set custom indentation levels

    # Remove any leading or trailing spaces from the new command
    new_mvn_command = new_mvn_command.strip()

    # Read the YAML file
    with open(file_path, 'r') as file:
        yml_data = yaml.load(file)

    # Function to update only the matching old mvn command
    def update_mvn_command_in_steps(steps, old_cmd, new_cmd):
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict) and 'run' in step:
                    # Check if the 'run' command matches the old_command exactly
                    if step['run'].strip() == old_cmd.strip():
                        # Use PlainScalarString to ensure no quotes are added
                        step['run'] = PlainScalarString(new_cmd)

    # Traverse and update the specific 'run' command in the YAML data
    for job in yml_data.get('jobs', {}).values():
        steps = job.get('steps', [])
        update_mvn_command_in_steps(steps, old_command, new_mvn_command)

    # Write the updated content back to the YAML file with controlled formatting
    with open(modified_yml_file_path, 'w') as file:
        yaml.dump(yml_data, file)

    print(f"The command '{old_command}' has been updated to: {new_mvn_command}")


def filter_duplicate_instance_in_json(data):
    unique_instances = defaultdict(list)
    for instance in data:
        command = instance["Responsible command"]
        unused_dir = instance["Unused directory"]
        responsible_plugin = instance["Responsible plugin"]
        key = f"{command} {unused_dir} {responsible_plugin}"
        unique_instances[key].append(instance)
    unique_data = []
    for key, instances in unique_instances.items():
        unique_data.append(instances[0])
    return unique_data


owner = sys.argv[1]
repo = sys.argv[2]
path_to_yaml_file=sys.argv[3]
branch = sys.argv[4]
workflow_file=sys.argv[5]
path_to_local_repo = sys.argv[6]
output_file = sys.argv[7]
input_yaml_filename = sys.argv[8]
output_workflow_name = sys.argv[9]
currentDir = sys.argv[10]

gemini = GeminiAPI()

old_commands = ""
fix_suggestion_str = ""
full_json_path = f"{currentDir}/responsible_plugins.json"

if not os.path.exists(full_json_path):
    print(f"File {full_json_path} does not exist")
    sys.exit(1)

# read the json file
with open(full_json_path) as json_file:
    data = json.load(json_file)

# Filter out duplicate instances
data = filter_duplicate_instance_in_json(data)
command_set = set()

for instance in data:
    print("instance=", instance)
    # Loop through each detection result in the JSON
    unused_dir = instance["Unused directory"]
    responsible_command = instance["Responsible command"]
    responsible_plugin = instance["Responsible plugin"]
    step_name = instance["Name of the step"]
        
    prompts = []
    results = {}
    
    # Generate prompt
    prompt = (
        f"The command `{responsible_command}` creates the following unused directory:\n"
        f"{unused_dir}\n"
        f"Please suggest an updated command to avoid unnecessary directory. Provide only the new command.\n"
    )
    print("prompt=",prompt)
    # Call the Gemini API to get the fix suggestion
    fix_suggestion = gemini.ask_prompt(prompt)
    print("fix_suggestion=",fix_suggestion )
    results[responsible_command] = {
        "fix_suggestion": fix_suggestion
    }
    
    time.sleep(6)
    # create a string of fix, concat all the fixes with a newline. Basically I wanted to put all the fixes in one string
    fix_suggestion_str = ""
    for key in results:
        fix_suggestion_str += results[key]['fix_suggestion'] + "\n"
        
    # old_commands = [key for key in results] \n separated, remive the last newline character
    if old_commands == "":
        old_commands = "\n".join([key for key in results])
    
    # remove the lat newline character
    fix_suggestion_str = fix_suggestion_str[:-1]
    
    print("=====================================")
    print(f"Owner: {owner}")
    print(f"Repo: {repo}")
    print(f"Old commands: {old_commands}")
    print(f"Fix suggestion: {fix_suggestion_str}")
    print("=====================================")
    print("\n\n")
    if fix_suggestion_str == "" or fix_suggestion_str == old_commands:
        print('There is no fix suggestions found')
    else:
        update_mvn_commands_in_yml(fix_suggestion_str, repo, old_commands, path_to_local_repo)
        print('End of update in mvn command=======')
        script_path = f"{currentDir}/utils.sh"
        print(script_path, owner, repo, path_to_yaml_file, branch, workflow_file, 
        path_to_local_repo, output_file+unused_dir, input_yaml_filename)

        unused_dir_only = os.path.basename(unused_dir.strip('/'))  # Strip trailing slash if present

        # Call the Bash script with the variables as arguments
        subprocess.run([script_path, owner, repo, path_to_yaml_file, branch,
                     workflow_file, path_to_local_repo, output_file+unused_dir_only+".txt", input_yaml_filename, "False"]
                    )

        old_commands = fix_suggestion_str

    directory_path = f"{repo}-{workflow_file}"
    shutil.rmtree(directory_path)
