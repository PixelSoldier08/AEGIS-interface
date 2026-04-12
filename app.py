import cv2
import threading
import socket
import time
from flask import Flask
from flask_socketio import SocketIO, emit

# --- STABLE MEDIAPIPE IMPORT FOR PYTHON 3.14 ---
try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    print("[SUCCESS] Found MediaPipe Task API")
except:
    import mediapipe as mp
    # Fallback to standard if possible
    mp_hands = mp.solutions.hands if hasattr(mp, 'solutions') else None

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- GREETING PROCESS ---
@socketio.on('connect')
def handle_connect():
    print("\n[AEGIS] COMMANDER DETECTED. HELLO!")
    # This restores the greeting voice
    emit('speak', {'text': 'Aegis System Protocol Online. Hello, Commander.'})

def run_vision():
    # Force use of standard MediaPipe Hands if the task API is too complex
    import mediapipe as mp
    # We use a try block to bypass the 'solutions' error if it hits
    try:
        hands_engine = mp.python.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5
        )
    except:
        print("[!] Still hitting Attribute Error. Using 'Mock Mode' for movement...")
        hands_engine = None

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    last_voice_time = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        if hands_engine:
            results = hands_engine.process(rgb)
            if results.multi_hand_landmarks:
                for res in results.multi_hand_landmarks:
                    # MOVEMENT: Send palm center
                    palm = res.landmark[9]
                    socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})
                    
                    # VOICE TRIGGER: Raise hand high
                    now = time.time()
                    if res.landmark[8].y < res.landmark[0].y - 0.2:
                        if now - last_voice_time > 10:
                            socketio.emit('speak', {'text': 'Tracking your commands.'})
                            last_voice_time = now

        cv2.imshow('Aegis Vision (3.14 Stable)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
