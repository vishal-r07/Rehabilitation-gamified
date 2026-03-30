"""
Vega Aries v2 USB Serial Client for Sensor Data
Handles IMU, Force, and EMG sensor data streaming via COM port
"""
import json
import threading
import time
import serial

class ESP32Client:
    def __init__(self):
        self.ser = None
        self.connected = False
        self.imu_data = {'roll': 0, 'pitch': 0, 'yaw': 0}
        self.force_data = 0
        self.emg_data = 0
        self.callbacks = []
        self.last_error = None
        self._thread = None
        self._stop_event = threading.Event()
        
    def connect(self, port_name, baudrate=115200):
        """Connect to Vega Aries v2 via USB Serial"""
        self.last_error = None
        print(f"[VegaAries] Connecting to {port_name} at {baudrate} baud...")
        
        try:
            self.ser = serial.Serial(port_name, baudrate, timeout=1)
            self.connected = True
            self._stop_event.clear()
            print("[VegaAries] Connected via Serial!")
            
            # Start reader thread
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        except serial.SerialException as e:
            self.last_error = str(e)
            self.connected = False
            print(f"[VegaAries] Check connection: {e}")
        
    def disconnect(self):
        """Close Serial connection"""
        self.connected = False
        self._stop_event.set()
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[VegaAries] Disconnected")
            
    def send_command(self, cmd_str):
        """Send a string command to the Vega Aries v2 (e.g. calibration)"""
        if self.connected and self.ser and self.ser.is_open:
            try:
                self.ser.write(f"{cmd_str}\n".encode('utf-8'))
                print(f"[VegaAries] Sent Command: {cmd_str}")
                return True
            except Exception as e:
                print(f"[VegaAries] Failed to send command: {e}")
                return False
        return False
        
    def add_callback(self, callback):
        """Register callback for new data"""
        self.callbacks.append(callback)

    def set_data_callback(self, callback):
        """Set a SINGLE high-speed callback (Optimized for Game)"""
        self.callbacks = [callback]
        
    def _read_loop(self):
        """Continuous background loop reading from serial port"""
        while not self._stop_event.is_set() and self.connected:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._parse_message(line)
                else:
                    time.sleep(0.01) # Prevent 100% CPU usage
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
                print(f"[VegaAries] Serial Error: {e}")
                self.disconnect()
                break
                
    def _parse_message(self, message):
        """Parse incoming JSON sensor data from serial line"""
        try:
            data = json.loads(message)
            
            # Vega Aries sends: r, p, y, f, e (abbreviated field names)
            if 'roll' in data or 'r' in data:
                self.imu_data['roll'] = data.get('roll', data.get('r', 0))
            if 'pitch' in data or 'p' in data:
                self.imu_data['pitch'] = data.get('pitch', data.get('p', 0))
            if 'yaw' in data or 'y' in data:
                self.imu_data['yaw'] = data.get('yaw', data.get('y', 0))
                
            # Force data
            if 'sensorValue' in data or 'f' in data:
                raw_force = data.get('sensorValue', data.get('f', 0))
                
                FORCE_THRESHOLD = 500
                FORCE_MAX = 4095
                
                if raw_force <= FORCE_THRESHOLD:
                    self.force_data = 0.0
                else:
                    force_range = FORCE_MAX - FORCE_THRESHOLD
                    self.force_data = ((raw_force - FORCE_THRESHOLD) / force_range) * 100.0
                    self.force_data = min(100.0, self.force_data)
                
            # EMG data
            if 'emgValue' in data or 'e' in data:
                raw_emg = data.get('emgValue', data.get('e', 0))
                
                EMG_THRESHOLD = 100
                EMG_MAX = 4095
                
                if raw_emg <= EMG_THRESHOLD:
                    self.emg_data = 0.0
                else:
                    emg_range = EMG_MAX - EMG_THRESHOLD
                    self.emg_data = ((raw_emg - EMG_THRESHOLD) / emg_range) * 100.0
                    self.emg_data = min(100.0, self.emg_data)
                
            # Notify callbacks
            for callback in self.callbacks:
                callback(self.imu_data, self.force_data, self.emg_data)
                
        except json.JSONDecodeError:
            # Ignore debug prints from firmware that aren't JSON
            pass
            
    def get_imu_data(self):
        return self.imu_data
        
    def get_force_data(self):
        return self.force_data
        
    def get_emg_data(self):
        return self.emg_data
