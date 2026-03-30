/*
 * ESP32 Arm Rehabilitation Trainer - High-Speed Serial Version
 * 
 * Features:
 * - Force/Flex sensor for bend detection
 * - EMG sensor for muscle activation
 * - BNO08x IMU for orientation tracking
 * - High-speed USB Serial communication (115200 baud) for ultra-low latency
 * 
 * Hardware Wiring:
 * - Force Sensor: GPIO32 with 10kΩ pull-down resistor
 * - EMG Sensor: GPIO35
 * - BNO08x IMU: SDA → GPIO21, SCL → GPIO22
 * - Haptic Motor: GPIO26
 */

#include <Wire.h>
#include <SparkFun_BNO08x_Arduino_Library.h>

// ============== GPIO PINS ==============
const int FORCE_PIN = 32;      // Force/flex sensor
const int EMG_PIN = 35;        // EMG sensor
const int SDA_PIN = 21;        // I2C SDA
const int SCL_PIN = 22;        // I2C SCL
const int MOTOR_PIN = 26;      // Haptic Motor

// ============== OBJECTS ==============
BNO08x imu;

// ============== SENSOR VARIABLES ==============
// Force sensor
const int FORCE_SAMPLES = 5; // Reduced for lower latency
int forceReadings[FORCE_SAMPLES];
int forceIndex = 0;
long forceTotal = 0;
int forceRaw = 0;
int forceSmoothed = 0;

// EMG sensor
const int EMG_SAMPLES = 10; // Reduced for lower latency
int emgReadings[EMG_SAMPLES];
int emgIndex = 0;
long emgTotal = 0;
int emgRaw = 0;
int emgSmoothed = 0;

// IMU data
bool imuConnected = false;
bool imuCalibrated = false;
float roll = 0, pitch = 0, yaw = 0;
float rollOffset = 0, pitchOffset = 0, yawOffset = 0;

// Timing
unsigned long lastBroadcast = 0;
const unsigned long BROADCAST_INTERVAL = 16;  // ~60Hz to match game frame rate

// ============== HAPTICS ==============
unsigned long hapticTimer = 0;
bool isVibrating = false;

// ============== FUNCTION PROTOTYPES ==============
void triggerBuzz(int duration);
void updateHaptics();
void setupIMU();
void readIMU();
void calibrateIMU();
void readForceSensor();
void readEMGSensor();
void broadcastData();

// ============== SETUP ==============
void setup() {
  Serial.begin(115200);
  delay(100);
  
  // ADC Configuration
  analogSetAttenuation(ADC_11db);
  analogReadResolution(12);
  pinMode(FORCE_PIN, INPUT);
  pinMode(EMG_PIN, INPUT);
  pinMode(MOTOR_PIN, OUTPUT);
  
  triggerBuzz(200); // Startup buzz
  
  // Initialize arrays
  memset(forceReadings, 0, sizeof(forceReadings));
  memset(emgReadings, 0, sizeof(emgReadings));
  
  // Setup IMU
  setupIMU();
  
  // Calibrate sensors
  if (imuConnected) {
    // Send a debug message (ignored by python parser if not JSON)
    Serial.println("{\"msg\":\"Calibrating IMU - keep arm still...\"}");
    delay(2000);
    calibrateIMU();
    triggerBuzz(200);
  }
  Serial.println("{\"msg\":\"SYSTEM READY\"}");
}

// ============== MAIN LOOP ==============
void loop() {
  // Read sensors as fast as possible
  readForceSensor();
  readEMGSensor();
  readIMU();
  
  // Check for commands from Serial (e.g. recalibrate)
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "calibrate") {
      calibrateIMU();
      Serial.println("{\"ack\":\"calibrated\"}");
    }
  }
  
  // Broadcast data at ~60Hz
  if (millis() - lastBroadcast >= BROADCAST_INTERVAL) {
    lastBroadcast = millis();
    broadcastData();
  }
  
  updateHaptics();
}

