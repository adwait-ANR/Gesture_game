# gesture.py
# Robust gesture detection system

import time

# Internal state for criss-cross timing
_last_criss_time = 0
_criss_start_time = None


def detect_L_gesture(lm, h, w, tolerance=40):
    """
    Detect L-shape gesture for recalibration.
    One arm vertical, the other horizontal.
    """
    # Left arm
    lx_e, ly_e = lm[13].x * w, lm[13].y * h
    lx_w, ly_w = lm[15].x * w, lm[15].y * h

    # Right arm
    rx_e, ry_e = lm[14].x * w, lm[14].y * h
    rx_w, ry_w = lm[16].x * w, lm[16].y * h

    left_vertical = abs(lx_w - lx_e) < tolerance and abs(ly_w - ly_e) > 2 * tolerance
    left_horizontal = abs(ly_w - ly_e) < tolerance and abs(lx_w - lx_e) > 2 * tolerance

    right_vertical = abs(rx_w - rx_e) < tolerance and abs(ry_w - ry_e) > 2 * tolerance
    right_horizontal = abs(ry_w - ry_e) < tolerance and abs(rx_w - rx_e) > 2 * tolerance

    return (left_vertical and right_horizontal) or (right_vertical and left_horizontal)



def detect_criss_cross(lm, h, w, paused=False):
    """
    Robust criss-cross detection with:
    - Wrist close condition
    - True crossing (side swap)
    - Chest-level check
    - Elbow crossing geometry
    - Hold for 0.2s requirement
    - Cooldown of 0.6s after exit
    - Disabled while paused
    """

    global _last_criss_time, _criss_start_time

    # 🚫 Do not allow criss-cross exit when paused
    if paused:
        _criss_start_time = None
        return False, False

    now = time.time()

    # Cooldown: ignore detection for 0.6 sec
    if now - _last_criss_time < 0.6:
        return False, False

    # Wrist coordinates
    lw_x, lw_y = lm[15].x * w, lm[15].y * h
    rw_x, rw_y = lm[16].x * w, lm[16].y * h

    # Elbow coordinates
    le_x, le_y = lm[13].x * w, lm[13].y * h
    re_x, re_y = lm[14].x * w, lm[14].y * h

    # Shoulder coordinates
    lsh_x, lsh_y = lm[11].x * w, lm[11].y * h
    rsh_x, rsh_y = lm[12].x * w, lm[12].y * h
    chest_y = (lsh_y + rsh_y) / 2

    # 1️⃣ Wrist distance check
    wrist_dist = ((lw_x - rw_x)**2 + (lw_y - rw_y)**2)**0.5
    if wrist_dist > 70:   # relaxed threshold
        _criss_start_time = None
        return False, False

    # 2️⃣ True crossing geometry — side swap
    # Left wrist should be on the RIGHT side
    # Right wrist should be on the LEFT side
    if not (lw_x > rw_x):
        _criss_start_time = None
        return False, False

    # 3️⃣ Check elbow cross hint (optional but makes MUCH safer)
    # Left elbow must be to the RIGHT of right elbow (crossing arms)
    if not (le_x > re_x):
        _criss_start_time = None
        return False, False

    # 4️⃣ Must occur around chest (avoid false positives near head)
    if not (chest_y - 100 < lw_y < chest_y + 140):
        _criss_start_time = None
        return False, False
    if not (chest_y - 100 < rw_y < chest_y + 140):
        _criss_start_time = None
        return False, False

    # If we reached here → a cross is *in progress*
    # -------------------------------
    #  HOLD detection (0.2 sec stable)
    # -------------------------------
    if _criss_start_time is None:
        _criss_start_time = now
        return False, True  # show red X but do not exit

    # held long enough?
    if now - _criss_start_time >= 0.2:
        _last_criss_time = now
        _criss_start_time = None
        return True, True   # exit + show X

    return False, True  # still holding → show X



def detect_pause_gesture(lm, h, w):
    """
    Pause gesture:
        Both wrists ABOVE head (landmark 0)
    """
    head_y = lm[0].y * h

    lw_y = lm[15].y * h
    rw_y = lm[16].y * h

    return lw_y < head_y and rw_y < head_y
