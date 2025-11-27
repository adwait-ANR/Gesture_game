# movement_logic.py
# Implements sit/jump detection with smoothing and debounce.

import time
from utils import ema, press_once

class MovementLogic:
    def __init__(self, config):
        self.cfg = config
        self.smoothed_hip = None
        self.smoothed_center_x = None
        self.baseline_hip = None
        self.baseline_center_x = None
        self.last_action_time = 0.0
        self.current_action = 'idle'

    def set_baseline(self, hip, center_x):
        self.baseline_hip = float(hip)
        self.baseline_center_x = float(center_x)

    def update(self, hip_y, center_x):
        """
        Call per-frame with raw hip_y and center_x (pixels).
        Returns (action, status_text) where action in {None, 'sit', 'jump', 'left', 'right'}.
        Always returns a tuple (action_or_None, status_string).
        """
        cfg = self.cfg
        self.smoothed_hip = ema(hip_y, self.smoothed_hip, cfg.EMA_ALPHA)
        self.smoothed_center_x = ema(center_x, self.smoothed_center_x, cfg.EMA_ALPHA)

        # If not calibrated, return idle-like tuple
        if self.baseline_hip is None or self.baseline_center_x is None:
            return None, 'not_calibrated'

        d_hip = self.smoothed_hip - self.baseline_hip
        d_x = self.smoothed_center_x - self.baseline_center_x

        now = time.time()
        # priority: sit/jump
        if d_hip > cfg.SIT_THRESHOLD:
            # sit detected
            if now - self.last_action_time > cfg.ACTION_COOLDOWN:
                # press key via config-specified key constant
                try:
                    press_once(cfg.DOWN_KEY)
                except Exception:
                    # graceful fallback for non-pynput environment
                    pass
                self.last_action_time = now
                self.current_action = 'sit'
                return 'sit', 'SIT -> DOWN'
            else:
                return None, 'sit_pending'
        elif d_hip < -cfg.JUMP_THRESHOLD:
            if now - self.last_action_time > cfg.ACTION_COOLDOWN:
                try:
                    press_once(cfg.UP_KEY)
                except Exception:
                    pass
                self.last_action_time = now
                self.current_action = 'jump'
                return 'jump', 'JUMP -> UP'
            else:
                return None, 'jump_pending'
        else:
            # lateral code left/right intentionally commented here for clarity
            # if d_x < -cfg.LEFT_THRESHOLD:
            #     return 'left', 'LEFT -> LEFT'
            # if d_x > cfg.RIGHT_THRESHOLD:
            #     return 'right', 'RIGHT -> RIGHT'
            self.current_action = 'idle'
            return None, 'idle'
