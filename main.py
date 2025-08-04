import keyboard
import pygame
import json
import os

pygame.mixer.init()

with open("sounds.json", "r") as f:
    sounds = json.load(f)

def play_sound(path):
    if os.path.exists(path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    else:
        print(f"Arquivo não encontrado: {path}")

for key, path in sounds.items():
    keyboard.add_hotkey(key, lambda p=path: play_sound(p))

print("🎵 Soundpad simples rodando! Pressione ESC para sair.")
keyboard.wait("esc")
