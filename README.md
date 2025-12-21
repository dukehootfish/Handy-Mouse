# HandyMouse

HandyMouse is a Python application that allows you to control your computer mouse using hand gestures captured by your webcam. It uses **MediaPipe** for robust hand tracking and a modular architecture to map specific gestures to system actions like cursor movement, clicking, scrolling, zooming, and microphone toggling.

## Features

### 🖱️ Cursor Control
- **Tracking**: Moves the mouse cursor based on the position of your **Index Finger Knuckle (MCP)**.
- **Smoothing**: Integrated smoothing algorithms reduce jitter for precise control.
- **Two-Handed Mode**: Supports using a second hand for auxiliary controls (Zoom, Exit).

### 👆 Interactions (Main Hand)
- **Left Click**: Pinch **Thumb** and **Index Finger** together.
- **Drag & Drop**: Hold a Left Click pinch.
- **Right Click**: Pinch **Thumb** and **Middle Finger** together.
- **Scroll**: Make a **Fist** and move your hand to drag the page.

### 🔍 Advanced Gestures
- **Mic Toggle**: Pinch **Thumb**, **Middle**, and **Ring** fingers together (quiet coyote).
- **Exit App**:
  - Press `Esc` key.
  - **Double Fist**: Hold fists with **BOTH hands** for 1 second (Two-Handed Mode only).

## Project Structure

The project follows a modular "Conditions & Events" architecture:

- `main.py`: Entry point. Initializes the application.
- `app.py`: Main application loop and context management.
- `config.py`: Configuration settings (sensitivity, thresholds, keybindings).
- `features/`: Individual gesture implementations.
  - `activation.py`: Hand activation logic.
  - `cursor.py`: Cursor movement and clicking.
  - `scroll.py`: Scrolling logic.
  - `zoom.py`: Two-handed zoom interactions.
  - `mic_toggle.py`: Microphone mute/unmute.
  - `exit_gesture.py`: Double-fist exit logic.
- `core/`: Core system logic (`condition.py`).
- `helpers/`: Utility modules (`hand_tracker.py`, `mouse_controller.py`, `detectors.py`).

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Handy-Mouse.git
   cd Handy-Mouse
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Activate Hand Control**:
   - **Gesture**: Curl your **Ring Finger** while extending all other fingers.
   - **Action**: Hold this pose steady for **1 second**.
   - **Feedback**: The status text on screen will show a countdown. Once active, your hand will be outlined in **Yellow** (Main Hand).

3. **Add a Secondary Hand (Optional)**:
   - Perform the same activation gesture with your other hand.
   - It will be outlined in **Green** (Secondary Hand).

4. **Visual Interface**:
   - **Status Overlay**: Shows active mode, hand roles, and pending actions.
   - **Hand Skeleton**: Visualizes tracking and gesture recognition state (Red = Bad Orientation, Yellow = Main, Green = Secondary).

## Configuration

You can customize sensitivity and thresholds in `config.py`:

## Requirements

- Python 3.10
- Webcam
