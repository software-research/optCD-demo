# import logger.utils
import sys
import classifier.utils
import clusterer.utils

if len(sys.argv) < 2:
    print("Usage: python local.py <filename>")
    sys.exit(1)

yaml_file = sys.argv[1]

# yaml_file_content = open(f"data/{yaml_file}", "r").read()

# f = logger.utils.modify_file_content(yaml_file_content)
# print(f)

# open(f"modified/{yaml_file}", "w").write(f)

inotify_log = open("jsql-parser-inotify-logs.csv", "r").read()
unused_files, used_files = classifier.utils.classify_files(inotify_log)

print("unused_files:")
for x in unused_files:
    print(x)
print("used_files:")
for x in used_files:
    print(x)

unused_dirs = clusterer.utils.cluster_files(list(unused_files), list(used_files))

print("unused dirs:")
for unused_dir in unused_dirs:
    print(unused_dir)