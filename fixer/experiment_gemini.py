import pandas as pd
import json
import os
import google.generativeai as genai
import requests
import time
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiAPI:
    def __init__(self):
        api_key = os.environ["API_KEY"]
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask_prompt(self, prompt):
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                },
                request_options={"timeout": 300}
            )
            aio_response = "".join(part.text for part in response.parts)
            aio_response = aio_response.replace("```", "").replace("\n", "")
        except Exception as e:
            aio_response = f"No fix suggested by gemini"
        
        return aio_response
    

def find_unused_dir_and_plugin_per_command(row, maven_only_results_json_basepath):
    print(row)
    yaml_filename = row['yaml_filename'].replace(".yml", "")
    yaml_filename = yaml_filename.replace(".yaml", "")
    file_fullpath = os.path.join(maven_only_results_json_basepath, row['owner'] + "_" + row['repo'] + "_" + yaml_filename + "_" + row['job'] + "_maven_only.json")
    # print(file_fullpath)

    output_json = {}
    
    # open the json file
    with open(file_fullpath) as f:
        data = json.load(f)
        commands = set()
        
        for detection in data:
            command = detection['Responsible command']
            Unused_directory = detection['Unused directory']
            Responsible_plugin = detection['Responsible plugin']
            step_name = detection['Name of the step']
            
            if command not in commands:
                commands.add(command)
                output_json[command] = {}
                output_json[command]['Unused_directory'] = []
                output_json[command]['Responsible_plugin'] = []
                output_json[command]['Step_name'] = []
            output_json[command]['Unused_directory'].append(Unused_directory)
            output_json[command]['Responsible_plugin'].append(Responsible_plugin)
            output_json[command]['Step_name'].append(step_name)
            
            # remove any duplicates
            output_json[command]['Unused_directory'] = list(set(output_json[command]['Unused_directory']))
            output_json[command]['Responsible_plugin'] = list(set(output_json[command]['Responsible_plugin']))
            output_json[command]['Step_name'] = list(set(output_json[command]['Step_name']))
    
    return output_json



maven_only_results_json_basepath = "/home/tbaral/research/optcd_demo/optCD-demo/maven_only_results"

json_data = {} #[command] = {owner, repo, yaml_filename, job, all_unused, maven_unused, fix_suggestion, old_commands}

projects="/home/tbaral/research/optcd_demo/optCD-demo/project-based-results.csv" #owner,repo,all_unused,maven_unused
jobs="/home/tbaral/research/optcd_demo/optCD-demo/job-based-results.csv" #owner;repo;yaml_filename;job;all_unused;maven_unused
fixer_result="/home/tbaral/research/optcd_demo/filter/results.csv" #owner;repo;yaml_filename;job;all_unused;maven_unused;fix_suggestion;old_commands

projects_df = pd.read_csv(projects)
jobs_df = pd.read_csv(jobs, sep=';')
fixer_result_df = pd.read_csv(fixer_result, sep=';')

# print number of rows with non 0 maven_unused in projects_df
print("Number of rows with non 0 maven_unused in projects_df: ", len(projects_df[projects_df['maven_unused'] != 0]))

# print number of rows with non 0 maven_unused in jobs_df
print("Number of rows with non 0 maven_unused in jobs_df: ", len(jobs_df[jobs_df['maven_unused'] != 0]))

# print number of rows with non 0 maven_unused in fixer_result_df
print("Number of rows with non 0 maven_unused in fixer_result_df: ", len(fixer_result_df[fixer_result_df['maven_unused'] != 0]))

# count total columns in each dataframe
print("Total columns in projects_df: ", len(projects_df.columns))
print("Total columns in jobs_df: ", len(jobs_df.columns))
print("Total columns in fixer_result_df: ", len(fixer_result_df.columns))

# count rows in each dataframe
print("Total rows in projects_df: ", len(projects_df))
print("Total rows in jobs_df: ", len(jobs_df))
print("Total rows in fixer_result_df: ", len(fixer_result_df))

