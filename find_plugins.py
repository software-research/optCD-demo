import sys
import classifier.utils
import clusterer.utils
import mapper.utils
from tabulate import tabulate


def main():
    if len(sys.argv) != 4:
        print("Usage: find_plugins.py <inotify_log_filename> <workflow_log_filename> <output_file>")
        sys.exit(1)

    inotify_log_filename = sys.argv[1]
    workflow_log_filename = sys.argv[2]
    output_file = sys.argv[3]

    with open(inotify_log_filename, "r") as f:
        inotify_log = f.read()

        unused_files, used_files, timestamps = classifier.utils.classify_files(inotify_log)
        unused_dirs = clusterer.utils.cluster_files(list(unused_files), list(used_files))

        with open(workflow_log_filename, "r") as w:
            workflow_log = w.read()
            responsible_plugins = mapper.utils.get_responsible_plugins(workflow_log, unused_dirs, timestamps)

            headers = ["Unused directory", "Responsible plugin"]
            tbl = tabulate(responsible_plugins, headers=headers, tablefmt="fancy_grid") + "\n\n"

            if output_file != "":
                with open(output_file, "a") as output:
                    output.write(tbl)
            else:
                print(tbl)


if __name__ == '__main__':
    main()