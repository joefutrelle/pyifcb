from cStringIO import StringIO

from PIL import Image
import numpy as np

PIL_FORMATS_BY_MIME_TYPE = {
    'image/jpeg': 'JPEG',
    'image/png': 'PNG',
    'image/tiff': 'TIFF',
    'image/gif': 'GIF',
    'image/x-ms-bmp': 'BMP',
    'image/x-portable-pixmap': 'PPM',
    'image/x-xbitmap': 'XBM'
}

def format_image(array, mimetype='image/png'):
    """
    Represent the image in the given format and
    return the bytes of the image.

    :param array: the image
    :param mimetype: the format's MIME type

    :returns: a buffer containing the bytes, with
      seek position at 0
    """
    fmt = PIL_FORMATS_BY_MIME_TYPE[mimetype]
    buf = StringIO()
    if array.dtype == np.bool:
        array = array.astype(np.uint8)
        array *= 255
        pil = Image.fromarray(array)
        pil.save(buf, fmt)
    else:
        pil = Image.fromarray(array)
        pil.save(buf, fmt)
    buf.seek(0)
    return buf

def read_image(buf_or_filename):
    pil = Image.open(buf_or_filename)
    return np.array(pil)
