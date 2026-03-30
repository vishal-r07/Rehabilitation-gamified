# ESP32 Bicep Curl Counter with Form Detection

Smart bicep curl trainer using force sensor + IMU to count curls and detect bad form.

## Communication

**Bluetooth Serial (SPP)** - Device Name: `ReflexAI-Trainer`

The ESP32 broadcasts JSON data over Bluetooth Serial at 50ms intervals. Connect using any Bluetooth Serial app or the Reflex-AI mobile app.

## Hardware Required

| Component | Purpose |
|-----------|---------|
| ESP32 DevKit V1 | Main controller |
| Strip Force Sensor | Detect curl motion |
| 7Semi BNO08x IMU | Detect arm orientation |
| 10kΩ Resistor | Voltage divider for sensor |

## Wiring

### Force Sensor
```
Sensor Pin 1 → 3.3V
Sensor Pin 2 → GPIO34 (VP)
10kΩ Resistor → GPIO34 to GND
```

### BNO08x IMU (I2C)
```
VCC → 3.3V
GND → GND
SDA → GPIO21
SCL → GPIO22
```

## Arduino Libraries Required

Install via **Sketch → Include Library → Manage Libraries**:

1. **SparkFun BNO08x Cortex Based IMU** by SparkFun

> Note: BluetoothSerial is included with ESP32 Arduino Core

## Setup

1. Upload to ESP32
2. Open Serial Monitor (115200 baud)
3. Enable Bluetooth on your phone
4. Pair with device named `ReflexAI-Trainer`
5. Open Reflex-AI app and connect
6. Click **Calibrate IMU** with arm in starting position
7. Start curling!

## JSON Data Format

```json
{
  "type": "data",
  "curlCount": 5,
  "goodFormCurls": 4,
  "sensorValue": 750,
  "rawValue": 780,
  "state": "BENT",
  "imuConnected": true,
  "isCalibrated": true,
  "roll": 5.2,
  "pitch": 45.3,
  "yaw": 2.1,
  "accel": 9.81,
  "formGood": true,
  "formWarning": "",
  "elbowFlareCount": 1,
  "wristTwistCount": 0,
  "jerkyMoveCount": 0,
  "thresholdHigh": 800,
  "thresholdLow": 300
}
```

## Bluetooth Commands

Send these commands via Bluetooth Serial:

| Command | Description |
|---------|-------------|
| `reset` | Reset all counters |
| `calibrate` | Recalibrate IMU starting position |
| `ping` | Get pong response |
| `setHigh:XXX` | Set high threshold (e.g. `setHigh:800`) |
| `setLow:XXX` | Set low threshold (e.g. `setLow:300`) |

## Form Detection

The IMU monitors:

| Issue | Detection | Alert |
|-------|-----------|-------|
| Wrist Twist | Roll exceeds ±20° | 🤚 Keep Wrist Straight |
| Elbow Flare | Yaw exceeds ±15° | 🦾 Elbow Flaring Out |
| Jerky Movement | Accel > 2.5g | ⚡ Too Fast |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| IMU not found | Check I2C wiring (SDA→21, SCL→22) |
| Form always bad | Recalibrate with arm in starting position |
| No curl detection | Adjust force thresholds |
| Bluetooth not visible | Ensure ESP32 Bluetooth is enabled |
| Connection drops | Move closer to ESP32, check battery |
