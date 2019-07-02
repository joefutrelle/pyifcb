import os
import re

def find_product_file(directory, filename, exhaustive=False):
    for fn in os.listdir(directory):
        if os.path.isdir(os.path.join(directory,fn)):
            if not exhaustive and fn not in filename:
                break
            child_directory = os.path.join(directory, fn)
            result = find_product_file(child_directory, filename)
            if result is not None:
                return result
        elif fn == filename:
            return os.path.join(directory, filename)
    return None

def list_product_files(directory, regex):
    for fn in os.listdir(directory):
        path = os.path.join(directory, fn)
        if os.path.isdir(path):
            yield from list_product_files(path, regex)
        elif re.match(regex, fn):
            yield os.path.join(directory, fn)
