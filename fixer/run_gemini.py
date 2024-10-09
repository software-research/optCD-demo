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


class GeminiAPI:
    def __init__(self):
        api_key = os.environ["API_KEY"]
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
    

csv_path="../job-based-results.csv"
json_path_base = "../maven_only_results"
postfix = "maven_only"
output_path = "fixer_results.csv" # output file
temp_csv = "temp.csv" # temporary file to save the results

reader = pd.read_csv(csv_path, delimiter=';')
out_df = pd.DataFrame(columns=['owner', 'repo', 'yaml_filename', 'job', 'all_unused', 'maven_unused', 'fix_suggestion', 'old_commands'])

gemini = GeminiAPI()

# iterate over the rows
for index, row in reader.iterrows():
    # header owner;repo;yaml_filename;job;all_unused;maven_unused
    # call the gemini_wrapper.py script with the following arguments 
    # pattern =owner_repo_yaml_filename_job.json
    owner = row['owner']
    repo = row['repo']
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
    
    old_commands = ""
    fix_suggestion_str = ""
    
    if numner_of_unused_dirs == "0":
        temp_df_out['fix_suggestion'] = ["No unused directories found"]
        continue

    
    full_json_path = os.path.join(json_path_base, json_filename)
    
    if not os.path.exists(full_json_path):
        print(f"File {full_json_path} does not exist")
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

        # Group by command
        command_to_unused_dirs[responsible_command].append(unused_dir)
        command_to_plugins[responsible_command].append(responsible_plugin)
        command_to_step_names[responsible_command].append(step_name)
            
        prompts = []
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
        
        
    # old_commands = [key for key in results] \n separated, remive the last newline character
    old_commands = "\n".join([key for key in results])
    old_commands = old_commands[:-1]
    
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
    
    # save the row to a csv file
    with open(temp_csv, 'w') as f:
        out_df.to_csv(f, sep=';', index=False)
    
out_df.to_csv(output_path, sep=';', index=False)  