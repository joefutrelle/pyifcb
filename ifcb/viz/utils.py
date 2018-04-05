import numpy as np
from skimage.io import imread, imsave
from skimage.transform import rescale

SQUARE_LETTERBOXED_DEFAULT_SIZE = 399

def square_letterboxed(img, size=SQUARE_LETTERBOXED_DEFAULT_SIZE, fill_value='median'):
    if fill_value == 'median':
        fill_value = int(np.median(img))
    elif fill_value == 'mean':
        fill_value = int(np.mean(img))
    scale = 1.0 * size / max(img.shape)
    scaled = rescale(img, scale, mode='reflect', preserve_range=True)
    h, w = scaled.shape
    ctr = size / 2
    letterboxed = np.zeros((size, size), dtype=np.uint8) + fill_value
    y = int(ctr - h/2)
    x = int(ctr - w/2)
    letterboxed[y:y+h,x:x+w] = scaled
    return letterboxed