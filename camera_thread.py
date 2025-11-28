# camera_thread.py
import cv2
import threading
import time


def start_camera_reader(index, w, h, flush=True, buffersize=3):
    cap = cv2.VideoCapture(index)

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    # Set buffer size safely (if supported)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffersize)
    except:
        pass  # Some cameras/drivers do not support this

    frame_lock = threading.Lock()
    latest = [None]
    stop_flag = [False]

    def reader_thread():
        while not stop_flag[0]:
            ret, frame = cap.read()
            if not ret:
                continue

            # Flush camera buffer to reduce lag
            if flush:
                for _ in range(2):
                    cap.read()

            with frame_lock:
                latest[0] = frame

            time.sleep(0.001)

    thread = threading.Thread(target=reader_thread, daemon=True)
    thread.start()

    def get_frame():
        with frame_lock:
            if latest[0] is None:
                return None
            return latest[0].copy()

    def stop_reader():
        stop_flag[0] = True
        time.sleep(0.05)
        cap.release()

    return stop_reader, get_frame
