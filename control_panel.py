# control_panel.py
# Simple Tkinter control panel that allows live tuning of thresholds.

import tkinter as tk
import threading

class ControlPanel:
    def __init__(self, config):
        self.cfg = config
        self.root = tk.Tk()
        self.root.title('Control Panel - Sensitivity')
        # build sliders
        self._make_slider('SIT_THRESHOLD', 5, 200, self.cfg.SIT_THRESHOLD)
        self._make_slider('JUMP_THRESHOLD', 5, 200, self.cfg.JUMP_THRESHOLD)
        self._make_slider('EMA_ALPHA', 1, 50, int(self.cfg.EMA_ALPHA*100))
        self._make_slider('ACTION_COOLDOWN_ms', 100, 2000, int(self.cfg.ACTION_COOLDOWN*1000))
        # NOTE: left/right sliders are present but commented-out in main
        # self._make_slider('LEFT_THRESHOLD', 5, 200, self.cfg.LEFT_THRESHOLD)
        # self._make_slider('RIGHT_THRESHOLD', 5, 200, self.cfg.RIGHT_THRESHOLD)
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._closed = False
        t = threading.Thread(target=self.root.mainloop, daemon=True)
        t.start()

    def _make_slider(self, name, a, b, initial):
        frame = tk.Frame(self.root)
        frame.pack(fill='x', padx=6, pady=6)
        tk.Label(frame, text=name).pack(side='left')
        var = tk.IntVar(value=initial)
        s = tk.Scale(frame, from_=a, to=b, orient='horizontal', variable=var, length=300)
        s.pack(side='right')
        setattr(self, name.lower(), var)

    def _on_close(self):
        # hide instead of destroy -- allows re-opening if needed
        try:
            self.root.withdraw()
        except:
            pass
        self._closed = True

    def is_closed(self):
        return self._closed

    def apply_to_config(self):
        # read widgets and apply to config object
        try:
            self.cfg.SIT_THRESHOLD = int(self.sit_threshold.get())
            self.cfg.JUMP_THRESHOLD = int(self.jump_threshold.get())
            self.cfg.EMA_ALPHA = max(0.01, min(0.9, self.ema_alpha.get()/100.0))
            self.cfg.ACTION_COOLDOWN = max(0.05, self.action_cooldown_ms.get()/1000.0)
        except Exception:
            pass
