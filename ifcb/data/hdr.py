"""
Support for parsing IFCB header files.
"""

import re
import fileinput

import ast

HDR='hdr'

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

def parse_hdr(lines):
    """
    Given the lines of a header file, return the properties in it.

    :param lines: an iterable of strings, the lines of the file
    :returns dict: the properties.
    """
    lines = [line.rstrip() for line in lines]
    if not lines:
        return {}
    if lines[0] == 'Imaging FlowCytobot Acquisition Software version 2.0; May 2010':
        props = { CONTEXT: lines[0] } # FIXME parse
    elif re.match(r'^[Ss]oftwareVersion:',lines[0]):
        props = { CONTEXT: lines[0] }
        for line in lines[1:]:
            try:
                k, v = re.split(r': ',line)
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
        props = { CONTEXT: '\n'.join([line.strip('"') for line in lines[:-2]]) }
        # now handle format variants
        if len(lines) >= 6: # don't fail on original header format
            columns = re.split(' +',re.sub('"','',lines[-2])) # columns of metadata in CSV format
            values = re.split(' +',re.sub(r'[",]',' ',lines[-1]).strip()) # values of those columns in CSV format
            # for each column take the string and cast it to the schema's column type
            for (column, (name, _), value) in zip(HDR_COLUMNS, HDR_SCHEMA, values):
                props[name] = value
    # cast any properties we know about in the schema
    for name, cast in HDR_SCHEMA:
        if name in props:
            props[name] = cast(props[name])
    return props

def parse_hdr_file(path):
    """
    Given a path to a header file, return the header properties.

    :param path: a pathname
    :returns dict: the header properties
    :see parse_hdr
    """
    lines = list(fileinput.FileInput(path))
    return parse_hdr(lines)
