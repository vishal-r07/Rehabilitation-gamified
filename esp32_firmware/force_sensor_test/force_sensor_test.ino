// Force Sensor Test - Upload this to verify pin 32 is working

const int FORCE_PIN = 32;  // GPIO 32

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Configure pin 32 as analog input
  pinMode(FORCE_PIN, INPUT);
  
  Serial.println("\n=== Force Sensor Test ===");
  Serial.println("Pin: GPIO 32");
  Serial.println("Reading every 100ms");
  Serial.println("========================\n");
}

void loop() {
  // Read raw ADC value (0-4095 on ESP32)
  int rawValue = analogRead(FORCE_PIN);
  
  // Convert to voltage (0-3.3V)
  float voltage = (rawValue / 4095.0) * 3.3;
  
  // Print both raw and voltage
  Serial.print("Raw ADC: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage, 2);
  Serial.println("V");
  
  delay(100);
}

/*
 * EXPECTED OUTPUT:
 * - No sensor: ~0-50 (near 0V)
 * - Light pressure: 100-500
 * - Medium pressure: 500-1500
 * - Hard pressure: 1500-4000
 * 
 * WIRING:
 * - Sensor Pin 1 → 3.3V
 * - Sensor Pin 2 → GPIO 32
 * - 10kΩ resistor between GPIO 32 and GND (pulldown)
 */
