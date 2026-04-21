import cv2
import threading
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def run_vision():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        gray = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(cv2.GaussianBlur(gray, (7, 7), 0), 50, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] != 0 and cv2.contourArea(largest) > 800:
                cX = (M["m10"] / M["m00"]) / frame.shape[1]
                cY = (M["m01"] / M["m00"]) / frame.shape[0]
                socketio.emit('hand_move', {'x': cX, 'y': cY, 'z': min(cv2.contourArea(largest)/50000, 1.0)})

        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
