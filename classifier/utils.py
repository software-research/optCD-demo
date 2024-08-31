import os


def classify_files(inotify_log: str) -> tuple[set, set]:
    unused_files = set()
    used_files = set()

    for line in inotify_log.splitlines():
        timestamp, directory, filename, event = line.split(';')
        if directory.split(os.sep)[6] == '.git' or directory.split(os.sep)[6] == '.github':
            continue
        if filename == '.git' or filename == '.github':
            continue

        event = event.split(',')
        full_path = directory + filename
        if 'ISDIR' in event and filename != '':
            full_path += os.sep

        if 'CREATE' in event:
            unused_files.add(full_path)
            used_files.discard(full_path)
        elif 'ACCESS' in event:
            used_files.add(full_path)
            unused_files.discard(full_path)

    return unused_files, used_files
