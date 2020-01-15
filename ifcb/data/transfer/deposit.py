import os
from glob import glob
import re
from shutil import copyfile

def safe_remove_file(path):
    # remove a file if it exists
    # returns None if no action taken,
    # True if success, False if failure
    if not os.path.exists(path):
        return None
    try:
        os.remove(path)
        return True # successfully removed
    except:
        # something went wrong
        return False

def safe_copy_file(source_path, destination_dir, if_not_exists=True):
    # copy a file atomically
    # returns None if no action taken,
    # True if success, False if failure
    basename = os.path.basename(source_path)
    destination_path = os.path.join(destination_dir, basename)
    if if_not_exists and os.path.exists(destination_path):
        # take no action in this case
        return None
    # create a temporary path to copy the file to
    tmp_path = destination_path + '.copy'
    try:
        copyfile(source_path, tmp_path)
    except:
        # copying failed, remove temporary file
        safe_remove_file(tmp_path)
        return False
    # done copying, rename temp file to destination name
    try:
        os.rename(tmp_path, destination_path)
        return True
    except:
        # renaming failed. remove temp file
        safe_remove_file(tmp_path)
        return False

def copy_fileset(hdr_path, adc_path, roi_path, dest_dir):
    # copy a set of hdr/adc/roi files
    hdr_copied = safe_copy_file(hdr_path, dest_dir)
    adc_copied = safe_copy_file(adc_path, dest_dir)
    roi_copied = safe_copy_file(roi_path, dest_dir)
    # return True if success, False otherwise
    return hdr_copied and adc_copied and roi_copied

def change_extension(path, new_extension):
    base_path, extension = os.path.splitext(path)
    return '{}.{}'.format(base_path, new_extension)

def fileset_destination_dir(hdr_path):
    # compute the destination dir for an IFCB file
    # based on year and yearday. Note: does not work
    # for old-style IFCB files whose names start "IFCB"
    basename = os.path.basename(hdr_path)
    year = re.match(r'D(....)', basename).group(1)
    yearday = re.match(r'(D........)', basename).group(1)
    return os.path.join(year, yearday)

def copy_all(source_dir, dest_dir):
    # given a source dir which is a flat structure containing hdr/adc/roi files,
    # copy the files into {dest_dir}/{year}/{yearday} directories
    for hdr_path in sorted(glob(os.path.join(source_dir, '*.hdr'))):
        adc_path = change_extension(hdr_path, 'adc')
        roi_path = change_extension(hdr_path, 'roi')
        if not os.path.exists(adc_path) or not os.path.exists(roi_path):
            # fileset is incomplete, skip
            continue
        dest_dir_suffix = fileset_destination_dir(hdr_path)
        dest_daydir = os.path.join(dest_dir, dest_dir_suffix)
        # make sure the destination year/day directory exists
        os.makedirs(dest_daydir, exist_ok=True)
        # now copy the fileset
        copy_fileset(hdr_path, adc_path, roi_path, dest_daydir)
