import sys
import logger.utils
import classifier.utils
import clusterer.utils


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <yaml-file>")
        sys.exit(1)
    yaml_file_path = sys.argv[1]
    yaml_file_content = logger.utils.get_file_content(yaml_file_path)

    modified_file = logger.utils.modify_file_content(yaml_file_content)
    print(modified_file)

    # run modified yaml file
    # get inotify-logs.csv

    inotify_log = open("logs/inotify-logs.csv", "r").read()
    unused_files, used_files, timestamps = classifier.utils.classify_files(inotify_log)

    print("unused_files:")
    for unused_file in unused_files:
        print(unused_file)
    print("used_files:")
    for used_file in used_files:
        print(used_file)

    unused_dirs = clusterer.utils.cluster_files(list(unused_files), list(used_files))

    for unused_dir in unused_dirs:
        print(unused_dir)


if __name__ == '__main__':
    main()
