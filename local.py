import utils
import sys

if len(sys.argv) < 2:
    print("Usage: python local.py <filename>")
    sys.exit(1)

yaml_file = sys.argv[1]

yaml_file_content = open(f"data/{yaml_file}", "r").read()

f = utils.modify_file_content(yaml_file_content)
print(f)

open(f"modified/{yaml_file}", "w").write(f)