"""
ESP32 Serial Client for Sensor Data
Handles IMU, Force, and EMG sensor data streaming via high-speed USB Serial
"""
import json
import threading
import time
import serial

class SerialClient:
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
        
    def connect(self, port, baudrate=115200):
        """Connect to ESP32 over Serial Port"""
        self.last_error = None
        print(f"[ESP32-Serial] Connecting to {port} at {baudrate} baud...")
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            self._stop_event.clear()
            print(f"[ESP32-Serial] Connected successfully to {port}!")
            
            # Start background reading thread
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            self.last_error = str(e)
            print(f"[ESP32-Serial] Connection Error: {e}")
            self.connected = False
            
    def disconnect(self):
        """Close Serial connection"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            
        if self.ser and self.ser.is_open:
            self.ser.close()
            
        self.connected = False
        print("[ESP32-Serial] Disconnected")
            
    def add_callback(self, callback):
        """Register callback for new data"""
        self.callbacks.append(callback)

    def set_data_callback(self, callback):
        """Set a SINGLE high-speed callback (Optimized for Game)"""
        self.callbacks = [callback]
        
    def calibrate(self):
        """Send calibration command to ESP32"""
        if self.connected and self.ser and self.ser.is_open:
            self.ser.write(b"calibrate\n")
            print("[ESP32-Serial] Sent calibration command")

    def send_command(self, cmd_str):
        """Send any command string to the board (e.g. premove, calibrate_servo)"""
        if self.connected and self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd_str + "\n").encode('utf-8'))
            except Exception as e:
                print(f"[ESP32-Serial] send_command error: {e}")
            
    def _read_loop(self):
        """Background thread loop to read lines from serial"""
        while not self._stop_event.is_set():
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._process_line(line)
                else:
                    time.sleep(0.001)  # tiny sleep to prevent 100% CPU usage
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"[ESP32-Serial] Read Error: {e}")
                    self.last_error = str(e)
                    self.connected = False
                    self._stop_event.set()
                break
                
    def _process_line(self, line):
        """Process incoming JSON line"""
        if not line.startswith('{'):
            # Probably a debug message like "SYSTEM READY"
            return
            
        try:
            data = json.loads(line)
            
            # ── NEW firmware format (descriptive keys) ──
            if 'roll' in data:
                self.imu_data['roll'] = float(data['roll'])
                self.imu_data['pitch'] = float(data['pitch'])
                self.imu_data['yaw'] = float(data['yaw'])
                
                # Force from flex sensor (bendForce: 0-1023)
                raw_force = data.get('bendForce', data.get('sensorValue', 0))
                self.force_data = min(100.0, max(0.0, (raw_force / 1023.0) * 100.0))
                
                # EMG (emgValue or emgRms)
                raw_emg = data.get('emgRms', data.get('emgValue', 0))
                self.emg_data = min(100.0, max(0.0, float(raw_emg)))
                
                # Extra data for advanced use
                self.imu_data['elbowAngle'] = float(data.get('elbowAngle', 90))
                self.imu_data['accel'] = float(data.get('accel', 0))
                self.imu_data['imuConnected'] = data.get('imuConnected', False)
                self.imu_data['bendForce'] = int(raw_force)
            
            # ── OLD firmware format (compact keys) ──
            elif 'r' in data:
                self.imu_data['roll'] = data['r']
                self.imu_data['pitch'] = data.get('p', 0)
                self.imu_data['yaw'] = data.get('y', 0)
                    
                if 'f' in data:
                    raw_force = data['f']
                    FORCE_THRESHOLD = 50 
                    FORCE_MAX = 4095
                    if raw_force <= FORCE_THRESHOLD:
                        self.force_data = 0.0
                    else:
                        self.force_data = ((raw_force - FORCE_THRESHOLD) / (FORCE_MAX - FORCE_THRESHOLD)) * 100.0
                        self.force_data = min(100.0, max(0.0, self.force_data))
                    
                if 'e' in data:
                    raw_emg = data['e']
                    EMG_THRESHOLD = 50
                    EMG_MAX = 4095
                    if raw_emg <= EMG_THRESHOLD:
                        self.emg_data = 0.0
                    else:
                        self.emg_data = ((raw_emg - EMG_THRESHOLD) / (EMG_MAX - EMG_THRESHOLD)) * 100.0
                        self.emg_data = min(100.0, max(0.0, self.emg_data))
                
            # Notify callbacks
            for callback in self.callbacks:
                callback(self.imu_data, self.force_data, self.emg_data)
                
        except json.JSONDecodeError:
            pass # ignore incomplete lines
            
    def get_imu_data(self):
        return self.imu_data
        
    def get_force_data(self):
        return self.force_data
        
    def get_emg_data(self):
        return self.emg_data
