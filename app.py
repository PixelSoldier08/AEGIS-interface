import cv2
import mediapipe as mp
from flask import Flask
from flask_socketio import SocketIO
import threading
import socket

# 1. SETUP ENGINE
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Accessing mediapipe solutions safely
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except: IP = '127.0.0.1'
    finally: s.close()
    return IP

def run_vision():
    cap = cv2.VideoCapture(0)
    print(f"\n[AEGIS ONLINE] CONNECT PHONE TO: http://{get_ip()}:5000")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                # TRACKING: Send palm center coordinates
                palm = res.landmark[9]
                socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})
                
                # VOICE TRIGGER: If your index finger (landmark 8) is raised 
                # higher than your wrist (landmark 0), trigger the voice.
                if res.landmark[8].y < res.landmark[0].y - 0.2:
                    socketio.emit('speak', {'text': 'Aegis System Protocol Engaged'})

        cv2.imshow('Aegis Vision Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
