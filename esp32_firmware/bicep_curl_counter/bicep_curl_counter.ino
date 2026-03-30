/*
 * ESP32 Arm Rehabilitation Trainer
 * 
 * Enhanced firmware with:
 * - EMG sensor with muscle fatigue detection
 * - IMU forearm posture tracking (BNO08x)
 * - Force/Bend sensor for movement detection
 * - Injury prevention algorithms
 * - Bluetooth Serial communication
 * 
 * Hardware Wiring:
 * - EMG Sensor (AD8232/MyoWare): Signal → GPIO35
 * - Force Sensor: GPIO32 with 10kΩ pull-down
 * - BNO08x IMU: SDA → GPIO21, SCL → GPIO22
 * 
 * Communication: Bluetooth Serial (Classic)
 */

#include <Wire.h>
#include <SparkFun_BNO08x_Arduino_Library.h>
#include <BluetoothSerial.h>

// ============== CONFIGURATION ==============
#define DEVICE_NAME "ReflexAI-Trainer"

// GPIO Pins
const int EMG_PIN = 35;        // EMG sensor analog input
const int FORCE_PIN = 32;      // Force/bend sensor
const int SDA_PIN = 21;        // I2C SDA
const int SCL_PIN = 22;        // I2C SCL
const int MOTOR_PIN = 26;      // Haptic Motor (Transistor Base)

// EMG Processing
const int EMG_SAMPLE_SIZE = 100;      // Samples for RMS calculation
const int EMG_FATIGUE_WINDOW = 500;   // Samples for fatigue detection
const float EMG_FATIGUE_THRESHOLD = 0.7; // 70% decrease = fatigue

// Posture Thresholds (degrees) - INCREASED for extreme conditions only
const float WRIST_EXTENSION_MAX = 60.0;   // Max safe wrist extension (was 45)
const float WRIST_FLEXION_MAX = 75.0;     // Max safe wrist flexion (was 60)
const float FOREARM_ROTATION_MAX = 100.0; // Max pronation/supination (was 80)
const float ELBOW_LOCK_ANGLE = 175.0;     // Near full extension warning (was 170)

// Injury Prevention
const int MAX_EXERCISE_DURATION_SEC = 1800; // 30 minutes max
const int REST_INTERVAL_SEC = 300;          // Suggest rest every 5 min
const int MAX_WARNINGS_BEFORE_CRITICAL = 10; // Risk escalation

// Force Sensor Thresholds - INCREASED to prevent false counting
const int FORCE_THRESHOLD_LOW = 500;   // Light bend (was 300)
const int FORCE_THRESHOLD_HIGH = 1200; // Full bend (was 700) - requires stronger bend
const int DEBOUNCE_MS = 800;           // Debounce time (was 500)

// ============== OBJECTS ==============
BluetoothSerial SerialBT;
BNO08x imu;

// ============== EMG VARIABLES ==============
int emgBuffer[EMG_SAMPLE_SIZE];
int emgBufferIndex = 0;
long emgSum = 0;
float emgRms = 0;
float emgRmsMax = 0;
float emgRmsBaseline = 0;
bool emgBaselineSet = false;

// Fatigue detection
float emgFatigueHistory[10];  // Running average of peak EMG
int emgFatigueIndex = 0;
float muscleFatigueLevel = 0; // 0-100%
bool muscleFatigueDetected = false;
float muscleActivation = 0;   // 0-100%

// ============== IMU VARIABLES ==============
bool imuConnected = false;
bool imuCalibrated = false;
float roll = 0, pitch = 0, yaw = 0;
float rollOffset = 0, pitchOffset = 0, yawOffset = 0;
float accelX = 0, accelY = 0, accelZ = 0;
float accelMagnitude = 0;
float gyroX = 0, gyroY = 0, gyroZ = 0;

// Posture analysis
float wristAngle = 0;      // Extension (+) / Flexion (-)
float forearmRotation = 0; // Pronation (+) / Supination (-)
float elbowAngle = 90;     // Estimated from sensors
bool postureGood = true;
String postureWarning = "";

// ============== FORCE/BEND VARIABLES ==============
int forceRaw = 0;
int forceSmoothed = 0;
int forceReadings[15];
int forceReadIndex = 0;
long forceTotal = 0;
bool isBending = false;
int bendCount = 0;
unsigned long lastBendTime = 0;

