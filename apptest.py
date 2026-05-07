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
import subprocess
import webbrowser
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("YOUR_API_KEY"))

# CONFIG

SCREEN_W, SCREEN_H = pyautogui.size()
EMA_ALPHA = 0.5          
DEAD_ZONE = 8        
PINCH_THRESHOLD = 35
DRAG_HOLD_TIME = 0.18
SWIPE_COOLDOWN = 0.6     
PINCH_FRAMES = 2         
SCROLL_COOLDOWN = 0.3    


# GLOBAL STATE

mouse_enabled = True
speech_enabled = True
auto_type_enabled = True

last_gesture_time = 0
last_swipe_time = 0        # NEW: dedicated swipe cooldown tracker
GESTURE_DELAY = 0.4
prev_hand_x = None         # Changed: None instead of 0 — avoids false swipe on first frame
frame_count = 0

recognized_text = ""
gesture_state = "idle"

prev_x, prev_y = SCREEN_W // 2, SCREEN_H // 2
pinch_start = 0
is_dragging = False
pinch_frame_count = 0      # NEW: counts consecutive pinch frames

lock = threading.Lock()


# INIT

eel.init("web")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True


# VOICE OUTPUT

# VOICE OUTPUT — Non-blocking

def speak(text):
    """Run TTS in a background thread so it never blocks the main loop."""
    def _speak():
        try:
            tts = gTTS(text)
            tts.save("voice.mp3")
            playsound.playsound("voice.mp3")
            os.remove("voice.mp3")
        except Exception as e:
            print(f"[SPEAK ERROR] {e}")
    threading.Thread(target=_speak, daemon=True).start()

# AI

def ask_ai(question):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}]
        )
        answer = response.choices[0].message.content
        speak(answer)
        return answer
    except:
        fallback = "AI not available"
        speak(fallback)
        return fallback


# VOICE COMMANDS

def handle_speech_command(text):
    t = text.lower().strip()

    if not t.startswith("computer"):
        return None

    t = t.replace("computer", "").strip()

    if t == "click":
        pyautogui.click()
        speak("Click")
        return "[click]"

    if t == "scroll down":
        pyautogui.scroll(-400)
        speak("Scrolling down")
        return "[scroll down]"

    if t == "scroll up":
        pyautogui.scroll(400)
        speak("Scrolling up")
        return "[scroll up]"
    
        # ---------------- SYSTEM APPS ----------------
    if t == "open notepad":
        os.system("start notepad")
        speak("Opening Notepad")
        return "[notepad]"

    if t == "open files":
        os.system("explorer")
        speak("Opening File Explorer")
        return "[files]"

    if t == "open powerpoint":
        os.system("start powerpnt")
        speak("Opening PowerPoint")
        return "[powerpoint]"

    if t == "open word":
        os.system("start winword")
        speak("Opening Word")
        return "[word]"

    # ---------------- GENERIC OPEN APP ----------------
    # ---------------- SMART COMMANDS ----------------

    # YouTube search
    if "youtube" in t and "search" in t:
        query = t.split("search")[-1].strip()
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        speak(f"Searching YouTube for {query}")
        return "[youtube search]"

    # Google search
    if "search google for" in t:
        query = t.replace("search google for", "").strip()
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        speak(f"Searching Google for {query}")
        return "[google search]"

    # Open website directly
    if t.startswith("open ") and ".com" in t:
        site = t.replace("open ", "")
        webbrowser.open(f"https://{site}")
        speak(f"Opening {site}")
        return "[website]"

    # ---------------- SYSTEM APPS ----------------

    if t == "open notepad":
        os.system("start notepad")
        speak("Opening Notepad")
        return "[notepad]"

    if t == "open files":
        os.system("explorer")
        speak("Opening File Explorer")
        return "[files]"

    if t == "open powerpoint":
        os.system("start powerpnt")
        speak("Opening PowerPoint")
        return "[powerpoint]"

    if t == "open word":
        os.system("start winword")
        speak("Opening Word")
        return "[word]"

    if t == "open chrome":
        os.system("start chrome")
        speak("Opening Chrome")
        return "[chrome]"

    if "open spotify" in t:
        os.system("start spotify")
        speak("Opening Spotify")
        return "[spotify]"

    if "open youtube" in t:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")
        return "[youtube]"
        # ---------------- CLOSE APPS ----------------

    # Specific closes (more reliable)
    if t == "close chrome":
        os.system("taskkill /f /im chrome.exe")
        speak("Closing Chrome")
        return "[close chrome]"

    if t == "close notepad":
        os.system("taskkill /f /im notepad.exe")
        speak("Closing Notepad")
        return "[close notepad]"

    if t == "close word":
        os.system("taskkill /f /im winword.exe")
        speak("Closing Word")
        return "[close word]"

    if t == "close powerpoint":
        os.system("taskkill /f /im powerpnt.exe")
        speak("Closing PowerPoint")
        return "[close powerpoint]"

    if t == "close spotify":
        os.system("taskkill /f /im spotify.exe")
        speak("Closing Spotify")
        return "[close spotify]"

    # Generic close: "close <app>"
    if t.startswith("close "):
        app = t.replace("close ", "").strip()

        # map common names to executables
        mapping = {
            "chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "word": "winword.exe",
            "powerpoint": "powerpnt.exe",
            "spotify": "spotify.exe",
            "discord": "discord.exe",
            "explorer": "explorer.exe",
        }

        exe = mapping.get(app, f"{app}.exe")

        try:
            subprocess.run(f"taskkill /f /im {exe}", shell=True)
            speak(f"Closing {app}")
            return f"[closing {app}]"
        except:
            speak("Could not close application")
            return "[error]"

    # ---------------- GENERIC OPEN ----------------

    if t.startswith("open "):
        app = t.replace("open ", "")
        try:
            os.system(f"start {app}")
            speak(f"Opening {app}")
            return f"[opening {app}]"
        except:
            speak("Could not open application")
            return "[error]"

    # ---------------- SYSTEM CONTROL ----------------

    if t == "shutdown":
        speak("Shutting down")
        os.system("shutdown /s /t 1")
        return "[shutdown]"

    if t == "restart":
        speak("Restarting")
        os.system("shutdown /r /t 1")
        return "[restart]"

    # ---------------- BRIGHTNESS ----------------

    if t == "brightness up":
        subprocess.run(
            "powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)",
            shell=True
        )
        speak("Brightness increased")
        return "[brightness up]"

    if t == "brightness down":
        subprocess.run(
            "powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)",
            shell=True
        )
        speak("Brightness decreased")
        return "[brightness down]"

    # ---------------- AI ----------------

    if t.startswith("what is") or t.startswith("who is") or t.startswith("explain"):
        return ask_ai(t)

    return None

