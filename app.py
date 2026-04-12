import cv2
import mediapipe as mp
from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import socket
import time

# --- CONFIGURATION ---
MY_IP = "192.168.31.51"  # Your confirmed IP
PORT = 5000

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- CONNECTION GREETING ---
@socketio.on('connect')
def handle_connect():
    print(f"\n[SUCCESS] Phone connected to Aegis Brain.")
    # This triggers the voice greeting on your phone immediately
    emit('speak', {'text': 'Aegis System Online. Connection established. Hello, Commander.'})

# --- VISION & GESTURE ENGINE ---
def run_vision():
    cap = cv2.VideoCapture(0)
    # Optimization to prevent lag/stopping
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    print(f"\n[AEGIS ACTIVE]")
    print(f"Losing his voice? -> Tap the phone screen once after loading!")
    print(f"Stopping/Restarting? -> Performance Mode is now ENABLED.")
    
    last_voice_time = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for res in results.multi_hand_landmarks:
                # 1. SEND MOVEMENT DATA
                palm = res.landmark[9]
                socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})
                
                # 2. GESTURE VOICE TRIGGER
                # If you raise your index finger (Landmark 8) high
                current_time = time.time()
                if res.landmark[8].y < res.landmark[0].y - 0.3:
                    if current_time - last_voice_time > 7: # 7-second cooldown
                        socketio.emit('speak', {'text': 'Movement protocol active.'})
                        last_voice_time = current_time

        cv2.imshow('Aegis Vision Feed (Press Q to Quit)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # Start the camera in the background
    threading.Thread(target=run_vision, daemon=True).start()
    # Run the server on your specific IP
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False)
