"""
Windows system volume controller using pycaw.
"""

from ctypes import POINTER, cast
from typing import Optional

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class VolumeController:
    """
    Controls system master volume as a percentage (0-100) via pycaw.
    """

    def __init__(self):
        """
        Initialize COM interfaces for the default audio endpoint volume.
        """
        speakers = AudioUtilities.GetSpeakers()
        interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self._volume = cast(interface, POINTER(IAudioEndpointVolume))

    def get_master_volume(self) -> float:
        """
        Returns:
            float: Current master volume in the range [0.0, 100.0]
        """
        scalar = float(self._volume.GetMasterVolumeLevelScalar())
        return max(0.0, min(100.0, scalar * 100.0))

    def set_master_volume(self, percent: float) -> None:
        """
        Sets the master volume.

        Args:
            percent (float): Target volume in [0.0, 100.0]
        """
        clamped = max(0.0, min(100.0, float(percent)))
        self._volume.SetMasterVolumeLevelScalar(clamped / 100.0, None)


