import os
import sys
import yaml
import logger.utils


def main():
    input_yaml_filename = sys.argv[1]
    output_yaml_filename = sys.argv[2]
    repo = sys.argv[3]

    if len(sys.argv) != 4:
        print("Usage: python modify_yaml.py <yaml_filename> <output_filename> <repo>")
        sys.exit(1)

    if not os.path.isfile(input_yaml_filename):
        print("Please provide a valid YAML file.")
        sys.exit(1)

    with open(input_yaml_filename, "r") as f:
        loaded_yaml = yaml.safe_load(f)
        modified_file = logger.utils.modify_file_content(repo, loaded_yaml)
        print(modified_file)

        with open(output_yaml_filename, "w+") as output:
            output.write(modified_file)


if __name__ == '__main__':
    main()
