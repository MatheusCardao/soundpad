import sounddevice as sd
import soundfile as sf
import numpy as np
import sys, os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class SoundEngine:
    def __init__(self, mic_device=None, volume=0.5):
        self.output_device = self._get_vbcable_device()
        self.mic_device = mic_device
        self.volume = volume
        self.fs = 44100

        self.sound_data = None
        self.sound_pos = 0
        self.is_playing = False

        self.preloaded_sounds = {}
        self.mic_buffer = np.zeros((1024, 2), dtype='float32')

        self.input_stream = None
        self.output_stream = None
        self.ptt_active = False  # Push-to-Talk automático
        self.pure_mode = False   # Novo: modo de áudio puro (sem microfone)

    def _get_vbcable_device(self):
        """Procura automaticamente pelo VB-Cable."""
        for i, d in enumerate(sd.query_devices()):
            if "CABLE Input" in d['name']:
                return i
        raise RuntimeError("VB-Cable não encontrado! Instale e reinicie o programa.")

    def list_input_devices(self):
        """Lista apenas dispositivos que parecem ser microfones reais."""
        devices = []
        for d in sd.query_devices():
            if d['max_input_channels'] > 0:
                name = d['name'].lower()
                if "cable" not in name and "vb-audio" not in name:
                    devices.append(d['name'])
        return devices

    def set_mic_device(self, name):
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if name.lower() in d['name'].lower():
                self.mic_device = i
                return
        raise ValueError(f"Microfone '{name}' não encontrado.")

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))

    def preload_sound(self, key, path):
        full_path = resource_path(path)
        data, fs = sf.read(full_path, dtype='float32')
        if len(data.shape) == 1:
            data = np.stack([data, data], axis=1)
        self.preloaded_sounds[key] = (data, fs)

    def play(self, key):
        if key not in self.preloaded_sounds:
            print(f"Som {key} não encontrado!")
            return
        self.sound_data, self.fs = self.preloaded_sounds[key]
        self.sound_pos = 0
        self.is_playing = True

    def stop(self):
        self.is_playing = False
        self.sound_pos = 0
        sd.stop()  # Interrompe qualquer reprodução imediatamente

    def _mic_callback(self, indata, frames, time, status):
        if status:
            print("Mic status:", status)
        self.mic_buffer = indata.copy()

    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print("Output status:", status)

        mic_data = self.mic_buffer

        # Pega o áudio do som
        if self.is_playing and self.sound_data is not None:
            end = self.sound_pos + frames
            chunk = self.sound_data[self.sound_pos:end]

            if chunk.shape[0] < frames:
                chunk = np.pad(chunk, ((0, frames - chunk.shape[0]), (0, 0)), 'constant')
                self.is_playing = False
            elif chunk.shape[0] > frames:
                chunk = chunk[:frames]

            chunk *= self.volume
            self.sound_pos = end
        else:
            chunk = np.zeros((frames, 2), dtype='float32')

        target_frames = outdata.shape[0]
        if mic_data.shape[0] != target_frames:
            mic_data = np.pad(mic_data, ((0, max(0, target_frames - mic_data.shape[0])), (0,0)), 'constant')[:target_frames]
        if chunk.shape[0] != target_frames:
            chunk = np.pad(chunk, ((0, max(0, target_frames - chunk.shape[0])), (0,0)), 'constant')[:target_frames]

        # Modo Puro = só som (sem microfone)
        if self.ptt_active:
            if self.pure_mode:
                mixed = chunk  # Som puro
            else:
                mixed = mic_data + chunk  # Mistura voz + som
        else:
            mixed = np.zeros_like(mic_data)

        outdata[:] = mixed

    def start_stream(self):
        if self.input_stream is None:
            self.input_stream = sd.InputStream(
                device=self.mic_device,
                channels=2,
                samplerate=self.fs,
                callback=self._mic_callback
            )
            self.input_stream.start()

        if self.output_stream is None:
            self.output_stream = sd.OutputStream(
                device=self.output_device,
                channels=2,
                samplerate=self.fs,
                callback=self._audio_callback
            )
            self.output_stream.start()

    def get_position(self):
        return self.sound_pos / self.fs if self.sound_data is not None else 0

    def get_duration(self):
        return len(self.sound_data) / self.fs if self.sound_data is not None else 0

    def seek(self, seconds):
        if self.sound_data is None:
            return
        new_pos = int(seconds * self.fs)
        if 0 <= new_pos < len(self.sound_data):
            self.sound_pos = new_pos

    def get_current_level(self):
        if self.mic_buffer is None:
            return 0
        return float(np.sqrt(np.mean(self.mic_buffer**2)))