// ============== INJURY PREVENTION ==============
enum InjuryRiskLevel { RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL };
InjuryRiskLevel injuryRisk = RISK_LOW;
unsigned long exerciseStartTime = 0;
int exerciseDuration = 0;
int restRecommendation = 0;
int totalWarnings = 0;
int consecutiveGoodForm = 0;
unsigned long lastRestReminder = 0;

// ============== TIMING ==============
unsigned long lastBroadcast = 0;
unsigned long lastDebug = 0;
const unsigned long BROADCAST_INTERVAL = 50;  // 20Hz streaming
const unsigned long DEBUG_INTERVAL = 1000;

// ============== BLUETOOTH ==============
bool btConnected = false;
String inputBuffer = "";

// ============== HAPTICS ==============
unsigned long hapticTimer = 0;
bool isVibrating = false;
unsigned long lastFormWarningTime = 0;
unsigned long lastSafetyWarning = 0;

// ============== FUNCTION PROTOTYPES ==============
void setupIMU();
void readIMU();
void calibrateIMU();
void readEMG();
void calculateEMGFatigue();
void readForceSensor();
void detectBend();
void analyzePosture();
void calculateInjuryRisk();
void handleBluetoothCommands();
void handleBluetoothCommands();
void broadcastData();
void triggerBuzz(int duration);
void updateHaptics();

// ============== SETUP ==============
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n========================================");
  Serial.println("   ESP32 Arm Rehabilitation Trainer");
  Serial.println("========================================\n");
  
  // ADC Configuration
  analogSetAttenuation(ADC_11db);
  analogReadResolution(12);
  pinMode(EMG_PIN, INPUT);
  pinMode(FORCE_PIN, INPUT);
  pinMode(MOTOR_PIN, OUTPUT);
  
  triggerBuzz(200); // Startup buzz
  
  // Initialize arrays
  memset(emgBuffer, 0, sizeof(emgBuffer));
  memset(forceReadings, 0, sizeof(forceReadings));
  memset(emgFatigueHistory, 0, sizeof(emgFatigueHistory));
  
  // Setup IMU
  setupIMU();
  
  // Setup Bluetooth
  Serial.println("[BT] Initializing Bluetooth Serial...");
  if (SerialBT.begin(DEVICE_NAME)) {
    Serial.println("[BT] ✓ Bluetooth ready as: " + String(DEVICE_NAME));
  } else {
    Serial.println("[BT] ✗ Bluetooth initialization failed!");
  }
  
  // Initial calibrations
  delay(1000);
  if (imuConnected) {
    Serial.println("\n[CAL] Calibrating IMU - keep arm still...");
    delay(2000);
    calibrateIMU();
    triggerBuzz(200);
  }
  
  // Calibrate EMG baseline
  Serial.println("[CAL] Calibrating EMG baseline - relax arm...");
  delay(1000);
  calibrateEMGBaseline();
  
  exerciseStartTime = millis();
  
  Serial.println("\n========================================");
  Serial.println("          SYSTEM READY");
  Serial.println("========================================\n");
}

// ============== MAIN LOOP ==============
void loop() {
  // Read all sensors
  readIMU();
  readEMG();
  calculateEMGFatigue();
  readForceSensor();
  detectBend();
  
  // Analysis
  analyzePosture();
  calculateInjuryRisk();
  
  // Update exercise duration
  exerciseDuration = (millis() - exerciseStartTime) / 1000;
  
  // Handle Bluetooth commands
  handleBluetoothCommands();
  
  // Broadcast data
  if (millis() - lastBroadcast >= BROADCAST_INTERVAL) {
    lastBroadcast = millis();
    broadcastData();
  }
  
  // Debug output
  if (millis() - lastDebug >= DEBUG_INTERVAL) {
    lastDebug = millis();
    printDebugInfo();
  }
  
  updateHaptics();
}

// ============== IMU FUNCTIONS ==============
void setupIMU() {
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  delay(100);
  
  Serial.println("[IMU] Scanning I2C bus...");
  byte count = 0;
  for (byte i = 1; i < 127; i++) {
    Wire.beginTransmission(i);
    if (Wire.endTransmission() == 0) {
      Serial.printf("[IMU] Found device at 0x%02X\n", i);
      count++;
    }
  }
  if (count == 0) {
    Serial.println("[IMU] No I2C devices found!");
  }
  
  Serial.println("[IMU] Initializing BNO08x...");
  
  if (imu.begin(0x4B, Wire) || imu.begin(0x4A, Wire)) {
    imuConnected = true;
    Serial.println("[IMU] ✓ BNO08x connected!");
    
    delay(100);
    imu.enableRotationVector(50);
    delay(50);
    imu.enableAccelerometer(50);
    delay(50);
    imu.enableGyro(50);
  } else {
    imuConnected = false;
    Serial.println("[IMU] ✗ BNO08x not found - posture tracking disabled");
  }
}

