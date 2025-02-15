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
import warnings
import time
# from urllib3.exceptions import NotOpenSSLWarning

# warnings.simplefilter("ignore", NotOpenSSLWarning)
warnings.filterwarnings("ignore")


class GeminiAPI:
    def __init__(self):
        api_key = os.environ["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask_prompt(self, prompt):
        response = self.model.generate_content(
            prompt,
            generation_config = genai.GenerationConfig(
                 temperature=0.0,
             )
        )
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
    fix_args = set()
    fixed_dirs = set()

    for unused_dir in unused_dirs:

        if os.path.basename(unused_dir) in fixed_dirs:
            continue

        prompt = (
                f"The command `{original_command}` creates the following unused directory:"
                f"{unused_dir}\n"
                f"while running the plugin `{responsible_plugins}`:\n"
                f"We can skip creating any files that are being created in this directory by updating the command.\n"
                f"Please suggest an updated command to avoid creating this unnecessary directory. Note that your command should not stop the test runs. For example, using -DskipTests would prevent Maven tests from running, which is not acceptable. Therefore, your solution should not include such options unless the command already contains -DskipTests\n"
                f"A valid fix would disable the generation of the unused directory without affecting the test runs. For example `-DdisableXmlReport=true` would disable generation of surefire reports directory without affecting test runs and is considered a valid fix if unused directory is surefire-reports.\n"
                f"Provide only the new command without additional explanation, code formatting, or backticks."
            )
            
        fix_suggestion = gemini.ask_prompt(prompt)
        # sleep for 10 seconds to avoid rate limiting
        time.sleep(10)

        unused_dir_name = os.path.basename(unused_dir)
        fixed_dirs.add(unused_dir_name)

        if str(fix_suggestion) == "" or str(fix_suggestion) == command_with_fix_tmp:
            print(f'There is no fix suggestion found for the unused directory: {unused_dir}')
            fixes.append("Gemini did not provide a fix")
        else:
            # find the difference between the original command and the fix suggestion
            difference = [x for x in fix_suggestion.split() if x not in original_command.split()]
            fixes.append(difference)
            fix_args.add(fix_suggestion)
            # command_with_fix_tmp = fix_suggestion

    # Flatten the fixes list
    flattened_fixes_list = [item for sublist in fixes for item in sublist if isinstance(sublist, list)]
    # fix_suggestion_str = original_command + ' ' + ' '.join([f'"{fix}"' for fix in flattened_fixes])

    # flatten the fix arguments, and join them with the original command
    # Extract only the new arguments from the fix suggestions
    flattened_fixes = {arg for fix in fix_args for arg in fix.split() if arg not in original_command.split()}
    fix_suggestion_str = original_command + ' ' + ' '.join(flattened_fixes)


    print(f"Fix suggestion for the command '{original_command}'")
    print(f"is:\n {fix_suggestion_str}")

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

    # remove duplicates from the list diff_only_in_old
    diff_only_in_old = list(dict.fromkeys(diff_only_in_old))

    # if any content in the diff_only_in_old list contains "maven-status" then remove it
    diff_only_in_old = [x for x in diff_only_in_old if "maven-status" not in x]


    with open(initial_output_file, 'a') as f:
        f.write(f"Command: {original_command}\n")
        f.write(f"Fixes: {flattened_fixes_list}\n")
        f.write(f"following directories are fixed:\n")
        # f.write(f"Fixed directories: {list(diff_only_in_old)}\n") print 1 directory per line. not as a list. each entry in a new line
        for dir in diff_only_in_old:
            f.write(f"{dir}\n")
        f.write("-"*10 + "\n")
        f.write("fixed command: " + fix_suggestion_str + "\n")
        f.write("-"*10 + "\n")
        f.write("\n")
    f.close()