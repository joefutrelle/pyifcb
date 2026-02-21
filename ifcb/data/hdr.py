"""
Support for parsing IFCB header files.
"""
import ast
import fileinput
from os import PathLike
import re
import yaml

HDR = 'hdr'

# hdr attributes. these are camel-case, mapped to column names below
TEMPERATURE = 'temperature'
HUMIDITY = 'humidity'
BINARIZE_THRESHOLD = 'binarizeThreshold'
SCATTERING_PMT_SETTING = 'scatteringPhotomultiplierSetting'
FLUORESCENCE_PMT_SETTING = 'fluorescencePhotomultiplierSetting'
BLOB_SIZE_THRESHOLD = 'blobSizeThreshold'

# column name / type pairs
HDR_SCHEMA = [(TEMPERATURE, float),
              (HUMIDITY, float),
              (BINARIZE_THRESHOLD, int),
              (SCATTERING_PMT_SETTING, float),
              (FLUORESCENCE_PMT_SETTING, float),
              (BLOB_SIZE_THRESHOLD, int)]
# hdr column names
HDR_COLUMNS = ['Temp', 'Humidity', 'BinarizeThresh', 'PMT1hv(ssc)', 'PMT2hv(chl)', 'BlobSizeThresh']

CONTEXT = 'context'


def parse_alt_header(lines: list) -> dict:
    props = {}
    for line in lines:
        m = re.match(r'^run time = ([\d.]+) s\s+inhibit time = ([\d.]+)', line)
        if m:
            props['runTime'] = float(m.group(1))
            props['inhibitTime'] = float(m.group(2))
            continue
        m = re.match(r'([\d.]+) temperature,\s+([\d.]+) humidity', line)
        if m:
            props['temperature'] = float(m.group(1))
            props['humidity'] = float(m.group(2))
    return props


def parse_hdr(lines: list) -> dict:
    """
    Given the lines of a header file, return the properties in it.

    :param lines: an iterable of strings, the lines of the file
    :returns dict: the properties.
    """
    lines = [line.rstrip() for line in lines]
    if not lines:
        return {}
    if lines[0] == 'Imaging FlowCytobot Acquisition Software version 2.0; May 2010':
        if lines[1].startswith('Sample Date'):
            return parse_alt_header(lines)
        props = {CONTEXT: lines[0]}  # FIXME parse
    elif re.match(r'^[Ss]oftwareVersion:', lines[0]):
        props = {CONTEXT: lines[0]}
        for line in lines[1:]:
            try:
                k, v = re.split(r': ', line)
                try:
                    v = ast.literal_eval(v)
                except ValueError:
                    pass
                except SyntaxError:
                    pass
                props[k] = v
            except ValueError:
                # not valid RFC 822. Ignore.
                pass
    else:
        # "context" is what the text on lines 2-4 is called in the header file
        props = {CONTEXT: '\n'.join([line.strip('"') for line in lines[:-2]])}
        # now handle format variants
        if len(lines) >= 6:  # don't fail on original header format
            columns = re.split(' +', re.sub('"', '', lines[-2]))  # columns of metadata in CSV format
            values = re.split(' +', re.sub(r'[",]', ' ', lines[-1]).strip())  # values of those columns in CSV format
            # for each column take the string and cast it to the schema's column type
            for (column, (name, _), value) in zip(HDR_COLUMNS, HDR_SCHEMA, values):
                props[name] = value
    # cast any properties we know about in the schema
    for name, cast in HDR_SCHEMA:
        if name in props:
            props[name] = cast(props[name])
    return props


def _get_software_version(hdr_filepath: PathLike) -> str:
    """
    Return the software version that is within an IFCB .hdr file.

    :param hdr_filepath: A path-like string to the .hdr file.
    :return: The software version as a string. Typically, in the format of N.N.N.N representing major.minor.patch.build.
    """
    with open(hdr_filepath, 'r') as _file:
        lines = _file.readlines()
    for line in lines:
        if 'software' in line.lower():
            version = re.findall(r'([0-9.]+)', line)[0]
            return version
    raise IOError(f"Software version information not found in header: {hdr_filepath}")


def _parse_hdr(hdr_filepath: PathLike) -> dict:
    """
    Parse a .hdr file as YAML.

    :param hdr_filepath: A path-like string to the .hdr file.
    :returns dict: A dictionary containing the parsed header data.
    """

    with open(hdr_filepath, 'r') as _file:
        hdr_data = yaml.safe_load(_file)
    return hdr_data


def parse_hdr_file(path: PathLike) -> dict:
    """
    Given a path to a header file, return the header properties.

    :param path: a pathname
    :returns dict: the header properties
    :see parse_hdr
    """
    lines = list(fileinput.FileInput(path))
    return parse_hdr(lines)
