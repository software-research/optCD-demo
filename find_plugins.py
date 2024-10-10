import sys
import os
import classifier.utils
import clusterer.utils
import mapper.utils
from tabulate import tabulate
import json


def main():
    if len(sys.argv) != 6:
        print("Usage: find_plugins.py <inotify_log_filename> <workflow_log_filename> <output_file> <input_yaml_filename> <job_name>")
        sys.exit(1)

    inotify_log_filename = sys.argv[1]
    workflow_log_filename = sys.argv[2]
    output_file = sys.argv[3]
    input_yaml_filename = sys.argv[4]
    job_name = sys.argv[5]

    if not os.path.isfile(inotify_log_filename):
        print("Inotify log does not exist.")
        if output_file != "":
            with open(output_file, "a") as output:
                output.write("Inotify log does not exist.\n")
        sys.exit(1)

    with open(inotify_log_filename, "r") as f:
        inotify_log = f.read()

        unused_files, used_files, timestamps = classifier.utils.classify_files(inotify_log)
        unused_dirs = clusterer.utils.cluster_files(list(unused_files), list(used_files))

        with open(workflow_log_filename, "r") as w:
            workflow_log = w.read()
            responsible_plugins = mapper.utils.get_responsible_plugins(workflow_log, unused_dirs, timestamps, input_yaml_filename, job_name)
            responsible_plugins.sort(key=lambda x: x[1], reverse=True)

            headers = ["Unused directory", "Responsible plugin", "Responsible command", "Name of the step"]
            tbl = tabulate(responsible_plugins, headers=headers, tablefmt="fancy_grid") + "\n"

            # dump as json
            responsible_plugins_maven = []
            for unused_dir, responsible_plugin, responsible_command, step_name in responsible_plugins:
                if responsible_plugin != "Not responsible by maven plugins":
                    responsible_plugins_maven.append({
                        "Unused directory": unused_dir,
                        "Responsible plugin": responsible_plugin,
                        "Responsible command": responsible_command,
                        "Name of the step": step_name
                    })
            with open("responsible_plugins.json", "w") as output:
                json.dump(responsible_plugins_maven, output, indent=2)

            if output_file != "":
                with open(output_file, "a") as output:
                    output.write(tbl)
            else:
                print(tbl)


if __name__ == '__main__':
    main()