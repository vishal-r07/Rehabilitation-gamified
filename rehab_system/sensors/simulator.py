"""
Simulated Sensor Data for Testing
Generates realistic sensor patterns without ESP32 hardware
"""
import threading
import time
import math
import random


class SimulatedSensorData:
    """
    Generate simulated sensor data for testing without hardware.
    Produces smooth, realistic motion patterns for IMU, Force, and EMG.
    """
    
    def __init__(self, callback):
        """
        Initialize simulator with data callback
        
        Args:
            callback: Function to call with sensor data.
                     Called with single dict: {'roll', 'pitch', 'yaw', 'force', 'emg'}
        """
        self.callback = callback
        self.running = False
        self.thread = None
        
        # Simulation state
        self.time = 0.0
        self.mode = 'wave'  # 'wave', 'random', 'figure8', 'circles'
        self.mode_time = 0.0
        self.mode_duration = 10.0  # Switch modes every 10 seconds
        
        # Smooth value tracking
        self.current_roll = 0.0
        self.current_pitch = 0.0
        self.current_yaw = 0.0
        self.current_force = 0.0
        self.current_emg = 0.0
        
        # Target values for smooth interpolation
        self.target_roll = 0.0
        self.target_pitch = 0.0
        self.target_force = 0.0
        self.target_emg = 0.0
        
    def start(self):
        """Start generating simulated data"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[Simulator] ▶️ Started - generating realistic sensor patterns")
        
    def stop(self):
        """Stop generating data"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[Simulator] ⏹️ Stopped")
        
    def set_mode(self, mode):
        """Set simulation mode: 'wave', 'random', 'figure8', 'circles'"""
        self.mode = mode
        self.mode_time = 0.0
        print(f"[Simulator] Mode changed to: {mode}")
        
    def _run(self):
        """Main simulation loop"""
        last_time = time.time()
        update_interval = 0.016  # ~60 FPS
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            
            if dt >= update_interval:
                self.time += dt
                self.mode_time += dt
                
                # Switch modes periodically
                if self.mode_time >= self.mode_duration:
                    self._switch_mode()
                    
                # Generate pattern based on mode
                self._generate_pattern(dt)
                
                # Smooth interpolation to targets
                self._smooth_values(dt)
                
                # Send data to callback
                data = {
                    'roll': self.current_roll,
                    'pitch': self.current_pitch,
                    'yaw': self.current_yaw,
                    'force': self.current_force,
                    'emg': self.current_emg
                }
                
                try:
                    self.callback(data, self.current_force, self.current_emg)
                except TypeError:
                    # Fallback for single-argument callbacks
                    self.callback(data)
                    
                last_time = current_time
            else:
                time.sleep(0.001)
                
    def _switch_mode(self):
        """Switch to a random mode"""
        modes = ['wave', 'random', 'figure8', 'circles', 'gentle']
        self.mode = random.choice(modes)
        self.mode_time = 0.0
        self.mode_duration = random.uniform(8, 15)
        print(f"[Simulator] Pattern: {self.mode}")
        
    def _generate_pattern(self, dt):
        """Generate target values based on current mode"""
        t = self.time
        
        if self.mode == 'wave':
            # Smooth sine wave motion
            self.target_roll = 30 * math.sin(t * 0.8)
            self.target_pitch = 20 * math.sin(t * 0.6 + 0.5)
            self.target_force = 50 + 40 * math.sin(t * 0.4)
            self.target_emg = 30 + 25 * math.sin(t * 0.3)
            
        elif self.mode == 'figure8':
            # Figure-8 pattern
            self.target_roll = 35 * math.sin(t * 0.7)
            self.target_pitch = 25 * math.sin(t * 1.4)
            self.target_force = 60 + 30 * abs(math.sin(t * 0.5))
            self.target_emg = 20 + 20 * (1 + math.sin(t * 0.8)) / 2
            
        elif self.mode == 'circles':
            # Circular motion
            self.target_roll = 25 * math.cos(t * 0.9)
            self.target_pitch = 25 * math.sin(t * 0.9)
            self.target_force = 55 + 35 * (1 + math.sin(t * 0.6)) / 2
            self.target_emg = 25 + 30 * (1 + math.cos(t * 0.4)) / 2
            
        elif self.mode == 'random':
            # Random target changes
            if random.random() < 0.02:
                self.target_roll = random.uniform(-40, 40)
                self.target_pitch = random.uniform(-30, 30)
            if random.random() < 0.03:
                self.target_force = random.uniform(20, 90)
            if random.random() < 0.02:
                self.target_emg = random.uniform(10, 70)
                
        elif self.mode == 'gentle':
            # Very gentle movements (good for calibration)
            self.target_roll = 15 * math.sin(t * 0.3)
            self.target_pitch = 10 * math.sin(t * 0.25 + 1)
            self.target_force = 30 + 15 * math.sin(t * 0.2)
            self.target_emg = 15 + 10 * math.sin(t * 0.15)
            
        # Add slight noise for realism
        self.target_roll += random.uniform(-1, 1)
        self.target_pitch += random.uniform(-0.5, 0.5)
        self.target_force += random.uniform(-2, 2)
        self.target_emg += random.uniform(-1, 1)
        
        # Clamp values
        self.target_roll = max(-45, min(45, self.target_roll))
        self.target_pitch = max(-35, min(35, self.target_pitch))
        self.target_force = max(0, min(100, self.target_force))
        self.target_emg = max(0, min(100, self.target_emg))
        
        # Yaw slowly drifts
        self.current_yaw += random.uniform(-0.1, 0.1)
        self.current_yaw = self.current_yaw % 360
        
    def _smooth_values(self, dt):
        """Smoothly interpolate current values towards targets"""
        smoothing = 5.0  # Higher = more responsive
        
        self.current_roll += (self.target_roll - self.current_roll) * smoothing * dt
        self.current_pitch += (self.target_pitch - self.current_pitch) * smoothing * dt
        self.current_force += (self.target_force - self.current_force) * smoothing * dt
        self.current_emg += (self.target_emg - self.current_emg) * smoothing * dt


