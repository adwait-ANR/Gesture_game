import mediapipe as mp

class PoseDetector:
    def __init__(self,model_complexity,min_detection_confidence,min_tracking_confidence):
        self.mp_pose=mp.solutions.pose
        self.pose=self.mp_pose.Pose(
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence)

    def process(self,img):
        return self.pose.process(img)

    def close(self):
        self.pose.close()