# =============================
# GESTURE DETECTION
# =============================
# =============================
# GESTURE DETECTION
# =============================
def detect_gesture(lm):
    """
    Returns: 'one_finger', 'two_fingers', or None.
    Checks ring + pinky are DOWN to reduce false positives.
    """
    index_tip,  index_pip  = lm[8],  lm[6]
    middle_tip, middle_pip = lm[12], lm[10]
    ring_tip,   ring_pip   = lm[16], lm[14]
    pinky_tip,  pinky_pip  = lm[20], lm[18]

    index_up  = index_tip.y  < index_pip.y
    middle_up = middle_tip.y < middle_pip.y
    ring_down = ring_tip.y   > ring_pip.y    # NEW: must be curled
    pinky_down = pinky_tip.y > pinky_pip.y   # NEW: must be curled

    if index_up and middle_up and ring_down and pinky_down:
        return "two_fingers"

    if index_up and not middle_up and ring_down and pinky_down:
        return "one_finger"

    return None

# HAND THREAD

def hand_thread():
    global prev_x, prev_y, gesture_state
    global last_gesture_time, last_swipe_time, mouse_enabled, frame_count
    global prev_hand_x, pinch_frame_count

    print("[HAND] Hand tracking thread started")

    while True:
        ret, frame = cap.read()   # ALWAYS read to drain buffer
        if not ret:
            time.sleep(0.01)
            continue

        frame_count += 1
        if frame_count % 2 != 0:  # Process every other frame
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False          # NEW: minor perf boost for mediapipe
        res = hands.process(rgb)
        rgb.flags.writeable = True

        now = time.time()

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark

            ix, iy = lm[8].x, lm[8].y
            mx, my = lm[12].x, lm[12].y

            dist = math.hypot((ix - mx) * w, (iy - my) * h)
            gesture = detect_gesture(lm)

            # ---------- CURSOR (always runs) ----------
            sx = int(ix * SCREEN_W)
            sy = int(iy * SCREEN_H)

            # EMA smoothing
            smooth_x = int(EMA_ALPHA * sx + (1 - EMA_ALPHA) * prev_x)
            smooth_y = int(EMA_ALPHA * sy + (1 - EMA_ALPHA) * prev_y)

            # Dead zone: only move if cursor moved meaningfully
            if abs(smooth_x - prev_x) > DEAD_ZONE or abs(smooth_y - prev_y) > DEAD_ZONE:
                prev_x, prev_y = smooth_x, smooth_y
                if mouse_enabled:
                    pyautogui.moveTo(smooth_x, smooth_y)

            # ---------- SWIPE (priority 1 — checked first) ----------
            current_x = ix * w
            if prev_hand_x is not None:
                diff = current_x - prev_hand_x
                if now - last_swipe_time > SWIPE_COOLDOWN:
                    if diff > 80:
                        pyautogui.hotkey('alt', 'right')
                        gesture_state = "swipe → forward"
                        last_swipe_time = now
                        print(f"[GESTURE] Swipe forward (diff={diff:.0f}px)")
                    elif diff < -80:
                        pyautogui.hotkey('alt', 'left')
                        gesture_state = "swipe ← back"
                        last_swipe_time = now
                        print(f"[GESTURE] Swipe back (diff={diff:.0f}px)")
            prev_hand_x = current_x

            # ---------- SCROLL (priority 2) ----------
            if now - last_swipe_time > SWIPE_COOLDOWN:  # don't scroll right after swipe
                if gesture == "two_fingers" and now - last_gesture_time > SCROLL_COOLDOWN:
                    pyautogui.scroll(-300)
                    gesture_state = "scroll ↓"
                    last_gesture_time = now
                    print("[GESTURE] Scroll down")

                elif gesture == "one_finger" and now - last_gesture_time > SCROLL_COOLDOWN:
                    pyautogui.scroll(300)
                    gesture_state = "scroll ↑"
                    last_gesture_time = now
                    print("[GESTURE] Scroll up")

            # ---------- PINCH/CLICK (priority 3 — debounced) ----------
            if dist < PINCH_THRESHOLD:
                pinch_frame_count += 1
                if pinch_frame_count >= PINCH_FRAMES and now - last_gesture_time > GESTURE_DELAY:
                    pyautogui.click()
                    gesture_state = "click 👆"
                    last_gesture_time = now
                    pinch_frame_count = 0
                    print("[GESTURE] Pinch click")
            else:
                pinch_frame_count = 0   # reset if pinch breaks

        else:
            gesture_state = "no hand"
            prev_hand_x = None   # reset so first-frame swipe doesn't false-fire
            pinch_frame_count = 0

        # ---------- DISPLAY ----------
        cv2.putText(
            frame, f"Gesture: {gesture_state}",
            (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
        )
        cv2.imshow("Hand Tracking", frame)
        cv2.waitKey(1)

        time.sleep(0.005)

# SPEECH THREAD

def speech_thread():
    global recognized_text
    print("[SPEECH] Speech thread started")

    while True:
        if not speech_enabled:
            time.sleep(0.2)
            continue

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, phrase_time_limit=5)

            text = recognizer.recognize_google(audio)
            print(f"[SPEECH] Heard: '{text}'")

            command = handle_speech_command(text)

            with lock:
                recognized_text = command if command else text

            if auto_type_enabled and not command:
                pyautogui.write(text + " ", interval=0.02)

        except sr.UnknownValueError:
            pass   # Silence — not an error
        except sr.RequestError as e:
            print(f"[SPEECH ERROR] Google API error: {e}")
        except Exception as e:
            print(f"[SPEECH ERROR] Unexpected: {e}")

# EEL

@eel.expose
def toggle_mouse(v):
    global mouse_enabled
    mouse_enabled = bool(v)
    return mouse_enabled

@eel.expose
def toggle_speech(v):
    global speech_enabled
    speech_enabled = bool(v)
    return speech_enabled

@eel.expose
def toggle_auto(v):
    global auto_type_enabled
    auto_type_enabled = bool(v)
    return auto_type_enabled

@eel.expose
def get_hand():
    return {"gesture": gesture_state}

@eel.expose
def get_text():
    return recognized_text

# =============================
# START
# =============================
threading.Thread(target=hand_thread, daemon=True).start()
threading.Thread(target=speech_thread, daemon=True).start()

eel.start("index.html", size=(900, 650))
