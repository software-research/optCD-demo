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

commands_to_fix = {}

# Extract the unique command and the unused directory from the JSON file
for instance in data:
    unused_dir = instance["Unused directory"]
    responsible_command = instance["Responsible command"]
    responsible_plugin = instance["Responsible plugin"]
    step_name = instance["Name of the step"]

    if responsible_command not in commands_to_fix:
        commands_to_fix[responsible_command] = {
            "unused_dirs_responsible_plugin": [],
            "step_names": []
        }
    commands_to_fix[responsible_command]["unused_dirs_responsible_plugin"].append((unused_dir, responsible_plugin))
    commands_to_fix[responsible_command]["step_names"].append(step_name)

# Create a list to store the commands that need to be fixed
commands_to_update = []

# Create a prompt for each unique command and get the fix suggestion from Gemini
for responsible_command, details in commands_to_fix.items():
    unused_dirs_responsible_plugin = details["unused_dirs_responsible_plugin"]
    step_names = details["step_names"]

    # Create a prompt for each unique command
    prompt = (
        f"The command `{responsible_command}` creates the following unused directories while running the following plugins given as (unused directory, responsible plugin):\n"
        f"{unused_dirs_responsible_plugin}\n"
        f"Please suggest an updated command to avoid unnecessary directories. Provide only the new command.\n"
    )

    print("prompt is as follows: \n", prompt)
    fix_suggestion = gemini.ask_prompt(prompt)
    print("suggested fix for the old command is as follows: \n ", fix_suggestion)

    # Ask gemini to make the fixed command compilable, if not compilable, then ask for the compilable version.
    # pass the old command saying that it was compilable, And here is the new command with some fix, ask gemini to make it compilable if not.
    # If the command is compilable, then return the same command.
    # create another prompt for this.
    ask_compilable_prompt = (
        f"The command `{responsible_command}` is compilable. The command `{fix_suggestion}` is a new command with some fix to prevent generation of unnecessary directories."
        f"Please make the command `{fix_suggestion}` compilable. If it is already compilable, please return the same command."
        f"Please give me only the command that is compilable."
    )

    compilable_fix_suggestion = gemini.ask_prompt(ask_compilable_prompt)
    print("compilable_fix_suggestion is as follows: \n", compilable_fix_suggestion)

    if compilable_fix_suggestion != fix_suggestion:
        print("The compilable fix suggestion is different from the original fix suggestion.")
        print("Original fix suggestion: ", fix_suggestion)
        print("Compilable fix suggestion: ", compilable_fix_suggestion)
        fix_suggestion = compilable_fix_suggestion

    if str(fix_suggestion) == "" or str(fix_suggestion) == responsible_command:
        print('There is no fix suggestions found')
    else:
        commands_to_update.append((fix_suggestion, responsible_command))

# Apply all the fixes to the YAML files
for fix_suggestion, responsible_command in commands_to_update:
    update_mvn_commands_in_yml(fix_suggestion, repo, responsible_command, path_to_local_repo)

# Call the Bash script with the variables as arguments after applying all fixes
script_path = f"{currentDir}/utils.sh"
subprocess.run([script_path, owner, repo, path_to_yaml_file, branch,
                workflow_file, path_to_local_repo, output_file, input_yaml_filename]
              )
