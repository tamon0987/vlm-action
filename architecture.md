# Integrated System Architecture

## High-Level Structure

This project integrates an Arduino-based servo controller with a Python SDK and control script for a robotic arm. The system enables networked control of servos via UDP and provides a Python interface for higher-level operations. It also supports an advanced auto feedback system with human-in-the-loop or fully autonomous modes.

```mermaid
flowchart TD
    subgraph Arduino
        A1["main.cpp"]
    end
    subgraph Python
        B1["main.py"]
        B2["tagurobo.py (RobotArmSDK)"]
        B3["orchestrator.py"]
        B4["camera_module.py"]
        B5["vision_llm_client.py"]
        B6["dashboard_app.py"]
    end
    B1 --> B2
    B2 <--> A1
    B3 --> B2
    B3 --> B4
    B3 --> B5
    B3 --> B6
```

---

## File Details

### [`main.cpp`](main.cpp)

**Purpose:**  
Implements the firmware for an ESP32-based controller, handling WiFi, UDP, web server, and servo PWM control for a robotic arm.

**Key Components:**  
- `setup()`, `loop()`, `serialPrintf()`, `wificheck()`, `ServoPwmStatus`, `readServoPwmStatus()`, `setServoPwm()`, `removeNewline()`, `floatArrayToCSV()`, `commandInterpreter()`, `processUdpPacket()`, `processSerialMessage()`
- Web server endpoints: `/`, `/servos`, `/stop_all`

---

### [`tagurobo.py`](tagurobo.py)

**Purpose:**  
Python SDK for controlling the robotic arm via UDP. Provides a high-level API for connection management, joint control, and trajectory execution.

**Key Class:**  
- `RobotArmSDK` with methods for connection, joint control, state update, and trajectory execution.

---

### [`main.py`](main.py)

**Purpose:**  
Example script demonstrating how to use `RobotArmSDK` to control the robotic arm.

**Key Function:**  
- `main()` — Instantiates SDK, connects, sets limits, moves joints, executes trajectory, disconnects.

---

### [`orchestrator.py`](orchestrator.py)

**Purpose:**  
Central controller for the feedback system. Coordinates robot commands, camera capture, LLM interaction, and mode control (auto/human approve).

---

### [`camera_module.py`](camera_module.py)

**Purpose:**  
Handles image capture from a connected camera for feedback and vision analysis.

---

### [`vision_llm_client.py`](vision_llm_client.py)

**Purpose:**  
Integrates with a vision LLM API (e.g., Gemini 2.0) to analyze images and generate robot commands or feedback.

---

### [`dashboard_app.py`](dashboard_app.py)

**Purpose:**  
Flask-based web dashboard for human-in-the-loop review, action approval, and mode switching.

- The dashboard serves `static/index.html` at the root URL (`/`).
- Users can interact with the system via their browser at `http://localhost:5000/`.
- You can enhance `static/index.html` to display feedback, approve actions, and control modes.

---

## Auto Feedback System Architecture

### Overview

This system enables a robot to perform actions, capture results via camera, analyze outcomes using a vision LLM, and present feedback to a human operator for review and approval before the next action.

---

### Operation Modes

- **Auto-Approve Mode:**  
  The LLM generates and sends commands directly to the robot after each analysis, enabling fully autonomous operation.

- **Approve by Human Mode:**  
  The LLM generates a suggested command, but the command is presented to a human operator via the web dashboard for review and approval before being sent to the robot.

A mode flag in the orchestrator and a toggle in the dashboard control which workflow is active.

---

## Sequential Diagrams

### Basic System

```mermaid
flowchart TD
    subgraph Arduino
        A1["main.cpp"]
    end
    subgraph Python
        B1["main.py"]
        B2["tagurobo.py (RobotArmSDK)"]
    end
    B1 --> B2
    B2 <--> A1
```

---

### Auto-Approve Mode

```mermaid
sequenceDiagram
    participant H as Human
    participant L as LLM (Vision Model)
    participant F as Feedback Orchestrator
    participant R as Robot Controller
    participant C as Camera Module

    H->>L: Give order (e.g., "pick up object")
    L->>F: Create and send command
    F->>R: Send action command
    R->>C: Perform action, trigger capture
    C->>F: Send captured image
    F->>L: Send image for analysis
    L->>F: Return feedback/suggestion (new command)
    F->>R: Send next action command
    ... (loop continues automatically)
```

---

### Approve by Human Mode

```mermaid
sequenceDiagram
    participant H as Human
    participant L as LLM (Vision Model)
    participant F as Feedback Orchestrator
    participant R as Robot Controller
    participant C as Camera Module
    participant W as Web Dashboard

    H->>L: Give order (e.g., "pick up object")
    L->>F: Create and send command
    F->>W: Display suggested command for approval
    W->>F: Human approves/edits command
    F->>R: Send action command
    R->>C: Perform action, trigger capture
    C->>F: Send captured image
    F->>L: Send image for analysis
    L->>F: Return feedback/suggestion (new command)
    F->>W: Display next suggested command for approval
    ... (loop continues with human in the loop)
```

---

## Example API Endpoints

### Feedback Orchestrator

- **POST `/api/action`** — Send a command to the robot.
- **POST `/api/capture`** — Upload a captured image after action.
- **POST `/api/vision`** — Send image to vision LLM and get feedback.

### Web Dashboard

- **GET `/api/feedback/latest`** — Get the latest vision feedback and image.
- **POST `/api/feedback/approve`** — Approve or modify the next action.
- **GET/POST `/api/mode`** — Get or set the current feedback mode.

---

## Data Formats

- **Action Command**
    ```json
    {
      "action": "move_arm",
      "parameters": {"joint": 1, "angle": 90}
    }
    ```
- **Vision Feedback**
    ```json
    {
      "feedback": "Object detected at position X.",
      "suggested_action": {"action": "move_arm", "parameters": {"joint": 2, "angle": 45}}
    }
    ```

---

## Technologies

- Robot: Existing Python SDK
- Camera: USB/CSI camera, OpenCV or similar
- Vision LLM: Cloud API (e.g., Gemini 2.0)
- Web Dashboard: Flask/FastAPI backend + React/Vue frontend
- Orchestrator: Python service (could be part of backend)

---

## Mode Control Implementation Notes

- The orchestrator maintains a mode flag (`auto-approve` or `human-approve`).
- The web dashboard provides a toggle to switch modes.
- In auto-approve mode, commands from the LLM are sent directly to the robot.
- In human-approve mode, commands are routed to the dashboard for review and approval before execution.