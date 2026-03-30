/*
 * ESP32 Arm Rehabilitation Trainer - WebSocket Version
 * 
 * Features:
 * - Force/Flex sensor for bend detection
 * - EMG sensor for muscle activation
 * - BNO08x IMU for orientation tracking
 * - WiFi WebSocket communication (compatible with Python app)
 * 
 * Hardware Wiring:
 * - Force Sensor: GPIO32 with 10kΩ pull-down resistor
 * - EMG Sensor: GPIO35
 * - BNO08x IMU: SDA → GPIO21, SCL → GPIO22
 *  v
 * UPDATE WIFI CREDENTIALS BELOW!
 */

#include <Wire.h>
#include <SparkFun_BNO08x_Arduino_Library.h>
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>

// ============== WIFI CONFIGURATION ==============
// UPDATE THESE WITH YOUR WIFI CREDENTIALS!
const char* WIFI_SSID = "moto g45 5G_3950";
const char* WIFI_PASSWORD = "ashwin07";

// ============== GPIO PINS ==============
const int FORCE_PIN = 32;      // Force/flex sensor
const int EMG_PIN = 35;        // EMG sensor
const int SDA_PIN = 21;        // I2C SDA
const int SCL_PIN = 22;        // I2C SCL
const int MOTOR_PIN = 26;      // Haptic Motor

// ============== THRESHOLDS ==============
// Force sensor thresholds (increased to prevent false counting)
int THRESHOLD_HIGH = 2500;     // Above this = bent/folded (was 2000)
int THRESHOLD_LOW = 1200;      // Below this = relaxed (was 800)

// ============== OBJECTS ==============
WebServer httpServer(80);
WebSocketsServer webSocket(81);
BNO08x imu;

// ============== SENSOR VARIABLES ==============
// Force sensor
const int FORCE_SAMPLES = 10;
int forceReadings[FORCE_SAMPLES];
int forceIndex = 0;
long forceTotal = 0;
int forceRaw = 0;
int forceSmoothed = 0;

// EMG sensor
const int EMG_SAMPLES = 20;
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

// Connection status
bool wifiConnected = false;
int clientCount = 0;

// Timing
unsigned long lastBroadcast = 0;
unsigned long lastDebug = 0;
const unsigned long BROADCAST_INTERVAL = 50;  // 20Hz

// ============== HAPTICS ==============
unsigned long hapticTimer = 0;
bool isVibrating = false;
bool isBending = false;
unsigned long lastStateChange = 0;

// ============== FUNCTION PROTOTYPES ==============
void triggerBuzz(int duration);
void updateHaptics();

// ============== SETUP ==============
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("  ESP32 Arm Rehab Trainer (WebSocket)");
  Serial.println("========================================\n");
  
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
  
  // Setup WiFi & WebSocket
  setupWiFi();
  
  // Calibrate sensors
  if (imuConnected) {
    Serial.println("[CAL] Calibrating IMU - keep arm still...");
    delay(2000);
    calibrateIMU();
    triggerBuzz(200);
  }
  
  Serial.println("\n========================================");
  Serial.println("          SYSTEM READY");
  Serial.println("========================================\n");
}

// ============== MAIN LOOP ==============
void loop() {
  // Read sensors
  readForceSensor();
  readEMGSensor();
  readIMU();
  
  // Handle WebSocket
  httpServer.handleClient();
  webSocket.loop();
  
  // Broadcast data at 20Hz
  if (millis() - lastBroadcast >= BROADCAST_INTERVAL) {
    lastBroadcast = millis();
    broadcastData();
  }
  
  // Debug output every second
  if (millis() - lastDebug >= 1000) {
    lastDebug = millis();
    printDebug();
  }
  
  updateHaptics();
  
  // Bend Detection - NO motor buzz on every bend (extreme conditions only)
  if (!isBending && forceSmoothed > THRESHOLD_HIGH) {
    isBending = true;
    // Motor buzz removed - only buzzes at extreme conditions now
  } else if (isBending && forceSmoothed < THRESHOLD_LOW) {
    isBending = false;
  }
}

