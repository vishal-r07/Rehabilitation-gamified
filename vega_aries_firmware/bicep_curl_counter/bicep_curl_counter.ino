#include <SPI.h>
#include <mcp_can.h>

const int spiCSPin = PA4;
MCP_CAN CAN(spiCSPin);

void printPriority(long unsigned int rxId) {
  if      (rxId == 0x005 || rxId == 0x010) Serial.print("[CRITICAL] ");
  else if (rxId == 0x050 || rxId == 0x060) Serial.print("[WARNING]  ");
  else if (rxId == 0x100 || rxId == 0x110) Serial.print("[NORMAL]   ");
}

void decodeEngine(unsigned char* buf) {
  uint16_t rpm      = ((uint16_t)buf[0] << 8) | buf[1];
  uint8_t throttle  = buf[2];
  uint8_t engTemp   = buf[3];

  Serial.print("ENGINE | RPM: ");
  Serial.print(rpm);
  Serial.print(" | Throttle: ");
  Serial.print(throttle);
  Serial.print("% | Eng.Temp: ");
  Serial.print(engTemp);
  Serial.print("C");
}

void decodeChassis(unsigned char* buf) {
  Serial.print("CHASSIS | Tires FL:");
  Serial.print(buf[0]);
  Serial.print("C FR:");
  Serial.print(buf[1]);
  Serial.print("C RL:");
  Serial.print(buf[2]);
  Serial.print("C RR:");
  Serial.print(buf[3]);
  Serial.print("C | Brake F:");
  Serial.print(buf[4]);
  Serial.print("% R:");
  Serial.print(buf[5]);
  Serial.print("%");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=== DPSF-CAN Master Host [F1 MONITOR] ===");

  while (CAN_OK != CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ)) {
    Serial.println("CAN Init FAILED... retrying");
    delay(1000);
  }

  CAN.setMode(MCP_NORMAL);
  Serial.println("Master Ready. Monitoring F1 Bus...");
  Serial.println("------------------------------------------");
}

void loop() {
  long unsigned int rxId;
  unsigned char len = 0;
  unsigned char rxBuf[8];

  if (CAN_MSGAVAIL == CAN.checkReceive()) {
    CAN.readMsgBuf(&rxId, &len, rxBuf);

    // Whitelist check
    bool validId = (rxId == 0x005 || rxId == 0x010 ||
                    rxId == 0x050 || rxId == 0x060 ||
                    rxId == 0x100 || rxId == 0x110);

    if (!validId || len == 0) return; // silently drop noise

    unsigned long ts = millis();
    Serial.print("[");
    Serial.print(ts);
    Serial.print("ms] ");

    printPriority(rxId);

    // Route to correct decoder
    if (rxId == 0x005 || rxId == 0x050 || rxId == 0x100) {
      decodeEngine(rxBuf);
    } else {
      decodeChassis(rxBuf);
    }

    Serial.println();
  }
}