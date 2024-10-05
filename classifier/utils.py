import os


def classify_files(inotify_log: str) -> tuple[set[str], set[str], dict[str, str]]:
    unused_files = set()
    used_files = set()
    timestamps = dict()

    for line in inotify_log.splitlines():
        timestamp, directory, filename, event = line.split(';')
        directory += os.sep

        event = event.split(',')
        full_path = directory + filename
        if 'IN_ISDIR' in event and filename != '':
            full_path += os.sep

        if 'IN_CREATE' in event:
            used_files.discard(full_path)
            unused_files.add(full_path)
            timestamps[full_path] = timestamp
        elif 'IN_ACCESS' in event:
            used_files.add(full_path)
            unused_files.discard(full_path)
            timestamps.pop(full_path, None)

    return unused_files, used_files, timestamps
