from flask import Flask, request, jsonify, send_from_directory, abort, render_template
from flask import Response
from flask_cors import CORS
from datetime import datetime
import subprocess
import os
import threading
import signal


app = Flask(__name__)
CORS(app)

SAVE_DIR = "/tmp"
@app.route('/healthz', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/')
def index():
    return render_template('video_page.html')


current_process_1 = None
current_process_2 = None


def get_next_filename():
    
    index = 0
    while True:
        filename = os.path.join(SAVE_DIR, f"Video-{index}.mp4")
        if not os.path.exists(filename):
            return filename
        index += 1
        
@app.route("/start_preview", methods=["POST"])
def start_live_preview_1():
    """Start live video preview."""
    global current_process_1
    global current_process_2
    
    try:
        current_process_1 = subprocess.Popen([
            "libcamera-vid",
            "--camera", "0",
            "--width", "640",
            "--height", "480",
            "--framerate", "20",
            "-t", "0"
        ])
        current_process_2 = subprocess.Popen([
            "libcamera-vid",
            "--camera", "1",
            "--width", "640",
            "--height", "480",
            "--framerate", "20",
            "-t", "0"
        ])
        return jsonify({"status": "success", "message": "Live preview started."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/stop_preview", methods=["POST"])
def stop_live_preview():
    """Stop live video preview."""
    global current_process_1
    global current_process_2
    if current_process_1 and current_process_2:
        current_process_1.terminate()
        current_process_2.terminate()
        current_process_1.wait()  
        current_process_2.wait()# Ensure the process has terminated
        current_process_1 = None
        current_process_2 = None
        return jsonify({"status": "success", "message": "Live preview stopped."})
    else:    
     	return jsonify({"status": "error", "message": "No process is currently running."}), 400



import cv2
import threading

# Event object to signal threads to stop
stop_event = threading.Event()

def record_video(camera_index, output_path, frame_width=1920, frame_height=1080, framerate=30):
    """Records video using OpenCV and stops when the stop event is set."""
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cap.set(cv2.CAP_PROP_FPS, framerate)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4
    out = cv2.VideoWriter(output_path, fourcc, framerate, (frame_width, frame_height))

    while not stop_event.is_set():  # Continue recording until stop_event is set
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            break

    cap.release()
    out.release()

# Flask endpoint to start recording
@app.route("/start_recording", methods=["POST"])
def start_recording():
    global current_process_1, current_process_2

    try:
        # Reset the stop event
        stop_event.clear()

        # Define output paths
        output_path_1 = os.path.join(recordings_dir, "camera1.mp4")
        output_path_2 = os.path.join(recordings_dir, "camera2.mp4")

        # Start recording with libcamera-vid
        current_process_1 = subprocess.Popen([
            "libcamera-vid",
            "--camera", "0",
            "--width", "1920",
            "--height", "1080",
            "--framerate", "30",
            "-t", "0",
            "-o", output_path_1
        ])

        current_process_2 = subprocess.Popen([
            "libcamera-vid",
            "--camera", "1",
            "--width", "1920",
            "--height", "1080",
            "--framerate", "30",
            "-t", "0",
            "-o", output_path_2
        ])

        return jsonify({"status": "success", "message": "Recording started"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Flask endpoint to stop recording
@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    global current_process_1, current_process_2

    try:
        # Stop the processes
        if current_process_1:
            current_process_1.terminate()
            current_process_1.wait()
            current_process_1 = None

        if current_process_2:
            current_process_2.terminate()
            current_process_2.wait()
            current_process_2 = None

        return jsonify({"status": "success", "message": "Recording stopped"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


BASE_DIR = os.path.join(os.path.expanduser("~"), "MindsEye")

os.makedirs(BASE_DIR, exist_ok=True)

def get_next_id():
    existing_ids = [
        int(folder[1:]) for folder in os.listdir(BASE_DIR) if folder.startswith('#') and folder[1:].isdigit()
    ]
    next_id = max(existing_ids, default=0) + 1
    return f"#{str(next_id).zfill(5)}"

def create_csv_if_not_exists(file_path, headers):
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers) 
    return file_path

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

       
        name = data.get('name')
        age = data.get('age')
        gender = data.get('gender')
        email = data.get('email')
        doctor = data.get('doctor')

        if not all([name, age, gender, email, doctor]):
            return jsonify({"error": "All fields are required"}), 400

        folder_id = get_next_id()
        folder_path = os.path.join(BASE_DIR, folder_id)
        os.makedirs(folder_path, exist_ok=True)
        reg_file = os.path.join(folder_path, f"{folder_id}_registration.csv")
        reg_headers = ['ID', 'Name', 'Age', 'Gender', 'Email', 'Doctor']
        create_csv_if_not_exists(reg_file, reg_headers)

        with open(reg_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([folder_id, name, age, gender, email, doctor]) 
        return jsonify({"message": "Data saved successfully", "id": folder_id}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

recordings_dir ="/home/MindsEye/eyepro/recordings"

@app.route("/recordings", methods=["GET"])
def list_recordings():
    try:
        files = [f for f in os.listdir(recordings_dir) if os.path.isfile(os.path.join(recordings_dir, f))]
        return jsonify({"Files": files})
    except Exception as e:
        return jsonify({"error": f"Unable to list recordings: {str(e)}"}), 500

@app.route("/download/recordings/<filename>", methods=["GET"])
def download_recordings(filename):
    try:
        # Check if the requested file exists
        file_path = os.path.join(recordings_dir, filename)
        if not os.path.exists(file_path):
            abort(404, description="File not found")

        # Serve the file for download
        return send_from_directory(recordings_dir, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Unable to download file: {str(e)}"}), 500

@app.route('/video-output')
def video_output():
    return render_template('video_page.html')
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug = True)

