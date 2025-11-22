from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class AudioController:
    def __init__(self):
        # Setup Speakers
        devices = AudioUtilities.GetSpeakers()
        # GetSpeakers returns an AudioDevice object which already has EndpointVolume
        self.volume = devices.EndpointVolume

        # Setup Microphone
        # Try to get default microphone
        try:
            mic_device = AudioUtilities.GetMicrophone()
            mic_interface = mic_device.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            self.mic_volume = cast(mic_interface, POINTER(IAudioEndpointVolume))
        except Exception as e:
            print(f"Error initializing microphone: {e}")
            self.mic_volume = None

    def set_volume(self, level):
        """
        Set master volume level.
        :param level: float between 0.0 and 1.0
        """
        # Clamp level between 0.0 and 1.0
        level = max(0.0, min(1.0, level))
        self.volume.SetMasterVolumeLevelScalar(level, None)

    def get_volume(self):
        """
        Get master volume level.
        :return: float between 0.0 and 1.0
        """
        return float(self.volume.GetMasterVolumeLevelScalar())

    def set_master_volume(self, percent: float):
        """
        Set master volume as percentage.
        :param percent: 0.0 to 100.0
        """
        percent = max(0.0, min(100.0, float(percent)))
        self.set_volume(percent / 100.0)

    def get_master_volume(self) -> float:
        """
        Get master volume as percentage.
        :return: 0.0 to 100.0
        """
        return max(0.0, min(100.0, self.get_volume() * 100.0))

    def increase_volume(self, delta_percent: float):
        """
        Increase (or decrease) master volume by a percentage delta.
        :param delta_percent: positive to increase, negative to decrease
        """
        current = self.get_master_volume()
        target = max(0.0, min(100.0, current + float(delta_percent)))
        self.set_master_volume(target)

    def mute_mic(self):
        """Mute the microphone."""
        if self.mic_volume:
            self.mic_volume.SetMute(1, None)

    def unmute_mic(self):
        """Unmute the microphone."""
        if self.mic_volume:
            self.mic_volume.SetMute(0, None)

    def toggle_mic(self):
        """Toggle microphone mute state."""
        current_mute = self.mic_volume.GetMute()
        self.mic_volume.SetMute(not current_mute, None)
