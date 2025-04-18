import fnmatch


def is_excluded(path, excludes):
    for pattern in excludes:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False