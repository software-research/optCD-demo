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
        step_name = instance["Name of the step"]

        if command not in unique_commands:
            unique_commands[command] = {
                "unused_dirs_responsible_plugin": [],
                "step_names": []
            }
        unique_commands[command]["unused_dirs_responsible_plugin"].append((unused_dir, responsible_plugin))
        unique_commands[command]["step_names"].append(step_name)
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
commands_to_fix = extract_unique_commands(data)
commands_to_update = []
unique_unused_dirs = set()

# Create a prompt for each unique command and get the fix suggestion from Gemini
for responsible_command, details in commands_to_fix.items():
    unused_dirs_responsible_plugin = details["unused_dirs_responsible_plugin"]
    step_names = details["step_names"]
    unused_dirs = [item[0] for item in unused_dirs_responsible_plugin]
    plugins = [item[1] for item in unused_dirs_responsible_plugin]
    unique_unused_dirs.update(unused_dirs)


    # Create a prompt for each unique command
    prompt = (
        f"The command `{responsible_command}` creates the following unused directories:\n"
        f"{', '.join(unused_dirs)}\n"
        f"Unused directories are the directories that are created by the execution of the plugins as part of the command, but are not accessed. We can prevent the creation of any of these unused directories and still execute the command successfully.\n"
        f"In most cases adding a standard plugin option to the command can prevent the creation of the unused directories.\n"
        f"Please suggest an updated command with an argument that avoids the creation of the unnecessary directories. Provide only the new command without additional explanation, code formatting, or backticks.\n"
        f"IMPORTANT: If the fix involves Maven options such as `-Dproperty=value`, ensure that each `-Dproperty=value` argument is individually wrapped in double quotes, e.g., \"-Dproperty=value\". This quoting requirement applies to every `-D` argument in the command.\n"
    )

    fix_suggestion = gemini.ask_prompt(prompt)
    if str(fix_suggestion) == "" or str(fix_suggestion) == responsible_command:
        print('There is no fix suggestions found')
    else:
        commands_to_update.append((fix_suggestion, responsible_command))

# Apply all the fixes to the YAML files

# if commands_to_update is not empty, update the commands in the YAML file
if len(commands_to_update) == 0:
    print("No fixes found for the commands in the YAML file.")
    sys.exit(0)

for fix_suggestion, responsible_command in commands_to_update:
    update_mvn_commands_in_yml(fix_suggestion, repo, responsible_command, path_to_local_repo)

# remove the responsible_plugins.json file
os.remove(full_json_path)

# Call the Bash script with the variables as arguments after applying all fixes
script_path = f"{currentDir}/utils.sh"
subprocess.run([script_path, owner, repo, path_to_yaml_file, branch,
                workflow_file, path_to_local_repo, output_file, input_yaml_filename]
              )

print("Fixes have been applied and tested successfully.")
print("summary of the fixes applied: ")
# read the responsible_plugins.json file and find the new set of unique unused directories
with open(full_json_path) as json_file:
    new_data = json.load(json_file)
new_unique_unused_dirs = set()
for instance in new_data:
    new_unique_unused_dirs.add(instance["Unused directory"])

for fix_suggestion, responsible_command in commands_to_update:
    print(f"Old command: {responsible_command}")
    print(f"New command: {fix_suggestion}")
    print("----------------------------------------------------")

print("Unused directories before the fix: ")
print(unique_unused_dirs)
print("Unused directories after the fix: ")
print(new_unique_unused_dirs)
   