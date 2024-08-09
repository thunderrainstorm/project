from flask import Flask, render_template, Response, jsonify
import cv2
from detector import load_known_faces, detect_objects
from ultralytics import YOLO
from database import initialize_db, clear_status_log, fetch_status_logs  # Import database functions
import torch  # Import PyTorch

app = Flask(__name__)

# Initialize video capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("Cannot open webcam")
cap.set(3, 640)
cap.set(4, 480)

# Load the model and known faces
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # Set device to GPU if available
model = YOLO("ppe.pt").to(device)  # Move model to GPU
known_faces_dir = "C:\\Users\\sambita\\webapp\\known_faces"
known_face_encodings, known_face_names = load_known_faces(known_faces_dir)

# Initialize the database and clear previous session logs
initialize_db()
clear_status_log()

# Generator function to yield frames from the webcam
def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read frame from camera.")
            break
        else:
            print("Frame captured")
            frame = detect_objects(frame, model, known_face_encodings, known_face_names)
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame")
                continue
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to serve the video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to fetch and display status logs as JSON
@app.route('/status_logs')
def status_logs():
    logs = fetch_status_logs()
    return jsonify(logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)