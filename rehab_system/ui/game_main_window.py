"""
Game Main Window for Flight Simulator
Enhanced UI with game controls and HUD
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGroupBox,
                             QProgressBar, QFrame, QStackedWidget)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from sensors.simulator import SimulatedSensorData
from games.flight_simulator import FlightSimulator


class HUDWidget(QWidget):
    """Heads-Up Display overlay for game stats"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Top HUD bar
        top_bar = QHBoxLayout()
        
        # Score display
        self.score_label = QLabel("SCORE: 0")
        self.score_label.setFont(QFont("Consolas", 24, QFont.Bold))
        self.score_label.setStyleSheet("""
            color: #00ffff;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px 20px;
            border-radius: 10px;
        """)
        top_bar.addWidget(self.score_label)
        
        top_bar.addStretch()
        
        # Level display
        self.level_label = QLabel("LEVEL 1")
        self.level_label.setFont(QFont("Consolas", 18, QFont.Bold))
        self.level_label.setStyleSheet("""
            color: #ffff00;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px 20px;
            border-radius: 10px;
        """)
        top_bar.addWidget(self.level_label)
        
        layout.addLayout(top_bar)
        layout.addStretch()
        
        # Bottom HUD bar
        bottom_bar = QHBoxLayout()
        
        # Health bar
        health_container = QVBoxLayout()
        health_label = QLabel("HEALTH")
        health_label.setStyleSheet("color: white; font-weight: bold;")
        health_container.addWidget(health_label)
        
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(100)
        self.health_bar.setTextVisible(False)
        self.health_bar.setFixedHeight(20)
        self.health_bar.setFixedWidth(200)
        self.health_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(0, 0, 0, 0.5);
                border: 2px solid #333;
                border-radius: 10px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:0.5 #ffff00, stop:1 #00ff00);
                border-radius: 8px;
            }
        """)
        health_container.addWidget(self.health_bar)
        bottom_bar.addLayout(health_container)
        
        bottom_bar.addStretch()
        
        # Distance display
        self.distance_label = QLabel("0 m")
        self.distance_label.setFont(QFont("Consolas", 16))
        self.distance_label.setStyleSheet("""
            color: #aaffaa;
            background: rgba(0, 0, 0, 0.5);
            padding: 8px 15px;
            border-radius: 8px;
        """)
        bottom_bar.addWidget(self.distance_label)
        
        bottom_bar.addStretch()
        
        # Boost bar
        boost_container = QVBoxLayout()
        boost_label = QLabel("BOOST")
        boost_label.setStyleSheet("color: white; font-weight: bold;")
        boost_container.addWidget(boost_label)
        
        self.boost_bar = QProgressBar()
        self.boost_bar.setRange(0, 100)
        self.boost_bar.setValue(100)
        self.boost_bar.setTextVisible(False)
        self.boost_bar.setFixedHeight(20)
        self.boost_bar.setFixedWidth(200)
        self.boost_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(0, 0, 0, 0.5);
                border: 2px solid #333;
                border-radius: 10px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0066ff, stop:1 #00ffff);
                border-radius: 8px;
            }
        """)
        boost_container.addWidget(self.boost_bar)
        bottom_bar.addLayout(boost_container)
        
        layout.addLayout(bottom_bar)
        
    def update_score(self, score):
        self.score_label.setText(f"SCORE: {score:,}")
        
    def update_level(self, level):
        self.level_label.setText(f"LEVEL {level}")
        
    def update_health(self, health):
        self.health_bar.setValue(int(health))
        
    def update_distance(self, distance):
        self.distance_label.setText(f"{int(distance):,} m")
        
    def update_boost(self, boost):
        self.boost_bar.setValue(int(boost))


