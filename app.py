import cv2
import mediapipe as mp
from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import socket
import time

# --- SETTINGS ---
MY_IP = "192.168.31.51"
PORT = 5000

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5, # Reduced for speed
    min_tracking_confidence=0.5
)

# --- 1. THE GREETING PROCESS ---
@socketio.on('connect')
def handle_connect():
    print(f"\n[SYSTEM] Commander joined at {MY_IP}")
    # This sends the greeting immediately upon connection
    emit('speak', {'text': 'Aegis system protocol engaged. Hello, Commander.'})

# --- 2. VISION ENGINE (LIGHTWEIGHT) ---
def run_vision():
    cap = cv2.VideoCapture(0)
    
    # Optimization: Lower resolution prevents the 'stop and restart' lag
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    print(f"\n[AEGIS ONLINE]")
    print(f"Server Running: http://{MY_IP}:{PORT}")
    
    last_voice_time = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                # MOVEMENT: Send palm center coordinates (Landmark 9)
                palm = res.landmark[9]
                socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})
                
                # VOICE GESTURE: Raise hand high to trigger voice
                current_time = time.time()
                if res.landmark[8].y < res.landmark[0].y - 0.3:
                    if current_time - last_voice_time > 8: # 8-second cooldown
                        socketio.emit('speak', {'text': 'Aegis is tracking your commands.'})
                        last_voice_time = current_time

        cv2.imshow('Aegis Vision (Performance Mode)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False)
