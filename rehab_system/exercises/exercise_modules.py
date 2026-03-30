"""
Exercise Modules for Hand Rehabilitation
ROM, Grip Strength, Fine Motor, EMG Training
"""
import time
import numpy as np


class BaseExercise:
    """Base class for all exercises"""
    def __init__(self, name, duration=60):
        self.name = name
        self.duration = duration
        self.start_time = None
        self.is_active = False
        self.score = 0
        self.reps_done = 0
        self.reps_target = 10
        
    def start(self):
        """Start exercise"""
        self.start_time = time.time()
        self.is_active = True
        self.score = 0
        self.reps_done = 0
        
    def stop(self):
        """Stop exercise"""
        self.is_active = False
        
    def get_elapsed_time(self):
        """Get elapsed seconds"""
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0
        
    def get_remaining_time(self):
        """Get remaining seconds"""
        elapsed = self.get_elapsed_time()
        return max(0, self.duration - elapsed)
        
    def get_progress(self):
        """Get progress percentage"""
        return min((self.reps_done / self.reps_target) * 100, 100)


class ROMExercise(BaseExercise):
    """Range of Motion Exercise"""
    def __init__(self):
        super().__init__("Wrist Flexion/Extension", duration=120)
        self.target_angles = {
            'flexion': 80,    # degrees
            'extension': 70,   # degrees
        }
        self.current_max_flex = 0
        self.current_max_ext = 0
        
    def update(self, pitch, roll, yaw):
        """Update with IMU data"""
        if not self.is_active:
            return
            
        # Track maximum angles reached
        if pitch > 0:
            self.current_max_flex = max(self.current_max_flex, pitch)
        else:
            self.current_max_ext = max(self.current_max_ext, abs(pitch))
            
        # Count rep if target reached
        if self.current_max_flex >= self.target_angles['flexion'] * 0.8:
            self.reps_done += 1
            self.score += 10
            self.current_max_flex = 0
            
    def get_feedback(self):
        """Get real-time feedback"""
        flex_percent = (self.current_max_flex / self.target_angles['flexion']) * 100
        ext_percent = (self.current_max_ext / self.target_angles['extension']) * 100
        return f"Flexion: {flex_percent:.0f}% | Extension: {ext_percent:.0f}%"


class GripStrengthExercise(BaseExercise):
    """Grip Strength Training"""
    def __init__(self):
        super().__init__("Grip Strength Challenge", duration=90)
        self.target_force = 50  # Newtons
        self.hold_duration = 3  # seconds
        self.hold_start = None
        self.max_force = 0
        
    def update(self, force):
        """Update with force sensor data"""
        if not self.is_active:
            return
            
        self.max_force = max(self.max_force, force)
        
        # Check if holding target force
        if force >= self.target_force * 0.9:
            if self.hold_start is None:
                self.hold_start = time.time()
            elif time.time() - self.hold_start >= self.hold_duration:
                # Completed one rep!
                self.reps_done += 1
                self.score += 15
                self.hold_start = None
        else:
            self.hold_start = None
            
    def get_feedback(self):
        """Get real-time feedback"""
        if self.hold_start:
            hold_time = time.time() - self.hold_start
            return f"Hold: {hold_time:.1f}s / {self.hold_duration}s | Force: {self.max_force:.1f}N"
        return f"Max Force: {self.max_force:.1f}N | Target: {self.target_force}N"


class FineMotorExercise(BaseExercise):
    """Fine Motor Control"""
    def __init__(self):
        super().__init__("Finger Precision", duration=120)
        self.target_sequence = [1, 2, 3, 4, 5]  # Finger activation order
        self.current_index = 0
        
    def update(self, finger_forces):
        """Update with individual finger forces"""
        if not self.is_active:
            return
            
        # Check if correct finger activated
        target_finger = self.target_sequence[self.current_index]
        if finger_forces[target_finger] > 10:  # Threshold
            self.current_index += 1
            self.score += 10
            
            if self.current_index >= len(self.target_sequence):
                # Completed one sequence
                self.reps_done += 1
                self.current_index = 0
                
    def get_feedback(self):
        """Get real-time feedback"""
        fingers = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        target = fingers[self.target_sequence[self.current_index]]
        return f"Press: {target} | Sequence {self.current_index + 1}/5"


class EMGBiofeedbackExercise(BaseExercise):
    """EMG Muscle Control Training"""
    def __init__(self):
        super().__init__("Muscle Activation Control", duration=90)
        self.target_emg_min = 30  # μV
        self.target_emg_max = 80  # μV
        self.in_zone_start = None
        self.zone_time_target = 5  # seconds
        
    def update(self, emg_value):
        """Update with EMG sensor data"""
        if not self.is_active:
            return
            
        # Check if EMG in target zone
        if self.target_emg_min <= emg_value <= self.target_emg_max:
            if self.in_zone_start is None:
                self.in_zone_start = time.time()
            elif time.time() - self.in_zone_start >= self.zone_time_target:
                # Completed one rep
                self.reps_done += 1
                self.score += 20
                self.in_zone_start = None
        else:
            self.in_zone_start = None
            
    def get_feedback(self):
        """Get real-time feedback"""
        if self.in_zone_start:
            zone_time = time.time() - self.in_zone_start
            return f"In Zone: {zone_time:.1f}s / {self.zone_time_target}s"
        return f"Target Zone: {self.target_emg_min}-{self.target_emg_max} μV"


class ExerciseManager:
    """Manage all exercise modules"""
    def __init__(self):
        self.exercises = {
            'rom': ROMExercise(),
            'grip': GripStrengthExercise(),
            'motor': FineMotorExercise(),
            'emg': EMGBiofeedbackExercise()
        }
        self.current_exercise = None
        
    def start_exercise(self, exercise_type):
        """Start specific exercise"""
        if exercise_type in self.exercises:
            # Stop any running exercise
            if self.current_exercise:
                self.current_exercise.stop()
                
            self.current_exercise = self.exercises[exercise_type]
            self.current_exercise.start()
            return True
        return False
        
    def stop_current(self):
        """Stop current exercise"""
        if self.current_exercise:
            self.current_exercise.stop()
            self.current_exercise = None
            
    def update(self, imu_data, force_data, emg_data):
        """Update current exercise with sensor data"""
        if not self.current_exercise or not self.current_exercise.is_active:
            return
            
        # Route data to appropriate exercise
        if isinstance(self.current_exercise, ROMExercise):
            self.current_exercise.update(
                imu_data['pitch'],
                imu_data['roll'],
                imu_data['yaw']
            )
        elif isinstance(self.current_exercise, GripStrengthExercise):
            self.current_exercise.update(force_data)
        elif isinstance(self.current_exercise, EMGBiofeedbackExercise):
            self.current_exercise.update(emg_data)
            
    def get_status(self):
        """Get current exercise status"""
        if not self.current_exercise:
            return None
            
        return {
            'name': self.current_exercise.name,
            'active': self.current_exercise.is_active,
            'elapsed': self.current_exercise.get_elapsed_time(),
            'remaining': self.current_exercise.get_remaining_time(),
            'reps': self.current_exercise.reps_done,
            'target_reps': self.current_exercise.reps_target,
            'score': self.current_exercise.score,
            'progress': self.current_exercise.get_progress(),
            'feedback': self.current_exercise.get_feedback()
        }