// ============== IMU FUNCTIONS ==============
void setupIMU() {
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000); // Reverted to stable 100kHz
  delay(100);
  
  // Scan I2C to log devices (helps with debugging "not found")
  byte count = 0;
  for (byte i = 1; i < 127; i++) {
    Wire.beginTransmission(i);
    if (Wire.endTransmission() == 0) {
      count++;
    }
  }
  
  if (imu.begin(0x4B, Wire) || imu.begin(0x4A, Wire)) {
    imuConnected = true;
    delay(100);
    imu.enableRotationVector(50); // Reverted to 50 interval
    delay(50);
    imu.enableAccelerometer(50);
  } else {
    imuConnected = false;
    Serial.printf("{\"err\":\"BNO08x not found. I2C devices found: %d\", \"imuConnected\": false}\n", count);
  }
}

void readIMU() {
  if (!imuConnected) return;
  
  if (imu.wasReset()) {
    imu.enableRotationVector(50);
    imu.enableAccelerometer(50);
  }
  
  int events = 0;
  while (imu.getSensorEvent() && events < 5) {
    events++;
    if (imu.getSensorEventID() == SENSOR_REPORTID_ROTATION_VECTOR) {
      roll = imu.getRoll() * 180.0 / PI;
      pitch = imu.getPitch() * 180.0 / PI;
      yaw = imu.getYaw() * 180.0 / PI;
    }
  }
}

void calibrateIMU() {
  if (!imuConnected) return;
  
  float rSum = 0, pSum = 0, ySum = 0;
  for (int i = 0; i < 20; i++) {
    readIMU();
    rSum += roll;
    pSum += pitch;
    ySum += yaw;
    delay(50);
  }
  rollOffset = rSum / 20.0;
  pitchOffset = pSum / 20.0;
  yawOffset = ySum / 20.0;
  imuCalibrated = true;
}

// ============== FORCE SENSOR ==============
void readForceSensor() {
  forceTotal -= forceReadings[forceIndex];
  forceRaw = analogRead(FORCE_PIN);
  forceReadings[forceIndex] = forceRaw;
  forceTotal += forceRaw;
  forceIndex = (forceIndex + 1) % FORCE_SAMPLES;
  forceSmoothed = forceTotal / FORCE_SAMPLES;
}

// ============== EMG SENSOR ==============
void readEMGSensor() {
  emgTotal -= emgReadings[emgIndex];
  emgRaw = analogRead(EMG_PIN);
  emgReadings[emgIndex] = emgRaw;
  emgTotal += emgRaw;
  emgIndex = (emgIndex + 1) % EMG_SAMPLES;
  emgSmoothed = emgTotal / EMG_SAMPLES;
}

// ============== BROADCAST DATA ==============
void broadcastData() {
  // Calculate relative IMU angles
  float relRoll = roll - rollOffset;
  float relPitch = pitch - pitchOffset;
  float relYaw = yaw - yawOffset;
  
  // Normalize angles
  while (relRoll > 180) relRoll -= 360;
  while (relRoll < -180) relRoll += 360;
  while (relPitch > 180) relPitch -= 360;
  while (relPitch < -180) relPitch += 360;
  while (relYaw > 180) relYaw -= 360;
  while (relYaw < -180) relYaw += 360;
  
  // Build JSON - SAME FORMAT as websocket for Python compatibility
  // f = force, e = emg, r = roll, p = pitch, y = yaw
  String json = "{";
  json += "\"sensorValue\":" + String(forceSmoothed);
  json += ",\"rawValue\":" + String(forceRaw);
  json += ",\"emgValue\":" + String(emgSmoothed);
  json += ",\"roll\":" + String(relRoll, 1);
  json += ",\"pitch\":" + String(relPitch, 1);
  json += ",\"yaw\":" + String(relYaw, 1);
  json += ",\"imuConnected\":" + String(imuConnected ? "true" : "false");
  json += ",\"isCalibrated\":" + String(imuCalibrated ? "true" : "false");
  json += ",\"state\":\"" + String(forceSmoothed > 500 ? "BENT" : "EXTENDED") + "\""; 
  json += "}";
  
  // Print exactly one line
  Serial.println(json);
}

// ============== HAPTIC ENGINE ==============
void triggerBuzz(int duration) {
  digitalWrite(MOTOR_PIN, HIGH);
  hapticTimer = millis() + duration;
  isVibrating = true;
}

void updateHaptics() {
  if (isVibrating && millis() > hapticTimer) {
    digitalWrite(MOTOR_PIN, LOW);
    isVibrating = false;
  }
}
