"""
Enhanced Main Window with TEST MODE
Offline testing without ESP32 hardware
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGroupBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from sensors.simulator import SimulatedSensorData


class MainWindow(QMainWindow):
    def __init__(self, arm_model, esp32_client):
        super().__init__()
        self.arm_model = arm_model
        self.esp32_client = esp32_client
        self.simulator = None
        
        self.setWindowTitle("🦾 3D Arm Rehabilitation System")
        self.setGeometry(100, 100, 1600, 1000)
        
        self._setup_ui()
        
        # Render timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._render)
        self.timer.start(16)  # 60 FPS
        
    def _setup_ui(self):
        """Create UI"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(350)
        left_panel.setStyleSheet("background: #2a2a2a; color: white;")
        
        # Title
        title = QLabel("ARM REHABILITATION SYSTEM")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00ffff; padding: 15px;")
        left_layout.addWidget(title)
        
        # Connection group
        conn_group = QGroupBox("Vega Aries v2 Connection")
        conn_layout = QVBoxLayout()
        
        self.ip_input = QLineEdit("COM3")
        self.ip_input.setPlaceholderText("e.g. COM3 or /dev/ttyUSB0")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background: #1e1e1e;
                color: white;
                border: 2px solid #555;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        conn_layout.addWidget(QLabel("COM Port:"))
        conn_layout.addWidget(self.ip_input)
        
        # Connect button
        self.connect_btn = QPushButton("📡 Connect to Vega Aries")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #27ae60;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_esp32)
        conn_layout.addWidget(self.connect_btn)
        
        # TEST MODE button
        self.test_btn = QPushButton("🧪 TEST MODE (No Hardware)")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """)
        self.test_btn.clicked.connect(self.start_test_mode)
        conn_layout.addWidget(self.test_btn)
        
        # Disconnect button
        self.disconnect_btn = QPushButton("❌ Disconnect")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #555;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect)
        conn_layout.addWidget(self.disconnect_btn)
        
        # Status label
        self.status_label = QLabel("⚪ Ready")
        self.status_label.setStyleSheet("color: #bdc3c7; font-weight: bold; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        conn_layout.addWidget(self.status_label)
        
        conn_group.setLayout(conn_layout)
        left_layout.addWidget(conn_group)
        
        # Sensor data group
        sensor_group = QGroupBox("📊 Live Sensor Data")
        sensor_layout = QVBoxLayout()
        
        self.imu_label = QLabel("IMU: --")
        self.force_label = QLabel("Force: --")  
        self.emg_label = QLabel("EMG: --")
        
        for label in [self.imu_label, self.force_label, self.emg_label]:
            label.setStyleSheet("color: #3498db; font-family: monospace; padding: 5px;")
            sensor_layout.addWidget(label)
            
        sensor_group.setLayout(sensor_layout)
        left_layout.addWidget(sensor_group)
        
        # Servo calibration group
        calib_group = QGroupBox("🎯 Servo Calibration")
        calib_layout = QVBoxLayout()
        
        self.offset_input = QLineEdit("0.0")
        self.offset_input.setPlaceholderText("Offset Angle (e.g., 10.5)")
        self.offset_input.setStyleSheet("""
            QLineEdit {
                background: #1e1e1e;
                color: white;
                border: 2px solid #555;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        calib_layout.addWidget(QLabel("Offset Angle:"))
        calib_layout.addWidget(self.offset_input)
        
        self.cal_servo_btn = QPushButton("🔧 Calibrate to 180°")
        self.cal_servo_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e67e22;
            }
        """)
        self.cal_servo_btn.clicked.connect(self.calibrate_servo)
        calib_layout.addWidget(self.cal_servo_btn)
        
        calib_group.setLayout(calib_layout)
        left_layout.addWidget(calib_group)
        
        left_layout.addStretch()
        
        main_layout.addWidget(left_panel)
        
        # Right panel - 3D View
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setStyleSheet("background: #1a1a1a;")
        
        # VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(right_panel)
        right_layout.addWidget(self.vtk_widget)
        
        # Add renderer
        render_window = self.vtk_widget.GetRenderWindow()
        render_window.AddRenderer(self.arm_model.get_renderer())
        
        # Initialize VTK
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
        
        main_layout.addWidget(right_panel, 3)
        
    def connect_esp32(self):
        """Connect to real Vega Aries"""
        port = self.ip_input.text().strip()
        if not port:
            self.status_label.setText("❌ Enter COM Port")
            return
            
        self.status_label.setText("🔄 Connecting...")
        print(f"[VegaAries] Connecting to {port}...")
        
        # Set callback FIRST
        self.esp32_client.add_callback(self.handle_sensor_data)
        
        # Connect
        self.esp32_client.connect(port)
        
        # Give it a moment to connect
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self._check_connection_status)
        
    def _check_connection_status(self):
        """Check if ESP32 connected successfully"""
        if self.esp32_client.connected:
            self.status_label.setText("✅ Vega Aries Connected")
            self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold; padding: 10px;")
            self.connect_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            print("[VegaAries] ✅ Connection confirmed - data flowing!")
        else:
            self.status_label.setText("❌ Connection Failed")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px;")

            
    def start_test_mode(self):
        """Start simulated data (no ESP32 needed)"""
        print("[TEST MODE] Starting simulator...")
        
        self.simulator = SimulatedSensorData(self.handle_sensor_data)
        self.simulator.start()
        
        self.status_label.setText("✅ TEST MODE ACTIVE")
        self.status_label.setStyleSheet("color: #9b59b6; font-weight: bold; padding: 10px;")
        self.connect_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        
        print("[TEST MODE] Watch the arm move automatically!")
        
    def disconnect(self):
        """Disconnect from ESP32 or stop simulator"""
        # Stop simulator if running
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
            
        # Disconnect ESP32
        self.esp32_client.disconnect()
        
        self.status_label.setText("⚪ Disconnected")
        self.status_label.setStyleSheet("color: #bdc3c7; font-weight: bold; padding: 10px;")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        
    def calibrate_servo(self):
        """Send the servo calibration command over serial"""
        if not hasattr(self.esp32_client, 'send_command') or not self.esp32_client.connected:
            self.status_label.setText("❌ Connect to Vega Aries first")
            return
            
        try:
            offset_val = float(self.offset_input.text().strip() or "0.0")
            self.esp32_client.send_command(f"calibrate_servo:{offset_val}")
            self.status_label.setText(f"🎯 Servo Calibrated (Offset {offset_val})")
            print(f"[UI] Calibrated Servo with offset {offset_val}")
        except ValueError:
            self.status_label.setText("❌ Invalid Angle. Enter a number.")
            
    def handle_sensor_data(self, imu_data, force, emg):
        """Handle sensor data from ESP32 (3 arguments) or simulator (1 dict)"""
        try:
            # If called from simulator with dict, extract values
            if isinstance(imu_data, dict) and 'roll' in imu_data and 'force' in imu_data:
                # Simulator format - single dict
                roll = imu_data.get('roll', 0)
                pitch = imu_data.get('pitch', 0)
                yaw = imu_data.get('yaw', 0)
                force = imu_data.get('force', 0)
                emg = imu_data.get('emg', 0)
            else:
                # ESP32 format - three separate arguments
                roll = imu_data.get('roll', 0)
                pitch = imu_data.get('pitch', 0)
                yaw = imu_data.get('yaw', 0)
                # force and emg already passed as separate args
            
            # Update UI labels
            self.imu_label.setText(f"IMU: R={roll:.1f}° P={pitch:.1f}° Y={yaw:.1f}°")
            self.force_label.setText(f"Force: {force:.1f} N")
            self.emg_label.setText(f"EMG: {emg:.1f} μV")
            
            # Update 3D model
            self.arm_model.update_from_imu(roll, pitch, yaw)
            self.arm_model.update_from_force(force)
            self.arm_model.update_from_emg(emg)
            
        except Exception as e:
            print(f"[ERROR] Data handling: {e}")
            
    def _render(self):
        """Render 3D view at 60 FPS"""
        self.vtk_widget.GetRenderWindow().Render()
