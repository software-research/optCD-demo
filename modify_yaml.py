import os
import sys
import yaml
import logger.utils


def main():
    if len(sys.argv) != 4:
        print("Usage: python modify_yaml.py <yaml_filename> <output_filename> <repo>")
        sys.exit(1)

    input_yaml_filename = sys.argv[1]
    output_yaml_filename = sys.argv[2]
    repo = sys.argv[3]

    if not os.path.isfile(input_yaml_filename):
        print("Please provide a valid YAML file.")
        sys.exit(1)

    with open(input_yaml_filename, "r") as f:
        loaded_yaml = yaml.safe_load(f)
        f.seek(0)
        comments = []
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                comments.append(line)

        modified_file = logger.utils.modify_file_content(repo, loaded_yaml)
        print(modified_file)

        with open(output_yaml_filename, "w") as output:
            for comment in comments:
                output.write(comment + "\n")
            output.write("\n")
            output.write(modified_file)


if __name__ == '__main__':
    main()
