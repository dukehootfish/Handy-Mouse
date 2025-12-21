# Double Fist Exit Feature

## Overview
This feature allows users to exit HandyMouse in two-handed mode by closing both fists for a configurable duration (default: 1 second).

## Implementation Details

### Files Modified:
1. **config.py** - Added `DOUBLE_FIST_EXIT_DURATION` config value (default: 1.0 seconds)
2. **flags.py** - Added state tracking:
   - `DOUBLE_FIST_START_TIME`: Tracks when both fists were first detected
   - `EXIT_REQUESTED`: Flag to signal the main loop to exit
3. **app.py** - Updates:
   - Stores `frame_landmarks` and `frame_handedness` in context for multi-hand features
   - Imports the new `exit_gesture` feature
   - Checks `EXIT_REQUESTED` flag and exits gracefully

### New Feature File:
**features/exit_gesture.py** - Implements the double fist detection and exit logic:
- Priority: 1 (checked after activation, same as scroll)
- Only active in two-handed mode
- Checks both hands for fist gestures
- Shows countdown on screen
- Consumes frame to prevent other interactions
- Releases mouse buttons when triggered

## How It Works

1. **Activation**: Only works when `TWO_HANDED_MODE` is active (both hands detected and activated)

2. **Detection**: 
   - When both hands are making fists, a timer starts
   - A countdown is displayed on screen showing remaining time
   - If either fist is released, the timer resets

3. **Exit**:
   - After holding both fists for the configured duration (default 1 second)
   - `EXIT_REQUESTED` flag is set
   - Main loop detects the flag and exits gracefully
   - Equivalent to pressing ESC key

4. **Visual Feedback**:
   - While holding: "Exiting in: X.Xs" displayed on screen
   - When triggered: "Exiting HandyMouse..." displayed

## Configuration

To change the duration required, edit in `config.py`:

```python
DOUBLE_FIST_EXIT_DURATION = 1.0  # Seconds (adjust as needed)
```

## Technical Notes

- The feature properly handles edge cases like losing hand detection
- Frame is consumed when both fists detected to prevent scroll or cursor movement
- Mouse buttons are released before exit for clean shutdown
- Works alongside other gestures without conflicts due to two-handed mode requirement

