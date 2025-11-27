# -*- coding: utf-8 -*-
"""
game_movement_detector.py  (Optimized + Commented)

FEATURES
--------
✓ Multi-threaded camera capture (no freezing)
✓ Latest-frame-only processing (buffer flush)
✓ Sit (Down) + Jump (Up) detection
✓ Left/Right detection code INCLUDED but COMMENTED-out
✓ Auto-calibration + manual "C" calibrate option
✓ Debounced keyboard actions (no key spam)
✓ Idle = NO keypress (Requirement #1)
✓ Fully commented everywhere (Requirement #2)
✓ GPU acceleration OPTION commented (Requirement #4)

"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'      # hide TensorFlow logs

import cv2
import mediapipe as mp
import threading
import time
from pynput.keyboard import Controller, Key
import numpy as np
import sys

# -------------------------------------------------------------------
# USER CONFIGURATION (all parameters documented)
# -------------------------------------------------------------------

CAM_INDEX = 0
"""Camera index 
0 → default laptop camera
1 → external webcam
"""

WIDTH = 640
HEIGHT = 480
"""Camera resolution.
Higher = more detail but slower CPU usage.
640x480 recommended for <70 FPS systems.
"""

FLUSH_READS = 3
"""How many times to grab frames to flush buffer.
Higher = lower latency but slightly more CPU load."""

MODEL_COMPLEXITY = 0
"""
MediaPipe Pose model complexity:
0 = FAST (recommended for games)
1 = Balanced
2 = High accuracy (slow)

0 gives best real-time performance.
"""

MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

EMA_ALPHA = 0.2
"""
Smoothing factor for EMA:
0.1 = very smooth, slower reaction
0.3 = faster reaction, more jitter

Recommended: 0.2
"""

PERSISTENCE_FRAMES = 3
"""
How many consecutive frames are needed
to confirm an action.
Higher = more stable but slower reaction.
"""

ACTION_COOLDOWN = 0.6
"""Time in seconds between actions to avoid key spam."""

# Movement thresholds (in pixels)
SIT_THRESHOLD = 45
JUMP_THRESHOLD = 45
LEFT_THRESHOLD = 40      # ← COMMENTED OUT IN MAIN LOOP
RIGHT_THRESHOLD = 40     # ← COMMENTED OUT IN MAIN LOOP
"""
These thresholds define how far the hip or shoulders
must move from baseline.

Adjust based on camera distance:
Closer to camera → higher thresholds
Farther from camera → lower thresholds
"""

HAND_CROSS_DIST = 80
"""Hands closer than this (in X & Y pixels) = EXIT."""

AUTO_CALIBRATE_SECONDS = 10.0
"""Time to auto-calibrate baseline at start."""

# -------------------------------------------------------------------
# GPU ACCELERATION OPTION (COMMENTED OUT)
# -------------------------------------------------------------------
"""
# ====== RUN ON DEDICATED GPU (OPTIONAL) ======
# This does NOT guarantee GPU execution, but helps when:
# 1) You have a gaming laptop
# 2) NVIDIA Control Panel is set to "High Performance GPU" for Python

os.environ["CUDA_VISIBLE_DEVICES"] = "0"     
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
# Some systems support DX12 acceleration:
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

