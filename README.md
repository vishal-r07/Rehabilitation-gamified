# RehabiHand — Gamified, Sensor-Driven Rehabilitation

<p align="center">
  <strong>Interactive 3D rehabilitation experiences powered by embedded sensing</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Focus-Rehabilitation%20Technology-0f766e?style=for-the-badge" alt="Rehabilitation Technology" />
  <img src="https://img.shields.io/badge/Hackathons-2%20Wins-f59e0b?style=for-the-badge" alt="Two hackathon wins" />
  <img src="https://img.shields.io/badge/Hardware-ESP32%20%7C%20VEGA%20ARIES-2563eb?style=for-the-badge" alt="ESP32 and VEGA ARIES" />
</p>

**RehabiHand** is a sensor-driven rehabilitation project that explores how physical movement and muscle-activity signals can control interactive exercise experiences. The repository brings together embedded firmware, sensor acquisition, real-time communication experiments, 3D visualisation, gamified rehabilitation interfaces, and a Python desktop prototype.

The project has won **two hackathons**. Its core idea is to make repetitive rehabilitation exercises more engaging while providing visual feedback from sensor inputs.

> **Repository scope:** This is a collection of related prototypes and implementation paths—not one single, fully integrated application. The browser-based hand experience, arm tracker, ESP32 firmware, VEGA ARIES experiments, and Python desktop application have separate entry points and transport implementations.

---

## Contents

