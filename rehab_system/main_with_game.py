"""
ARM REHABILITATION SYSTEM - PREMIUM EDITION
Stable PyQt5 + VTK arm viewer, launching Ursina 3D game as a subprocess.
Sensor data is correctly forwarded to both UI and game.
"""
import sys
import os
import subprocess
import webbrowser
import socket
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QGroupBox, QProgressBar, QComboBox,
    QDialog, QDialogButtonBox
)
from PyQt5.QtCore  import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui   import QFont, QColor

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from models.realistic_arm   import EnhancedRealisticArm
from sensors.serial_client  import SerialClient
from sensors.simulator      import SimulatedSensorData


# ── Thread-safe Qt signal bridge ──────────────────────────────────────────
class SensorBridge(QObject):
    data = pyqtSignal(float, float, float, float, float, float)  # roll pitch yaw force emg elbowAngle


class RehabMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🦾 ARM REHABILITATION SYSTEM — PREMIUM EDITION")
        self.setGeometry(80, 80, 1500, 900)

        # Models / sensors
        self.arm_model   = EnhancedRealisticArm()
        self.esp32       = SerialClient()
        self.simulator   = None
        self.game_proc   = None     # Ursina subprocess
        self.servo_offset = 0.0     # Calibration offset between two sticks

        # Thread-safe bridge
        self.bridge = SensorBridge()
        self.bridge.data.connect(self._update_ui)

        # Latest values (main-thread cache)
        self.roll = self.pitch = self.yaw = self.force = self.emg = self.elbow_angle = 0.0

        # UDP Socket for broadcasting telemetry to the Web Bridge
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_addr = ("127.0.0.1", 9000)

        self._build_ui()
        self._init_vtk()

        # 60 FPS render timer
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._render)
        self.render_timer.start(16)
        
        # ── Return telemetry (UDP -> hardware)
        self.incoming_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.incoming_udp.setblocking(False)
        self.incoming_udp.bind(('127.0.0.1', 9001))
        
        self.udp_timer = QTimer()
        self.udp_timer.timeout.connect(self._poll_incoming_udp)
        self.udp_timer.start(20) # 50Hz polling for hardware commands

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── LEFT PANEL ────────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(300)
        left.setStyleSheet("""
            QWidget { background: #0d0d1a; color: #cdd; }
            QGroupBox {
                font-weight: bold; font-size: 12px;
                border: 1px solid #2a4060;
                border-radius: 8px; margin-top: 10px; padding-top: 6px;
                background: #121225;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #00e5ff; }
            QLabel  { font-size: 12px; color: #99b; }
            QLineEdit {
                background: #1a1a30; border: 1px solid #334; border-radius: 4px;
                padding: 6px; color: white; font-size: 13px;
            }
        """)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(10, 10, 10, 10)
        lv.setSpacing(8)

        # Title
        title = QLabel("🦾  ARM REHAB")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#00e5ff; padding:12px; background:rgba(0,229,255,.07); border-radius:8px;")
        lv.addWidget(title)

        # ── Connection ─────────────────────────────────────────────────────
        cg = QGroupBox("🔌  SERIAL CONNECTION")
        cv = QVBoxLayout(cg)

        self.port_box = QLineEdit("COM17")
        self.port_box.setPlaceholderText("e.g. COM3 or /dev/ttyUSB0")
        cv.addWidget(QLabel("COM Port:"))
        cv.addWidget(self.port_box)

        self.connect_btn = QPushButton("📡  Connect VEGA Aries V2")
        self.connect_btn.setStyleSheet(self._btn("#1a8a3a"))
        self.connect_btn.clicked.connect(self._connect)
        cv.addWidget(self.connect_btn)

        self.test_btn = QPushButton("🧪  Test Mode (No Aries)")
        self.test_btn.setStyleSheet(self._btn("#6a3ab0"))
        self.test_btn.clicked.connect(self._test_mode)
        cv.addWidget(self.test_btn)

        self.disc_btn = QPushButton("❌  Disconnect")
        self.disc_btn.setEnabled(False)
        self.disc_btn.setStyleSheet(self._btn("#8a1a1a"))
        self.disc_btn.clicked.connect(self._disconnect)
        cv.addWidget(self.disc_btn)

        self.status_lbl = QLabel("⚪  Not Connected")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color:#666; padding:6px;")
        cv.addWidget(self.status_lbl)
        lv.addWidget(cg)

        # ── Game ────────────────────────────────────────────────────────────
        gg = QGroupBox("🎮  3D FLIGHT GAME")
        gv = QVBoxLayout(gg)

        self.launch_btn = QPushButton("🚀  LAUNCH 3D GAME")
        self.launch_btn.setEnabled(False)
        self.launch_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.launch_btn.setStyleSheet(self._btn("#0050c0"))
        self.launch_btn.clicked.connect(self._launch_game)
        gv.addWidget(self.launch_btn)

        hint = QLabel("Game opens in dedicated high-performance\n3D window. Close it to stop.")
        hint.setStyleSheet("color:#556; font-size:11px;")
        hint.setAlignment(Qt.AlignCenter)
        gv.addWidget(hint)
        lv.addWidget(gg)

        # ── Live Sensor Panel ───────────────────────────────────────────────
        sg = QGroupBox("📊  LIVE SENSOR DATA")
        sv = QVBoxLayout(sg)

        def _bar(label, color_chunk):
            sv.addWidget(QLabel(label))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFixedHeight(16)
            bar.setStyleSheet(f"""
                QProgressBar {{ background:#1a1a2e; border-radius:4px; color:white; font-size:10px; }}
                QProgressBar::chunk {{ background:{color_chunk}; border-radius:4px; }}
            """)
            sv.addWidget(bar)
            return bar

        self.roll_bar  = _bar("Roll  (Bank)",  "#00bfff")
        self.pitch_bar = _bar("Pitch (Climb)", "#00ff80")
        self.force_bar = _bar("Force (Speed)", "#ffaa00")
        self.emg_bar   = _bar("EMG   (Boost)", "#ff4488")

        self.imu_lbl   = QLabel("IMU:  R=0°  P=0°  Y=0°")
        self.imu_lbl.setStyleSheet("color:#7af; font-family:Consolas; font-size:11px;")
        sv.addWidget(self.imu_lbl)
        lv.addWidget(sg)

        lv.addStretch()
        root.addWidget(left)

        # ── RIGHT: VTK 3D Arm ──────────────────────────────────────────────
        rw = QWidget()
        rv = QVBoxLayout(rw)
        rv.setContentsMargins(0, 0, 0, 0)

        vtk_title = QLabel("🦾  3D ARM MODEL — LIVE TRACKING")
        vtk_title.setFont(QFont("Arial", 13, QFont.Bold))
        vtk_title.setAlignment(Qt.AlignCenter)
        vtk_title.setStyleSheet("color:#00e5ff; background:#090916; padding:8px;")
        rv.addWidget(vtk_title)

        self.vtk_widget = QVTKRenderWindowInteractor(rw)
        rv.addWidget(self.vtk_widget)
        root.addWidget(rw, 1)

    def _btn(self, bg):
        return (f"QPushButton {{ background:{bg}; color:white; border:none; padding:10px; "
                f"border-radius:6px; font-weight:bold; font-size:13px; }}"
                f"QPushButton:hover {{ background:{bg}dd; }}"
                f"QPushButton:disabled {{ background:#2a2a2a; color:#555; }}")

    # ── VTK init ───────────────────────────────────────────────────────────
    def _init_vtk(self):
        self.rw = self.vtk_widget.GetRenderWindow()
        self.rw.AddRenderer(self.arm_model.get_renderer())
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    # ── Connection ────────────────────────────────────────────────────────
    def _sensor_callback(self, imu, force=None, emg=None):
        """Called from background thread — emit Qt signal to cross thread safely."""
        r = imu.get('roll', 0) if isinstance(imu, dict) else 0
        p = imu.get('pitch', 0) if isinstance(imu, dict) else 0
        y = imu.get('yaw', 0) if isinstance(imu, dict) else 0
        ea = imu.get('elbowAngle', 90) if isinstance(imu, dict) else 90
        f = force if force is not None else 0
        e = emg if emg is not None else 0
        self.bridge.data.emit(float(r), float(p), float(y), float(f), float(e), float(ea))

    def _update_ui(self, roll, pitch, yaw, force, emg, elbow_angle):
        """Main-thread handler — update cache + UI bars immediately and broadcast data."""
        self.roll, self.pitch, self.yaw = roll, pitch, yaw
        self.force, self.emg, self.elbow_angle = force, emg, elbow_angle

        # Update UI bars
        self.roll_bar.setValue(int(((roll + 45) / 90.0) * 100))
        self.pitch_bar.setValue(int(((pitch + 35) / 70.0) * 100))
        self.force_bar.setValue(int(min(100, max(0, force))))
        self.emg_bar.setValue(int(min(100, max(0, emg))))
        self.imu_lbl.setText(f"IMU:  R={roll:+.1f}°  P={pitch:+.1f}°  Y={yaw:+.1f}°")
        
        # Broadcast to WebGL Bridge instantly
        try:
            payload = json.dumps({
                "r": roll, "p": pitch, "y": yaw,
                "f": force, "e": emg, "ea": elbow_angle,
                "c": True
            }).encode('utf-8')
            self.udp_sock.sendto(payload, self.udp_addr)
        except Exception:
            pass
            
    def _poll_incoming_udp(self):
        """Listen for bi-directional commands from the game via UDP 9001"""
        try:
            while True:
                data, _ = self.incoming_udp.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get("cmd") == "servo_angle" and "val" in msg:
                    # Game sends exact servo angle (45-180) — forward directly to board
                    angle = int(float(msg["val"]))
                    if hasattr(self.esp32, 'send_command'):
                        self.esp32.send_command(f"servo:{angle}")
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"[UDP_IN] Error: {e}")

    def _connect(self):
        port = self.port_box.text().strip()
        if not port:
            self.status_lbl.setText("❌  Enter COM port"); return
        self.status_lbl.setText("🔄  Connecting…")
        self.status_lbl.setStyleSheet("color:#fa0; padding:6px;")
        self.esp32.set_data_callback(self._sensor_callback)
        self.esp32.connect(port)
        QTimer.singleShot(1800, self._check_conn)

    def _check_conn(self):
        if self.esp32.connected:
            self.status_lbl.setText("✅ Aries V2 Connected (Serial)")
            self.status_lbl.setStyleSheet("color:#0f9; padding:6px;")
            self._enable(True)
        else:
            err = self.esp32.last_error or "Connection failed"
            self.status_lbl.setText(f"❌  {str(err)[:40]}")
            self.status_lbl.setStyleSheet("color:#f44; padding:6px;")

    def _test_mode(self):
        self.simulator = SimulatedSensorData(self._sensor_callback)
        self.simulator.start()
        self.status_lbl.setText("✅  TEST MODE Active")
        self.status_lbl.setStyleSheet("color:#b080ff; padding:6px;")
        self._enable(True)

    def _disconnect(self):
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
        self.esp32.disconnect()
        self.status_lbl.setText("⚪  Disconnected")
        self.status_lbl.setStyleSheet("color:#666; padding:6px;")
        self._enable(False)

    def _enable(self, on):
        self.launch_btn.setEnabled(on)
        self.connect_btn.setEnabled(not on)
        self.test_btn.setEnabled(not on)
        self.disc_btn.setEnabled(on)

    def _launch_game(self):
        port    = self.port_box.text().strip()
        script  = os.path.join(os.path.dirname(__file__), "games", "web_bridge.py")
        dl_script = os.path.join(os.path.dirname(__file__), "assets", "download_assets.py")

        self.launch_btn.setText("⚙️  DOWNLOADING AAA ASSETS (GLB)...")
        self.launch_btn.setStyleSheet("background:#a0f; color:#fff; font-size:24px; font-weight:bold; border-radius:10px;")
        self.launch_btn.repaint() # Force UI refresh
        
        # Download assets synchronously first
        subprocess.run([sys.executable, dl_script])
        
        self.launch_btn.setText("🌐  STARTING ASSET SERVER...")
        self.launch_btn.repaint()
        
        # Start Asset Server (8000)
        http_script = os.path.join(os.path.dirname(__file__), "games", "http_server.py")
        self.http_server = subprocess.Popen([sys.executable, http_script, "8000"], cwd=os.path.dirname(__file__))

        # Start Clinical DB Server (8081)
        db_script = os.path.join(os.path.dirname(__file__), "games", "clinical_db.py")
        self.db_server = subprocess.Popen([sys.executable, db_script, "8081"], cwd=os.path.dirname(__file__))

        # Choose args for bridge
        if self.simulator:
            cmd = [sys.executable, script, "--test"]
        else:
            cmd = [sys.executable, script, "--com", port]

        self.game_proc = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))
        
        # Open Clinical Portal
        QTimer.singleShot(500, lambda: webbrowser.open("http://localhost:8000/games/web_game/portal.html"))

        self.launch_btn.setText("🎮  WEBGL GAME RUNNING…")
        self.launch_btn.setEnabled(False)

        # Re-enable button when process ends
        QTimer.singleShot(2000, self._poll_game_proc)

    def _poll_game_proc(self):
        if self.game_proc and self.game_proc.poll() is not None:
            self.launch_btn.setText("🚀  LAUNCH 3D GAME")
            self.launch_btn.setEnabled(True)
            self.game_proc = None
            if hasattr(self, 'http_server') and self.http_server:
                self.http_server.terminate()
                self.http_server = None
            if hasattr(self, 'db_server') and self.db_server:
                self.db_server.terminate()
                self.db_server = None
        else:
            QTimer.singleShot(1000, self._poll_game_proc)

    # ── Render loop ────────────────────────────────────────────────────────
    def _render(self):
        try:
            self.arm_model.update_from_imu(self.roll, self.pitch, self.yaw)
            self.arm_model.update_from_force(self.force)
            self.arm_model.update_from_emg(self.emg)
            self.rw.Render()
        except Exception:
            pass

    def closeEvent(self, event):
        self.render_timer.stop()
        if self.simulator:
            self.simulator.stop()
        if self.esp32.connected:
            self.esp32.disconnect()
        event.accept()


