# gesture.py
# All gesture detection functions used in main.py

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

    # Vertical on one arm + horizontal on the other arm = L gesture
    return (left_vertical and right_horizontal) or (right_vertical and left_horizontal)


def detect_criss_cross(lm, h, w, threshold=60):
    """
    Detect criss-cross gesture for EXIT.
    Both wrists come very close together.
    """
    lx, ly = lm[15].x * w, lm[15].y * h
    rx, ry = lm[16].x * w, lm[16].y * h

    dist = ((lx - rx) ** 2 + (ly - ry) ** 2) ** 0.5
    return dist < threshold


def detect_pause_gesture(lm, h, w):
    """
    Pause gesture:
        Both wrists ABOVE the head (landmark 0)
    """
    head_y = lm[0].y * h

    lw_y = lm[15].y * h
    rw_y = lm[16].y * h

    # Both hands above head level
    return lw_y < head_y and rw_y < head_y
