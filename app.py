import cv2
import mediapipe as mp
from flask import Flask
from flask_socketio import SocketIO
import threading

# 1. Initialize Server & Socket
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 2. Initialize Mediapipe Hand Solution (from your screenshot)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=1, 
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

def track_motion():
    cap = cv2.VideoCapture(0) # Open Camera
    print("AEGIS VISION SYSTEM: ONLINE")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        # Process Frame
        frame = cv2.flip(frame, 1) # Mirror effect
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            # Extract coordinates of the Palm (Landmark 0)
            palm = results.multi_hand_landmarks[0].landmark[0]
            # Emit normalized data to the interface
            socketio.emit('hand_move', {'x': palm.x, 'y': palm.y})

    cap.release()

if __name__ == '__main__':
    # Run tracking in a separate thread to keep the server responsive
    threading.Thread(target=track_motion, daemon=True).start()
    # Run on 0.0.0.0 to allow mobile devices on your network to connect
    socketio.run(app, host='0.0.0.0', port=5000)