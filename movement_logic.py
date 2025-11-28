# movement_logic.py
# Uses strong Win32 injection via key_control. Continuous behavior: start repeating / stop repeating.

from utils import ema
from key_control import start_repeat, stop_repeat, press_hold, release_hold, USE_WIN32

class MovementLogic:
    def __init__(self, cfg):
        self.cfg = cfg
        self.baseline_hip = None
        self.smoothed_hip = None

        self.current_action = None  # "jump", "sit", or None

        # left/right future expansion
        self.current_lr = None

        # needed if later we use lean-based LR
        self.baseline_center_x = None

    def set_baseline(self, hip, center):
        self.baseline_hip = hip
        self.smoothed_hip = hip
        self.baseline_center_x = center

    def update(self, hip_y, center_x):
        # smooth hip signal
        self.smoothed_hip = ema(hip_y, self.smoothed_hip, self.cfg.EMA_ALPHA)
        hip = self.smoothed_hip

        if self.baseline_hip is None:
            return None, "not_calibrated"

        base = self.baseline_hip
        M = self.cfg.HIP_MARGIN

        # ---------------------------- JUMP ---------------------------------
        if hip < base - M:
            if self.current_action != "jump":
                # Stop sit repetition
                try: stop_repeat(self.cfg.DOWN_KEY)
                except: pass
                # Start jump repetition
                try: start_repeat(self.cfg.UP_KEY)
                except: pass

                self.current_action = "jump"
            return "jump", "JUMP (holding)"

        # ---------------------------- SIT ----------------------------------
        if hip > base + M:
            if self.current_action != "sit":
                try: stop_repeat(self.cfg.UP_KEY)
                except: pass
                try: start_repeat(self.cfg.DOWN_KEY)
                except: pass

                self.current_action = "sit"
            return "sit", "SIT (holding)"

        # ---------------------------- NEUTRAL ------------------------------
        if self.current_action is not None:
            # Stop both repeat streams
            try:
                stop_repeat(self.cfg.UP_KEY)
                stop_repeat(self.cfg.DOWN_KEY)
            except:
                pass

            # Release held keys (safe even if not pressed)
            try:
                release_hold(self.cfg.UP_KEY)
                release_hold(self.cfg.DOWN_KEY)
            except:
                pass

            self.current_action = None

        return None, "idle"
