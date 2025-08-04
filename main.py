import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSlider, QLabel, QComboBox
from PyQt5.QtCore import Qt
from sound_engine import SoundEngine

# Carregar sons do JSON
with open("sounds.json", "r") as f:
    sounds = json.load(f)

class SoundpadApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundpad Simples")
        self.setGeometry(200, 200, 300, 400)

        # Engine de áudio
        self.engine = SoundEngine()

        layout = QVBoxLayout()

        # Dispositivos
        self.device_box = QComboBox()
        self.devices = self.engine.list_devices()
        self.device_box.addItems(self.devices)
        self.device_box.currentTextChanged.connect(self.change_device)
        layout.addWidget(QLabel("Dispositivo de saída:"))
        layout.addWidget(self.device_box)

        # Slider volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.change_volume)
        layout.addWidget(QLabel("Volume:"))
        layout.addWidget(self.volume_slider)

        # Botões de sons
        for key, path in sounds.items():
            btn = QPushButton(f"{key.upper()} - {os.path.basename(path)}")
            btn.clicked.connect(lambda checked, p=path: self.engine.play(p))
            layout.addWidget(btn)

        self.setLayout(layout)

    def change_device(self, device_name):
        self.engine.set_device(device_name)

    def change_volume(self, value):
        self.engine.set_volume(value / 100.0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoundpadApp()
    window.show()
    sys.exit(app.exec_())
