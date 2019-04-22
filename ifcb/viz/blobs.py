import numpy as np
from skimage.segmentation import find_boundaries

def blob_outline(roi_image, blob_image, outline_color=[255, 0, 0]):
    result = np.dstack([roi_image,roi_image,roi_image])
    outline = find_boundaries(blob_image)
    result[outline] = outline_color
    return result
