import serial
import serial.tools.list_ports
import time

def find_vega_port():
    ports = serial.tools.list_ports.comports()
    if not ports:
        return None
        
    print("Available COM Ports:")
    for i, port in enumerate(ports):
        print(f"[{i}] {port.device} - {port.description}")
        
    try:
        choice = int(input("\nEnter the number of the port to connect to: "))
        return ports[choice].device
    except (ValueError, IndexError):
        print("Invalid choice.")
        return None

def monitor_serial():
    port_name = find_vega_port()
    if not port_name:
        print("No COM ports found. Is the board plugged in?")
        return

    print(f"Connecting to {port_name} at 115200 baud...")
    
    try:
        # Open serial port
        ser = serial.Serial(port_name, 115200, timeout=1)
        print("Connected! Listening for raw data...\n" + "-"*40)
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print(line)
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"Error opening {port_name}: {e}")
        print("Make sure the Arduino IDE Serial Monitor is CLOSED.")
    except KeyboardInterrupt:
        print("\nExiting monitor.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    monitor_serial()