class BurstSimulator(SimulatedSensorData):
    """
    Simulator that generates burst patterns for exercise simulation.
    Good for testing grip exercises with holds and releases.
    """
    
    def __init__(self, callback):
        super().__init__(callback)
        self.burst_state = 'rest'
        self.burst_timer = 0.0
        self.rep_count = 0
        
    def _generate_pattern(self, dt):
        """Generate burst/hold pattern"""
        self.burst_timer += dt
        
        if self.burst_state == 'rest':
            # Resting - low values
            self.target_force = 5 + random.uniform(-2, 2)
            self.target_emg = 5 + random.uniform(-2, 2)
            self.target_roll = random.uniform(-5, 5)
            self.target_pitch = random.uniform(-5, 5)
            
            if self.burst_timer > 2.0:  # Rest for 2 seconds
                self.burst_state = 'ramp_up'
                self.burst_timer = 0
                
        elif self.burst_state == 'ramp_up':
            # Ramping up grip
            progress = min(1.0, self.burst_timer / 0.5)  # 0.5 second ramp
            self.target_force = 5 + 85 * progress
            self.target_emg = 5 + 75 * progress
            
            if self.burst_timer > 0.5:
                self.burst_state = 'hold'
                self.burst_timer = 0
                
        elif self.burst_state == 'hold':
            # Holding grip
            self.target_force = 90 + random.uniform(-5, 5)
            self.target_emg = 80 + random.uniform(-5, 5)
            self.target_roll = random.uniform(-3, 3)
            
            if self.burst_timer > 3.0:  # Hold for 3 seconds
                self.burst_state = 'ramp_down'
                self.burst_timer = 0
                
        elif self.burst_state == 'ramp_down':
            # Releasing grip
            progress = min(1.0, self.burst_timer / 0.5)
            self.target_force = 90 - 85 * progress
            self.target_emg = 80 - 75 * progress
            
            if self.burst_timer > 0.5:
                self.burst_state = 'rest'
                self.burst_timer = 0
                self.rep_count += 1
                print(f"[Simulator] Rep #{self.rep_count} complete")
                
        # Smoothing
        self.current_yaw += random.uniform(-0.05, 0.05)


class FlightPatternSimulator(SimulatedSensorData):
    """
    Simulator optimized for flight game testing.
    Generates smooth banking and altitude changes.
    """
    
    def __init__(self, callback):
        super().__init__(callback)
        self.flight_phase = 'cruise'
        self.phase_timer = 0.0
        
    def _generate_pattern(self, dt):
        """Generate flight-like patterns"""
        t = self.time
        self.phase_timer += dt
        
        # Base throttle (always flying forward)
        self.target_force = 60 + 20 * math.sin(t * 0.2)
        
        # Banking patterns every few seconds
        phase_duration = 4.0
        phase_progress = (self.phase_timer % phase_duration) / phase_duration
        
        # Cycle through maneuvers
        maneuver = int(self.phase_timer / phase_duration) % 6
        
        if maneuver == 0:
            # Left bank
            self.target_roll = -30 * math.sin(phase_progress * math.pi)
            self.target_pitch = 5
        elif maneuver == 1:
            # Right bank
            self.target_roll = 30 * math.sin(phase_progress * math.pi)
            self.target_pitch = 5
        elif maneuver == 2:
            # Climb
            self.target_roll = 0
            self.target_pitch = 25 * math.sin(phase_progress * math.pi)
        elif maneuver == 3:
            # Dive
            self.target_roll = 0
            self.target_pitch = -20 * math.sin(phase_progress * math.pi)
        elif maneuver == 4:
            # S-curve left-right
            self.target_roll = 35 * math.sin(phase_progress * 2 * math.pi)
            self.target_pitch = 10 * math.cos(phase_progress * 2 * math.pi)
        else:
            # Boost run
            self.target_roll = random.uniform(-10, 10)
            self.target_pitch = 5
            self.target_force = 95
            if phase_progress > 0.3 and phase_progress < 0.7:
                self.target_emg = 80  # Trigger boost
            else:
                self.target_emg = 20
                
        # Add subtle noise
        self.target_roll += random.uniform(-2, 2)
        self.target_pitch += random.uniform(-1, 1)
        
        # Clamp
        self.target_roll = max(-45, min(45, self.target_roll))
        self.target_pitch = max(-35, min(35, self.target_pitch))
        self.target_force = max(0, min(100, self.target_force))
        self.target_emg = max(0, min(100, self.target_emg))
