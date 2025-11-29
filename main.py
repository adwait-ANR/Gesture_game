# main.py - Final version with:
# - Win32 strong key injection
# - Robust criss-cross exit gesture with RED X overlay
# - L gesture (5s calibration)
# - Pause gesture (both hands above head)
# - Auto calibration on start
# - Stick figure + baseline lines
# - FPS counter
# - Left/right logic PRESENT but COMMENTED OUT

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import time
import cv2
import numpy as np

from config import *
from camera_thread import start_camera_reader
from pose_detector import PoseDetector
from movement_logic import MovementLogic
from pose_draw import draw_stick_figure, draw_hip_thresholds
from utils import median_baseline_from_landmarks
from gesture import detect_L_gesture, detect_criss_cross, detect_pause_gesture
from graph_window import EmbeddedGraph

from key_control import start_repeat, stop_repeat, press_hold, release_hold, USE_WIN32

# key mapping: using VK codes for strong injection
try:
    from pynput.keyboard import Key
    PYNPUT_AVAILABLE = True
except:
    PYNPUT_AVAILABLE = False


# ---------------- CONFIG OBJECT BUILD ----------------
class C:
    pass

cfg = C()
for name in [n for n in dir() if n.isupper()]:
    try:
        setattr(cfg, name, globals()[name])
    except:
        pass


# Strong-mode mapping
if USE_WIN32:
    cfg.UP_KEY = 0x26      # VK_UP
    cfg.DOWN_KEY = 0x28    # VK_DOWN
    cfg.LEFT_KEY = 0x25    # VK_LEFT   (commented)
    cfg.RIGHT_KEY = 0x27   # VK_RIGHT
else:
    if PYNPUT_AVAILABLE:
        cfg.UP_KEY = Key.up
        cfg.DOWN_KEY = Key.down
        cfg.LEFT_KEY = Key.left
        cfg.RIGHT_KEY = Key.right
    else:
        cfg.UP_KEY = "w"
        cfg.DOWN_KEY = "s"
        cfg.LEFT_KEY = "a"
        cfg.RIGHT_KEY = "d"


