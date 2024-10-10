To run the fixer run this command:
```bash
export API_KEY=<gemini_api_key>
python3 run_gemini.py
```

It will take reference from `optCD-demo/job-based-results.csv` file to find the result of mapper component. The detail result is in `optCD-demo/maven_only_results` folder.

Currently, it uses 1 prompt for each command.

Potential improvement: take a json file as input, or simply unused dir and plugin responsible as an input to prompt the gemini to run the fixer. i.e. integrate fixer with the rest of the tool (refer to readme in the root directory).

To run the gemini in the experimented 89 projects, run this command:
```bash
export API_KEY=<gemini_api_key>
python experiment_gemini.py
```

The result from this experiment is in json_data_w_fix_wo_step_name.json file.
This file shows that gemini was not able to suggest fix for 77 out of 216 cases. The fixer was able to suggest fix for 139 cases. The fixer was able to suggest fix for 62% of the cases.