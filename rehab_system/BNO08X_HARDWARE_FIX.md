# BNO08x IMU Hardware Troubleshooting Guide

The ESP32 is reporting `{"err":"BNO08x not found. I2C devices found: 0"}`. 

**This means the ESP32 physically cannot see the IMU sensor on the wires.** The I2C scanner asks every possible address on the wire to respond, and 0 devices responded. Here is exactly how to fix this hardware issue:

## 1. Check the Wiring (Most Common Issue)
The BNO08x MUST be connected to the exact pins specified in the code.
*   **SDA (Data)** -> ESP32 **GPIO 21**
*   **SCL (Clock)** -> ESP32 **GPIO 22**
*   **VIN / VCC** -> ESP32 **3.3V** (Do NOT connect to 5V unless your breakout board specifically has a 5V regulator. 3.3V is safest for BNO08x).
*   **GND** -> ESP32 **GND**

*Double check that SDA and SCL are not swapped.*

## 2. Check the Breakout Board Specific Pins
Many BNO08x breakout boards (like SparkFun or Adafruit) require specific pins to be pulled HIGH or LOW to select I2C mode over SPI/UART.
*   **PS0**: Must be HIGH or LOW depending on the board to select I2C. Usually, leaving it unconnected or tying to 3.3V sets it to I2C.
*   **PS1**: Usually tied to GND for I2C.
*   **Wake (WAK)**: Sometimes needs to be pulled HIGH (3.3V) for the sensor to wake up.

**If you are using a bare BNO08x or a generic breakout:**
Try connecting the **WAK** (Wake) pin to **3.3V**.

## 3. Breadboard / Jumper Wire Issues
*   Jumper wires frequently break internally. Try swapping the SDA and SCL wires with brand new ones.
*   Breadboards can have dead rows. Try moving the IMU to a different spot on the breadboard.

## 4. Reset the ESP32
Sometimes the I2C bus locks up. Power cycle the whole system:
1. Unplug the ESP32 from USB.
2. Wait 5 seconds.
3. Plug it back in.
4. Open the Serial Monitor.

## 5. Alternative I2C Address
The code currently tries to connect to `0x4B` and `0x4A`. If your specific board has a solder jumper that changes the address to something else, it won't be found. However, since the scanner found `0` devices overall, this means the sensor is either not powered, wired incorrectly, or in the wrong communication mode (e.g. it thinks it should be using SPI).

## Summary
Focus on the physical connections. The software is actively scanning the pins, and there is no electrical response. Once you secure the wires, press the EN/RST button on the ESP32. You should see `I2C devices found: 1` (or more) in the Serial Monitor!
