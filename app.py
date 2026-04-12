import cv2
import mediapipe as mp
from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import socket
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except: IP = '127.0.0.1'
    finally: s.close()
    return IP

@socketio.on('connect')
def handle_connect():
    print("[SYSTEM] Phone Connected. Sending Greeting...")
    # This restores the greeting process
    emit('speak', {'text': 'Aegis System Online. Hello, Commander.'})

def run_vision():
    cap = cv2.VideoCapture(0)
    # Lower resolution to prevent the 'stop and restart' lag
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    print(f"\n[AEGIS ACTIVE] IP: {get_ip()}")
    
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
                
                # 2. GESTURE VOICE (Trigger by raising hand high)
                current_time = time.time()
                if res.landmark[8].y < res.landmark[0].y - 0.3:
                    if current_time - last_voice_time > 5: # Prevent voice spam
                        socketio.emit('speak', {'text': 'I am tracking your movements.'})
                        last_voice_time = current_time

        cv2.imshow('Aegis Vision', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