void readIMU() {
  if (!imuConnected) return;
  
  if (imu.wasReset()) {
    Serial.println("[IMU] Reset detected, re-initializing...");
    imu.enableRotationVector(50);
    imu.enableAccelerometer(50);
    imu.enableGyro(50);
  }
  
  int events = 0;
  while (imu.getSensorEvent() && events < 10) {
    events++;
    uint8_t eventID = imu.getSensorEventID();
    
    if (eventID == SENSOR_REPORTID_ROTATION_VECTOR) {
      roll = imu.getRoll() * 180.0 / PI;
      pitch = imu.getPitch() * 180.0 / PI;
      yaw = imu.getYaw() * 180.0 / PI;
    }
    else if (eventID == SENSOR_REPORTID_ACCELEROMETER) {
      accelX = imu.getAccelX();
      accelY = imu.getAccelY();
      accelZ = imu.getAccelZ();
      accelMagnitude = sqrt(accelX*accelX + accelY*accelY + accelZ*accelZ);
    }
    else if (eventID == SENSOR_REPORTID_GYROSCOPE_CALIBRATED) {
      gyroX = imu.getGyroX();
      gyroY = imu.getGyroY();
      gyroZ = imu.getGyroZ();
    }
  }
}

void calibrateIMU() {
  if (!imuConnected) return;
  
  float rollSum = 0, pitchSum = 0, yawSum = 0;
  for (int i = 0; i < 20; i++) {
    readIMU();
    rollSum += roll;
    pitchSum += pitch;
    yawSum += yaw;
    delay(50);
  }
  
  rollOffset = rollSum / 20.0;
  pitchOffset = pitchSum / 20.0;
  yawOffset = yawSum / 20.0;
  imuCalibrated = true;
  
  Serial.printf("[IMU] Calibrated! Offsets: R=%.1f P=%.1f Y=%.1f\n", 
                rollOffset, pitchOffset, yawOffset);
}

// ============== EMG FUNCTIONS ==============
void readEMG() {
  // Remove oldest value from sum
  emgSum -= emgBuffer[emgBufferIndex];
  
  // Read new value
  int rawValue = analogRead(EMG_PIN);
  emgBuffer[emgBufferIndex] = rawValue;
  emgSum += rawValue;
  
  emgBufferIndex = (emgBufferIndex + 1) % EMG_SAMPLE_SIZE;
  
  // Calculate RMS (Root Mean Square) for envelope detection
  long sumSquares = 0;
  for (int i = 0; i < EMG_SAMPLE_SIZE; i++) {
    int centered = emgBuffer[i] - 2048; // Center around 0
    sumSquares += (long)centered * centered;
  }
  emgRms = sqrt((float)sumSquares / EMG_SAMPLE_SIZE);
  
  // Track maximum for normalization
  if (emgRms > emgRmsMax) {
    emgRmsMax = emgRms;
  }
  
  // Calculate muscle activation percentage
  if (emgRmsMax > emgRmsBaseline && emgRmsMax > 0) {
    muscleActivation = ((emgRms - emgRmsBaseline) / (emgRmsMax - emgRmsBaseline)) * 100.0;
    muscleActivation = constrain(muscleActivation, 0, 100);
  }
}

void calibrateEMGBaseline() {
  // Read EMG for 2 seconds while relaxed
  long sum = 0;
  int samples = 0;
  unsigned long start = millis();
  
  while (millis() - start < 2000) {
    sum += analogRead(EMG_PIN);
    samples++;
    delay(10);
  }
  
  int avgRaw = sum / samples;
  
  // Calculate baseline RMS
  long sumSquares = 0;
  for (int i = 0; i < 50; i++) {
    int val = analogRead(EMG_PIN) - 2048;
    sumSquares += (long)val * val;
    delay(10);
  }
  emgRmsBaseline = sqrt((float)sumSquares / 50);
  emgBaselineSet = true;
  
  Serial.printf("[EMG] Baseline set: raw=%d, RMS=%.1f\n", avgRaw, emgRmsBaseline);
}

