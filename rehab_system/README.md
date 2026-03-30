# 3D Hand Rehabilitation System

Professional desktop application for hand physiotherapy with real-time sensor feedback.

## Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the application**:
```bash
python main.py
```

3. **Connect ESP32**:
   - Enter ESP32 IP address
   - Click "Connect"
   - Your hand movements will appear in 3D!

## Features

- ✅ Real-time 3D hand visualization
- ✅ IMU sensor (orientation tracking)
- ✅ Force sensor (grip strength)
- ✅ EMG sensor (muscle activity)
- ✅ Professional desktop UI
- 🔄 Exercise modules (coming soon)
- 🔄 Progress tracking (coming soon)

## System Requirements

- Python 3.8+
- Windows/Linux/Mac
- ESP32 with IMU, Force, EMG sensors

## Project Structure

```
rehab_system/
├── main.py              # Application entry
├── models/
│   └── hand_model.py    # 3D hand visualization
├── sensors/
│   └── esp32_client.py  # Sensor communication
├── ui/
│   └── main_window.py   # Main GUI
└── requirements.txt     # Dependencies
```

## Current Status

**Phase 1 Complete**: Foundation ✅
- PyQt5 main window
- VTK 3D hand model
- ESP32 WebSocket client
- Real-time sensor display

**Next**: Phase 2 - Advanced hand model with all bones and joints

## Usage

1. Start application
2. Connect ESP32
3. Move your hand
4. See real-time 3D visualization
5. View sensor data (IMU, Force, EMG)

---

**Professional biomedical tool for hand rehabilitation** 🏥💪
