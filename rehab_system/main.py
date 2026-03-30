"""
3D Hand Rehabilitation System
Main Application Entry Point
"""
import sys
from PyQt5.QtWidgets import QApplication
from models.realistic_arm import EnhancedRealisticArm
from sensors.esp32_client import ESP32Client
from ui.main_window import MainWindow


def main():
    """Launch application"""
    print("="*50)
    print("ENHANCED Arm Rehabilitation System")
    print("Perfect Smooth Animations + Sensor Integration")
    print("="*50)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Initialize components
    print("[Init] Creating ENHANCED realistic arm...")
    print("[Init] ✓ Smooth animations (interpolated)")
    print("[Init] ✓ IMU → Arm rotation")
    print("[Init] ✓ Force → Elbow bending (0-140°)")
    print("[Init] ✓ EMG → Muscle activation glow")
    arm_model = EnhancedRealisticArm()
    
    print("[Init] Setting up ESP32 client...")
    esp32_client = ESP32Client()
    
    print("[Init] Creating UI...")
    window = MainWindow(arm_model, esp32_client)
    window.show()
    
    print("[Ready] Application started!")
    print("Connect your ESP32 to begin...")
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
