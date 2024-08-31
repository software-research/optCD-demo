import os.path


def is_file(filename: str) -> bool:
    return filename[-1] != os.sep


def longest_unused_files_path_prefix(unused_files: list[str]) -> str:
    return os.path.commonpath(unused_files)


def one_deeper(path: str, filename: str) -> str:
    if not filename.startswith(path):
        return ''
    remaining_path = filename[len(path):].strip(os.sep)
    if remaining_path.count(os.sep) == 0:
        return ''
    first_dir = remaining_path.split(os.sep)[0] if remaining_path else ''
    return os.path.join(path, first_dir + os.sep)


def path_match(path: str, used_files: list[str]) -> bool:
    for used_file in used_files:
        if used_file != path and used_file.startswith(path):
            return True
    return False


def cluster_files(unused_files: list[str], used_files: list[str]) -> list[str]:
    if len(unused_files) == 0:
        return []

    paths = []
    unused_dirs = []

    if len(unused_files) == 1 and is_file(unused_files[0]):
        last_sep_index = unused_files[0].rfind(os.sep)
        paths.append(unused_files[0][:last_sep_index + 1])
    else:
        paths.append(longest_unused_files_path_prefix(unused_files))

    while len(paths):
        path = paths.pop()
        if not path_match(path, used_files):
            unused_dirs.append(path)
            continue

        for unused_file in unused_files:
            if path_match(path, [unused_file]):
                new_path = one_deeper(path, unused_file)
                if new_path == '' or is_file(new_path):
                    continue
                if new_path not in paths and new_path not in unused_dirs:
                    paths.append(new_path)

    return unused_dirs
