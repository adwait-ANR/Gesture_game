# pose_draw.py
# draws a full stick-figure skeleton + hip threshold lines on the frame

import cv2
import numpy as np


# Pairs of landmarks to connect with lines (stick figure)
POSE_CONNECTIONS = [
    (11, 12),   # shoulders
    (11, 23),   # left shoulder to left hip
    (12, 24),   # right shoulder to right hip
    (23, 24),   # hips line

    (11, 13), (13, 15),  # left arm
    (12, 14), (14, 16),  # right arm

    (23, 25), (25, 27),  # left leg
    (24, 26), (26, 28)   # right leg
]


def draw_stick_figure(frame, lm, h, w):
    """Draw skeleton from MediaPipe landmarks."""
    for (a, b) in POSE_CONNECTIONS:
        ax, ay = int(lm[a].x * w), int(lm[a].y * h)
        bx, by = int(lm[b].x * w), int(lm[b].y * h)
        cv2.line(frame, (ax, ay), (bx, by), (0, 255, 255), 2)

    # draw joints
    for idx in [11,12,23,24,13,14,15,16,25,26,27,28]:
        x = int(lm[idx].x * w)
        y = int(lm[idx].y * h)
        cv2.circle(frame, (x, y), 5, (0, 180, 255), -1)

    return frame


def draw_hip_thresholds(frame, logic, cfg):
    """
    Draw horizontal lines showing jump and sit thresholds.
    Base hip: logic.baseline_hip
    """
    if logic.baseline_hip is None:
        return frame

    h, w = frame.shape[:2]

    baseline = int(logic.baseline_hip)
    jump_line = baseline - cfg.JUMP_THRESHOLD
    sit_line = baseline + cfg.SIT_THRESHOLD

    # baseline
    cv2.line(frame, (0, baseline), (w, baseline), (255, 255, 0), 2)
    cv2.putText(frame, "BASELINE", (10, baseline - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

    # jump threshold
    cv2.line(frame, (0, jump_line), (w, jump_line), (0, 255, 0), 2)
    cv2.putText(frame, f"JUMP ({cfg.JUMP_THRESHOLD})", (10, jump_line - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    # sit threshold
    cv2.line(frame, (0, sit_line), (w, sit_line), (0, 0, 255), 2)
    cv2.putText(frame, f"SIT ({cfg.SIT_THRESHOLD})", (10, sit_line + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    return frame