// ============== WIFI SETUP ==============
void setupWiFi() {
  Serial.println("[WIFI] Connecting to: " + String(WIFI_SSID));
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n[WIFI] ✓ Connected!");
    Serial.println("[WIFI] IP Address: " + WiFi.localIP().toString());
    Serial.println("[WIFI] WebSocket Port: 81");
    
    // Setup HTTP server
    httpServer.on("/", []() {
      httpServer.send(200, "text/html", 
        "<!DOCTYPE html><html><body style='background:#111;color:#0f0;font-family:monospace;padding:20px;'>"
        "<h1>ESP32 Arm Rehab Trainer</h1>"
        "<p>WebSocket running on port 81</p>"
        "<p>Connect Python app to: " + WiFi.localIP().toString() + "</p>"
        "</body></html>");
    });
    httpServer.begin();
    
    // Setup WebSocket
    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
    
  } else {
    wifiConnected = false;
    Serial.println("\n[WIFI] ✗ Failed to connect!");
  }
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      clientCount++;
      Serial.printf("[WS] Client #%u connected! Total: %d\n", num, clientCount);
      break;
    case WStype_DISCONNECTED:
      clientCount--;
      Serial.printf("[WS] Client #%u disconnected! Total: %d\n", num, clientCount);
      break;
    case WStype_TEXT:
      // Handle commands from Python
      String cmd = String((char*)payload);
      if (cmd == "calibrate") {
        calibrateIMU();
        webSocket.sendTXT(num, "{\"ack\":\"calibrated\"}");
      }
      break;
  }
}

// ============== IMU FUNCTIONS ==============
void setupIMU() {
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  delay(100);
  
  Serial.println("[IMU] Scanning I2C...");
  byte count = 0;
  for (byte i = 1; i < 127; i++) {
    Wire.beginTransmission(i);
    if (Wire.endTransmission() == 0) {
      Serial.printf("[IMU] Found device at 0x%02X\n", i);
      count++;
    }
  }
  
  Serial.println("[IMU] Initializing BNO08x...");
  if (imu.begin(0x4B, Wire) || imu.begin(0x4A, Wire)) {
    imuConnected = true;
    Serial.println("[IMU] ✓ BNO08x connected!");
    delay(100);
    imu.enableRotationVector(50);
    delay(50);
    imu.enableAccelerometer(50);
  } else {
    imuConnected = false;
    Serial.println("[IMU] ✗ BNO08x not found");
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
  Serial.printf("[IMU] Calibrated! Offsets: R=%.1f P=%.1f Y=%.1f\n", rollOffset, pitchOffset, yawOffset);
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
  if (!wifiConnected || clientCount == 0) return;
  
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
  
  // Build JSON - SAME FORMAT as bicep_curl_counter for Python compatibility
  // f = force, e = emg, r = roll, p = pitch, y = yaw
  String json = "{";
  json += "\"f\":" + String(forceSmoothed);
  json += ",\"e\":" + String(emgSmoothed);
  json += ",\"r\":" + String(relRoll, 1);
  json += ",\"p\":" + String(relPitch, 1);
  json += ",\"y\":" + String(relYaw, 1);
  json += "}";
  
  webSocket.broadcastTXT(json);
}

// ============== DEBUG OUTPUT ==============
void printDebug() {
  Serial.println("\n--- Sensor Status ---");
  Serial.printf("Force: raw=%d smooth=%d\n", forceRaw, forceSmoothed);
  Serial.printf("EMG:   raw=%d smooth=%d\n", emgRaw, emgSmoothed);
  Serial.printf("IMU:   R=%.1f P=%.1f Y=%.1f %s\n", roll, pitch, yaw, imuConnected ? "[OK]" : "[NONE]");
  Serial.printf("WiFi:  %s | Clients: %d\n", wifiConnected ? WiFi.localIP().toString().c_str() : "DISCONNECTED", clientCount);
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