class GameMainWindow(QMainWindow):
    """Main window for Flight Simulator game"""
    
    def __init__(self, arm_model, esp32_client):
        super().__init__()
        self.arm_model = arm_model
        self.esp32_client = esp32_client
        self.simulator = None
        self.flight_game = None
        
        self.setWindowTitle("🛩️ ARM REHABILITATION - FLIGHT SIMULATOR")
        self.setGeometry(50, 50, 1800, 1000)
        
        self._setup_ui()
        self._setup_game()
        
        # Render timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._game_loop)
        self.timer.start(16)
        
    def _setup_ui(self):
        """Create the game UI"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(320)
        left_panel.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
            }
        """)
        
        # Game Title
        title = QLabel("✈️ FLIGHT SIMULATOR")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #00ffff;
            padding: 20px;
            background: rgba(0, 255, 255, 0.1);
            border-bottom: 2px solid #00ffff;
        """)
        left_layout.addWidget(title)
        
        # Connection group
        conn_group = QGroupBox("🔌 Vega Aries v2 Connection")
        conn_layout = QVBoxLayout()
        
        self.ip_input = QLineEdit("COM3")
        self.ip_input.setPlaceholderText("e.g. COM3 or /dev/ttyUSB0")
        conn_layout.addWidget(QLabel("COM Port:"))
        conn_layout.addWidget(self.ip_input)
        
        # Connect button
        self.connect_btn = QPushButton("📡 Connect Vega Aries")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #27ae60; }
        """)
        self.connect_btn.clicked.connect(self.connect_esp32)
        conn_layout.addWidget(self.connect_btn)
        
        # Test mode button
        self.test_btn = QPushButton("🧪 TEST MODE")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #8e44ad; }
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
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
            QPushButton:disabled { background: #555; }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect)
        conn_layout.addWidget(self.disconnect_btn)
        
        # Status
        self.status_label = QLabel("⚪ Ready to Connect")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #bdc3c7; padding: 10px;")
        conn_layout.addWidget(self.status_label)
        
        conn_group.setLayout(conn_layout)
        left_layout.addWidget(conn_group)
        
        # Game Controls
        game_group = QGroupBox("🎮 Game Controls")
        game_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("▶️ START GAME")
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background: #2980b9; }
            QPushButton:disabled { background: #555; color: #888; }
        """)
        self.start_btn.clicked.connect(self.start_game)
        game_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸️ PAUSE")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background: #e67e22; }
            QPushButton:disabled { background: #555; }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        game_layout.addWidget(self.pause_btn)
        
        self.reset_btn = QPushButton("🔄 RESET")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7f8c8d; }
        """)
        self.reset_btn.clicked.connect(self.reset_game)
        game_layout.addWidget(self.reset_btn)
        
        game_group.setLayout(game_layout)
        left_layout.addWidget(game_group)
        
        # Sensor Data Display
        sensor_group = QGroupBox("📊 Sensor Data")
        sensor_layout = QVBoxLayout()
        
        self.imu_label = QLabel("IMU: R=0° P=0° Y=0°")
        self.force_label = QLabel("Throttle: 0%")
        self.emg_label = QLabel("EMG/Boost: 0%")
        
        for label in [self.imu_label, self.force_label, self.emg_label]:
            label.setStyleSheet("""
                color: #3498db;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 5px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 4px;
            """)
            sensor_layout.addWidget(label)
            
        sensor_group.setLayout(sensor_layout)
        left_layout.addWidget(sensor_group)
        
        # Instructions
        instructions = QLabel("""
📋 CONTROLS:
━━━━━━━━━━━━━━━━━━
🔄 Roll arm → Bank left/right
📐 Tilt arm → Climb/dive
💪 Squeeze → Throttle
⚡ Flex hard → BOOST!

🎯 OBJECTIVE:
━━━━━━━━━━━━━━━━━━
✨ Fly through rings
🚫 Avoid red obstacles
🏆 Score points!
        """)
        instructions.setStyleSheet("""
            color: #aaaaaa;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        """)
        left_layout.addWidget(instructions)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Right panel - Game View
        game_container = QWidget()
        game_layout = QVBoxLayout(game_container)
        game_layout.setContentsMargins(0, 0, 0, 0)
        
        # VTK widget for 3D game
        self.vtk_widget = QVTKRenderWindowInteractor(game_container)
        game_layout.addWidget(self.vtk_widget)
        
        main_layout.addWidget(game_container, 1)
        
        # Create HUD overlay
        self.hud = HUDWidget(self.vtk_widget)
        self.hud.setGeometry(0, 0, self.vtk_widget.width(), self.vtk_widget.height())
        
    def _setup_game(self):
        """Initialize flight simulator game"""
        self.flight_game = FlightSimulator()
        
        # Set callbacks
        self.flight_game.on_score_update = self._on_score_update
        self.flight_game.on_game_over = self._on_game_over
        self.flight_game.on_ring_collected = self._on_ring_collected
        self.flight_game.on_collision = self._on_collision
        
        # Add game renderer to VTK widget
        render_window = self.vtk_widget.GetRenderWindow()
        render_window.AddRenderer(self.flight_game.get_renderer())
        
        # Initialize VTK
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
        
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        if hasattr(self, 'hud'):
            self.hud.setGeometry(0, 0, self.vtk_widget.width(), self.vtk_widget.height())
            
    def connect_esp32(self):
        """Connect to ESP32"""
        port = self.ip_input.text().strip()
        if not port:
            self.status_label.setText("❌ Enter COM Port")
            return
            
        self.status_label.setText("🔄 Connecting...")
        self.esp32_client.set_data_callback(self.handle_sensor_data)
        self.esp32_client.connect(port)
        
        QTimer.singleShot(1500, self._check_connection)
        
    def _check_connection(self):
        """Check if connection was successful"""
        if self.esp32_client.connected:
            self.status_label.setText("✅ Vega Aries Connected")
            self.status_label.setStyleSheet("color: #2ecc71; padding: 10px;")
            self._enable_game_controls(True)
        else:
            error = self.esp32_client.last_error or "Connection failed"
            self.status_label.setText(f"❌ {error[:30]}")
            self.status_label.setStyleSheet("color: #e74c3c; padding: 10px;")
            
    def start_test_mode(self):
        """Start with simulated data"""
        self.simulator = SimulatedSensorData(self.handle_sensor_data)
        self.simulator.start()
        
        self.status_label.setText("✅ TEST MODE Active")
        self.status_label.setStyleSheet("color: #9b59b6; padding: 10px;")
        self._enable_game_controls(True)
        
    def _enable_game_controls(self, enabled):
        """Enable/disable game controls"""
        self.start_btn.setEnabled(enabled)
        self.connect_btn.setEnabled(not enabled)
        self.test_btn.setEnabled(not enabled)
        self.disconnect_btn.setEnabled(enabled)
        
    def disconnect(self):
        """Disconnect from ESP32/simulator"""
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
            
        self.esp32_client.disconnect()
        
        if self.flight_game and self.flight_game.is_running:
            self.flight_game.stop()
            
        self.status_label.setText("⚪ Disconnected")
        self.status_label.setStyleSheet("color: #bdc3c7; padding: 10px;")
        self._enable_game_controls(False)
        self.pause_btn.setEnabled(False)
        
    def start_game(self):
        """Start the flight simulator"""
        if self.flight_game:
            self.flight_game.start()
            self.start_btn.setText("🛫 FLYING...")
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            print("[Game] 🛫 Flight Started!")
            
    def toggle_pause(self):
        """Pause/resume game"""
        if not self.flight_game:
            return
            
        if self.flight_game.is_paused:
            self.flight_game.resume()
            self.pause_btn.setText("⏸️ PAUSE")
        else:
            self.flight_game.pause()
            self.pause_btn.setText("▶️ RESUME")
            
    def reset_game(self):
        """Reset the game"""
        if self.flight_game:
            self.flight_game.reset()
            self.start_btn.setText("▶️ START GAME")
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.pause_btn.setText("⏸️ PAUSE")
            self.hud.update_score(0)
            self.hud.update_level(1)
            self.hud.update_health(100)
            self.hud.update_distance(0)
            self.hud.update_boost(100)
            
    def handle_sensor_data(self, imu_data, force=None, emg=None):
        """Handle incoming sensor data"""
        try:
            # Handle both ESP32 format (3 args) and simulator format (1 dict)
            if isinstance(imu_data, dict) and 'force' in imu_data:
                roll = imu_data.get('roll', 0)
                pitch = imu_data.get('pitch', 0)
                yaw = imu_data.get('yaw', 0)
                force = imu_data.get('force', 0)
                emg = imu_data.get('emg', 0)
            else:
                roll = imu_data.get('roll', 0)
                pitch = imu_data.get('pitch', 0)
                yaw = imu_data.get('yaw', 0)
                force = force if force is not None else 0
                emg = emg if emg is not None else 0
                
            # Update sensor labels
            self.imu_label.setText(f"IMU: R={roll:.1f}° P={pitch:.1f}° Y={yaw:.1f}°")
            self.force_label.setText(f"Throttle: {force:.0f}%")
            self.emg_label.setText(f"EMG/Boost: {emg:.0f}%")
            
            # Update game if running
            if self.flight_game and self.flight_game.is_running:
                self.flight_game.update(
                    {'roll': roll, 'pitch': pitch, 'yaw': yaw},
                    force,
                    emg
                )
                
                # Update HUD
                state = self.flight_game.get_game_state()
                self.hud.update_health(state['health'])
                self.hud.update_boost(state['boost_fuel'])
                
        except Exception as e:
            print(f"[Error] Sensor data: {e}")
            
    def _on_score_update(self, score, distance, level):
        """Handle score updates from game"""
        self.hud.update_score(score)
        self.hud.update_distance(distance)
        self.hud.update_level(level)
        
    def _on_ring_collected(self):
        """Handle ring collection"""
        # Flash effect could be added here
        pass
        
    def _on_collision(self, health):
        """Handle collision"""
        self.hud.update_health(health)
        
    def _on_game_over(self, final_score):
        """Handle game over"""
        print(f"[Game] 💥 GAME OVER! Score: {final_score}")
        self.start_btn.setText("▶️ PLAY AGAIN")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        
    def _game_loop(self):
        """Main game loop - renders at 60 FPS"""
        self.vtk_widget.GetRenderWindow().Render()
        
    def closeEvent(self, event):
        """Clean up on close"""
        if self.simulator:
            self.simulator.stop()
        if self.flight_game:
            self.flight_game.stop()
        self.timer.stop()
        event.accept()
