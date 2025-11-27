# Motion Tracker (modular)

This project is a modular, local, real-time movement tracking system that:
- Detects sit (Down) and jump (Up) using MediaPipe pose
- Provides a background camera reader to avoid buffering/lag
- Includes a live matplotlib graph for hip and center-x deltas
- Includes a Tkinter control panel to tune thresholds in real-time
- Training overlay shows thresholds and numeric deltas
- All processing happens locally (no internet)

## How to use
1. Create a Python 3.10 virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate     # macOS / Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python main.py
   ```

## Files
- `main.py`: orchestration entrypoint
- `camera_thread.py`: threaded reader
- `pose_detector.py`: mediapipe wrapper
- `movement_logic.py`: decision logic (sit/jump)
- `graph_window.py`: matplotlib live graph
- `control_panel.py`: Tkinter sliders
- `training_mode.py`: HUD overlay helpers
- `utils.py`, `config.py`: utilities & central config

## Git Workflow
This project is intended to be used with a feature-branch workflow:
- `main` for releases
- `dev` for integration
- `feature/*` for features (e.g. `feature/ui-graphs-controls`)

## Notes
- If `pynput` keypresses do not register in a target game, run as Administrator.
- If matplotlib window steals focus, you can minimize it; graphs run in a separate thread.
