import sounddevice as sd
import soundfile as sf

class SoundEngine:
    def __init__(self, device=None, volume=0.5):
        self.device = device
        self.volume = volume

    def set_device(self, device_name):
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if device_name.lower() in d['name'].lower():
                self.device = i
                return
        raise ValueError(f"Dispositivo '{device_name}' não encontrado.")

    def list_devices(self):
        return [d['name'] for d in sd.query_devices()]

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))

    def play(self, path):
        data, fs = sf.read(path, dtype='float32')
        data *= self.volume
        sd.play(data, fs, device=self.device)
