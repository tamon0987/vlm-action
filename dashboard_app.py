from flask import Flask, request, jsonify, send_from_directory
from vision_llm_client import VisionLLMClient
import io

app = Flask(__name__, static_folder="static")

# Configure your LLM API endpoint and key here
llm_client = VisionLLMClient(api_url="https://your-llm-api-endpoint", api_key=None)

# In-memory storage for demo purposes
latest_feedback = {
    "image_url": "/static/sample.jpg",
    "feedback": "Object detected at position X.",
    "suggested_action": {"action": "move_arm", "parameters": {"joint": 2, "angle": 45}}
}
approved_action = None
mode = "human-approve"  # or "auto-approve"

import cv2
import threading

@app.route("/")
def index():
    # Serve the static HTML dashboard if it exists
    return send_from_directory(app.static_folder, "index.html")

# Camera snapshot endpoint (returns JPEG)
@app.route("/api/camera", methods=["GET"])
def get_camera_image():
    # Use OpenCV to capture a frame from the default camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "Camera error", 500
    _, jpeg = cv2.imencode('.jpg', frame)
    return jpeg.tobytes(), 200, {'Content-Type': 'image/jpeg'}

# LLM order endpoint (real LLM integration)
@app.route("/api/llm_order", methods=["POST"])
def llm_order():
    data = request.json
    order = data.get("order", "")
    # Call VisionLLMClient for text order
    llm_result = llm_client.generate_command_from_text(order)
    response = f"LLM response: {llm_result}"
    return jsonify({"response": response})

# LLM order with image endpoint (real LLM integration)
@app.route("/api/llm_order_with_image", methods=["POST"])
def llm_order_with_image():
    order = request.form.get("order", "")
    image_file = request.files.get("image")
    if image_file:
        image_bytes = image_file.read()
        # Save to a BytesIO for compatibility
        image_io = io.BytesIO(image_bytes)
        # Call VisionLLMClient for image+order
        llm_result = llm_client.analyze_image_with_order(image_io, order)
        angles = llm_result.get("angles", [0]*6)
        response_text = llm_result.get("feedback", "LLM processed order and image.")
    else:
        angles = [0]*6
        response_text = "No image provided."
    command = {"angles": angles}
    response = {
        "llm_response": response_text,
        "command": command
    }
    return jsonify(response)

@app.route("/api/joint_values", methods=["GET"])
def get_joint_values():
    # DEMO: animate all 6 joints with different angles
    num_joints = 6
    from_values = [0] * num_joints
    import math, time
    t = time.time()
    # Demo: oscillate each joint with different phase/speed
    to_values = [
        30 * math.sin(t),
        45 * math.sin(t + 0.5),
        60 * math.sin(t + 1.0),
        20 * math.sin(t + 1.5),
        15 * math.sin(t + 2.0),
        10 * math.sin(t + 2.5)
    ]
    return jsonify({"from": from_values, "to": to_values})

@app.route("/api/feedback/latest", methods=["GET"])
def get_latest_feedback():
    return jsonify(latest_feedback)

@app.route("/api/feedback/approve", methods=["POST"])
def approve_action():
    global approved_action
    data = request.json
    approved_action = data.get("approved_action")
    # In production, trigger orchestrator to proceed
    return jsonify({"status": "queued"})

@app.route("/api/mode", methods=["GET", "POST"])
def mode_control():
    global mode
    if request.method == "POST":
        data = request.json
        mode = data.get("mode", mode)
        return jsonify({"status": "updated", "mode": mode})
    return jsonify({"mode": mode})

if __name__ == "__main__":
    app.run(debug=True)