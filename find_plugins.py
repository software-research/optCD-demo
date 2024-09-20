import sys
import classifier.utils
import clusterer.utils
import mapper.utils

if len(sys.argv) != 3:
    print("Usage: find_plugins.py <inotify_log_filename> <workflow_log_filename>")
    sys.exit(1)

inotify_log_filename = sys.argv[1]
workflow_log_filename = sys.argv[2]

with open(inotify_log_filename, "r") as f:
    inotify_log = f.read()

    unused_files, used_files, timestamps = classifier.utils.classify_files(inotify_log)
    unused_dirs = clusterer.utils.cluster_files(list(unused_files), list(used_files))

    with open(workflow_log_filename, "r") as w:
        workflow_log = w.read()
        responsible_plugins = mapper.utils.get_responsible_plugins(workflow_log, unused_dirs, timestamps)
        for unused_dir, responsible_plugin in responsible_plugins:
            print(unused_dir, responsible_plugin)
