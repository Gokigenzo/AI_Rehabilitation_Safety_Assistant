import tkinter as tk
from tkinter import scrolledtext
import sounddevice as sd
import queue
import json
import time
import threading
import re
from vosk import Model, KaldiRecognizer
import os

from intents import classify_intent
from tts_utils import speak

MODEL_PATH = "models/vosk_model"
SAMPLE_RATE = 16000
INPUT_DEVICE_INDEX = None
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Please download Vosk model into models/vosk-model")

try:
    sd.default.samplerate = SAMPLE_RATE
    sd.default.channels = 1
    if INPUT_DEVICE_INDEX is not None:
        sd.default.device = (INPUT_DEVICE_INDEX, None)
except Exception as e:
    print("[Audio init warning] Could not initialize default input device:", e)

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)
audio_q = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio status:", status)
    audio_q.put(bytes(indata))

def listen_and_recognize(timeout=8):
    recognizer.AcceptWaveform(b"")
    start_time = time.time()
    text = ""
    last_partial = ""

    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=4000, dtype='int16',
                               channels=1, callback=audio_callback, device=INPUT_DEVICE_INDEX):
            while True:
                if (time.time() - start_time) > timeout:
                    break
                try:
                    data = audio_q.get(timeout=timeout)
                except queue.Empty:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    if text.strip():
                        break
                else:
                    try:
                        pres = json.loads(recognizer.PartialResult())
                        ptxt = pres.get("partial", "")
                        if ptxt:
                            last_partial = ptxt
                    except Exception:
                        pass
    except Exception as e:
        print("[Audio error] Could not open input stream:", e)
        return ""
    if not text:
        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "")
        if not text and last_partial:
            text = last_partial
    return text.strip()

root = tk.Tk()
root.title("Elder Voice Command Assistant (Emergency Enabled)")
root.geometry("760x520")
root.configure(bg="#F3F3F3")

title_label = tk.Label(root, text="🎙 Elder Voice Command Assistant", font=("Arial", 20, "bold"), bg="#F3F3F3")
title_label.pack(pady=10)

output_box = scrolledtext.ScrolledText(root, width=85, height=14, font=("Arial", 13))
output_box.pack(padx=10, pady=10)
output_box.insert(tk.END, "Click 'Speak' and say something...\n")

def log_message(msg):
    ts = time.strftime("%I:%M:%S %p")
    output_box.insert(tk.END, f"[{ts}] {msg}\n")
    output_box.see(tk.END)
    root.update()

reminders = []

def set_reminder(delay_seconds):
    def reminder_action():
        speak("It’s time to take your medicine.")
        log_message("\n💊 Reminder: It's time to take your medicine!")
    threading.Timer(delay_seconds, reminder_action).start()

def parse_time_phrase(text):
    text = text.lower()
    match = re.search(r'in (\d+) minute', text)
    if match:
        mins = int(match.group(1))
        return mins * 60
    match = re.search(r'in (\d+) hour', text)
    if match:
        hrs = int(match.group(1))
        return hrs * 3600
    match = re.search(r'at (\d+)(?:\s*)(am|pm)', text)
    if match:
        hour = int(match.group(1))
        ampm = match.group(2)
        if ampm == "pm" and hour != 12:
            hour += 12
        now = time.localtime()
        reminder_time = time.struct_time((
            now.tm_year, now.tm_mon, now.tm_mday, hour, 0, 0,
            now.tm_wday, now.tm_yday, now.tm_isdst
        ))
        target = time.mktime(reminder_time)
        diff = target - time.time()
        if diff < 0:
            diff += 86400
        return diff
    return None

_emergency_active = False
_emergency_thread = None

def _speak_repeated_emergency(stop_event):
    """Speak the emergency message repeatedly until stop_event is set."""
    while not stop_event.is_set():
        speak("Emergency! Help is needed. Notifying caregiver.")
        for _ in range(6):
            if stop_event.is_set():
                break
            time.sleep(0.5)

def notify_caregiver_simulated(details="User requested help"):
    """Simulated caregiver notification — replace with real API later."""
    # For demo: log to GUI and print
    log_message("!!! SIMULATION: Notifying caregiver: " + details)
    print("SIMULATION: notify caregiver ->", details)

