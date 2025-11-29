# control_panel.py
# Tkinter control panel that runs in the main thread via periodic update() calls.
# Call panel.update() each frame from your main loop (non-blocking).

import tkinter as tk

class ControlPanel:
    def __init__(self, config):
        """
        Create the UI but DO NOT call mainloop(). Instead call update() on each frame.
        This avoids threading / apartment issues on Windows.
        """
        self.cfg = config
        try:
            self.root = tk.Tk()
        except Exception as e:
            # If Tk can't be created (headless), raise so caller can fallback
            raise RuntimeError("Tk creation failed: " + str(e))

        self.root.title('Control Panel - Sensitivity')

        # Build sliders
        self._make_slider('SIT_THRESHOLD', 5, 200, int(self.cfg.SIT_THRESHOLD))
        self._make_slider('JUMP_THRESHOLD', 5, 200, int(self.cfg.JUMP_THRESHOLD))
        self._make_slider('EMA_ALPHA', 1, 50, int(self.cfg.EMA_ALPHA * 100))
        self._make_slider('ACTION_COOLDOWN_ms', 100, 2000, int(self.cfg.ACTION_COOLDOWN * 1000))
        # left/right present but commented in main
        # self._make_slider('LEFT_THRESHOLD', 5, 200, self.cfg.LEFT_THRESHOLD)
        # self._make_slider('RIGHT_THRESHOLD', 5, 200, self.cfg.RIGHT_THRESHOLD)

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._closed = False

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
        """Read widget values and apply them to config object."""
        try:
            self.cfg.SIT_THRESHOLD = int(self.sit_threshold.get())
            self.cfg.JUMP_THRESHOLD = int(self.jump_threshold.get())
            self.cfg.EMA_ALPHA = max(0.01, min(0.9, self.ema_alpha.get() / 100.0))
            self.cfg.ACTION_COOLDOWN = max(0.05, self.action_cooldown_ms.get() / 1000.0)
        except Exception:
            pass

    def update(self):
        """
        Must be called periodically from the main loop (once per frame).
        This processes Tk events without blocking.
        """
        if self._closed:
            return
        try:
            # Process pending events
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            # If the window was destroyed or mainloop not available, mark closed
            self._closed = True
