import json
import google.generativeai as genai
import os
from jinja2 import Template
import xml.etree.ElementTree as ET
import sys
import os
import subprocess
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

    # print(f"The command '{old_command}' has been updated to: {new_mvn_command}")

def extract_unique_commands(data):
    unique_commands = {}
    for instance in data:
        command = instance["Responsible command"]
        unused_dir = instance["Unused directory"]
        responsible_plugin = instance["Responsible plugin"]

        if command not in unique_commands:
            unique_commands[command] = {
                "command": command,
                "unused_dirs": [],
                "responsible_plugin": [],
                "fixes": [],
            }

        if unused_dir not in unique_commands[command]["unused_dirs"]:
            unique_commands[command]["unused_dirs"].append(unused_dir)
        if responsible_plugin not in unique_commands[command]["responsible_plugin"]:
            unique_commands[command]["responsible_plugin"].append(responsible_plugin)
    return unique_commands


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
initial_output_file = sys.argv[11]

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

unique_commands = extract_unique_commands(data)

for instance in unique_commands:
    original_command = unique_commands[instance]["command"]
    unused_dirs = unique_commands[instance]["unused_dirs"]
    responsible_plugins = unique_commands[instance]["responsible_plugin"]
    fixes = unique_commands[instance]["fixes"]
    command_with_fix_tmp = original_command

    for unused_dir in unused_dirs:
        prompt = (
            f"The command `{command_with_fix_tmp}` creates the following unused directory while running the plugin `{responsible_plugins}`:\n"
            f"{unused_dir}\n"
            f"We can skip creating any files that are being created in this directory by updating the command.\n"
            f"Please suggest an updated command to avoid creating this unnecessary directory. Provide only the new command without additional explanation, code formatting, or backticks.\n"
        )

        fix_suggestion = gemini.ask_prompt(prompt)
        if str(fix_suggestion) == "" or str(fix_suggestion) == command_with_fix_tmp:
            print(f'There is no fix suggestion found for the unused directory: {unused_dir}')
            fixes.append("Gemini did not provide a fix")
        else:
            # find the difference between the original command and the fix suggestion
            difference = [x for x in fix_suggestion.split() if x not in command_with_fix_tmp.split()]
            fixes.append(difference)
            command_with_fix_tmp = fix_suggestion

    # Flatten the fixes list
    flattened_fixes = [item for sublist in fixes for item in sublist if isinstance(sublist, list)]
    fix_suggestion_str = original_command + ' ' + ' '.join([f'"{fix}"' for fix in flattened_fixes])

    update_mvn_commands_in_yml(fix_suggestion_str, repo, original_command, path_to_local_repo)

    os.remove(full_json_path)
    script_path = f"{currentDir}/utils.sh"
    subprocess.run([script_path, owner, repo, path_to_yaml_file, branch,
                    workflow_file, path_to_local_repo, output_file, input_yaml_filename]
                )

    with open(full_json_path) as json_file:
        new_data = json.load(json_file)
    
    all_unused_old = set()
    all_unused_new = set()
    for instance in data:
        if instance["Responsible command"] == original_command:
            all_unused_old.add(os.path.normpath(instance["Unused directory"]).rstrip('/'))
    
    for instance in new_data:
        all_unused_new.add(os.path.normpath(instance["Unused directory"]).rstrip('/'))

    diff_only_in_old = all_unused_old - all_unused_new

    print("Summary of the fixes applied:")
    print("-"*10)
    for i in range(len(flattened_fixes)):
        print("directory:", unused_dirs[i])
        print("Suggested fix:", flattened_fixes[i])
        print("-"*10)
    
    print("The command with all the fixes is:\n", fix_suggestion_str)
    print("The directories that were fixed are:\n", list(diff_only_in_old))
