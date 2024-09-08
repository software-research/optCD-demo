import os
from collections import defaultdict


def classify_files(inotify_log: str) -> tuple[set[str], set[str], defaultdict[str, str]]:
    unused_files = set()
    used_files = set()
    directory_first_access = set()
    timestamps = defaultdict(str)

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

        # when a directory gets created, inotifywait logs that it gets accessed, but it is still unused regardless
        if 'CREATE' in event:
            used_files.discard(full_path)
            unused_files.add(full_path)
            timestamps[full_path] = timestamp
            if 'ISDIR' in event:
                directory_first_access.add(full_path)
        elif 'ACCESS' in event:
            if full_path in directory_first_access:
                directory_first_access.discard(full_path)
                continue
            used_files.add(full_path)
            unused_files.discard(full_path)
            timestamps.pop(full_path, None)

    return unused_files, used_files, timestamps
