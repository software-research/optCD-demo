from dateutil import parser
from bisect import bisect_right
import yaml


def get_responsible_plugins(log: str, unused_dirs: list[str], timestamps: dict[str, str], input_yaml_filename: str, job_name: str) -> list[tuple[str, str, str, str]]:
    dummy_file_timestamps = []
    for file, timestamp in timestamps.items():
        if "optcd" in file:
            dummy_file_timestamps.append(parser.isoparse(timestamp))

    run_commands_in_steps = []
    uses_in_steps = []
    names_of_steps = []
    with open(input_yaml_filename, "r") as input_yaml:
        loaded_yaml = yaml.safe_load(input_yaml)
        job_id = job_name.split("(")[0].strip()
        for step in loaded_yaml["jobs"][job_id]["steps"]:
            run_commands_in_steps.append(step.get("run"))
            uses_in_steps.append(step.get("uses"))
            names_of_steps.append(step.get("name") or step.get("uses") or step.get("run"))

    in_maven = False
    tmp_plugin_timestamps = []
    tmp_plugin_names = []
    plugin_timestamps = []
    plugin_names = []
    responsible_plugins = []
    for line in log.splitlines():
        tokens = line.split(" ")
        if "##[group]" in line and in_maven:  # maven part ended
            in_maven = False
            timestamp = parser.isoparse(tokens[0])
            tmp_plugin_timestamps.append(timestamp)
            plugin_timestamps.append(tmp_plugin_timestamps)
            plugin_names.append(tmp_plugin_names)
            tmp_plugin_timestamps = []
            tmp_plugin_names = []
            continue
        if len(tokens) < 3:
            continue
        if tokens[1] != "[INFO]" or tokens[2] != "---":
            continue
        in_maven = True
        timestamp = parser.isoparse(tokens[0])
        name = ' '.join(tokens[3:-1])
        tmp_plugin_timestamps.append(timestamp)
        tmp_plugin_names.append(name)

    for unused_dir in unused_dirs:
        if unused_dir not in timestamps:
            continue
        timestamp = parser.isoparse(timestamps[unused_dir])
        j = bisect_right(dummy_file_timestamps, timestamp)
        for k in range(len(plugin_timestamps)):
            i = bisect_right(plugin_timestamps[k], timestamp)
            if 0 < i < len(plugin_timestamps[k]):
                responsible_plugins.append((unused_dir, plugin_names[k][i - 1], run_commands_in_steps[j] or uses_in_steps[j], names_of_steps[j]))
                break
        else:
            responsible_plugins.append((unused_dir, "Not responsible by maven plugins", run_commands_in_steps[j] or uses_in_steps[j], names_of_steps[j]))

    return responsible_plugins
