from flask import Flask, request, jsonify, send_from_directory, abort, render_template
from flask import Response
from flask_cors import CORS
from datetime import datetime
import subprocess
import os

app = Flask(__name__)
CORS(app)

def health_check():
    return "OK", 200

@app.route('/')
def index():
    return render_template('video_page.html')


current_process_1 = None
current_process_2 = None

#----------Start/Stop preview button----------#

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
        current_process_2.wait()
        current_process_1 = None
        current_process_2 = None
        return jsonify({"status": "success", "message": "Live preview stopped."})
    else:    
     	return jsonify({"status": "error", "message": "No process is currently running."}), 400


#------------- Endpoint to start recording -----------#

SAVE_DIR = "home/Desktop/eyepro_app/recordings"  
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def output_filename():
    index = 0
    while True:
        filename_0 = os.path.join(SAVE_DIR, f"NEAR_EYE_CAM-{index}.mp4")
        filename_1 = os.path.join(SAVE_DIR, f"SCENE_CAM-{index}.mp4")
        if not os.path.exists(filename_0) and not os.path.exists(filename_1):
            return filename_0, filename_1
        index += 1

@app.route("/start_recording", methods=["POST"])
def start_recording():
    global current_process_1, current_process_2

    output_path_1, output_path_2 = output_filename()

    try:
        
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


@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    try:
        if current_process_1:
            current_process_1.terminate()
            current_process_1.wait()

        if current_process_2:
            current_process_2.terminate()
            current_process_2.wait()

        return jsonify({"status": "success", "message": "Recording stopped"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

 
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
        file_path = os.path.join(recordings_dir, filename)
        if not os.path.exists(file_path):
            abort(404, description="File not found")

        return send_from_directory(recordings_dir, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Unable to download file: {str(e)}"}), 500

@app.route('/video-output')
def video_output():
    return render_template('video_page.html')
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug = True)

