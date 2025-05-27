from flask import Flask, request, jsonify, send_from_directory
from vision_llm_client import VisionLLMClient
import io
import socket
import threading

app = Flask(__name__, static_folder="static")

# シンプルなCORS対応
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response

# Configure your LLM API endpoint and key here
llm_client = VisionLLMClient(api_url="https://your-llm-api-endpoint", api_key=None)

# 現在の関節角度を保持
current_angles = [0.0] * 6

# UDPサーバーの設定
UDP_IP = "127.0.0.1"  # localhostで待ち受け
UDP_PORT = 4210

def start_udp_server():
    """UDPサーバーを起動してtagurobo SDKからの接続を待ち受ける"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"UDPサーバーを起動: {UDP_IP}:{UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            command = data.decode('utf-8').strip()
            print(f"受信: {command} from {addr}")
            
            # すべてのコマンドに"OK"を返す
            sock.sendto(b"OK", addr)
        except Exception as e:
            print(f"UDPサーバーエラー: {e}")

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

def load_trajectory():
    """軌道データを読み込む"""
    global trajectory_data, trajectory_start_time
    try:
        with open('trajectory.json', 'r') as f:
            trajectory_data = json.load(f)
            trajectory_start_time = time.time()
    except Exception as e:
        print(f"Error loading trajectory data: {e}")
        trajectory_data = {
            "trajectory": [[0]*6],
            "timestamps": [0],
            "actual_angles": [[0]*6]
        }

# 接続エンドポイント
@app.route("/api/connect", methods=["POST"])
def connect():
    print("main.pyから接続されました")
    return jsonify({"status": "connected"})

# 角度更新エンドポイント
@app.route("/api/update_angles", methods=["POST"])
def update_angles():
    global current_angles
    data = request.json
    angles = data.get("angles", [0.0] * 6)
    current_angles = angles
    print(f"新しい角度を受信: {angles}")
    return jsonify({"status": "updated"})

@app.route("/api/joint_values", methods=["GET"])
def get_joint_values():
    """現在の関節角度を返す"""
    return jsonify({
        "from": current_angles,
        "to": current_angles
    })

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
    # UDPサーバーを別スレッドで起動
    udp_thread = threading.Thread(target=start_udp_server)
    udp_thread.daemon = True  # メインスレッド終了時に一緒に終了
    udp_thread.start()
    
    # FlaskサーバーをHTTPで起動
    print("Flaskサーバーを起動: http://localhost:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)