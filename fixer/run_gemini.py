import json
import google.generativeai as genai
import os
import time
from collections import defaultdict
import sys

owner = sys.argv[1]
repo = sys.argv[2]
yaml_filename = sys.argv[3]
job = sys.argv[4]
output_file = sys.argv[5]


class GeminiAPI:
    def __init__(self):
        api_key = os.environ["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask_prompt(self, prompt):
        response = self.model.generate_content(prompt)
        aio_response = ""

        print(response)
        for part in response.parts:
            aio_response += part.text
        
        # remove ``` from the response
        aio_response = aio_response.replace("```", "").replace("\n", "")
        return aio_response


gemini = GeminiAPI()

# iterate over the rows
# header owner;repo;yaml_filename;job;all_unused;maven_unused
# call the gemini_wrapper.py script with the following arguments
# pattern =owner_repo_yaml_filename_job.json
json_filename = "responsible_plugins.json"

old_commands = ""
fix_suggestion_str = ""

if not os.path.exists(json_filename):
    print(f"File {json_filename} does not exist")
    sys.exit(1)

# read the json file
with open(json_filename) as json_file:
    data = json.load(json_file)

command_to_unused_dirs = defaultdict(list)
command_to_step_names = defaultdict(list)
command_to_plugins = defaultdict(list)

for instance in data:
    # Loop through each detection result in the JSON
    unused_dir = instance["Unused directory"]
    responsible_command = instance["Responsible command"]
    responsible_plugin = instance["Responsible plugin"]
    step_name = instance["Name of the step"]

    # Group by command
    command_to_unused_dirs[responsible_command].append(unused_dir)
    command_to_plugins[responsible_command].append(responsible_plugin)
    command_to_step_names[responsible_command].append(step_name)

results = {}

for command, unused_dirs in command_to_unused_dirs.items():
    plugins = command_to_plugins[command]
    step_name = command_to_step_names[command]

    # Generate prompt
    prompt = (
        f"I am trying to optimize the command I use in my CI pipeline. And I am asking you for help on finding a fix.\n"
        f"The command `{command}` creates these unused directories:\n"
        f"{', '.join(unused_dirs)} with plugins: {', '.join(plugins)}.\n"
        f"\nThese were generated in CI step `{step_name}`. "
        f"Please suggest an updated command to avoid unnecessary directories. Provide only the new command.\n"
    )

    # Call the Gemini API to get the fix suggestion
    fix_suggestion = gemini.ask_prompt(prompt)
    results[command] = {
        "fix_suggestion": fix_suggestion
    }

    time.sleep(6)
time.sleep(6)

# create a string of fix, concat all the fixes with a newline. Basically I wanted to put all the fixes in one string
fix_suggestion_str = ""
for key in results:
    fix_suggestion_str += results[key]['fix_suggestion'] + "\n"


# old_commands = [key for key in results] \n separated, remove the last newline character
old_commands = "\n".join([key for key in results])

# remove the last newline character
fix_suggestion_str = fix_suggestion_str[:-1]

print("=====================================")
print(f"Owner: {owner}")
print(f"Repo: {repo}")
print(f"Yaml filename: {yaml_filename}")
print(f"Job: {job}")
print(f"Old commands: {old_commands}")
print(f"Fix suggestion: {fix_suggestion_str}")
print("=====================================")
print("\n\n")

if output_file != "":
    with open(output_file, "a") as output:
        output.write("=====================================\n")
        output.write(f"Owner: {owner}\n")
        output.write(f"Repo: {repo}\n")
        output.write(f"Yaml filename: {yaml_filename}\n")
        output.write(f"Job: {job}\n")
        output.write(f"Old commands: {old_commands}\n")
        output.write(f"Fix suggestion: {fix_suggestion_str}\n")
        output.write("=====================================\n\n\n")
