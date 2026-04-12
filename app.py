import cv2
import socket
import threading
import time
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def get_ip():
    return "My_IP"

# --- VOICE GREETING ---
@socketio.on('connect')
def handle_connect():
    print("\n[!] COMMANDER CONNECTED")
    # This forces the voice to trigger
    emit('speak', {'text': 'Emergency Protocol Active. System Online.'})

def run_vision():
    cap = cv2.VideoCapture(0)
    print(f"\n[SYSTEM] BYPASS MODE ONLINE")
    print(f"URL: http://{get_ip()}:5000")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        # Convert to grayscale to find movement without MediaPipe
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Track the largest moving object
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 500:
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"]) / frame.shape[1]
                    cY = int(M["m01"] / M["m00"]) / frame.shape[0]
                    # MOVE THE SHARDS
                    socketio.emit('hand_move', {'x': cX, 'y': cY})

        cv2.imshow('Aegis Emergency Vision', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
