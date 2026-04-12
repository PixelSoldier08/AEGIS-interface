import cv2
import mediapipe as mp
from flask import Flask
from flask_socketio import SocketIO
import threading
import socket
import time

# 1. ENGINE SETUP
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

mp_hands = mp.solutions.hands
# Optimization: Lower complexity for faster tracking
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5, # Faster detection
    min_tracking_confidence=0.5
)

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
    # Optimization: Lower camera resolution to reduce CPU load
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    print(f"\n[AEGIS PERFORMANCE MODE] IP: {get_ip()}")
    
    prev_time = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        # Optimization: Process only every 2nd frame to prevent lag
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                # TRACKING
                palm = res.landmark[9]
                socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})
                
                # VOICE: Add a small cooldown so he doesn't speak too much
                current_time = time.time()
                if res.landmark[8].y < res.landmark[0].y - 0.2:
                    if current_time - prev_time > 3: # 3-second voice cooldown
                        socketio.emit('speak', {'text': 'System Online'})
                        prev_time = current_time

        cv2.imshow('Aegis Vision (Light)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
