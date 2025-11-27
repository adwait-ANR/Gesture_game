# config.py
# Central configuration for thresholds and settings.

# Camera
CAM_INDEX = 0
WIDTH = 1280
HEIGHT = 720
FLUSH_READS = 3
CAP_PROP_BUFFERSIZE = 1  # may be ignored by some drivers

# MediaPipe / model
# model_complexity: 0 (fast), 1 (balanced), 2 (accurate)
MODEL_COMPLEXITY = 2
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Smoothing & timing
EMA_ALPHA = 0.2          # 0..1 smoothing factor
PERSISTENCE_FRAMES = 3  # frames required to confirm a state
ACTION_COOLDOWN = 0.6   # seconds between actions

# Thresholds (tuned for 640x480; adjust for your camera distance)
SIT_THRESHOLD = 45      # hip lower than baseline => sit
JUMP_THRESHOLD = 45     # hip higher than baseline => jump
LEFT_THRESHOLD = 40     # commented-out lateral threshold
RIGHT_THRESHOLD = 40    # commented-out lateral threshold

# Gesture settings
HAND_CROSS_DIST = 80    # hands within this box => exit

# UI / training
AUTO_CALIBRATE_SECONDS = 10.0