def show_emergency_popup(details="Help requested"):
    global _emergency_active, _emergency_thread
    if _emergency_active:
        return
    _emergency_active = True

    popup = tk.Toplevel(root)
    popup.title("!! EMERGENCY ALERT !!")
    popup.geometry("680x320")
    popup.configure(bg="red")
    popup.attributes("-topmost", True)

    lbl = tk.Label(popup, text="EMERGENCY!", font=("Arial", 36, "bold"), bg="red", fg="white")
    lbl.pack(pady=10)

    detail_label = tk.Label(popup, text=details, font=("Arial", 18), bg="red", fg="white")
    detail_label.pack(pady=5)

    info_label = tk.Label(popup, text="The assistant will keep alerting. Press 'Notify' to simulate notifying caregiver, or 'Cancel' to stop.", 
                          font=("Arial", 12), bg="red", fg="white", wraplength=640, justify="center")
    info_label.pack(pady=8)

    button_frame = tk.Frame(popup, bg="red")
    button_frame.pack(pady=12)

    stop_event = threading.Event()

    def on_notify():
        notify_caregiver_simulated(details)
        stop_event.set()
        cleanup()

    def on_cancel():
        log_message("Emergency canceled by user.")
        stop_event.set()
        cleanup()

    def cleanup():
        global _emergency_active, _emergency_thread
        _emergency_active = False
        try:
            popup.destroy()
        except:
            pass

    notify_btn = tk.Button(button_frame, text="Notify Caregiver (Simulate)", font=("Arial", 14, "bold"),
                           bg="#FFD700", command=on_notify, padx=12, pady=8)
    notify_btn.pack(side="left", padx=12)

    cancel_btn = tk.Button(button_frame, text="Cancel Alert", font=("Arial", 14, "bold"),
                           bg="#D3D3D3", command=on_cancel, padx=12, pady=8)
    cancel_btn.pack(side="left", padx=12)

    _emergency_thread = threading.Thread(target=_speak_repeated_emergency, args=(stop_event,), daemon=True)
    _emergency_thread.start()

    log_message("!!! Emergency mode active. Popup shown and repeated alerting started.")

def handle_intent(intent, transcript):
    if intent == "time":
        t = time.strftime("%I:%M %p")
        response = f"The time is {t}."
    elif intent == "date":
        d = time.strftime("%A, %B %d, %Y")
        response = f"Today is {d}."
    elif intent == "help":
        response = "Emergency detected. Activating emergency mode."
        log_message("Assistant: " + response)
        speak(response)
        show_emergency_popup(details=transcript or "User requested help")
        return
    elif intent == "medicine":
        delay = parse_time_phrase(transcript)
        if delay:
            set_reminder(delay)
            mins = int(delay // 60)
            response = f"Okay, I will remind you in {mins} minute(s)."
        else:
            response = "When should I remind you? You can say, remind me in 2 minutes or at 8 PM."
    elif intent == "lights_on":
        response = "Turning on the light (simulated)."
    elif intent == "lights_off":
        response = "Turning off the light (simulated)."
    else:
        response = "I'm sorry, I didn’t understand that."

    log_message("Assistant: " + response)
    speak(response)

def start_listening():
    log_message("\nListening... please speak now.")
    speak("I'm listening.")
    text = listen_and_recognize()
    if not text:
        log_message("No speech detected.")
        speak("I didn't hear you clearly.")
        return
    log_message("You said: " + text)
    intent = classify_intent(text)
    log_message(f"→ Detected intent: {intent}")
    handle_intent(intent, text)

controls_frame = tk.Frame(root, bg="#F3F3F3")
controls_frame.pack(pady=6)

speak_button = tk.Button(controls_frame, text="🎤 Speak", font=("Arial", 16), bg="#4CAF50", fg="white",
                         padx=30, pady=10, command=start_listening)
speak_button.pack(side="left", padx=8)

help_demo_btn = tk.Button(controls_frame, text="🔴 Emergency Demo", font=("Arial", 12), bg="#FF5555", fg="white",
                          padx=12, pady=8,
                          command=lambda: (log_message("Emergency demo triggered."), show_emergency_popup("Demo: Emergency triggered manually.")))
help_demo_btn.pack(side="left", padx=8)

root.mainloop()