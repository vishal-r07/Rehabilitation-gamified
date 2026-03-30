"""
ENHANCED Robotic Arm Model - Sci-Fi Prosthetic Style
Matches the sleek white/black robotic aesthetic requested.
"""
import vtk
import numpy as np


class SmoothAnimator:
    """Smooth interpolation for natural movements"""
    def __init__(self, smoothness=0.3):  # Increased for faster response!
        self.smoothness = smoothness  # 0.1 = very smooth, 0.5 = responsive
        self.targets = {}
        self.current = {}
        
    def update(self, name, target_value):
        """Smoothly interpolate to target"""
        if name not in self.current:
            self.current[name] = target_value
            return target_value
            
        # Exponential smoothing
        self.current[name] += (target_value - self.current[name]) * self.smoothness
        return self.current[name]


class EnhancedRealisticArm:
    """Sleek White & Black Robotic Arm"""
    
    def __init__(self):
        self.renderer = vtk.vtkRenderer()
        # Professional Lab Background
        self.renderer.SetBackground(0.85, 0.9, 0.95) # Clinical Light Blue
        self.renderer.SetBackground2(0.6, 0.7, 0.8)  # Lab Grey
        self.renderer.SetGradientBackground(True)
        
        # Smooth animation controller
        self.animator = SmoothAnimator(smoothness=0.12)
        
        # Model components
        self.shells = {}  # Outer white shells
        self.joints = {}  # Black mechanical joints
        
        # Current state
        self.elbow_angle = 0
        self.wrist_rotation = [0, 0, 0]
        
        # Build model
        self._create_robotic_structure()
        self._setup_studio_lighting()
        
    def _create_robotic_structure(self):
        """Create the sci-fi prosthetic arm"""
        
        # === UPPER ARM ASSEMBLY ===
        self.upper_arm = vtk.vtkAssembly()
        
        # 1. Shoulder Joint (Black Sphere)
        shoulder = self._create_mechanical_joint(radius=0.9)
        shoulder.SetPosition(0, 5.5, 0)
        self.joints['shoulder'] = shoulder
        self.upper_arm.AddPart(shoulder)
        
        # 2. Upper Arm Shell (White, Sleek)
        # We use a sphere stretched into a capsule shape for the main bulk
        upper_shell = self._create_shell_volume(
            center_x=0, y_pos=2.5, 
            radius=0.8, length=5.0, 
            taper_top=1.0, taper_bottom=0.7
        )
        self.shells['upper_arm'] = upper_shell
        self.upper_arm.AddPart(upper_shell)
        
        # Add a subtle "inner frame" detail (Black strip)
        inner_frame = self._create_cylinder_prop(radius=0.25, length=5.5, color=(0.1, 0.1, 0.1))
        inner_frame.SetPosition(0, 2.75, 0)
        self.upper_arm.AddPart(inner_frame)

        # Add upper arm to renderer
        self.renderer.AddActor(self.upper_arm)
        
        # === ELBOW JOINT (The Hinge) ===
        # Main pivot (Black Cylinder transverse)
        elbow_hinge = vtk.vtkCylinderSource()
        elbow_hinge.SetRadius(0.55)
        elbow_hinge.SetHeight(1.4) # Wide hinge
        elbow_hinge.SetResolution(32)
        
        eh_mapper = vtk.vtkPolyDataMapper()
        eh_mapper.SetInputConnection(elbow_hinge.GetOutputPort())
        
        self.elbow_actor = vtk.vtkActor()
        self.elbow_actor.SetMapper(eh_mapper)
        self.elbow_actor.GetProperty().SetColor(0.1, 0.1, 0.1)  # Matte Black
        self.elbow_actor.GetProperty().SetSpecular(0.8)
        self.elbow_actor.SetPosition(0, 0, 0)
        self.elbow_actor.RotateZ(90) # Horizontal hinge
        
        # Add to Upper Arm (so it moves with it)
        self.upper_arm.AddPart(self.elbow_actor)
        self.joints['elbow'] = self.elbow_actor

        # === FOREARM ASSEMBLY ===
        self.forearm = vtk.vtkAssembly()
        
        # Forearm Shell (White, Tapered)
        forearm_shell = self._create_shell_volume(
            center_x=0, y_pos=-2.5,
            radius=0.6, length=4.5,
            taper_top=0.9, taper_bottom=0.5
        )
        self.shells['forearm'] = forearm_shell
        self.forearm.AddPart(forearm_shell)
        
        # Wrist Joint (Black)
        wrist = self._create_mechanical_joint(radius=0.45)
        wrist.SetPosition(0, -5.0, 0)
        self.forearm.AddPart(wrist)
        
        # Position Forearm correctly relative to Elbow
        self.forearm.SetOrigin(0, 0, 0)
        self.forearm.SetPosition(0, 0, 0)
        
        # Parent Forearm to Upper Arm
        self.upper_arm.AddPart(self.forearm)
        
        # === ROBOTIC HAND ===
        hand = self._create_robotic_hand()
        hand.SetPosition(0, -5.5, 0) # Below wrist
        self.forearm.AddPart(hand)
        
    def _create_shell_volume(self, center_x, y_pos, radius, length, taper_top, taper_bottom):
        """Create a white glossy shell that looks like molded plastic/metal"""
        # Using a Cylinder for better control
        source = vtk.vtkCylinderSource()
        source.SetRadius(radius)
        source.SetHeight(length)
        source.SetResolution(40)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(center_x, y_pos, 0)
        
        prop = actor.GetProperty()
        prop.SetColor(0.95, 0.95, 0.97) # Ultra White
        prop.SetSpecular(0.9)     # Very Shiny
        prop.SetSpecularPower(80) # Tight highlights (Glossy)
        prop.SetAmbient(0.2)
        prop.SetDiffuse(0.8)
        
        return actor

    def _create_mechanical_joint(self, radius):
        """Create a matte black sphere joint"""
        source = vtk.vtkSphereSource()
        source.SetRadius(radius)
        source.SetThetaResolution(32)
        source.SetPhiResolution(32)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        prop = actor.GetProperty()
        prop.SetColor(0.1, 0.1, 0.15) # Black with slight blue tint
        prop.SetSpecular(0.5)         # Metallic
        prop.SetSpecularPower(40)
        
        return actor
        
    def _create_cylinder_prop(self, radius, length, color):
        """Helper for internal structural parts"""
        source = vtk.vtkCylinderSource()
        source.SetRadius(radius)
        source.SetHeight(length)
        source.SetResolution(16)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        
        return actor

    def _create_robotic_hand(self):
        """Create segmented robotic hand"""
        self.hand_assembly = vtk.vtkAssembly()
        self.fingers = [] 
        
        white_shell = (0.95, 0.95, 0.97)
        black_joint = (0.1, 0.1, 0.1)
        
        # 1. PALM (White clean plate)
        palm_source = vtk.vtkCubeSource()
        palm_source.SetXLength(1.8)
        palm_source.SetYLength(2.2)
        palm_source.SetZLength(0.4)
        
        palm_mapper = vtk.vtkPolyDataMapper()
        palm_mapper.SetInputConnection(palm_source.GetOutputPort())
        
        palm = vtk.vtkActor()
        palm.SetMapper(palm_mapper)
        palm.SetPosition(0, -1.0, 0)
        palm.GetProperty().SetColor(white_shell)
        palm.GetProperty().SetSpecular(0.6)
        
        self.hand_assembly.AddPart(palm)
        
        # 2. FINGERS
        angle_offsets = [
             (-0.9, -0.2, 0.2, -50), # Thumb
             (-0.6, -2.1, 0, 0),     # Index
             (0.0, -2.2, 0, 0),      # Middle
             (0.6, -2.1, 0, 0),      # Ring
             (1.1, -1.9, 0, 10)      # Pinky
        ]
        
        for i, (x, y, z, angle) in enumerate(angle_offsets):
            segments = []
            
            # Base Rotation Group
            finger_base = vtk.vtkAssembly()
            finger_base.SetPosition(x, y, z)
            finger_base.RotateZ(angle)
            self.hand_assembly.AddPart(finger_base)
            
            is_thumb = (i == 0)
            num_segments = 2 if is_thumb else 3
            seg_len = 0.6 if is_thumb else 0.55
            width = 0.24 if is_thumb else 0.20
            
            prev_assembly = finger_base
            
            for s in range(num_segments):
                # KNUCKLE (Black Sphere)
                knuckle = vtk.vtkSphereSource()
                knuckle.SetRadius(width * 1.05)
                km = vtk.vtkPolyDataMapper()
                km.SetInputConnection(knuckle.GetOutputPort())
                ka = vtk.vtkActor()
                ka.SetMapper(km)
                ka.GetProperty().SetColor(black_joint)
                prev_assembly.AddPart(ka)
                
                # PHALANX (White Segment)
                phalanx = vtk.vtkCubeSource() # Boxy robot fingers look cooler
                phalanx.SetXLength(width * 1.6)
                phalanx.SetYLength(seg_len * 0.9)
                phalanx.SetZLength(width * 0.8)
                
                pm = vtk.vtkPolyDataMapper()
                pm.SetInputConnection(phalanx.GetOutputPort())
                pa = vtk.vtkActor()
                pa.SetMapper(pm)
                pa.SetPosition(0, -seg_len/2, 0)
                pa.GetProperty().SetColor(white_shell)
                pa.GetProperty().SetSpecular(0.7)
                
                # Container
                segment_container = vtk.vtkAssembly()
                segment_container.AddPart(pa)
                segment_container.SetOrigin(0, 0, 0) # Pivot at knuckle
                
                prev_assembly.AddPart(segment_container)
                segments.append(segment_container)
                
                # Next Joint Offset
                next_offset = vtk.vtkAssembly()
                next_offset.SetPosition(0, -seg_len, 0)
                segment_container.AddPart(next_offset)
                
                prev_assembly = next_offset
                width *= 0.85
                
            self.fingers.append(segments)
            
        return self.hand_assembly

    def set_hand_curl(self, curl_factor):
        """Animate robotic grasp"""
        angle_per_segment = curl_factor * 85.0
        for finger in self.fingers:
            for i, segment in enumerate(finger):
                bend = angle_per_segment
                if i > 0: bend *= 1.1
                segment.SetOrientation(bend, 0, 0)
        
    def _setup_studio_lighting(self):
        """Clean Studio Lighting"""
        # Key Light - Cold White
        key = vtk.vtkLight()
        key.SetPosition(10, 10, 10)
        key.SetColor(0.9, 0.95, 1.0)
        key.SetIntensity(1.3)
        self.renderer.AddLight(key)
        
        # Rim Light - Blue Sci-Fi
        rim = vtk.vtkLight()
        rim.SetPosition(-10, 5, -10)
        rim.SetColor(0.0, 0.5, 1.0) # Electric Blue Rim
        rim.SetIntensity(0.8)
        self.renderer.AddLight(rim)
        
        # Fill Light
        fill = vtk.vtkLight()
        fill.SetPosition(0, -10, 10)
        fill.SetColor(0.8, 0.8, 0.9)
        fill.SetIntensity(0.4)
        self.renderer.AddLight(fill)
        
    def update_from_imu(self, roll, pitch, yaw):
        """SMOOTH IMU rotation"""
        smooth_roll = self.animator.update('roll', roll)
        smooth_pitch = self.animator.update('pitch', pitch)
        smooth_yaw = self.animator.update('yaw', yaw)
        
        self.upper_arm.SetOrientation(smooth_pitch, smooth_yaw, smooth_roll)
        
    def update_from_force(self, force_value):
        """Elbow Flexion - SLIGHTLY MORE SENSITIVE"""
        # force_value is 0-100 (percentage)
        # Divide by 35 for more sensitivity (was 50)
        # Now requires 35% force for full bend
        normalized_force = min(force_value / 35.0, 1.0)
        target_angle = normalized_force * 120.0  # Max 120°
        
        smooth_angle = self.animator.update('elbow', target_angle)
        self.forearm.SetOrientation(smooth_angle, 0, 0)
        self.elbow_angle = smooth_angle
        
        # Close hand with force (also reduced)
        self.set_hand_curl(normalized_force * 1.2)
        
    def update_from_emg(self, emg_value):
        """Sci-Fi Power Glow Effect"""
        activation = min(emg_value / 100.0, 1.0)
        smooth_act = self.animator.update('emg', activation)
        
        # Glow the Elbow Joint Blue when active
        # Blue (0, 0.5, 1.0) to Bright Cyan (0.5, 1.0, 1.0)
        
        glow_intensity = 0.1 + (smooth_act * 0.9)
        
        self.elbow_actor.GetProperty().SetColor(
            0.1 + (smooth_act * 0.4),  # R: Dark -> Med
            0.1 + (smooth_act * 0.8),  # G: Dark -> Bright
            0.15 + (smooth_act * 0.85) # B: Dark Blue -> Bright
        )
        self.elbow_actor.GetProperty().SetAmbient(smooth_act * 0.8) # Self-illumination
        
        print(f"[EMG] {emg_value:.1f}μV → Reactor Level: {smooth_act*100:.1f}%")
        
    def get_renderer(self):
        return self.renderer