void calculateEMGFatigue() {
  // Store peak EMG RMS in rolling history
  static unsigned long lastFatigueUpdate = 0;
  
  if (millis() - lastFatigueUpdate >= 3000) { // Update every 3 seconds
    lastFatigueUpdate = millis();
    
    // Store current peak
    emgFatigueHistory[emgFatigueIndex] = emgRms;
    emgFatigueIndex = (emgFatigueIndex + 1) % 10;
    
    // Compare first half to second half of history
    float firstHalf = 0, secondHalf = 0;
    for (int i = 0; i < 5; i++) {
      firstHalf += emgFatigueHistory[i];
      secondHalf += emgFatigueHistory[i + 5];
    }
    
    if (firstHalf > 0) {
      float fatigueRatio = secondHalf / firstHalf;
      
      // If EMG amplitude decreased significantly = fatigue
      if (fatigueRatio < EMG_FATIGUE_THRESHOLD) {
        muscleFatigueLevel = (1.0 - fatigueRatio) * 100.0;
        muscleFatigueDetected = true;
        // Buzz on fatigue
        if (millis() - lastSafetyWarning > 2000) {
             triggerBuzz(1000);
             lastSafetyWarning = millis();
        }
      } else {
        muscleFatigueLevel = max(0.0f, muscleFatigueLevel - 5.0f); // Gradual recovery
        if (muscleFatigueLevel < 20) muscleFatigueDetected = false;
      }
    }
  }
}

// ============== FORCE SENSOR FUNCTIONS ==============
void readForceSensor() {
  forceTotal -= forceReadings[forceReadIndex];
  forceRaw = analogRead(FORCE_PIN);
  forceReadings[forceReadIndex] = forceRaw;
  forceTotal += forceRaw;
  forceReadIndex = (forceReadIndex + 1) % 15;
  forceSmoothed = forceTotal / 15;
}

void detectBend() {
  unsigned long now = millis();
  
  if (now - lastBendTime < DEBOUNCE_MS) return;
  
  if (!isBending && forceSmoothed > FORCE_THRESHOLD_HIGH) {
    isBending = true;
    lastBendTime = now;
    Serial.println("[BEND] → Bend detected");
    // NOTE: Motor buzz removed here - only buzzes at extreme conditions now
  }
  else if (isBending && forceSmoothed < FORCE_THRESHOLD_LOW) {
    isBending = false;
    lastBendTime = now;
    bendCount++;
    Serial.printf("[BEND] ← Release! Total: %d\n", bendCount);
  }
}

// ============== POSTURE ANALYSIS ==============
void analyzePosture() {
  if (!imuConnected || !imuCalibrated) {
    postureGood = true;
    postureWarning = "";
    return;
  }
  
  postureGood = true;
  postureWarning = "";
  
  // Calculate relative angles from calibrated position
  float relRoll = roll - rollOffset;
  float relPitch = pitch - pitchOffset;
  float relYaw = yaw - yawOffset;
  
  // Normalize angles to -180 to 180
  while (relRoll > 180) relRoll -= 360;
  while (relRoll < -180) relRoll += 360;
  while (relPitch > 180) relPitch -= 360;
  while (relPitch < -180) relPitch += 360;
  
  // Wrist angle approximation (pitch relates to wrist flex/extend)
  wristAngle = relPitch;
  
  // Forearm rotation (roll relates to pronation/supination)
  forearmRotation = relRoll;
  
  // Elbow angle estimation (simplified - based on force sensor and orientation)
  // Higher force + certain pitch = more bent elbow
  elbowAngle = 180 - (forceSmoothed / 4095.0 * 90);
  elbowAngle = constrain(elbowAngle, 30, 180);
  
  // Check for posture issues
  if (wristAngle > WRIST_EXTENSION_MAX) {
    postureGood = false;
    postureWarning = "WRIST_OVEREXTENDED";
    totalWarnings++;
  }
  else if (wristAngle < -WRIST_FLEXION_MAX) {
    postureGood = false;
    postureWarning = "WRIST_FLEXED";
    totalWarnings++;
  }
  else if (abs(forearmRotation) > FOREARM_ROTATION_MAX) {
    postureGood = false;
    postureWarning = "FOREARM_STRAINED";
    totalWarnings++;
  }
  else if (elbowAngle > ELBOW_LOCK_ANGLE) {
    postureGood = false;
    postureWarning = "ELBOW_LOCKED";
    totalWarnings++;
  }
  else if (muscleFatigueDetected) {
    postureGood = false;
    postureWarning = "MUSCLE_FATIGUE";
    totalWarnings++;
  }
  
  // Haptic feedback REMOVED here - only buzzes at HIGH/CRITICAL risk level now
  // Motor will be triggered in calculateInjuryRisk() for extreme conditions only

  // Track consecutive good form
  if (postureGood) {
    consecutiveGoodForm++;
    if (consecutiveGoodForm > 100) {
      totalWarnings = max(0, totalWarnings - 1); // Reduce warnings for good behavior
    }
  } else {
    consecutiveGoodForm = 0;
  }
}

