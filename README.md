
# Soundpad Pro

Soundpad Pro é um aplicativo simples que permite tocar sons diretamente no seu microfone virtual (ex: VB-Cable) para que outras pessoas em chamadas (Discord, Meet, etc.) possam ouvir.

---

## Funcionalidades
- Interface gráfica com PyQt5.
- Suporte a múltiplos sons com atalhos rápidos (F1-F12).
- Mixagem de áudio para enviar som do arquivo diretamente para o microfone virtual.
- Controle de volume.
- Botão de teste (beep).
- Botão de parar áudio (F12).
- Suporte a VB-Cable para capturar e enviar áudio limpo.

---

## Pré-requisitos
- **Python 3.9+** (foi testado com Python 3.13)
- **VB-Cable** (driver de áudio virtual gratuito) – [Baixar aqui](https://vb-audio.com/Cable/)
- **Pip** atualizado

---

## Instalação
No terminal (PowerShell ou CMD):
```bash
pip install pygame keyboard
pip install sounddevice soundfile
pip install PyQt5
```

---

## Executando
Para rodar diretamente:
```bash
python main.py
```

Para gerar um `.exe` (sem precisar do Python instalado):
```bash
python -m PyInstaller --onefile --noconsole --icon=SoundPad.ico --name="SoundpadPro" main.py
```

O arquivo final estará na pasta `dist/` como `SoundpadPro.exe`.

---

## Como usar
1. **Configure seu microfone virtual (VB-Cable)** no Discord/Meet como dispositivo de entrada.
2. Abra o **Soundpad Pro**.
3. Escolha o microfone correto na lista do app.
4. Adicione sons pelo botão `+ Adicionar Som`.
5. Use os atalhos (`F1-F12`) para tocar os sons.
6. Pressione **F8** para enviar o som para o microfone.
7. Pressione **F12** para parar.

---

## Estrutura do Projeto
```
Soundpad/
│
├── dist/                 # Executável gerado
├── icons/                # Ícones do player
├── sons/                 # Sons adicionados
├── main.py               # Código principal
├── sound_engine.py       # Motor de áudio
├── settings.json         # Configurações
├── sounds.json           # Sons salvos
├── SoundPad.ico          # Ícone do app
├── README.md             # Documentação
```

---

## Autor
Projeto desenvolvido por Matheus.
