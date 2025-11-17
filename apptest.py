# apptest.py
import eel
import cv2
import mediapipe as mp
import pyautogui
import threading
import time
import math
import speech_recognition as sr

# -----------------------------
# Config / global state
# -----------------------------
WEB_FOLDER = 'web'
INDEX_PAGE = 'index.html'
SCREEN_W, SCREEN_H = pyautogui.size()

# control flags (shared between UI and threads)
mouse_control_enabled = True
speech_control_enabled = False
auto_type_enabled = True  # when True, recognized speech will be typed into the active window
recognized_text = ""      # latest recognized text (for UI display)

# hand position shared state
current_pos = {"x": 0, "y": 0, "visible": False}

# -----------------------------
# Setup Eel
# -----------------------------
eel.init(WEB_FOLDER)

# -----------------------------
# Mediapipe hand tracker setup
# -----------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

# -----------------------------
# Speech recognition setup
# -----------------------------
recognizer = sr.Recognizer()

def speech_thread_func():
    global speech_control_enabled, recognized_text, auto_type_enabled
    # We'll open and close the microphone stream repeatedly to allow toggling
    while True:
        if not speech_control_enabled:
            time.sleep(0.2)
            continue

        try:
            with sr.Microphone() as source:
                # calibrate ambient noise briefly
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # listen for a short phrase (phrase_time_limit can be adjusted)
                audio = recognizer.listen(source, phrase_time_limit=6)
                # attempt recognition (Google Web Speech API)
                try:
                    text = recognizer.recognize_google(audio)
                    # update shared text for UI
                    recognized_text = text
                    # If auto typing is enabled, type to the currently focused window
                    if auto_type_enabled:
                        # pyautogui types relatively slowly to avoid missing keys on some systems
                        pyautogui.write(text + " ", interval=0.02)
                except sr.UnknownValueError:
                    # couldn't understand audio
                    recognized_text = "[unintelligible]"
                except sr.RequestError as e:
                    # network / API error
                    recognized_text = f"[speech API error: {e}]"
        except Exception as e:
            # microphone not available or other error; keep thread alive
            recognized_text = f"[mic error: {e}]"
            # avoid tight loop if mic failing
            time.sleep(1)

# -----------------------------
# Hand tracking thread
# -----------------------------
def track_hand():
    global current_pos, mouse_control_enabled
    last_click_time = 0
    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)  # mirror
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            # index fingertip = landmark 8, middle fingertip = 12
            ix = hand_landmarks.landmark[8].x
            iy = hand_landmarks.landmark[8].y
            mx = hand_landmarks.landmark[12].x
            my = hand_landmarks.landmark[12].y

            # convert to pixel coordinates
            px = int(ix * w)
            py = int(iy * h)
            screen_x = int(ix * SCREEN_W)
            screen_y = int(iy * SCREEN_H)

            current_pos["x"] = screen_x
            current_pos["y"] = screen_y
            current_pos["visible"] = True

            if mouse_control_enabled:
                # move mouse (no smoothing here; add smoothing if needed)
                pyautogui.moveTo(screen_x, screen_y)

                # pinch detection for click (distance in pixels on camera frame)
                dx = (px - int(mx * w))
                dy = (py - int(my * h))
                dist = math.hypot(dx, dy)

                # click threshold (may need calibration)
                if dist < 40 and (time.time() - last_click_time) > 0.3:
                    pyautogui.click()
                    last_click_time = time.time()
        else:
            current_pos["visible"] = False

        # small sleep to free CPU (tune as needed)
        time.sleep(0.01)

# -----------------------------
# Eel exposed functions (UI -> Python)
# -----------------------------
@eel.expose
def toggle_mouse_control(enabled: bool):
    global mouse_control_enabled
    mouse_control_enabled = bool(enabled)
    return mouse_control_enabled

@eel.expose
def toggle_speech_control(enabled: bool):
    global speech_control_enabled
    speech_control_enabled = bool(enabled)
    return speech_control_enabled

@eel.expose
def toggle_auto_type(enabled: bool):
    global auto_type_enabled
    auto_type_enabled = bool(enabled)
    return auto_type_enabled

@eel.expose
def get_hand_pos():
    # return dictionary for the UI to show
    return current_pos

@eel.expose
def get_recognized_text():
    # UI can poll this to show last recognized phrase
    return recognized_text

# -----------------------------
# Start background threads
# -----------------------------
t_hand = threading.Thread(target=track_hand, daemon=True)
t_hand.start()

t_speech = threading.Thread(target=speech_thread_func, daemon=True)
t_speech.start()

# -----------------------------
# Start Eel
# -----------------------------
try:
    eel.start(INDEX_PAGE, size=(900, 600), block=False)
    # keep the program alive so daemon threads run
    while True:
        eel.sleep(0.1)
except (KeyboardInterrupt, SystemExit):
    pass
finally:
    try:
        cap.release()
        hands.close()
    except:
        pass
