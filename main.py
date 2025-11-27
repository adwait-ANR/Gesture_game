# main.py
# Top-level script with embedded graph rendering (no Matplotlib GUI threads)

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import time
import cv2
from config import *
from camera_thread import start_camera_reader
from pose_detector import PoseDetector
from movement_logic import MovementLogic
from graph_window import EmbeddedGraph
from control_panel import ControlPanel
from training_mode import draw_training_overlay
from utils import median_baseline_from_landmarks
import numpy as np

# Optional: map keys in config namespace
try:
    from pynput.keyboard import Key
    DOWN_KEY = Key.down
    UP_KEY = Key.up
except Exception:
    DOWN_KEY = 'down'
    UP_KEY = 'up'

# Create a lightweight config object for modules to mutate
class C: pass
cfg = C()
for name in [n for n in dir() if n.isupper()]:
    try:
        setattr(cfg, name, globals()[name])
    except Exception:
        pass

# attach key constants to cfg (movement_logic expects cfg.DOWN_KEY / UP_KEY)
cfg.DOWN_KEY = DOWN_KEY
cfg.UP_KEY = UP_KEY

def main():
    stop_reader, get_frame = start_camera_reader(CAM_INDEX, WIDTH, HEIGHT, FLUSH_READS, CAP_PROP_BUFFERSIZE)
    detector = PoseDetector(model_complexity=MODEL_COMPLEXITY,
                            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
                            min_tracking_confidence=MIN_TRACKING_CONFIDENCE)
    logic = MovementLogic(cfg)
    graph = EmbeddedGraph(max_points=300, width=300, height=100)

    # control panel may fail in some environments; keep optional
    try:
        panel = ControlPanel(cfg)
    except Exception as e:
        print('[main] control panel failed to start:', e)
        panel = None

    # auto-calibrate
    calibrated = False
    calib_samples = []
    calib_end = time.time() + AUTO_CALIBRATE_SECONDS
    print('Auto-calibrating for', AUTO_CALIBRATE_SECONDS, 's - stand straight facing camera.')

    try:
        while True:
            if panel is not None:
                panel.apply_to_config()
            frame = get_frame()
            if frame is None:
                time.sleep(0.005)
                continue
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = detector.process(rgb)

            status = 'starting'
            if not calibrated:
                if res.pose_landmarks:
                    calib_samples.append(res.pose_landmarks.landmark)
                if time.time() >= calib_end:
                    hip_base, center_base = median_baseline_from_landmarks(calib_samples, WIDTH, HEIGHT)
                    if hip_base is not None:
                        logic.set_baseline(hip_base, center_base)
                        calibrated = True
                        status = 'calibrated'
                        print('[main] calibrated baseline:', hip_base, center_base)
                    else:
                        print('[main] calibration failed - use C for manual calibration')
                        status = 'need_calibration'
                else:
                    remaining = max(0.0, calib_end - time.time())
                    cv2.putText(frame, f'Calibrating... {remaining:.1f}s', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,200,200), 2)
            else:
                if res.pose_landmarks:
                    lm = res.pose_landmarks.landmark
                    lh_y = lm[23].y * h
                    rh_y = lm[24].y * h
                    hip_y = (lh_y + rh_y) / 2.0
                    lsh = lm[11].x * w
                    rsh = lm[12].x * w
                    center_x = (lsh + rsh) / 2.0

                    action, status_text = logic.update(hip_y, center_x)
                    # ensure status_text defined
                    status = status_text if status_text is not None else 'idle'

                    # push deltas into embedded graph
                    hip_delta = (logic.smoothed_hip - logic.baseline_hip) if logic.baseline_hip is not None else 0.0
                    center_delta = (logic.smoothed_center_x - logic.baseline_center_x) if logic.baseline_center_x is not None else 0.0
                    graph.push(hip_delta, center_delta)

                    # draw training overlay if needed (always on for now)
                    frame = draw_training_overlay(frame, hip_delta, center_delta, cfg)

                    # exit gesture: hands close
                    lw_x = lm[15].x * w; lw_y = lm[15].y * h
                    rw_x = lm[16].x * w; rw_y = lm[16].y * h
                    if abs(lw_x - rw_x) < HAND_CROSS_DIST and abs(lw_y - rw_y) < HAND_CROSS_DIST:
                        print('Hands crossed -> exiting')
                        break

            # draw embedded graph in top-right corner
            graph.draw_on_frame(frame, x= w - graph.width - 10, y=10)

            cv2.putText(frame, f'Status: {status}', (10, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.imshow('motion-tracker', frame)

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
                        time.sleep(0.01); continue
                    f = cv2.flip(f, 1)
                    r = detector.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
                    if r.pose_landmarks:
                        samples.append(r.pose_landmarks.landmark)
                    time.sleep(0.02)
                hip_b, cen_b = median_baseline_from_landmarks(samples, WIDTH, HEIGHT)
                if hip_b is not None:
                    logic.set_baseline(hip_b, cen_b)
                    calibrated = True
                    print('[main] manual calibration OK')
                else:
                    print('[main] manual calibration failed')
            if key == ord('t'):
                # training toggle placeholder (overlay always on in this build)
                pass

    except KeyboardInterrupt:
        pass
    finally:
        stop_reader()
        detector.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