# ---------------- FLASH SCREEN ----------------
def show_flash_screen(frame, color, text, w, h, duration=700):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), color, -1)
    flash = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)

    cv2.putText(flash, text, (60, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 5)
    cv2.imshow("motion-tracker", flash)
    cv2.waitKey(duration)


# ---------------- L GESTURE (5-SECOND CALIBRATION) ----------------
def do_gesture_calibration(detector, get_frame, logic, w, h):
    CAL_TIME = 5.0
    print("L gesture detected -> Starting 5 second calibration...")

    samples = []
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= CAL_TIME:
            break

        f = get_frame()
        if f is None:
            continue

        f = cv2.flip(f, 1)
        remaining = int(CAL_TIME - elapsed) + 1

        overlay = f.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        f = cv2.addWeighted(overlay, 0.3, f, 0.7, 0)

        cv2.putText(f, "GESTURE CALIBRATION", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        cv2.putText(f, str(remaining), (w // 2 - 30, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6)

        progress = int((elapsed / CAL_TIME) * (w - 100))
        cv2.rectangle(f, (50, h - 60), (50 + progress, h - 20),
                      (0, 0, 255), -1)
        cv2.rectangle(f, (50, h - 60), (w - 50, h - 20),
                      (255, 255, 255), 2)

        cv2.imshow("motion-tracker", f)
        cv2.waitKey(1)

        r = detector.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        if r.pose_landmarks:
            samples.append(r.pose_landmarks.landmark)

    # Compute baseline
    hip_b, cen_b = median_baseline_from_landmarks(samples, w, h)

    frame = get_frame()
    if frame is None:
        return
    frame = cv2.flip(frame, 1)

    if hip_b is not None:
        logic.set_baseline(hip_b, cen_b)
        print("[main] Gesture calibration OK")
        show_flash_screen(frame, (0, 255, 0), "CALIBRATION OK", w, h)
    else:
        print("[main] Gesture calibration FAILED")
        show_flash_screen(frame, (0, 0, 255), "CALIBRATION FAILED", w, h)


# ---------------- MAIN ----------------
def main():

    already_closed = False

    stop_reader, get_frame = start_camera_reader(
        CAM_INDEX, WIDTH, HEIGHT,
        FLUSH_READS, CAP_PROP_BUFFERSIZE
    )

    detector = PoseDetector(
        model_complexity=MODEL_COMPLEXITY,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    )

    logic = MovementLogic(cfg)
    graph = EmbeddedGraph(max_points=300, width=300, height=100)

    calibrated = False
    calib_samples = []
    calib_end = time.time() + AUTO_CALIBRATE_SECONDS

    paused = False
    last_fps_time = time.time()
    fps = 0
    frame_count = 0

    print("Auto-calibrating for", AUTO_CALIBRATE_SECONDS, "seconds. Stand straight.")

    try:
        while True:

            frame = get_frame()
            if frame is None:
                continue
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = detector.process(rgb)

            # FPS counter
            frame_count += 1
            if time.time() - last_fps_time >= 1.0:
                fps = frame_count
                frame_count = 0
                last_fps_time = time.time()

            # ---------------- AUTO CALIBRATION ----------------
            if not calibrated:
                if result.pose_landmarks:
                    calib_samples.append(result.pose_landmarks.landmark)

                remaining = calib_end - time.time()
                if remaining > 0:
                    cv2.putText(frame, f"Calibrating... {remaining:.1f}s",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0, 200, 200), 2)
                else:
                    hip_b, cen_b = median_baseline_from_landmarks(
                        calib_samples, w, h)
                    if hip_b is not None:
                        logic.set_baseline(hip_b, cen_b)
                        calibrated = True
                        print("[main] Baseline OK:", hip_b, cen_b)
                    else:
                        print("[main] Auto calibration failed. Use L gesture.")

            status = "idle"

            # ---------------- MOVEMENT + GESTURES ----------------
            if calibrated and result.pose_landmarks:

                lm = result.pose_landmarks.landmark

                # --------- PAUSE GESTURE ---------
                if detect_pause_gesture(lm, h, w):
                    paused = not paused
                    print("PAUSED" if paused else "RESUMED")
                    time.sleep(0.6)  # debounce

                # --------- CRISS-CROSS EXIT (robust) ---------
                exit_now, show_cross = detect_criss_cross(
                    lm, h, w, paused)

                if show_cross:
                    cv2.line(frame,
                             (w // 2 - 80, h // 2 - 80),
                             (w // 2 + 80, h // 2 + 80),
                             (0, 0, 255), 8)
                    cv2.line(frame,
                             (w // 2 + 80, h // 2 - 80),
                             (w // 2 - 80, h // 2 + 80),
                             (0, 0, 255), 8)

                if exit_now:
                    print("Criss-cross gesture HELD x Exiting safely.")
                    try:
                        stop_repeat(cfg.UP_KEY)
                        stop_repeat(cfg.DOWN_KEY)
                    except:
                        pass
                    try:
                        release_hold(cfg.UP_KEY)
                        release_hold(cfg.DOWN_KEY)
                    except:
                        pass

                    stop_reader()
                    try:
                        detector.close()
                    except:
                        pass
                    cv2.destroyAllWindows()
                    already_closed = True
                    return

                # --------- IF NOT PAUSED → PROCESS MOVEMENT ---------
                if not paused:

                    frame = draw_stick_figure(frame, lm, h, w)

                    lh_y = lm[23].y * h
                    rh_y = lm[24].y * h
                    hip_y = (lh_y + rh_y) / 2.0

                    lsh = lm[11].x * w
                    rsh = lm[12].x * w
                    center_x = (lsh + rsh) / 2.0

                    action, status = logic.update(hip_y, center_x)

                    frame = draw_hip_thresholds(frame, logic, cfg)

                    # --------- L-GESTURE RECALIBRATE ---------
                    if detect_L_gesture(lm, h, w):
                        do_gesture_calibration(
                            detector, get_frame, logic, w, h)
                        continue

                    # --------- LEFT/RIGHT (commented out) ---------
                    """
                    if center_x < logic.baseline_center_x - LEAN_MARGIN:
                        start_repeat(cfg.LEFT_KEY)
                    elif center_x > logic.baseline_center_x + LEAN_MARGIN:
                        start_repeat(cfg.RIGHT_KEY)
                    else:
                        stop_repeat(cfg.LEFT_KEY)
                        stop_repeat(cfg.RIGHT_KEY)
                    """

            # ---------------- HUD ----------------
            cv2.putText(frame, f"Status: {status}",
                        (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 0), 2)

            cv2.putText(frame, f"FPS: {fps}",
                        (w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (200, 200, 0), 2)

            cv2.imshow("motion-tracker", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        if not already_closed:
            stop_reader()
            try:
                detector.close()
            except:
                pass
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
