from dateutil import parser
from collections import defaultdict
from bisect import bisect_right


def get_responsible_plugins(log: str, unused_dirs: list[str], timestamps: defaultdict[str, str]) -> list[tuple[str, str]]:
    plugin_timestamps = []
    plugin_names = []
    responsible_plugins = []
    for line in log.splitlines():
        tokens = line.split(" ")
        if len(tokens) != 8 or tokens[1] != "[INFO]" or tokens[2] != "---":
            continue
        timestamp = parser.isoparse(tokens[0])
        name = ' '.join(tokens[3:7])
        plugin_timestamps.append(timestamp)
        plugin_names.append(name)

    for unused_dir in unused_dirs:
        if unused_dir not in timestamps:
            continue
        timestamp = parser.isoparse(timestamps[unused_dir])
        i = bisect_right(plugin_timestamps, timestamp)
        if i > 0:
            responsible_plugins.append((unused_dir, plugin_names[i - 1]))

    return responsible_plugins
