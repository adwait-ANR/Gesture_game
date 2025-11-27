# main.py
# Final stable version with:
# - Stick figure skeleton drawing
# - Hip baseline + SIT + JUMP lines
# - Embedded OpenCV oscilloscope graph
# - Thread-safe camera reader
# - Tkinter control panel
# - Auto + manual calibration
# - Gesture exit (hands crossed)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import time
import cv2
import numpy as np

from config import *
from camera_thread import start_camera_reader
from pose_detector import PoseDetector
from movement_logic import MovementLogic
from graph_window import EmbeddedGraph
from control_panel import ControlPanel
from training_mode import draw_training_overlay
from pose_draw import draw_stick_figure, draw_hip_thresholds
from utils import median_baseline_from_landmarks

# Optional key mapping
try:
    from pynput.keyboard import Key
    DOWN_KEY = Key.down
    UP_KEY = Key.up
except Exception:
    DOWN_KEY = 'down'
    UP_KEY = 'up'


# Build config-like object
class C: pass
cfg = C()
for name in [n for n in dir() if n.isupper()]:
    try:
        setattr(cfg, name, globals()[name])
    except:
        pass

cfg.DOWN_KEY = DOWN_KEY
cfg.UP_KEY = UP_KEY


def main():
    # --- START CAMERA THREAD ---
    stop_reader, get_frame = start_camera_reader(
        CAM_INDEX, WIDTH, HEIGHT, FLUSH_READS, CAP_PROP_BUFFERSIZE
    )

    detector = PoseDetector(
        model_complexity=MODEL_COMPLEXITY,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    )

    logic = MovementLogic(cfg)
    graph = EmbeddedGraph(max_points=300, width=300, height=100)

    # Try to start control panel
    try:
        panel = ControlPanel(cfg)
    except Exception as e:
        print("[main] control panel failed:", e)
        panel = None

    # -------- AUTO CALIBRATION ----------
    calibrated = False
    calib_samples = []
    calib_end_time = time.time() + AUTO_CALIBRATE_SECONDS

    print(f"Auto-calibrating for {AUTO_CALIBRATE_SECONDS} seconds. Stand straight.")

    try:
        while True:
            if panel:
                panel.apply_to_config()

            frame = get_frame()
            if frame is None:
                time.sleep(0.005)
                continue

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = detector.process(rgb)

            # ---------------- AUTO CALIBRATION ----------------
            if not calibrated:
                if result.pose_landmarks:
                    calib_samples.append(result.pose_landmarks.landmark)

                remaining = calib_end_time - time.time()
                if remaining > 0:
                    cv2.putText(frame, f"Calibrating... {remaining:.1f}s",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 200, 200), 2)
                else:
                    hip_base, center_base = median_baseline_from_landmarks(
                        calib_samples, WIDTH, HEIGHT
                    )
                    if hip_base:
                        logic.set_baseline(hip_base, center_base)
                        calibrated = True
                        print("[main] Baseline OK:", hip_base, center_base)
                    else:
                        print("[main] Auto calibration failed. Press C to retry.")

            # ---------------- MOVEMENT PROCESSING ----------------
            status = "idle"

            if calibrated and result.pose_landmarks:
                lm = result.pose_landmarks.landmark

                # Draw skeleton body
                frame = draw_stick_figure(frame, lm, h, w)

                # Get hip + center positions
                lh_y = lm[23].y * h
                rh_y = lm[24].y * h
                hip_y = (lh_y + rh_y) / 2.0

                lsh = lm[11].x * w
                rsh = lm[12].x * w
                center_x = (lsh + rsh) / 2.0

                # movement logic
                action, status = logic.update(hip_y, center_x)

                # deltas for graph
                hip_delta = logic.smoothed_hip - logic.baseline_hip
                center_delta = logic.smoothed_center_x - logic.baseline_center_x
                graph.push(hip_delta, center_delta)

                # training overlay
                frame = draw_training_overlay(frame, hip_delta, center_delta, cfg)

                # hip threshold visual lines
                frame = draw_hip_thresholds(frame, logic, cfg)

                # hands-cross exit
                lw_x = lm[15].x * w; lw_y = lm[15].y * h
                rw_x = lm[16].x * w; rw_y = lm[16].y * h

                if abs(lw_x - rw_x) < HAND_CROSS_DIST and abs(lw_y - rw_y) < HAND_CROSS_DIST:
                    print("Hands crossed -> exiting")
                    break

            # ---------------- RENDER GRAPH ----------------
            graph.draw_on_frame(frame, x=w - graph.width - 10, y=10)

            # Status text
            cv2.putText(frame, f"Status: {status}", (10, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow("motion-tracker", frame)

            # -------------- KEY INPUT -----------------
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            if key == ord('c'):
                # manual calibration
                samples = []
                t0 = time.time()
                while time.time() - t0 < 1.0:
                    f = get_frame()
                    if f is None: 
                        continue
                    f = cv2.flip(f, 1)

                    r = detector.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
                    if r.pose_landmarks:
                        samples.append(r.pose_landmarks.landmark)
                hip_b, cen_b = median_baseline_from_landmarks(samples, WIDTH, HEIGHT)
                if hip_b:
                    logic.set_baseline(hip_b, cen_b)
                    calibrated = True
                    print("[main] Manual calibration OK")

    except KeyboardInterrupt:
        pass
    finally:
        stop_reader()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
