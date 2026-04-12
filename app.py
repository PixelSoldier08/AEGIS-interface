import cv2
import threading
import socket
import time
from flask import Flask
from flask_socketio import SocketIO, emit

# --- DEEP IMPORT FIX ---
# This ignores the 'mp.solutions' shortcut that is causing your error
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- GREETING LOGIC ---
@socketio.on('connect')
def handle_connect():
    print("\n[AEGIS] COMMANDER DETECTED. INITIATING GREETING...")
    # This sends the voice command to the phone
    emit('speak', {'text': 'Aegis System Online. Greetings, Commander.'})

def run_vision():
    cap = cv2.VideoCapture(0)
    # Performance fix: Lower resolution to stop the lagging/restarting
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    print(f"\n[AEGIS ONLINE] SERVER: http://192.168.31.51:5000")
    
    last_voice_time = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                # 1. MOVEMENT
                palm = res.landmark[9]
                socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})
                
                # 2. VOICE GESTURE (Raise Index Finger)
                now = time.time()
                if res.landmark[8].y < res.landmark[0].y - 0.2:
                    if now - last_voice_time > 10: # 10-second cooldown
                        socketio.emit('speak', {'text': 'I am monitoring your gestures.'})
                        last_voice_time = now

        cv2.imshow('Aegis Vision Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
