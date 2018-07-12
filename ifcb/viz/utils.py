import numpy as np
from skimage.transform import rescale, resize

SQUARE_DEFAULT_SIZE = 399

def square(img, size=SQUARE_DEFAULT_SIZE):
    scaled = resize(img, (size, size), mode='reflect', preserve_range=True).astype(np.uint8)
    return scaled

def square_letterboxed(img, size=SQUARE_DEFAULT_SIZE, fill_value='median'):
    if fill_value == 'median':
        fill_value = int(np.median(img))
    elif fill_value == 'mean':
        fill_value = int(np.mean(img))
    scale = 1.0 * size / max(img.shape)
    scaled = rescale(img, scale, mode='reflect', preserve_range=True).astype(np.uint8)
    h, w = scaled.shape
    ctr = size / 2
    letterboxed = np.zeros((size, size), dtype=np.uint8) + fill_value
    y = int(ctr - h/2)
    x = int(ctr - w/2)
    letterboxed[y:y+h,x:x+w] = scaled
    return letterboxed