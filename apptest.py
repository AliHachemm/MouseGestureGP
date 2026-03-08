import eel
import cv2
import mediapipe as mp
import pyautogui
import threading
import time
import math
import speech_recognition as sr
from gtts import gTTS
import playsound
import os

# =============================
# CONFIG
# =============================
SCREEN_W, SCREEN_H = pyautogui.size()
EMA_ALPHA = 0.3
DEAD_ZONE = 6
PINCH_THRESHOLD = 35
DRAG_HOLD_TIME = 0.18

# =============================
# GLOBAL STATE
# =============================
mouse_enabled = True
speech_enabled = False
auto_type_enabled = True

recognized_text = ""
gesture_state = "idle"

current_pos = {"x": 0, "y": 0, "visible": False}

prev_x, prev_y = SCREEN_W // 2, SCREEN_H // 2
pinch_start = 0
is_dragging = False

lock = threading.Lock()

# =============================
# EEL INIT
# =============================
eel.init("web")

# =============================
# MEDIAPIPE SETUP
# =============================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
cap = cv2.VideoCapture(0)

# =============================
# SPEECH SETUP
# =============================
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True


def handle_speech_command(text):
    global mouse_enabled

    t = text.lower().strip()

    # Wake word
    if not t.startswith("computer"):
        return None

    t = t.replace("computer", "").strip()

    if t == "click":
        pyautogui.click()
        speak("Click")
        return "[command] click"

    if t == "double click":
        pyautogui.doubleClick()
        speak("Double click")
        return "[command] double click"

    if t == "scroll down":
        pyautogui.scroll(-400)
        speak("Scrolling down")
        return "[command] scroll down"

    if t == "scroll up":
        pyautogui.scroll(400)
        speak("Scrolling up")
        return "[command] scroll up"

    if t == "stop mouse":
        mouse_enabled = False
        speak("Mouse control disabled")
        return "[command] mouse disabled"

    if t == "start mouse":
        mouse_enabled = True
        speak("Mouse control enabled")
        return "[command] mouse enabled"

    if t == "open chrome":
        os.system("start chrome")
        speak("Opening Chrome")
        return "[command] opening chrome"

    if t == "open notepad":
        os.system("start notepad")
        speak("Opening Notepad")
        return "[command] opening notepad"

    if t == "volume up":
        pyautogui.press("volumeup")
        speak("Volume up")
        return "[command] volume up"

    if t == "volume down":
        pyautogui.press("volumedown")
        speak("Volume down")
        return "[command] volume down"

    if t == "mute":
        pyautogui.press("volumemute")
        speak("Muted")
        return "[command] mute"

    if t == "take screenshot":
        pyautogui.screenshot("screenshot.png")
        speak("Screenshot taken")
        return "[command] screenshot taken"

    return None

# =============================
# VOICE FEEDBACK
# =============================
def speak(text):
    try:
        tts = gTTS(text)
        tts.save("assistant_voice.mp3")
        playsound.playsound("assistant_voice.mp3")
        os.remove("assistant_voice.mp3")
    except:
        pass


# =============================
# SPEECH THREAD (FIXED)
# =============================
def speech_thread():
    global recognized_text

    print("🎤 Speech thread started")

    while True:
        if not speech_enabled:
            time.sleep(0.2)
            continue

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = recognizer.listen(source, phrase_time_limit=5)

            text = recognizer.recognize_google(audio)
            print("Recognized:", text)

            command = handle_speech_command(text)

            with lock:
                recognized_text = command if command else text

            if auto_type_enabled and not command:
                pyautogui.write(text + " ", interval=0.02)

        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            with lock:
                recognized_text = "[speech api error]"
        except Exception as e:
            print("Speech error:", e)


# =============================
# HAND TRACKING THREAD
# =============================
def hand_thread():
    global prev_x, prev_y, pinch_start, is_dragging, gesture_state

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            ix, iy = lm[8].x, lm[8].y
            mx, my = lm[12].x, lm[12].y

            sx, sy = int(ix * SCREEN_W), int(iy * SCREEN_H)

            if abs(sx - prev_x) < DEAD_ZONE and abs(sy - prev_y) < DEAD_ZONE:
                continue

            smooth_x = int(EMA_ALPHA * sx + (1 - EMA_ALPHA) * prev_x)
            smooth_y = int(EMA_ALPHA * sy + (1 - EMA_ALPHA) * prev_y)

            prev_x, prev_y = smooth_x, smooth_y
            current_pos.update({"x": smooth_x, "y": smooth_y, "visible": True})

            if mouse_enabled:
                pyautogui.moveTo(smooth_x, smooth_y)

            dist = math.hypot((ix - mx) * w, (iy - my) * h)
            now = time.time()

            if dist < PINCH_THRESHOLD:
                if pinch_start == 0:
                    pinch_start = now
                elif now - pinch_start > DRAG_HOLD_TIME and not is_dragging:
                    pyautogui.mouseDown()
                    is_dragging = True
                    gesture_state = "dragging"
            else:
                if is_dragging:
                    pyautogui.mouseUp()
                elif pinch_start != 0:
                    pyautogui.click()
                    gesture_state = "click"

                pinch_start = 0
                is_dragging = False
        else:
            current_pos["visible"] = False
            gesture_state = "no hand"

        time.sleep(0.01)


# =============================
# EEL EXPOSED FUNCTIONS
# =============================
@eel.expose
def toggle_mouse(v):
    global mouse_enabled
    mouse_enabled = bool(v)
    print("Mouse enabled:", mouse_enabled)
    return mouse_enabled


@eel.expose
def toggle_speech(v):
    global speech_enabled
    speech_enabled = bool(v)
    print("Speech enabled:", speech_enabled)
    return speech_enabled


@eel.expose
def toggle_auto(v):
    global auto_type_enabled
    auto_type_enabled = bool(v)
    return auto_type_enabled


@eel.expose
def get_hand():
    return {
        "x": current_pos["x"],
        "y": current_pos["y"],
        "visible": current_pos["visible"],
        "gesture": gesture_state
    }


@eel.expose
def get_text():
    with lock:
        return recognized_text


# =============================
# THREADS
# =============================
threading.Thread(target=hand_thread, daemon=True).start()
threading.Thread(target=speech_thread, daemon=True).start()

# =============================
# START APP
# =============================
eel.start("index.html", size=(900, 650), block=True)

