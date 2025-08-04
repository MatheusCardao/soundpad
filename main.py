import sys
import json
import os
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QSlider, QLabel, QComboBox, QHBoxLayout, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from sound_engine import SoundEngine

SETTINGS_FILE = "settings.json"

with open("sounds.json", "r") as f:
    sounds = json.load(f)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"device": None, "volume": 0.5}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

class SoundpadApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundpad Pro")
        self.setGeometry(200, 200, 500, 600)

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

        # Dispositivo
        self.device_box = QComboBox()
        self.devices = self.engine.list_devices()
        self.device_box.addItems(self.devices)
        if self.settings["device"] in self.devices:
            self.device_box.setCurrentText(self.settings["device"])
            self.engine.set_device(self.settings["device"])
        self.device_box.currentTextChanged.connect(self.change_device)
        layout.addWidget(QLabel("Dispositivo de saída:"))
        layout.addWidget(self.device_box)

        # Volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.settings["volume"] * 100))
        self.volume_slider.valueChanged.connect(self.change_volume)
        layout.addWidget(QLabel("Volume:"))
        layout.addWidget(self.volume_slider)
        self.engine.set_volume(self.settings["volume"])

        # Área rolável para sons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sound_list = QWidget()
        sound_layout = QVBoxLayout()

        for key, path in sounds.items():
            btn = QPushButton(f"{key.upper()} - {os.path.basename(path)}")
            btn.clicked.connect(lambda checked, p=path: self.engine.play(p))
            sound_layout.addWidget(btn)
            keyboard.add_hotkey(key.lower(), lambda p=path: self.engine.play(p))

        sound_list.setLayout(sound_layout)
        scroll.setWidget(sound_list)
        layout.addWidget(scroll)

        # Controles de reprodução
        control_layout = QHBoxLayout()
        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(QIcon("icons/pause.svg"))
        self.pause_btn.clicked.connect(self.engine.pause)
        control_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton()
        self.resume_btn.setIcon(QIcon("icons/play.svg"))
        self.resume_btn.clicked.connect(self.engine.resume)
        control_layout.addWidget(self.resume_btn)

        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(QIcon("icons/stop.svg"))
        self.stop_btn.clicked.connect(self.engine.stop)
        control_layout.addWidget(self.stop_btn)

        layout.addLayout(control_layout)

        # Barra de progresso
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderReleased.connect(self.seek_audio)
        layout.addWidget(self.progress_slider)

        # Labels de tempo
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        layout.addLayout(time_layout)

        self.setLayout(layout)

        # Atualização da barra de progresso
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(200)

    def change_device(self, device_name):
        self.engine.set_device(device_name)
        self.settings["device"] = device_name
        save_settings(self.settings)

    def change_volume(self, value):
        vol = value / 100.0
        self.engine.set_volume(vol)
        self.settings["volume"] = vol
        save_settings(self.settings)

    def update_progress(self):
        duration = self.engine.get_duration()
        position = self.engine.get_position()
        if duration > 0:
            self.progress_slider.setRange(0, int(duration))
            self.progress_slider.setValue(int(position))
            self.current_time_label.setText(self.format_time(position))
            self.total_time_label.setText(self.format_time(duration))

    def seek_audio(self):
        self.engine.seek(self.progress_slider.value())

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"

    def closeEvent(self, event):
        self.engine.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoundpadApp()
    window.show()
    sys.exit(app.exec_())
