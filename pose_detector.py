# pose_detector.py
# Small wrapper around MediaPipe Pose for convenience

import mediapipe as mp

class PoseDetector:
    def __init__(self, model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process(self, rgb_frame):
        """Process an RGB image (HWC, BGR->RGB expected externally) and return result."""
        return self.pose.process(rgb_frame)

    def close(self):
        try:
            self.pose.close()
        except Exception:
            pass