- [Project overview](#project-overview)
- [Problem and approach](#problem-and-approach)
- [System architecture](#system-architecture)
- [Repository structure](#repository-structure)
- [Main modules](#main-modules)
- [Hardware](#hardware)
- [Software stack](#software-stack)
- [Getting started](#getting-started)
- [Firmware setup](#firmware-setup)
- [Sensor data and communication](#sensor-data-and-communication)
- [Known integration notes](#known-integration-notes)
- [Troubleshooting](#troubleshooting)
- [Awards and recognition](#awards-and-recognition)
- [Roadmap](#roadmap)
- [Safety and medical disclaimer](#safety-and-medical-disclaimer)
- [Contributing](#contributing)
- [License](#license)

---

## Project overview

Rehabilitation exercises often involve repeated movements over an extended period. Maintaining engagement and understanding movement quality can be difficult when an exercise offers limited immediate feedback.

RehabiHand explores an engineering approach that combines:

1. **Sensing** — collect orientation, force/bend, and muscle-activity signals.
2. **Processing** — parse sensor readings and map them to application inputs.
3. **Visualisation** — represent hand or arm movement using interactive 3D models.
4. **Gamification** — use game objectives, repetitions, scores, levels, and achievements to structure exercise interactions.
5. **Feedback** — present sensor and movement feedback to the participant.

The project is intended for prototyping, demonstrations, and further research. It is not a clinically validated medical device.

## Problem and approach

The project investigates how sensor-assisted interaction can make exercise sessions more interactive and measurable.

| Challenge | Project approach |
|---|---|
| Repetitive exercise can feel monotonous | Multiple game modes and progression mechanics |
| Movement is not always easy to observe | 3D hand and arm visualisation |
| Exercise input needs to be captured | IMU, force/bend, and EMG sensor experiments |
| Users need immediate interaction feedback | Live status, form indicators, scores, and feedback |
| Development needs to be testable without hardware | Desktop simulation/test mode and sensor diagnostics |

## System architecture

The broad sensor-to-application data path is shown below. The exact connection depends on which firmware and client module is being used.

~~~mermaid
flowchart LR
    A[ BNO08x IMU ] --> D[ Embedded Firmware ]
    B[ Force / Bend Sensor ] --> D
    C[ EMG Sensor ] --> D
    D --> E[ Serial or Wireless Transport ]
    E --> F[ Application Data Parser ]
    F --> G[ Motion and Input Mapping ]
    G --> H[ 3D Hand / Arm Visualisation ]
    G --> I[ Rehabilitation Game Logic ]
    I --> J[ Score, Repetition and Feedback ]
    J --> K[ Participant ]
~~~

The repository contains different transport paths (Bluetooth Serial, WebSocket client code, and USB Web Serial). These are alternatives/experiments and should not be assumed to work interchangeably.

---

## Repository structure

~~~text
Rehabilitation-gamified/
├── arm_tracker/
│   ├── index.html
│   └── README.md
│
├── esp32_firmware/
│   ├── arm_rehab_serial_imu/
│   ├── arm_rehab_trainer/
│   ├── bicep_curl_counter/
│   ├── force_sensor_test/
│   ├── test_client/
│   └── README.md
│
├── hand_rehab/
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── README.md
│
├── rehab_system/
│   ├── main.py
│   ├── START.bat
│   ├── requirements.txt
│   ├── models/
│   ├── sensors/
│   ├── ui/
│   ├── exercises/
│   └── games/
│
├── vega_aries_firmware/
│   ├── bicep_curl_counter/
│   ├── bno08x_raw_test/
│   └── vega_aries_i2c_scanner/
│
├── serial_monitor.py
├── ARIESv2 0_Datasheet_v2 .pdf
└── pdf_content.txt
~~~

| Directory / file | Purpose |
|---|---|
| hand_rehab/ | Browser-based 3D hand rehabilitation experience |
| arm_tracker/ | Browser-based 3D arm tracking interface |
| esp32_firmware/ | ESP32 firmware variants and sensor experiments |
| vega_aries_firmware/ | VEGA ARIES v2 / THEJAS32 firmware diagnostics and experiments |
| rehab_system/ | Python desktop, visualisation, and game prototypes |
| serial_monitor.py | Selects a COM port and prints incoming serial data |
| ARIESv2 datasheet | Hardware reference document included in the repository |

---

## Main modules

### 1. RehabiHand — 3D hand rehabilitation

**Path:** hand_rehab/

The browser application renders a 3D hand using Three.js and connects application logic for sensor input, animation, game mechanics, and feedback.

**Implemented interface and application components:**

- 3D hand model with a palm, wrist, and five articulated finger groups.
- Sensor-driven hand animation and pose updates.
- Five rehabilitation game modes:
  - **Range of Motion:** interact with target finger positions.
  - **Grip Strength:** interact with target muscle/force levels.
  - **Coordination:** follow a sequence of hand gestures.
  - **Object Manipulation:** control virtual object interactions.
  - **Endurance:** perform repeated open/close interactions.
- Score and repetition tracking.
- Levels and achievement conditions.
- Difficulty and visual-quality settings.
- Visual indicators and procedural audio feedback.
- Browser localStorage for progress persistence.

**Key source files**

| File | Responsibility |
|---|---|
| js/main.js | Application bootstrap and UI event wiring |
| js/scene_manager.js | Three.js scene, renderer, camera, and visual scene |
| js/hand_model.js | 3D hand geometry and finger structure |
| js/animation_controller.js | Maps incoming sensor data to hand movement |
| js/game_engine.js | Game selection, game state, objectives, and scoring |
| js/gamification_system.js | Progress, levels, achievements, and persistence |
| js/feedback_system.js | Visual notifications and audio feedback |
| js/serial_client.js | WebSocket-based ESP32 client implementation |
| js/websocket_client.js | USB Web Serial client implementation |
| css/styles.css | Browser application styling |
| index.html | Application layout and script loading |

**Run the interface locally**

From the repository root:

~~~bash
cd hand_rehab
python -m http.server 8000
~~~

Open http://localhost:8000 in a modern browser.

This starts the web interface. A working sensor session additionally requires a compatible firmware and communication endpoint; see [Known integration notes](#known-integration-notes).

### 2. 3D arm tracker

**Path:** arm_tracker/

A standalone browser interface for visualising arm orientation. The page uses a 3D view and requests access to a serial device through the browser's Web Serial API.

The serial connection is configured for **115200 baud** in the page source.

**Run locally**

~~~bash
cd arm_tracker
python -m http.server 8001
~~~

Open http://localhost:8001 in Chrome or Edge. Use a browser that supports Web Serial, and connect the board when prompted.

### 3. ESP32 firmware

**Path:** esp32_firmware/

The ESP32 firmware folder contains multiple sketches for arm rehabilitation and sensor testing.

The main bicep-curl/arm trainer sketch includes:

- BNO08x IMU orientation acquisition.
- EMG signal sampling and RMS-based muscle activity processing.
- EMG baseline and fatigue-related calculations.
- Force/bend sensor sampling and repetition state.
- Posture and movement warning logic.
- Bluetooth Classic Serial communication.
- Haptic motor output.

**Pin assignments documented in the firmware source**

| Signal | ESP32 pin |
|---|---:|
| EMG analog input | GPIO 35 |
| Force/bend sensor | GPIO 32 |
| BNO08x SDA | GPIO 21 |
| BNO08x SCL | GPIO 22 |
| Haptic motor control | GPIO 26 |

The firmware declares the Bluetooth device name **ReflexAI-Trainer**. Serial debug output uses **115200 baud**.

**Arduino library**

- SparkFun BNO08x Arduino Library (Cortex Based IMU)
- ESP32 Arduino Core (provides BluetoothSerial)

For exact wiring, sensor power requirements, and sketch-specific setup, refer to the README and comments within esp32_firmware/.

### 4. VEGA ARIES v2 / THEJAS32 experiments

**Path:** vega_aries_firmware/

This folder currently contains hardware bring-up and diagnostic sketches:

| Sketch | Purpose |
|---|---|
| bno08x_raw_test/ | Checks BNO08x I2C presence and attempts a minimal raw device interaction |
| vega_aries_i2c_scanner/ | Scans I2C addresses and reports responding devices |
| bicep_curl_counter/ | Current source is a CAN-bus monitor using an MCP_CAN interface; it is not the same sensor-streaming protocol as the ESP32 rehabilitation firmware |

The repository also includes the ARIES v2 datasheet. The board is based on the THEJAS32 SoC; consult the included datasheet and the relevant board documentation before wiring peripherals or selecting pin mappings.

### 5. Python desktop rehabilitation prototype

**Path:** rehab_system/

The Python application is a separate desktop prototype that combines a PyQt5 interface, VTK visualisation, sensor-client code, and game experiments.

**Main components**

| Path | Responsibility |
|---|---|
| main.py | Desktop application entry point |
| models/ | Hand and arm visualisation models |
| sensors/esp32_client.py | USB serial sensor client and JSON parsing |
| sensors/serial_client.py | Serial communication utilities |
| sensors/simulator.py | Simulated sensor data for testing |
| ui/main_window.py | Main desktop interface |
| ui/game_main_window.py | Game-oriented desktop interface |
| ui/sensor_graphs.py | Sensor graph components |
| ui/emg_page.py | EMG-related interface |
| games/flight_simulator.py | Sensor-controlled flight simulator experiment |
| games/clinical_db.py | SQLite patient/session API prototype |
| requirements.txt | Python dependencies |
| START.bat | Windows dependency installation and launch helper |

**Install and launch**

Python 3.8 or later is specified in the subproject documentation.

~~~bash
cd rehab_system
python -m venv .venv
~~~

Activate the environment:

**Windows PowerShell**
~~~powershell
.venv\Scripts\Activate.ps1
~~~

**Linux / macOS**
~~~bash
source .venv/bin/activate
~~~

Install the pinned dependencies and launch:

~~~bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
~~~

On Windows, the included helper can also be used:

~~~bat
START.bat
~~~

The desktop application uses PyQt5 and VTK. Hardware mode expects a serial port; the desktop interface also contains a test/simulation path. The game and clinical database modules are separate experiments and should not be assumed to be enabled by the default main window.

---

## Hardware

The exact hardware configuration varies between the repository's prototype branches. Components evidenced by the firmware and documentation include:

| Component | Role |
|---|---|
| ESP32 development board | Embedded sensor acquisition and wireless communication |
| VEGA ARIES v2 / THEJAS32 board | Alternate embedded platform and hardware experiments |
| BNO08x IMU | Orientation and motion sensing |
| EMG sensor (AD8232 / MyoWare referenced in firmware comments) | Muscle activity signal acquisition |
| Force / bend sensor | Movement or force-related input |
| Haptic motor | Tactile feedback output in the ESP32 firmware |
| Supporting resistors and wiring | Sensor interface and signal conditioning |

**Electrical note:** verify each sensor's supply voltage, output range, ADC compatibility, grounding, and interface wiring against the exact component datasheet and board before powering the circuit. Do not infer a board pin mapping from a different firmware folder.

## Software stack

| Layer | Technologies present in the repository |
|---|---|
| Browser UI | HTML5, CSS3, JavaScript |
| 3D browser rendering | Three.js |
| Browser animation | GSAP |
| Browser device access | Web Serial API |
| Browser networking | Native WebSocket API |
| Embedded development | Arduino framework / C++ |
| Embedded connectivity | BluetoothSerial on ESP32 |
| Desktop UI | Python, PyQt5 |
| Desktop 3D rendering | VTK |
| Data and numerical processing | NumPy, SciPy, pandas |
| Serial communications | pySerial |
| Local session storage prototype | SQLite |

---

## Getting started

Choose the module you want to work on; the repository does not currently provide one universal launcher for all modules.

| Goal | Start here |
|---|---|
| Explore the browser-based hand games | hand_rehab/index.html |
| Explore 3D arm orientation tracking | arm_tracker/index.html |
| Upload ESP32 sensor firmware | esp32_firmware/ |
| Test BNO08x / I2C on VEGA ARIES | vega_aries_firmware/ |
| Run the Python desktop prototype | rehab_system/main.py |
| Inspect serial output from a board | serial_monitor.py |

### Serial monitor utility

The root-level serial monitor lists available COM ports and connects to the selected port at 115200 baud.

Install pySerial if it is not already available:

~~~bash
pip install pyserial
python serial_monitor.py
~~~

Close other serial terminals (including Arduino Serial Monitor) before connecting to the same port.

---

## Sensor data and communication

The repository contains more than one data transport and more than one JSON shape.

### ESP32 Bluetooth Serial

The main ESP32 arm-trainer sketch starts Bluetooth Classic Serial with the device name **ReflexAI-Trainer** and sends newline-terminated JSON data packets while a Bluetooth client is connected.

Fields emitted by the firmware include:

| Category | Example fields |
|---|---|
| EMG | emgValue, emgRms, emgFatigueLevel, muscleActivation, muscleFatigueDetected |
| IMU | imuConnected, isCalibrated, roll, pitch, yaw, accel |
| Posture | wristAngle, forearmRotation, elbowAngle, postureGood, postureWarning |
| Force/bend | bendForce, isBending, bendCount |
| Exercise / risk | injuryRisk, exerciseDuration, restRecommendation, totalWarnings |
| Compatibility | curlCount, goodFormCurls, sensorValue, rawValue, state, formGood, formWarning |

Bluetooth commands handled by the firmware include reset, calibrate, and ping. Threshold command strings are also acknowledged by the current sketch; inspect the implementation before relying on them to modify thresholds.

### Browser WebSocket client

The browser WebSocket client in hand_rehab/js/serial_client.js connects to:

~~~text
ws://<ESP32-IP>:81
~~~

Its parser expects compact JSON keys such as f, e, r, p, y, a, tc, gc, th, tl, and w.

### Browser USB Serial client

The separate hand_rehab/js/websocket_client.js file implements the Web Serial API client. It requests a serial port from the browser and opens it at 115200 baud. It expects newline-delimited JSON from the connected board.

### Python serial client

The desktop sensor client opens a selected serial port at 115200 baud and parses newline-delimited JSON messages.

---

## Known integration notes

These are important when bringing the prototypes together:

1. **The ESP32 firmware transport and browser WebSocket client are not automatically compatible.** The ESP32 arm-trainer sketch uses Bluetooth Classic Serial, whereas the browser WebSocket client connects to a WebSocket endpoint on port 81. A compatible bridge/server or a matching client/firmware implementation is required.
2. **The browser USB Serial client is a separate implementation.** The current hand_rehab/index.html script list loads serial_client.js, not websocket_client.js. To use Web Serial, align the page's script loading and application class/interface with that client.
3. **Data field names differ between firmware and clients.** The ESP32 sketch emits descriptive fields such as emgValue and bendForce, while the WebSocket parser currently expects compact keys such as e and f. Add an explicit mapping or update both ends to use one documented schema.
4. **VEGA ARIES firmware folders are experiments, not a drop-in replacement for ESP32 sketches.** The current VEGA ARIES bicep_curl_counter path contains an MCP_CAN bus monitor. Use the BNO08x raw test and I2C scanner for hardware diagnostics; do not assume the CAN monitor streams rehabilitation data.
5. **Subproject documentation may describe an earlier configuration.** Treat the source code in the selected sketch/client as the final authority for the exact pins, protocol, and supported commands.

These notes are included so that developers can reproduce the correct module instead of encountering avoidable communication or pin-mapping issues.

---

## Troubleshooting

| Symptom | Checks |
|---|---|
| Browser page opens but no 3D scene appears | Check browser console, CDN/network access, and WebGL support |
| Web Serial device picker is unavailable | Use a supported browser such as Chrome/Edge and serve from localhost or HTTPS |
| Serial port cannot be opened | Close Arduino Serial Monitor and any other process using the port |
| ESP32 Bluetooth device is not visible | Confirm ESP32 firmware uploaded successfully and Bluetooth initialisation succeeded |
| Browser WebSocket remains disconnected | Confirm a WebSocket server is actually running at the configured IP and port 81 |
| Sensor values appear incorrect | Verify wiring, supply voltage, common ground, sensor calibration, and JSON schema |
| BNO08x is not detected | Run the I2C scanner, verify SDA/SCL, power, pull-ups, and configured I2C address |
| Desktop application fails during startup | Activate the correct virtual environment and install requirements.txt dependencies |
| Desktop simulation is needed | Use the test/simulation mode exposed by the desktop UI |

For module-specific issues, also consult:

- esp32_firmware/README.md
- esp32_firmware/FORCE_SENSOR_FIX.md
- rehab_system/BNO08X_HARDWARE_FIX.md
- rehab_system/ESP32_TROUBLESHOOTING.md
- hand_rehab/README.md
- arm_tracker/README.md

---

## Awards and recognition

**The rehabilitation project has won two hackathons.**

The recognition reflects the project's combination of embedded sensing, interactive software, and gamified rehabilitation concepts. Add the official event names, award categories, dates, and certificate links here when you are ready to publish those details.

---

## Roadmap

Potential next steps for the project:

- [ ] Standardise one sensor JSON schema across ESP32, VEGA ARIES, browser, and desktop clients.
- [ ] Align the selected firmware transport with the selected application transport.
- [ ] Complete and document the VEGA ARIES sensor acquisition path.
- [ ] Expand from aggregate force input toward individually measured finger movement where suitable hardware is available.
- [ ] Improve calibration workflows and sensor-quality checks.
- [ ] Add repeatable session export and clinician-facing review tools.
- [ ] Validate movement metrics with qualified rehabilitation professionals before making clinical claims.
- [ ] Add build, test, and setup instructions for each supported hardware configuration.

## Safety and medical disclaimer

This repository is an engineering prototype for educational, demonstration, and research use. It is **not** a medical device, diagnostic system, or substitute for professional assessment or treatment.

- Exercise selection, intensity, duration, and progression should be determined by a qualified healthcare professional.
- Do not use the prototype to make clinical decisions or to claim a validated clinical outcome.
- Stop using the system if an activity causes pain, discomfort, dizziness, or unexpected symptoms.
- Sensor-derived posture, fatigue, force, and repetition indicators are experimental and should not be treated as medical measurements.

## Contributing

Contributions that improve reproducibility, safety, documentation, sensor compatibility, or application reliability are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Keep hardware-specific changes in the relevant firmware/module directory.
4. Document board model, pin mapping, sensor model, transport, and data format when changing hardware integration.
5. Test the affected module and provide steps to reproduce the result.
6. Submit a pull request describing the change.

## License

No repository-level LICENSE file was present when this README was prepared. Unless a license is added by the project owner, all rights remain with the respective copyright holder and reuse should be treated as not yet explicitly licensed.

## Project

**Repository:** https://github.com/vishal-r07/Rehabilitation-gamified

**Maintainer:**
[vishal-r07](https://github.com/vishal-r07)
[Kishore-VS](https://github.com/Kishore-VS)
[ashwinr-act-cit](https://github.com/ashwinr-act-cit)
[Deepak-prog15](https://github.com/Deepak-prog15)
[Loki-i](https://github.com/Loki-i)

---

<p align="center">
  <strong>Making rehabilitation more interactive through embedded systems, sensing, and gamification.</strong>
</p>
