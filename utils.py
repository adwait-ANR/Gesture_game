# utils.py
# Utility functions: EMA smoothing, keypress, calibration helpers

import time
import numpy as np
from pynput.keyboard import Controller

keyboard = Controller()

def press_once(key):
    """Press and release a key once."""
    try:
        keyboard.press(key)
        keyboard.release(key)
    except Exception as e:
        # In headless or restricted environments this can fail silently
        print("[utils] key press failed:", e)

def ema(value, prev, alpha):
    if prev is None:
        return float(value)
    return prev * (1 - alpha) + float(value) * alpha

def median_baseline_from_landmarks(landmarks, width, height):
    """Compute median baseline hip and shoulder-center from collected landmarks."""
    hips = []
    centers = []
    for lm in landmarks:
        if lm is None:
            continue
        lh_y = lm[23].y * height
        rh_y = lm[24].y * height
        hip_y = (lh_y + rh_y) / 2.0
        lsh = lm[11].x * width
        rsh = lm[12].x * width
        center_x = (lsh + rsh) / 2.0
        hips.append(hip_y)
        centers.append(center_x)
    if len(hips) == 0:
        return None, None
    return float(np.median(hips)), float(np.median(centers))
