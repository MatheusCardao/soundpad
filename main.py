import sys
import json
import os
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QSlider, QLabel, QComboBox, QScrollArea, QFileDialog, QInputDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, QTimer
from sound_engine import SoundEngine
import numpy as np
import sounddevice as sd
import threading, time

SETTINGS_FILE = "settings.json"
SOUNDS_FILE = "sounds.json"

if not os.path.exists(SOUNDS_FILE):
    with open(SOUNDS_FILE, "w") as f:
        json.dump({}, f)

with open(SOUNDS_FILE, "r") as f:
    sounds = json.load(f)

def load_settings():
    default_settings = {"mic_device": None, "volume": 0.5}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            for key in default_settings:
                if key not in data:
                    data[key] = default_settings[key]
            return data
    return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def save_sounds():
    with open(SOUNDS_FILE, "w") as f:
        json.dump(sounds, f)

class SoundpadApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundpad Pro - VB-Cable")
        self.setGeometry(200, 200, 500, 650)

        self.engine = SoundEngine()
        self.settings = load_settings()

        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #fff; font-size: 14px; }
            QPushButton { background-color: #1e1e1e; border: 1px solid #333; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background-color: #333; }
            QSlider::groove:horizontal { height: 6px; background: #333; }
            QSlider::handle:horizontal { background: #555; width: 12px; border-radius: 6px; }
            QComboBox { background: #1e1e1e; border: 1px solid #333; padding: 5px; }
        """)

        layout = QVBoxLayout()

        # ComboBox para microfone
        self.mic_box = QComboBox()
        self.mics = self.engine.list_input_devices()
        self.mic_box.addItems(self.mics)
        if self.settings["mic_device"] in self.mics:
            self.mic_box.setCurrentText(self.settings["mic_device"])
            try:
                self.engine.set_mic_device(self.settings["mic_device"])
            except ValueError:
                QMessageBox.warning(self, "Erro", "Microfone salvo não encontrado. Selecione novamente.")
        self.mic_box.currentTextChanged.connect(self.change_mic_device)
        layout.addWidget(QLabel("Seu microfone:"))
        layout.addWidget(self.mic_box)

        # Volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.settings["volume"] * 100))
        self.volume_slider.valueChanged.connect(self.change_volume)
        layout.addWidget(QLabel("Volume do som:"))
        layout.addWidget(self.volume_slider)
        self.engine.set_volume(self.settings["volume"])

        # Botão para adicionar sons
        add_sound_btn = QPushButton("+ Adicionar Som")
        add_sound_btn.clicked.connect(self.add_sound)
        layout.addWidget(add_sound_btn)

        # Área rolável para sons
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.sound_list = QWidget()
        self.sound_layout = QVBoxLayout()
        self.sound_list.setLayout(self.sound_layout)
        self.scroll.setWidget(self.sound_list)
        layout.addWidget(self.scroll)

        self.load_sounds()

        # Botão Stop
        self.stop_btn = QPushButton("Parar (F12)")
        self.stop_btn.setIconSize(QSize(32, 32))
        self.stop_btn.clicked.connect(self.stop_sound)
        layout.addWidget(self.stop_btn)
        keyboard.add_hotkey("f12", self.stop_sound)

        # Botão de teste
        test_btn = QPushButton("🔊 Testar (Beep)")
        test_btn.clicked.connect(self.test_beep)
        layout.addWidget(test_btn)

        # Botão para alternar modos
        self.mode_btn = QPushButton("Modo: Mixagem")
        self.mode_btn.clicked.connect(self.toggle_mode)
        layout.addWidget(self.mode_btn)

        # VU meter
        self.vu_meter = QProgressBar()
        self.vu_meter.setRange(0, 100)
        self.vu_meter.setTextVisible(False)
        self.vu_meter.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                background: #1e1e1e;
                height: 12px;
            }
            QProgressBar::chunk {
                background: #00ff00;
            }
        """)
        layout.addWidget(QLabel("Nível de áudio:"))
        layout.addWidget(self.vu_meter)

        # Timer para atualizar VU
        self.vu_timer = QTimer()
        self.vu_timer.timeout.connect(self.update_vu)
        self.vu_timer.start(50)

        self.setLayout(layout)
        try:
            self.engine.start_stream()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Áudio", f"Não foi possível iniciar o áudio:\n{str(e)}")

    def change_mic_device(self, device_name):
        try:
            self.engine.set_mic_device(device_name)
            self.settings["mic_device"] = device_name
            save_settings(self.settings)
        except ValueError:
            QMessageBox.warning(self, "Erro", f"Não foi possível selecionar o microfone: {device_name}")

    def change_volume(self, value):
        vol = value / 100.0
        self.engine.set_volume(vol)
        self.settings["volume"] = vol
        save_settings(self.settings)

    def load_sounds(self):
        for i in reversed(range(self.sound_layout.count())):
            self.sound_layout.itemAt(i).widget().deleteLater()

        for key, path in sounds.items():
            self.engine.preload_sound(key, path)
            btn = QPushButton(f"{key.upper()} - {os.path.basename(path)}")
            btn.clicked.connect(lambda checked, k=key: self.play_with_ptt(k))
            self.sound_layout.addWidget(btn)
            keyboard.add_hotkey(key.lower(), lambda k=key: self.play_with_ptt(k))

    def play_with_ptt(self, key):
        self.engine.ptt_active = True
        self.engine.play(key)

        def disable_after():
            duration = self.engine.get_duration()
            time.sleep(duration + 0.2)
            self.engine.ptt_active = False
        threading.Thread(target=disable_after, daemon=True).start()

    def add_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Escolher som", "", "Áudio (*.mp3 *.wav)")
        if file_path:
            key, ok = QInputDialog.getText(self, "Atalho", "Digite a tecla (ex: F1):")
            if ok and key:
                sounds[key] = file_path
                save_sounds()
                self.load_sounds()

    def stop_sound(self):
        self.engine.stop()
        self.engine.ptt_active = False

    def test_beep(self):
        fs = 44100
        t = np.linspace(0, 0.5, int(fs*0.5), False)
        beep = 0.2 * np.sin(2 * np.pi * 440 * t)
        stereo_beep = np.stack([beep, beep], axis=1)
        sd.play(stereo_beep, fs, device=self.engine.output_device)

    def toggle_mode(self):
        self.engine.pure_mode = not self.engine.pure_mode
        mode_name = "Qualidade Pura" if self.engine.pure_mode else "Mixagem"
        self.mode_btn.setText(f"Modo: {mode_name}")

    def update_vu(self):
        level = self.engine.get_current_level()
        self.vu_meter.setValue(int(level * 100))

    def closeEvent(self, event):
        self.engine.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoundpadApp()
    window.show()
    sys.exit(app.exec_())
