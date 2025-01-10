import requests
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
import yaml
from ruamel.yaml import YAML




#TheAlgorithms_Java_infer_run_infer_maven_only.json                                                                                                                                                                    

class GeminiAPI:
    def __init__(self):
        api_key = os.environ["API_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask_prompt(self, prompt):
        response = self.model.generate_content(prompt)
        aio_response = ""

        #print(response)
        for part in response.parts:
            aio_response += part.text
        
        # remove ``` from the response
        aio_response = aio_response.replace("```", "").replace("\n", "")
        return aio_response
    
def push_in_ci_and_run_new_command(mvn_command_str, unused_dir, repo, clone_directory):
    os.chdir(clone_directory)
    current_directory = os.getcwd()
    #print("Current Directory:", current_directory)
    file_path = f".github/workflows/modified-build_1.yml"

    # Run the mvn command using subprocess
    '''try:
        # Run the command using shell=True to interpret the entire command string
        subprocess.run(mvn_command_str, shell=True, check=True)
        print(f"Successfully ran: {mvn_command_str}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run: {mvn_command_str}")
        print(f"Error: {e}")'''
     
    try:
        # 1. Add the file to the staging area
        subprocess.run(['git', 'add', '-f', file_path], check=True)
        #print(f"File '{file_path}' added to the staging area.")
        
        # 2. Check the status to see if there are any changes to commit
        result = subprocess.run(['git', 'status'], stdout=subprocess.PIPE, text=True)
        #print("Git status before committing:\n", result.stdout)
        commit_message="command updated"
        # 2. Commit the file with a message
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        #print(f"Committed the file '{file_path}' with commit")

        # 3. Push the changes to the specified remote and branch
        subprocess.run(['git', 'push'], check=True)
        print(f"Successfully pushed.")

    except subprocess.CalledProcessError as e:
         print(f"An error occurred while running git command: {e}")
   
    #exit()
from ruamel.yaml.scalarstring import PlainScalarString

def update_mvn_commands_in_yml(new_mvn_command, repo, old_command, clone_directory):
    file_path = f"{clone_directory}/.github/workflows/modified-build.yml"
    modified_yml_file_path = f"{clone_directory}/.github/workflows/modified-build.yml"

    # Initialize ruamel.yaml with indentation settings
    yaml = YAML()
    yaml.preserve_quotes = True  # Preserve quotes in the original YAML file
    yaml.indent(mapping=2, sequence=4, offset=2)  # Set custom indentation levels

    # Remove any leading or trailing spaces from the new command
    new_mvn_command = new_mvn_command.strip()

    # Read the YAML file
    with open(file_path, 'r') as file:
        yml_data = yaml.load(file)

    # Debug: Check the initial structure of the YAML file
    #print("Initial YAML structure:")
    #print(yml_data)

    # Function to update only the matching old mvn command
    def update_mvn_command_in_steps(steps, old_cmd, new_cmd):
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict) and 'run' in step:
                    # Print the current command for debugging
                    #print(f"Current command: '{step['run']}' (repr: {repr(step['run'])})")

                    # Check if the 'run' command matches the old_command exactly
                    if step['run'].strip() == old_cmd.strip():
                        #print(f"Updating command: '{step['run']}' -> '{new_cmd}'")

                        # Use PlainScalarString to ensure no quotes are added
                        step['run'] = PlainScalarString(new_cmd)

    # Traverse and update the specific 'run' command in the YAML data
    for job in yml_data.get('jobs', {}).values():
        steps = job.get('steps', [])
        update_mvn_command_in_steps(steps, old_command, new_mvn_command)
    
    # Debug: Check the modified structure of the YAML file
    print("Modified YAML structure:")
    #print(yml_data)

    # Write the updated content back to the YAML file with controlled formatting
    with open(modified_yml_file_path, 'w') as file:
        yaml.dump(yml_data, file)

    print(f"The command '{old_command}' has been updated to: {new_mvn_command}")


csv_path="job-based-results.csv"
json_path_base = "maven_only_results"
postfix = "maven_only"
output_path = "fixer_results_shanto.csv" # output file
temp_csv = "temp.csv" # temporary file to save the results

reader = pd.read_csv(csv_path, delimiter=';')
out_df = pd.DataFrame(columns=['owner', 'repo', 'yaml_filename', 'job', 'all_unused', 'maven_unused', 'fix_suggestion', 'old_commands'])
#print(out_df)
gemini = GeminiAPI()

