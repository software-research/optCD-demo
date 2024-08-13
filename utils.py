import os
import requests
import base64
import re

owner = os.environ['GITHUB_REPOSITORY'].split('/')[0]
repo = os.environ['GITHUB_REPOSITORY'].split('/')[1]
token: str = os.environ['GITHUB_TOKEN']
base_api_url: str = "https://api.github.com"
headers: dict = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28"
}


def get_file_content(yaml_file_path: str) -> str:
    url = f"{base_api_url}/repos/{owner}/{repo}/contents/{yaml_file_path}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.text)
    return base64.b64decode(response.json()['content']).decode('utf-8')


def add_set_up_python_and_dependencies(modified_file: str, indent: int, python_version: str) -> str:
    modified_file += " " * indent + "- uses: actions/setup-python@v5\n"
    modified_file += " " * (indent + 2) + "with:\n"
    modified_file += " " * (indent + 4) + f"python-version: '{python_version}'\n"
    modified_file += " " * indent + "- name: Install dependencies\n"
    modified_file += " " * (indent + 2) + "run: |\n"
    modified_file += " " * (indent + 4) + "python -m pip install --upgrade pip\n"
    modified_file += " " * (indent + 4) + "pip install pandas\n"
    modified_file += " " * (indent + 4) + "pip install numpy\n"
    modified_file += " " * indent + "- run: sudo apt update\n"
    modified_file += " " * indent + "- run: sudo apt install inotify-tools\n"
    modified_file += " " * indent + f"- run: inotifywait -dmr /home/runner/work/{owner}/{repo}/ --format '%T;%w;%f;%e' --timefmt '%T' -o /home/runner/inotify-logs.csv\n"
    return modified_file


def add_push_results_to_another_repository(modified_file: str, indent: int) -> str:
    modified_file += " " * indent + "- name: add code to push results to another repository\n"
    return modified_file


def get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def handle_if(modified_file: str, initial_file: list[str], current_line: int) -> (str, int):
    line = initial_file[current_line]

    dash_if_pattern = r"\s*-\s+if\s*:"  # matches - if:
    dash_if_regex = re.compile(dash_if_pattern)

    # if indent - dash indent - 1 == spaces after -

    if dash_if_regex.match(line):  # " - if"
        current_line += 1
        dash_indent = get_indent(line)
        if_indent = line.index("i")

        while current_line < len(initial_file) and if_indent < get_indent(initial_file[current_line]):
            # string in the multiline block if multiline, otherwise won't enter this loop
            current_line += 1

        first_to_be_added = True
        while current_line < len(initial_file) and if_indent <= get_indent(initial_file[current_line]):
            # other key value pairs in the object
            if first_to_be_added:
                modified_file += " " * dash_indent + "-" + " " * (if_indent - dash_indent - 1)
                modified_file += initial_file[current_line].lstrip() + "\n"
                current_line += 1
                first_to_be_added = False
                continue
            modified_file += initial_file[current_line] + "\n"
            current_line += 1

        return modified_file, current_line

    current_line += 1
    if_indent = get_indent(line)
    while current_line < len(initial_file) and if_indent < get_indent(initial_file[current_line]):
        current_line += 1  # skip everything in if block for multilines
    return modified_file, current_line


def handle_on(modified_file: str, initial_file: list[str], current_line: int) -> (str, int):
    on_indent = get_indent(initial_file[current_line])
    modified_file += " " * on_indent + "on: [push]\n"  # we only need on: [push]
    current_line += 1
    while current_line < len(initial_file) and on_indent < get_indent(initial_file[current_line]):  # while in "on"
        current_line += 1
    return modified_file, current_line


def handle_steps(modified_file: str, initial_file: list[str], current_line: int) -> (str, int, int, int, bool):
    if current_line + 1 >= len(initial_file):
        raise Exception("Invalid YAML file, steps field is null")

    steps_indent = get_indent(initial_file[current_line])
    steps_dashes_indent = get_indent(initial_file[current_line + 1])

    modified_file += initial_file[current_line] + "\n"
    modified_file = add_set_up_python_and_dependencies(modified_file, steps_dashes_indent, "3.10")
    current_line += 1

    return modified_file, current_line, steps_indent, steps_dashes_indent, True


def modify_file_content(yaml_file_content: str) -> str:
    modified_file = ""

    initial_file = yaml_file_content.split("\n")  # filter out empty lines and comment lines
    initial_file = list(filter(lambda _line: len(_line.strip()) != 0 and _line.strip()[0] != "#", initial_file))

    steps_indent = -1
    steps_dashes_indent = -1
    in_step = False
    current_line = 0

    if_pattern = r"\s*-\s+if\s*:|\s*if\s*:"  # match - if:  or  if:
    if_regex = re.compile(if_pattern)

    on_pattern = r"\s*on\s*:"  # match on:
    on_regex = re.compile(on_pattern)

    steps_pattern = r"\s*steps\s*:"  # match steps:
    steps_regex = re.compile(steps_pattern)

    while current_line < len(initial_file):
        line = initial_file[current_line]
        line_indent = get_indent(line)

        if in_step and line_indent <= steps_indent and line.strip()[0] != "-":  # step block ends
            in_step = False
            modified_file = add_push_results_to_another_repository(modified_file, steps_dashes_indent)

        if if_regex.match(line):  # "if" block
            modified_file, current_line = handle_if(modified_file, initial_file, current_line)
            continue

        if on_regex.match(line):  # "on" block
            modified_file, current_line = handle_on(modified_file, initial_file, current_line)
            continue

        if steps_regex.match(line):  # "steps" - add prefix steps
            modified_file, current_line, steps_indent, steps_dashes_indent, in_step = handle_steps(modified_file,
                                                                                                   initial_file,
                                                                                                   current_line)
            continue

        # by default, simply add the line
        modified_file += initial_file[current_line] + "\n"
        current_line += 1

    if in_step:
        modified_file = add_push_results_to_another_repository(modified_file, steps_dashes_indent)

    return modified_file
