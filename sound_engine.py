import sounddevice as sd
import soundfile as sf
import threading

class SoundEngine:
    def __init__(self, device=None, volume=0.5):
        self.device = device
        self.volume = volume
        self.data = None
        self.fs = None
        self.current_pos = 0
        self.is_paused = False
        self.play_thread = None
        self.stop_flag = False
        self.stream = None
        self.lock = threading.Lock()

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
        self.stop()
        self.data, self.fs = sf.read(path, dtype='float32')
        self.data *= self.volume
        self.current_pos = 0
        self.stop_flag = False
        self.is_paused = False

        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()

    def _play_loop(self):
        blocksize = 1024
        with sd.OutputStream(
            device=self.device,
            samplerate=self.fs,
            channels=self.data.shape[1] if len(self.data.shape) > 1 else 1
        ) as stream:
            self.stream = stream
            while self.current_pos < len(self.data) and not self.stop_flag:
                if self.is_paused:
                    sd.sleep(100)
                    continue
                end = min(self.current_pos + blocksize, len(self.data))
                stream.write(self.data[self.current_pos:end])
                self.current_pos = end
        self.stream = None

    def pause(self):
        self.is_paused = True

    def resume(self):
        if self.is_paused:
            self.is_paused = False

    def stop(self):
        self.stop_flag = True
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()
        self.is_paused = False
        self.current_pos = 0

    def get_position(self):
        """Retorna a posição atual em segundos."""
        if self.data is None: return 0
        return self.current_pos / self.fs

    def get_duration(self):
        """Retorna a duração total do áudio em segundos."""
        if self.data is None: return 0
        return len(self.data) / self.fs

    def seek(self, seconds):
        """Vai para um ponto específico do áudio."""
        if self.data is None: return
        with self.lock:
            new_pos = int(seconds * self.fs)
            if 0 <= new_pos < len(self.data):
                self.current_pos = new_pos