#os.makedirs("projects", exist_ok=True)
# iterate over the rows
for index, row in reader.iterrows():
    # header owner;repo;yaml_filename;job;all_unused;maven_unused
    # call the gemini_wrapper.py script with the following arguments 
    # pattern =owner_repo_yaml_filename_job.json
    owner = row['owner']
    repo = row['repo']

    clone_directory = f"../{repo}"
    repo_url = "https://github.com/butterfly-lab/"+repo
    if os.path.exists(clone_directory) and os.listdir(clone_directory):
        print(f"Directory '{clone_directory}' already exists and is not empty. Skipping clone.")
    else:
        try:
            subprocess.run(['git', 'clone', repo_url , "../../"+repo], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone the repository: {e}")

    yaml_filename = row['yaml_filename']
    job = row['job']

    yaml_file_in_filename = yaml_filename.replace(".yml", "")
    json_filename = f"{owner}_{repo}_{yaml_file_in_filename}_{job}_{postfix}.json"
    
    numner_of_unused_dirs = row['maven_unused']
    
    temp_df_out = pd.DataFrame(columns=['owner', 'repo', 'yaml_filename', 'job', 'all_unused', 'maven_unused', 'fix_suggestion'])
    temp_df_out['owner'] = [owner]
    temp_df_out['repo'] = [repo]
    temp_df_out['yaml_filename'] = [yaml_filename]
    temp_df_out['job'] = [job]
    temp_df_out['all_unused'] = [row['all_unused']]
    temp_df_out['maven_unused'] = [row['maven_unused']]
    #exit() 
    old_commands = ""
    fix_suggestion_str = ""
    
    if numner_of_unused_dirs == "0":
        temp_df_out['fix_suggestion'] = ["No unused directories found"]
        continue

    
    full_json_path = os.path.join(json_path_base, json_filename)
    
    if not os.path.exists(full_json_path):
        #print(f"File {full_json_path} does not exist")
        continue
    
    # read the json file
    with open(full_json_path) as json_file:
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
        #print(unused_dir)

        # Group by command
        command_to_unused_dirs[responsible_command].append(unused_dir)
        command_to_plugins[responsible_command].append(responsible_plugin)
        command_to_step_names[responsible_command].append(step_name)
            
        prompts = []
        results = {}
        
    #for command, unused_dirs in command_to_unused_dirs.items():
        #plugins = command_to_plugins[command]
        #step_name = command_to_step_names[command]

        # Generate prompt
        prompt = (
            #f"I am trying to optimize the command I use in my CI pipeline. And I am asking you for help on finding a fix.\n"
            f"The command `{responsible_command}` creates the following unused directory:\n"
            #f"{', '.join(unused_dir)}\n"
            f"{unused_dir}\n"
            #f"{', '.join(unused_dirs)} with plugins: {', '.join(plugins)}.\n"
            #f"\nThese were generated in CI step `{step_name}`. "
            f"Please suggest an updated command to avoid unnecessary directory. Provide only the new command.\n"
        )
        print("***Prompt***")
        print(prompt)
        print("***")
        #print()
        #exit()
        # Call the Gemini API to get the fix suggestion
        fix_suggestion = gemini.ask_prompt(prompt)
        results[responsible_command] = {
            "fix_suggestion": fix_suggestion
        }
        
        time.sleep(6)
    #time.sleep(6)
    #exit()  
    # create a string of fix, concat all the fixes with a newline. Basically I wanted to put all the fixes in one string
        fix_suggestion_str = ""
        for key in results:
            fix_suggestion_str += results[key]['fix_suggestion'] + "\n"
            
        #print('Results=',results)    
        # old_commands = [key for key in results] \n separated, remive the last newline character
        old_commands = "\n".join([key for key in results])
        #old_commands = old_commands[:-1]
        
        # remove the lat newline character
        fix_suggestion_str = fix_suggestion_str[:-1]
        
        temp_df_out['fix_suggestion'] = [fix_suggestion_str]
        temp_df_out['old_commands'] = [old_commands]
        out_df = pd.concat([out_df, temp_df_out], ignore_index=True)
        
        print("=====================================")
        print(index)
        print(f"Owner: {owner}")
        print(f"Repo: {repo}")
        print(f"Yaml filename: {yaml_filename}")
        print(f"Job: {job}")
        print(f"Number of unused directories: {numner_of_unused_dirs}")
        print(f"Processed {json_filename}")
        print(f"Old commands: {old_commands}")
        print(f"Fix suggestion: {fix_suggestion_str}")
        print("=====================================")
        print("\n\n")
        update_mvn_commands_in_yml(fix_suggestion_str, repo, old_commands, clone_directory) 
        push_in_ci_and_run_new_command(fix_suggestion_str, unused_dir, repo, clone_directory)
        # save the row to a csv file
        with open(temp_csv, 'a') as f:
            out_df.to_csv(f, sep=';', index=False)

        exit()
    
out_df.to_csv(output_path, sep=';', index=False)  
