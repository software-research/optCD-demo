import yaml


def str_presenter(dumper, data):
    if data.count('\n') > 0:
        data = "\n".join([line.rstrip() for line in data.splitlines()])
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
yaml.SafeDumper.ignore_aliases = lambda self, data: True


def run_inotifywait(log_name: str, repo: str) -> dict:
    return {
        "name": "Run inotifywait",
        "run": "python3 -c \"\n"
               "import inotify.adapters\n"
               "import inotify.constants\n"
               "import os\n"
               "from datetime import datetime, timezone\n"
               f"with open('/home/runner/inotifywait-log-{log_name}.csv', 'w') as log_file:\n"
               f"  i = inotify.adapters.InotifyTree('/home/runner/work/{repo}/{repo}', inotify.constants.IN_CREATE | inotify.constants.IN_ACCESS)\n"
                "  for event in i.event_gen(yield_nones=False):\n"
                "    (_, type_names, path, filename) = event\n"
                "    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'\n"
                "    events = ','.join(type_names)\n"
                "    log_file.write(f'{now};{path};{filename};{events}\\n')\n"
                "    log_file.flush()\n"
                "    os.fsync(log_file.fileno())\n"
                "\" &\n"
    }


def upload_inotifywait_artifact(log_name: str) -> dict:
    return {
        "name": "Upload inotifywait logs",
        "uses": "actions/upload-artifact@v4",
        "with": {
            "name": f"inotifywait-{log_name}",
            "path": f"/home/runner/inotifywait-log-{log_name}.csv",
        }
    }


def modify_file_content(repo: str, loaded_yaml: dict) -> str:
    set_up_python = {
        "name": "Setup Python 3.10",
        "uses": "actions/setup-python@v5",
        "with": {
            "python-version": "3.10"
        }
    }
    install_dependencies = {
        "name": "Install dependencies",
        "run": "python -m pip install --upgrade pip\n"
               "pip install inotify\n"
    }

    loaded_yaml["on"] = ["push", "workflow_dispatch"]
    loaded_yaml.pop(True, None)
    loaded_yaml.pop("concurrency", None)
    loaded_yaml["name"] = "Modified " + loaded_yaml["name"]

    for job in loaded_yaml["jobs"]:
        if "steps" not in loaded_yaml["jobs"][job]:
            continue
        # modify the name based on strategy matrix
        job_name = job
        if "strategy" in loaded_yaml["jobs"][job] and "matrix" in loaded_yaml["jobs"][job]["strategy"]:
            job_name += " ("
            matrix_variable_names = []
            for key in loaded_yaml["jobs"][job]["strategy"]["matrix"].keys():
                if key == "include" or key == "exclude":
                    continue
                matrix_variable_names.append("${{ matrix." + key + " }}")
            job_name += ', '.join(matrix_variable_names)
            job_name += ")"

        loaded_yaml["jobs"][job]["name"] = job_name
        setup = [set_up_python, install_dependencies, run_inotifywait(job_name, repo)]

        # add setup to beginning of each job
        loaded_yaml["jobs"][job]["steps"] = setup + loaded_yaml["jobs"][job]["steps"]
        # upload artifacts at the end of each job
        loaded_yaml["jobs"][job]["steps"].append(upload_inotifywait_artifact(job_name))

        # remove all if's
        loaded_yaml["jobs"][job].pop("if", None)

        for step in loaded_yaml["jobs"][job]["steps"]:
            step.pop("if", None)

        n = len(loaded_yaml["jobs"][job]["steps"])
        new_steps = []
        for i in range(n):
            new_steps.append(loaded_yaml["jobs"][job]["steps"][i])
            if 3 <= i < n - 1:
                new_steps.append({
                    "run": f"touch optcd-{i}.txt"
                })
        loaded_yaml["jobs"][job]["steps"] = new_steps

    return yaml.safe_dump(loaded_yaml, sort_keys=False)