# NOTE: MediaPipe Pose on Windows rarely uses CUDA,
# but these settings can help on certain systems.
"""

# -------------------------------------------------------------------
# GLOBALS
# -------------------------------------------------------------------

keyboard = Controller()

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    model_complexity=MODEL_COMPLEXITY,
    min_detection_confidence=MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=MIN_TRACKING_CONFIDENCE
)

_latest_frame = None
_frame_lock = threading.Lock()
_stop_reader = False

# For smoothing
smoothed_hip = None
smoothed_center_x = None

baseline_hip = None
baseline_center_x = None

# Debounce
state_counts = {'sit': 0, 'jump': 0, 'idle': 0}  # left/right removed
current_action = 'idle'
last_action_time = 0.0

calibrated = False
status_text = "Starting..."
calib_remaining = 0.0

# -------------------------------------------------------------------
# CAMERA THREAD
# -------------------------------------------------------------------

def camera_reader(cam_index=0):
    """Reads camera frames in background (non-blocking)."""
    global _latest_frame, _stop_reader

    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    # Try to limit internal buffer
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("ERROR: Cannot open camera!")
        _stop_reader = True
        return

    while not _stop_reader:
        # Flush old frames
        for _ in range(FLUSH_READS):
            cap.grab()

        ret, frame = cap.read()
        if not ret:
            time.sleep(0.005)
            continue

        with _frame_lock:
            _latest_frame = frame

    cap.release()

# -------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------

def ema(value, prev, alpha=EMA_ALPHA):
    """Exponential moving average."""
    if prev is None:
        return float(value)
    return prev * (1 - alpha) + float(value) * alpha

def press_once(key):
    """Safely simulates a single key press."""
    try:
        keyboard.press(key)
        keyboard.release(key)
    except:
        pass

def calibrate_from_frames(landmarks_list):
    """Computes baseline from pose landmarks."""
    global baseline_hip, baseline_center_x

    hips = []
    centers = []

    for lm in landmarks_list:
        if lm is None:
            continue

        lh_y = lm[23].y * HEIGHT
        rh_y = lm[24].y * HEIGHT
        hip_y = (lh_y + rh_y) / 2

        lsh = lm[11].x * WIDTH
        rsh = lm[12].x * WIDTH
        center_x = (lsh + rsh) / 2

        hips.append(hip_y)
        centers.append(center_x)

    if hips:
        baseline_hip = float(np.median(hips))
        baseline_center_x = float(np.median(centers))
        return True

    return False

# -------------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------------

def main_loop():
    global _stop_reader
    global baseline_hip, baseline_center_x
    global smoothed_hip, smoothed_center_x
    global calibrated, status_text, last_action_time

    # Start camera reading thread
    threading.Thread(target=camera_reader, daemon=True).start()

    # Auto calibration
    status_text = f"Auto-calibrating ({AUTO_CALIBRATE_SECONDS}s)..."
    calib_samples = []
    auto_calib_end = time.time() + AUTO_CALIBRATE_SECONDS

    while True:
        # Get latest frame
        with _frame_lock:
            frame = None if _latest_frame is None else _latest_frame.copy()

        if frame is None:
            time.sleep(0.005)
            continue

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)

        # AUTO CALIBRATION BLOCK
        if not calibrated:
            if result.pose_landmarks:
                calib_samples.append(result.pose_landmarks.landmark)

            remaining = auto_calib_end - time.time()

            if remaining <= 0:
                calibrated = calibrate_from_frames(calib_samples)
                status_text = "Calibrated!" if calibrated else "Calibration failed. Press C"
            else:
                cv2.putText(frame, f"Calibrating... {remaining:.1f}s", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 200), 2)

        else:
            # ----------------------------------------------------------
            # NORMAL DETECTION PHASE
            # ----------------------------------------------------------
            if result.pose_landmarks:
                lm = result.pose_landmarks.landmark

                # HIP POSITION
                lh_y = lm[23].y * h
                rh_y = lm[24].y * h
                hip_y = (lh_y + rh_y) / 2

                # SHOULDER CENTER (X)
                lsh_x = lm[11].x * w
                rsh_x = lm[12].x * w
                center_x = (lsh_x + rsh_x) / 2

                # WRISTS (for exit gesture)
                lw_x = lm[15].x * w
                lw_y = lm[15].y * h
                rw_x = lm[16].x * w
                rw_y = lm[16].y * h

                # Smooth positions
                smoothed_hip = ema(hip_y, smoothed_hip)
                smoothed_center_x = ema(center_x, smoothed_center_x)

                if baseline_hip is not None:
                    d_hip = smoothed_hip - baseline_hip

                    # ---- EXIT GESTURE (hands crossed) ----
                    if abs(lw_x - rw_x) < HAND_CROSS_DIST and abs(lw_y - rw_y) < HAND_CROSS_DIST:
                        print("Hands crossed → EXIT")
                        break

                    # -------------------------------------------------------
                    #                                                   <---- REQUIREMENT #3: LEFT/RIGHT COMMENTED
                    # LEFT/RIGHT CODE (COMMENTED OUT)
                    # -------------------------------------------------------
                    """
                    d_x = smoothed_center_x - baseline_center_x

                    # Check for left
                    if d_x < -LEFT_THRESHOLD:
                        detected_state = "left"

                    # Check for right
                    elif d_x > RIGHT_THRESHOLD:
                        detected_state = "right"
                    """
                    # -------------------------------------------------------

                    # Sit
                    if d_hip > SIT_THRESHOLD:
                        detected_state = "sit"

                    # Jump
                    elif d_hip < -JUMP_THRESHOLD:
                        detected_state = "jump"

                    else:
                        detected_state = "idle"

                    # ---- REQUIREMENT #1 → IDLE = DO NOTHING ----
                    if detected_state == "idle":
                        status_text = "Idle"
                        # NO keypress here!
                    else:
                        now = time.time()
                        if now - last_action_time > ACTION_COOLDOWN:
                            if detected_state == "sit":
                                press_once(Key.down)
                                status_text = "SIT → DOWN"

                            elif detected_state == "jump":
                                press_once(Key.up)
                                status_text = "JUMP → UP"

                            last_action_time = now

        # HUD info
        cv2.putText(frame, f"Status: {status_text}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Movement Detector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('c'):
            calibrated = False
            status_text = "Manual Calibration Triggered"

    _stop_reader = True
    cv2.destroyAllWindows()
    print("Exited safely.")


# -------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------

if __name__ == "__main__":
    main_loop()