# find the rows owner;repo;yaml_filename;job;all_unused;maven_unused that are in jobs but not in fixer_result
jobs_not_in_fixer_result = jobs_df[~jobs_df.isin(fixer_result_df)].dropna()
print("Rows in jobs_df but not in fixer_result_df: ", len(jobs_not_in_fixer_result))

# create a subdataset where maven_unused is not 0 in jobs_df
jobs_df_maven_unused_not_zero = jobs_df[jobs_df['maven_unused'] != 0]
print("Rows in jobs_df where maven_unused is not 0: ", len(jobs_df_maven_unused_not_zero))

# find rows that are in jobs_df_maven_unused_not_zero but not in fixer_result_df
jobs_df_maven_unused_not_zero_not_in_fixer_result = jobs_df_maven_unused_not_zero[~jobs_df_maven_unused_not_zero.isin(fixer_result_df)].dropna()
print("Rows in jobs_df_maven_unused_not_zero but not in fixer_result_df: ", len(jobs_df_maven_unused_not_zero_not_in_fixer_result))

# for each row in jobs_df_maven_unused_not_zero iterate through the row and fill up json
for index, row in jobs_df_maven_unused_not_zero.iterrows():
    # we need to fill up unused_dirs and plugin_responsible
    # unused_dirs, plugin_responsible,command = find_unused_dir_and_plugin_per_command(row)
    object_dir_plugin_command = find_unused_dir_and_plugin_per_command(row, maven_only_results_json_basepath)
    
    for command in object_dir_plugin_command:
        json_data[index] = {
            "owner": row['owner'],
            "repo": row['repo'],
            "yaml_filename": row['yaml_filename'],
            "job": row['job'],
            "#all_unused": row['all_unused'],
            "#maven_unused": row['maven_unused'],
            "fix_suggestion": "",
            "old_commands": str(command),
            "unused_dirs": object_dir_plugin_command[command]['Unused_directory'],
            "plugin_responsible": object_dir_plugin_command[command]['Responsible_plugin'],
            "step_name": object_dir_plugin_command[command]['Step_name']
        }

# save the json_data to a file
# with open('json_data.json', 'w') as f:
#     json.dump(json_data, f)
    
# count number of rows in json_data
print("Total rows in json_data: ", len(json_data))


# for each object run the gemini prompt
# prompt = (
#                         f"The command `{command}` generates the following unused directories while running the respective plugins:\n"
#                         f"{', '.join(unused_dirs)} with plugins {', '.join(plugins)}.\n"
#                         f"\nThe unused directories were generated in GitHub Actions run in a step named `{step_name}`. "
#                         f"Suggest an optimal command that minimizes the generation of as many unnecessary directories as possible. "
#                         f"Give only the updated command as a solution.\n"
#                     )

# and fill the fix_suggestion

gemini = GeminiAPI()

for index in json_data:
    command = json_data[index]['old_commands']
    unused_dirs = json_data[index]['unused_dirs']
    plugins = json_data[index]['plugin_responsible']
    step_name = json_data[index]['step_name']
    
    prompt = (
        f"The command `{command}` generates the following unused directories:\n"
        f"{', '.join(unused_dirs)}\n"
        f"while running these plugins {', '.join(plugins)}.\n"
        f"Suggest an optimal command that prevents the generation of as many unnecessary directories as possible. "
        f"Give only the updated command as a solution.\n"
    )
    
    fix_suggestion = gemini.ask_prompt(prompt)
    
    if fix_suggestion:
        json_data[index]['fix_suggestion'] = fix_suggestion
    
    else:
        json_data[index]['fix_suggestion'] = "No fix suggested by gemini"
    
    print(json_data[index])
    print("=====================================")
    print("\n")
    time.sleep(10)
    
# save the json_data to a file
with open('json_data_w_fix_wo_step_name.json', 'w') as f:
    json.dump(json_data, f)
