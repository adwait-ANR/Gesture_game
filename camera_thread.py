# camera_thread.py
# Non-blocking camera reader that stores the latest frame.

import cv2, time
import threading

_latest_frame = None
_frame_lock = threading.Lock()
_stop_reader = False

def start_camera_reader(cam_index, width, height, flush_reads, buffersize=1):
    """Start background thread to read camera frames.
    Returns a (stop_func, get_frame_func) tuple.
    """
    def reader():
        global _latest_frame, _stop_reader
        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, buffersize)
        except Exception:
            pass
        if not cap.isOpened():
            print("[camera_thread] ERROR: cannot open camera", cam_index)
            _stop_reader = True
            return
        while not _stop_reader:
            for _ in range(flush_reads):
                cap.grab()
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            with _frame_lock:
                _latest_frame = frame
        cap.release()

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    def get_frame_copy():
        with _frame_lock:
            return None if _latest_frame is None else _latest_frame.copy()

    def stop():
        global _stop_reader
        _stop_reader = True

    return stop, get_frame_copy
