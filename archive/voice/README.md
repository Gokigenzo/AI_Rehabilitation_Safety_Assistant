# 🎙 Elder Voice Command Assistant (Emergency Enabled)

An offline, voice-controlled system designed specifically to assist elderly users with daily interactions and emergency situations. The system prioritizes reliability, simplicity, and safety by operating completely offline.

## 🌟 Overview

Elderly people and patients with reduced mobility often face difficulties operating electronic devices or calling for help quickly during emergencies (like falls, sudden illness, or chest pain). Traditional interfaces such as keyboards, mice, and touchscreens may not be suitable when they are physically weak, visually impaired, or under medication.

The **Elder Voice Command Assistant** is a desktop application providing an offline voice-based interface. It listens to spoken commands, recognizes speech using the **Vosk speech recognition engine**, classifies user intent through a rule-based classifier, and responds using the **pyttsx3 text-to-speech engine**. A graphical user interface (GUI) built with **Tkinter** displays interaction logs and provides large, accessible buttons for initiating commands or simulating an emergency.

## ✨ Core Features

- **Offline Speech Recognition:** Uses Vosk for completely offline speech-to-text conversion (no internet required).
- **Emergency Alert System:** A dedicated emergency mode that repeatedly announces an audible warning, displays a high-priority popup, and simulates caregiver notification.
- **Medicine Reminders:** Allows users to set time-based reminders for medication ("Remind me in 5 minutes").
- **Basic Assistance:** Responds to frequent queries such as current time and date.
- **Simulated Smart Home Control:** Basic intents configured to simulate turning lights on and off.
- **Elder-Friendly Interface:** Very simple Tkinter GUI showing conversation history and easily accessible action buttons.

## 📂 Project Structure

- `main.py`: The entry point of the application containing the GUI, audio recording logic, and emergency handling.
- `intents.py`: A rule-based intent classification module mapping spoken phrases to system actions.
- `tts_utils.py`: A utility wrapper for pyttsx3, configured with an appropriate voice and speaking rate.
- `requirements.txt`: Python package dependencies.
- `models/vosk_model`: The directory where the Vosk speech recognition model should be placed.
- `Elder_Voice_Command_Assistant_Report.md`: In-depth project report, analysis, and architecture details.
- `index.html`: A minimal landing page for the project.

## 🛠️ Prerequisites

1. **Python 3.x**
2. A working microphone and speaker setup.
3. The **Vosk English model**.
   - Download the model from the [Vosk Models Page](https://alphacephei.com/vosk/models).
   - A good starting point is the smaller model: `vosk-model-small-en-us-0.15`.
   - Extract the downloaded zip file and place the folder inside the `models/` directory.
   - Rename the extracted folder to `vosk_model` (so the path `models/vosk_model` exists).

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SiranjeeviE/Elder_Command_Assisstant.git
   cd Elder_Command_Assisstant
   ```

2. **(Optional) Create a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: `tkinter` is used for the GUI. On Windows and macOS, it comes pre-installed with Python. On Linux, you may need to install it via your package manager, e.g., `sudo apt-get install python3-tk`)*

## 💡 Usage

Run the main application file:
```bash
python main.py
```

### Voice Commands Supported

Click the **"🎤 Speak"** button or interact verbally when the assistant is listening. Supported phrases include:
- **Time/Date:** "What time is it?", "Tell me the date", "Today's date"
- **Medicine:** "Take medicine", "Set reminder", "Remind me in 5 minutes"
- **Smart Home (Simulated):** "Turn on light", "Lights off"
- **Emergency:** "Help", "I need help", "Call for help", "Call nurse"

### Emergency Mode

If the assistant detects an emergency intent (e.g., "Help"), or if you press the **"🔴 Emergency Demo"** button on the GUI, the application will:
1. Show a prominent, red warning popup that stays on top of other windows.
2. Continually announce "Emergency! Help is needed. Notifying caregiver."
3. Present options to either "Notify Caregiver (Simulate)" or "Cancel Alert".

## 🔮 Future Enhancements
- Integration with real SMS or phone calling APIs (e.g., Twilio) for actual caregiver notification.
- NLP-based intent detection replacing the current rule-based approach.
- Wake-word activation (e.g., "Hey Assistant") for completely hands-free operation without needing to click the Speak button.
- Support for multiple languages.
- Integration with real IoT devices in a smart home environment.

## 📚 References
- [Vosk Speech Recognition](https://alphacephei.com/vosk)
- [pyttsx3 Text-to-Speech](https://pyttsx3.readthedocs.io)
- [Python Tkinter](https://docs.python.org/3/library/tkinter.html)
- [sounddevice Library](https://python-sounddevice.readthedocs.io)
