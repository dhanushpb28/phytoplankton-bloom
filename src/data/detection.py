import numpy as np

def detect_bloom(chl, threshold):
    return chl > threshold

def classify_intensity(chl):
    return np.where(
        chl < 1, 0,
        np.where(chl < 5, 1, 2)
    )
