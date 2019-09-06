import os
import re

def find_product_file(directory, filename, exhaustive=False):
    candidate = os.path.join(directory, filename)
    if os.path.exists(candidate):
        return candidate
    for dir_entry in os.scandir(directory):
        fn = dir_entry.name
        if dir_entry.is_dir():
            if not exhaustive and fn not in filename:
                continue
            child_directory = os.path.join(directory, fn)
            result = find_product_file(child_directory, filename)
            if result is not None:
                return result
        elif fn == filename:
            return os.path.join(directory, filename)
    return None

def list_product_files(directory, regex):
    for dir_entry in os.scandir(directory):
        fn = dir_entry.name
        path = dir_entry.path
        if dir_entry.is_dir():
            yield from list_product_files(path, regex)
        elif re.match(regex, fn):
            yield os.path.join(directory, fn)