# ── Startup Calibration Dialog ─────────────────────────────────────────────
class ServoCalibrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 Servo Arm Calibration")
        self.setFixedSize(480, 320)
        self.setStyleSheet("""
            QDialog { background: #0d0d1a; color: #cdd; }
            QLabel { font-size: 13px; color: #99b; }
            QLineEdit {
                background: #1a1a30; border: 2px solid #00e5ff; border-radius: 8px;
                padding: 12px; color: white; font-size: 18px; font-weight: bold;
            }
            QLineEdit:focus { border-color: #00ff77; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🦾 ARM SERVO CALIBRATION")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00e5ff; padding: 8px; background: rgba(0,229,255,0.08); border-radius: 10px;")
        layout.addWidget(title)

        desc = QLabel(
            "Align the two sticks to be perfectly straight (180°).\n"
            "Measure the current offset angle between them.\n"
            "Enter the offset below so the servo calibrates to 180°."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #7788aa; font-size: 12px; line-height: 1.5;")
        layout.addWidget(desc)

        layout.addWidget(QLabel("Offset Angle (degrees):  e.g. 10, -5, 0"))
        self.offset_input = QLineEdit("0")
        self.offset_input.setPlaceholderText("Enter angle offset between sticks")
        layout.addWidget(self.offset_input)

        btn = QPushButton("✅  Calibrate & Start")
        btn.setFont(QFont("Arial", 14, QFont.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00c853, stop:1 #00e5ff);
                color: white; border: none; padding: 14px; border-radius: 10px;
            }
            QPushButton:hover { background: #00e5ff; }
        """)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

        self.offset_value = 0.0

    def accept(self):
        try:
            self.offset_value = float(self.offset_input.text().strip())
        except ValueError:
            self.offset_value = 0.0
        super().accept()


# ── Entry point ────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Show calibration dialog FIRST
    calib = ServoCalibrationDialog()
    if calib.exec_() != QDialog.Accepted:
        sys.exit(0)

    win = RehabMainWindow()
    win.servo_offset = calib.offset_value
    win.show()

    # After connection, send calibration offset to the board
    def apply_calibration():
        if win.esp32.connected and hasattr(win.esp32, 'send_command'):
            win.esp32.send_command(f"calibrate_servo:{win.servo_offset}")
            print(f"[CALIBRATION] Sent offset {win.servo_offset}° → servo moves to 180°")
    # Subscribe to connection event via a timer check
    def check_and_calibrate():
        if win.esp32.connected:
            apply_calibration()
        else:
            QTimer.singleShot(500, check_and_calibrate)
    QTimer.singleShot(2500, check_and_calibrate)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
