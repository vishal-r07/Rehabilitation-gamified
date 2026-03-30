#include <Wire.h>

#define BNO08X_ADDR 0x4B // Default address for SparkFun BNO08x
#define SHTP_REPORT_PRODUCT_ID_REQUEST 0xF9
#define CHANNEL_CONTROL 2

TwoWire Wire(0); // Vega Aries v2 default I2C

void setup() {
  Serial.begin(115200);
  while (!Serial); // Wait for connection
  delay(1000);
  
  Serial.println("\n--- BNO08x MINIMAL RAW I2C TEST ---");
  Wire.begin();
  
  // 1. Check if device is physically there
  Wire.beginTransmission(BNO08X_ADDR);
  if (Wire.endTransmission() != 0) {
    Serial.println("FAIL: BNO08x I2C device not found. Check wiring/pull-ups.");
    while(1);
  }
  Serial.println("SUCCESS: BNO08x I2C address found!");

  // Wait for the BNO08x to boot up after power-on
  delay(300);

  // 2. Perform a software reset
  Serial.println("Sending Soft Reset...");
  uint8_t softreset_pkt[] = {5, 0, 1, 0, 1}; // SHTP header len=5, chan=1 (executable), seq=0, reset command=1
  Wire.beginTransmission(BNO08X_ADDR);
  Wire.write(softreset_pkt, 5);
  Wire.endTransmission();
  
  delay(300); // Wait for reset to complete
  Serial.println("Soft Reset sent. Attempting to read boot sequence headers...");

  // 3. Try to read anything from the device (just the 4-byte header)
  Wire.requestFrom((uint8_t)BNO08X_ADDR, (uint8_t)4);
  Serial.print("Received bytes: ");
  Serial.println(Wire.available());
  if (Wire.available() == 4) {
    uint8_t lsb = Wire.read();
    uint8_t msb = Wire.read();
    uint8_t chan = Wire.read();
    uint8_t seq = Wire.read();
    uint16_t length = (msb << 8) | lsb;
    length &= ~(1 << 15); // Clear continuation bit
    Serial.print("Header: Len="); Serial.print(length);
    Serial.print(" Chan="); Serial.print(chan);
    Serial.print(" Seq="); Serial.println(seq);
  } else {
    Serial.println("FAIL: Could not read header after reset! I2C bus might be locked.");
    while(Wire.available()) Wire.read(); // clear buffer
  }

  Serial.println("\n--- TEST COMPLETE ---");
}

void loop() {
  delay(1000);
}
