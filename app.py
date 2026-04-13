import cv2
import threading
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def run_vision():
    cap = cv2.VideoCapture(0)
    print(f"\n[SYSTEM] AEGIS 3D BYPASS ONLINE")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Blur slightly to reduce noise for smoother 3D movement
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            
            if area > 800:
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"]) / frame.shape[1]
                    cY = int(M["m01"] / M["m00"]) / frame.shape[0]
                    
                    # SIMULATED Z-AXIS: Larger area = closer to screen (negative Z in Three.js)
                    # Normalizing area to a scale of 0.0 to 1.0
                    cZ = min(area / 50000, 1.0) 
                    
                    socketio.emit('hand_move', {'x': cX, 'y': cY, 'z': cZ})

        # Keep the debug window if you want to see what Aegis "sees"
        cv2.imshow('Aegis Vision Feed', thresh)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    threading.Thread(target=run_vision, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
