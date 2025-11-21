# HandyMouse

HandyMouse is a Python application that allows you to control your mouse cursor using hand gestures captured by your webcam. It uses MediaPipe for robust hand tracking and maps hand movements to screen coordinates.

## Features

- **Hand Tracking**: Real-time hand tracking using MediaPipe.
- **Cursor Control**: Moves the mouse cursor based on the position of your index finger knuckle (MCP joint).
- **Clicking**: Simulates a left mouse click when you pinch your thumb and index finger together.
- **Smoothing**: Implements a stability threshold to reduce cursor jitter.

## Project Structure

The project has been refactored into modular components:

- `main.py`: The entry point of the application. Handles the main loop and video processing.
- `hand_tracker.py`: Handles MediaPipe initialization and hand landmark extraction.
- `mouse_controller.py`: Manages mouse movement and clicking using `pynput` and `wxPython`.
- `config.py`: Contains configuration constants (camera resolution, thresholds, etc.).
- `utils.py`: Helper functions (e.g., movement stability check).

## Prerequisites

- Python 3.7+
- A webcam

## Installation

1. Clone the repository.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application using:

```bash
python main.py
```

- **Move Cursor**: Move your hand in front of the camera. The cursor follows the base of your index finger.
- **Click**: Pinch your thumb and index finger tips together.
- **Exit**: Press the `Esc` key to close the application.

## Configuration

You can adjust settings in `config.py`:

- `CAM_WIDTH`, `CAM_HEIGHT`: Set your webcam resolution.
- `CLICK_DISTANCE_THRESHOLD`: Adjust how close fingers need to be to register a click.
- `MOVEMENT_STABILITY_THRESHOLD`: Adjust to change how much movement is needed to update cursor position (helps with jitter).

## TODO
- [X] Stabilization
- [ ] General setting
  - [ ] Deciding hand
  - [ ] Set Boundries
- [ ] Mouse Toggle
  - [ ] Right Click
  - [ ] Scroll
- [ ] Volume Control
- [ ] Toggle mute
- [ ] Decide gestures
- [ ] Extra click options
  - [ ] Scroll
  - [ ] Right Click
  - [X] Keep on/off

