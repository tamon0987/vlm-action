from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# In-memory storage for demo purposes
latest_feedback = {
    "image_url": "/static/sample.jpg",
    "feedback": "Object detected at position X.",
    "suggested_action": {"action": "move_arm", "parameters": {"joint": 2, "angle": 45}}
}
approved_action = None
mode = "human-approve"  # or "auto-approve"

@app.route("/")
def index():
    # Serve the static HTML dashboard if it exists
    return send_from_directory(app.static_folder, "index.html")

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