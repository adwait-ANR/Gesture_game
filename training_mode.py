# training_mode.py
# Simple helper for overlaying training info onto frames.

import cv2

def draw_training_overlay(frame, delta_hip, delta_x, cfg):
    h, w = frame.shape[:2]
    # Draw threshold lines and numeric info
    cv2.putText(frame, f'DeltaHip: {delta_hip:.1f}', (10, h-80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,0), 2)
    cv2.putText(frame, f'SIT_T: {cfg.SIT_THRESHOLD}', (10, h-55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 1)
    cv2.putText(frame, f'JUMP_T: {cfg.JUMP_THRESHOLD}', (10, h-35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
    # color band for thresholds
    cy = int(h/2)
    cv2.rectangle(frame, (0, cy - int(cfg.SIT_THRESHOLD/2)), (w, cy + int(cfg.JUMP_THRESHOLD/2)), (50,50,50), 1)
    return frame