// ============== INJURY PREVENTION ==============
void calculateInjuryRisk() {
  int riskScore = 0;
  
  // Factor 1: Total warnings accumulated
  riskScore += min(totalWarnings, 30);
  
  // Factor 2: Muscle fatigue
  riskScore += (int)(muscleFatigueLevel * 0.3);
  
  // Factor 3: Exercise duration
  if (exerciseDuration > REST_INTERVAL_SEC) {
    riskScore += (exerciseDuration / REST_INTERVAL_SEC) * 10;
  }
  
  // Factor 4: Current posture warning
  if (!postureGood) riskScore += 15;
  
  // Factor 5: High acceleration (impact)
  if (accelMagnitude > 15.0) riskScore += 10;
  
  // Determine risk level
  if (riskScore < 20) {
    injuryRisk = RISK_LOW;
    restRecommendation = 0;
  }
  else if (riskScore < 40) {
    injuryRisk = RISK_MEDIUM;
    restRecommendation = 30; // 30 second rest
  }
  else if (riskScore < 60) {
    injuryRisk = RISK_HIGH;
    restRecommendation = 60; // 1 minute rest
    // MOTOR BUZZ at HIGH risk - extreme condition
    if (millis() - lastFormWarningTime > 2000) {
      triggerBuzz(500);
      lastFormWarningTime = millis();
    }
  }
  else {
    injuryRisk = RISK_CRITICAL;
    restRecommendation = 180; // 3 minute rest
    // MOTOR BUZZ at CRITICAL risk - extreme condition (stronger)
    if (millis() - lastFormWarningTime > 1500) {
      triggerBuzz(1000);
      lastFormWarningTime = millis();
    }
  }
  
  // Override: too long without break
  if (exerciseDuration > MAX_EXERCISE_DURATION_SEC) {
    injuryRisk = RISK_CRITICAL;
    restRecommendation = 300; // 5 minute rest
    // MOTOR BUZZ for exercise timeout
    if (millis() - lastFormWarningTime > 3000) {
      triggerBuzz(1500);
      lastFormWarningTime = millis();
    }
  }
}

