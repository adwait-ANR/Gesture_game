# graph_window.py
# Embedded graph drawer: draws a small oscilloscope-style plot onto the OpenCV frame.
# No Matplotlib required. Lightweight and thread-safe.

import collections
import cv2
import numpy as np
import time

class EmbeddedGraph:
    def __init__(self, max_points=200, width=300, height=100):
        # circular buffer of recent values (timestamps not strictly needed for display)
        self.max_points = max_points
        self.hip_history = collections.deque(maxlen=max_points)
        self.center_history = collections.deque(maxlen=max_points)
        self.width = width
        self.height = height

    def push(self, hip_delta, center_delta):
        self.hip_history.append(float(hip_delta))
        self.center_history.append(float(center_delta))

    def draw_on_frame(self, frame, x=10, y=10):
        """
        Draw the mini-graph at top-left corner (x,y).
        frame: OpenCV BGR image (will be modified in place)
        x,y: top-left origin of the graph box
        """
        h, w = frame.shape[:2]
        gw, gh = self.width, self.height
        # background rect
        cv2.rectangle(frame, (x, y), (x + gw, y + gh), (30, 30, 30), -1)

        # axes lines
        cv2.line(frame, (x + 0, y + gh//2), (x + gw, y + gh//2), (80, 80, 80), 1)

        # prepare normalized points for hip (red) and center (cyan)
        if len(self.hip_history) >= 2:
            hip_arr = np.array(self.hip_history)
            cen_arr = np.array(self.center_history)
            # autoscale using max(abs(...)) to center around 0
            maxval = max(np.max(np.abs(hip_arr)) if hip_arr.size else 1.0,
                         np.max(np.abs(cen_arr)) if cen_arr.size else 1.0, 1.0)
            # scale to half-height
            scale = (gh/2.0) / maxval if maxval != 0 else 1.0

            # convert to polyline coordinates
            n = len(hip_arr)
            xs = np.linspace(x, x + gw - 1, n).astype(np.int32)
            hip_ys = (y + gh//2 - (hip_arr * scale)).astype(np.int32)
            cen_ys = (y + gh//2 - (cen_arr * scale)).astype(np.int32)

            # draw hip polyline (red)
            pts = np.vstack((xs, hip_ys)).T.reshape(-1, 1, 2)
            cv2.polylines(frame, [pts], False, (0, 0, 255), 2, lineType=cv2.LINE_AA)

            # draw center polyline (cyan)
            pts2 = np.vstack((xs, cen_ys)).T.reshape(-1, 1, 2)
            cv2.polylines(frame, [pts2], False, (255, 255, 0), 1, lineType=cv2.LINE_AA)

            # draw small legend
            cv2.putText(frame, 'hip', (x + 6, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)
            cv2.putText(frame, 'center', (x + 50, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,0), 1)

        # border
        cv2.rectangle(frame, (x, y), (x + gw, y + gh), (100, 100, 100), 1)
        return frame
