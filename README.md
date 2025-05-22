# Robotic Arm Auto Feedback System

This project enables networked and vision-based control of a robotic arm, supporting both fully autonomous and human-in-the-loop feedback modes. The system integrates Arduino firmware, a Python SDK, orchestrator, camera capture, LLM vision analysis, and a web dashboard.

---

## Features

- Control a robotic arm via UDP and Python SDK
- Auto feedback loop using camera and vision LLM (e.g., Gemini 2.0)
- Human-in-the-loop or fully autonomous operation modes
- Web dashboard for reviewing and approving actions
- Modular architecture for easy extension

---

## Architecture

See [`integrated_architecture.md`](integrated_architecture.md) for detailed diagrams and component descriptions.

---

## Directory Structure

```
.
├── main.cpp                # Arduino/ESP32 firmware
├── tagurobo.py             # Python SDK for robot control
├── main.py                 # Example usage script
├── orchestrator.py         # Feedback orchestrator (core logic)
├── camera_module.py        # Camera capture module
├── vision_llm_client.py    # Vision LLM integration
├── dashboard_app.py        # Flask web dashboard backend
├── requirements.txt        # Python dependencies
├── integrated_architecture.md # Full architecture documentation
└── README.md               # Project overview and instructions
```

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Web Dashboard

```bash
python dashboard_app.py
```

- Open your browser and go to [http://localhost:5000/](http://localhost:5000/) to access the dashboard UI, served from `static/index.html`.

### 3. Run the Orchestrator

```bash
python orchestrator.py
```

### 4. (Optional) Run Example Robot Control

```bash
python main.py
```

---

## Usage

- Use the web dashboard at [http://localhost:5000/](http://localhost:5000/) to review and approve robot actions, view feedback, or switch to auto-approve mode for full autonomy.
- The dashboard UI is served from `static/index.html` and can be customized to display system status and interact with API endpoints.
- The orchestrator coordinates robot commands, camera capture, and LLM feedback.
- Integrate your own LLM API and camera hardware as needed.

---

## Contributing

Contributions are welcome! Please see [`integrated_architecture.md`](integrated_architecture.md) for system details before submitting pull requests.

---

## License

MIT License