// ============== BLUETOOTH ==============
void handleBluetoothCommands() {
  while (SerialBT.available()) {
    char c = SerialBT.read();
    if (c == '\n') {
      processCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
  
  // Update connection status
  btConnected = SerialBT.hasClient();
}

void processCommand(String cmd) {
  cmd.trim();
  Serial.println("[CMD] Received: " + cmd);
  
  if (cmd == "reset") {
    bendCount = 0;
    totalWarnings = 0;
    exerciseStartTime = millis();
    emgRmsMax = 0;
    muscleFatigueLevel = 0;
    muscleFatigueDetected = false;
    Serial.println("[CMD] Reset complete");
    SerialBT.println("{\"type\":\"ack\",\"cmd\":\"reset\",\"status\":\"ok\"}");
  }
  else if (cmd == "calibrate") {
    calibrateIMU();
    calibrateEMGBaseline();
    Serial.println("[CMD] Calibration complete");
    SerialBT.println("{\"type\":\"ack\",\"cmd\":\"calibrate\",\"status\":\"ok\"}");
  }
  else if (cmd == "ping") {
    SerialBT.println("{\"type\":\"ack\",\"cmd\":\"ping\",\"status\":\"ok\"}");
  }
  else if (cmd.startsWith("setHigh:")) {
    // Future: adjust thresholds
    SerialBT.println("{\"type\":\"ack\",\"cmd\":\"setHigh\",\"status\":\"ok\"}");
  }
  else if (cmd.startsWith("setLow:")) {
    SerialBT.println("{\"type\":\"ack\",\"cmd\":\"setLow\",\"status\":\"ok\"}");
  }
}

void broadcastData() {
  if (!btConnected) return;
  
  // Build JSON data packet
  String json = "{\"type\":\"data\"";
  
  // EMG data
  json += ",\"emgValue\":" + String((int)emgRms);
  json += ",\"emgRms\":" + String(emgRms, 1);
  json += ",\"emgFatigueLevel\":" + String(muscleFatigueLevel, 1);
  json += ",\"muscleActivation\":" + String(muscleActivation, 1);
  json += ",\"muscleFatigueDetected\":" + String(muscleFatigueDetected ? "true" : "false");
  
  // IMU data
  json += ",\"imuConnected\":" + String(imuConnected ? "true" : "false");
  json += ",\"isCalibrated\":" + String(imuCalibrated ? "true" : "false");
  json += ",\"roll\":" + String(roll, 1);
  json += ",\"pitch\":" + String(pitch, 1);
  json += ",\"yaw\":" + String(yaw, 1);
  json += ",\"accel\":" + String(accelMagnitude, 1);
  
  // Posture data
  json += ",\"wristAngle\":" + String(wristAngle, 1);
  json += ",\"forearmRotation\":" + String(forearmRotation, 1);
  json += ",\"elbowAngle\":" + String(elbowAngle, 1);
  json += ",\"postureGood\":" + String(postureGood ? "true" : "false");
  json += ",\"postureWarning\":\"" + postureWarning + "\"";
  
  // Force/bend data
  json += ",\"bendForce\":" + String(forceSmoothed);
  json += ",\"isBending\":" + String(isBending ? "true" : "false");
  json += ",\"bendCount\":" + String(bendCount);
  
  // Injury prevention
  String riskStr = "LOW";
  if (injuryRisk == RISK_MEDIUM) riskStr = "MEDIUM";
  else if (injuryRisk == RISK_HIGH) riskStr = "HIGH";
  else if (injuryRisk == RISK_CRITICAL) riskStr = "CRITICAL";
  
  json += ",\"injuryRisk\":\"" + riskStr + "\"";
  json += ",\"exerciseDuration\":" + String(exerciseDuration);
  json += ",\"restRecommendation\":" + String(restRecommendation);
  json += ",\"totalWarnings\":" + String(totalWarnings);
  
  // Legacy compatibility fields
  json += ",\"curlCount\":" + String(bendCount);
  json += ",\"goodFormCurls\":" + String(bendCount - min(bendCount, totalWarnings));
  json += ",\"sensorValue\":" + String(forceSmoothed);
  json += ",\"rawValue\":" + String(forceRaw);
  json += ",\"state\":\"" + String(isBending ? "BENT" : "EXTENDED") + "\"";
  json += ",\"formGood\":" + String(postureGood ? "true" : "false");
  json += ",\"formWarning\":\"" + postureWarning + "\"";
  
  json += "}";
  
  SerialBT.println(json);
}

void printDebugInfo() {
  Serial.println("\n--- Status ---");
  Serial.printf("EMG: RMS=%.1f Act=%.0f%% Fat=%.0f%%\n", 
                emgRms, muscleActivation, muscleFatigueLevel);
  Serial.printf("IMU: R=%.1f P=%.1f Y=%.1f\n", roll, pitch, yaw);
  Serial.printf("Posture: Wrist=%.1f° Forearm=%.1f° Elbow=%.1f° %s\n",
                wristAngle, forearmRotation, elbowAngle,
                postureGood ? "OK" : postureWarning.c_str());
  Serial.printf("Bend: Force=%d Count=%d %s\n",
                forceSmoothed, bendCount, isBending ? "[BENDING]" : "");
  
  String riskStr = "LOW";
  if (injuryRisk == RISK_MEDIUM) riskStr = "MEDIUM";
  else if (injuryRisk == RISK_HIGH) riskStr = "HIGH";
  else if (injuryRisk == RISK_CRITICAL) riskStr = "CRITICAL";
  
  Serial.printf("Risk: %s (Warnings: %d, Duration: %ds)\n",
                riskStr.c_str(), totalWarnings, exerciseDuration);
  Serial.printf("BT: %s\n", btConnected ? "Connected" : "Waiting...");
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
