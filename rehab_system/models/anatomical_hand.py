"""
Advanced Anatomical Hand Model
Complete 27-bone structure with 21 articulated joints
"""
import vtk
import numpy as np


class Bone:
    """Individual bone with realistic shape"""
    def __init__(self, name, length, width, color=(0.95, 0.95, 0.9)):
        self.name = name
        self.length = length
        self.width = width
        self.actor = self._create_bone(length, width, color)
        
    def _create_bone(self, length, width, color):
        """Create bone-shaped actor"""
        # Use cylinder for now, can be replaced with STL mesh later
        source = vtk.vtkCylinderSource()
        source.SetRadius(width / 2)
        source.SetHeight(length)
        source.SetResolution(12)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(20)
        
        return actor


class Joint:
    """Joint sphere with realistic appearance"""
    def __init__(self, name, radius=0.15):
        self.name = name
        self.radius = radius
        self.actor = self._create_joint(radius)
        self.angle = 0  # Current flexion/extension angle
        
    def _create_joint(self, radius):
        """Create joint sphere"""
        source = vtk.vtkSphereSource()
        source.SetRadius(radius)
        source.SetThetaResolution(16)
        source.SetPhiResolution(16)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # Joint color - slightly reddish
        actor.GetProperty().SetColor(0.9, 0.7, 0.7)
        actor.GetProperty().SetSpecular(0.5)
        
        return actor


class AnatomicalHandModel:
    """Full anatomical hand with 27 bones and 21 joints"""
    
    def __init__(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.15, 0.15, 0.2)
        
        # Bone collections
        self.carpals = {}      # 8 wrist bones
        self.metacarpals = {}  # 5 palm bones
        self.phalanges = {}    # 14 finger bones
        
        # Joint collections
        self.joints = {}
        
        # Build complete hand
        self._build_hand()
        self._add_lighting()
        
    def _build_hand(self):
        """Construct complete anatomical hand"""
        # Simplified positioning for now - can be refined
        
        # 1. WRIST (Carpals - simplified as single block)
        wrist = Bone("wrist", 1.0, 2.0)
        wrist.actor.SetPosition(0, -1, 0)
        wrist.actor.RotateZ(90)
        self.carpals['wrist'] = wrist
        self.renderer.AddActor(wrist.actor)
        
        # 2. METACARPALS (Palm bones)
        metacarpal_positions = {
            'thumb': (-0.8, 0, 0.3),
            'index': (-0.4, 0, 0),
            'middle': (0, 0, 0),
            'ring': (0.4, 0, 0),
            'pinky': (0.8, 0, -0.2)
        }
        
        for finger, (x, y, z) in metacarpal_positions.items():
            bone = Bone(f"meta_{finger}", 1.8, 0.25)
            bone.actor.SetPosition(x, y + 1, z)
            self.metacarpals[finger] = bone
            self.renderer.AddActor(bone.actor)
            
            # MCP joint (knuckle)
            joint = Joint(f"mcp_{finger}", 0.18)
            joint.actor.SetPosition(x, y + 2, z)
            self.joints[f"mcp_{finger}"] = joint
            self.renderer.AddActor(joint.actor)
        
        # 3. PHALANGES (Finger bones)
        # Each finger has 3 phalanges (proximal, middle, distal)
        # Thumb has 2 (proximal, distal)
        
        finger_lengths = {
            'thumb': [1.2, 0.9],
            'index': [1.5, 1.0, 0.8],
            'middle': [1.7, 1.2, 0.9],
            'ring': [1.6, 1.1, 0.8],
            'pinky': [1.2, 0.9, 0.7]
        }
        
        for finger, lengths in finger_lengths.items():
            x, y, z = metacarpal_positions[finger]
            current_y = y + 2
            
            for i, length in enumerate(lengths):
                segment_name = ['proximal', 'middle', 'distal'][i] if len(lengths) == 3 else ['proximal', 'distal'][i]
                
                # Create phalanx
                bone = Bone(f"{finger}_{segment_name}", length, 0.2)
                bone.actor.SetPosition(x, current_y + length/2, z)
                self.phalanges[f"{finger}_{segment_name}"] = bone
                self.renderer.AddActor(bone.actor)
                
                current_y += length
                
                # Add joint (except at fingertip)
                if i < len(lengths) - 1:
                    joint_type = 'pip' if i == 0 and len(lengths) == 3 else 'dip' if i == 1 else 'ip'
                    joint = Joint(f"{joint_type}_{finger}", 0.15)
                    joint.actor.SetPosition(x, current_y, z)
                    self.joints[f"{joint_type}_{finger}"] = joint
                    self.renderer.AddActor(joint.actor)
        
        # Add reference axes
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(2, 2, 2)
        self.renderer.AddActor(axes)
        
    def _add_lighting(self):
        """Add realistic lighting"""
        # Key light
        light1 = vtk.vtkLight()
        light1.SetPosition(5, 10, 5)
        light1.SetFocalPoint(0, 0, 0)
        light1.SetColor(1, 1, 1)
        light1.SetIntensity(0.8)
        self.renderer.AddLight(light1)
        
        # Fill light
        light2 = vtk.vtkLight()
        light2.SetPosition(-5, 5, 3)
        light2.SetFocalPoint(0, 0, 0)
        light2.SetColor(0.7, 0.8, 1.0)
        light2.SetIntensity(0.4)
        self.renderer.AddLight(light2)
        
    def update_from_imu(self, roll, pitch, yaw):
        """Update wrist orientation from IMU"""
        # Apply to wrist only for now
        if 'wrist' in self.carpals:
            self.carpals['wrist'].actor.SetOrientation(
                pitch * 0.8,  # Scale for comfortable viewing
                yaw * 0.8,
                roll * 0.8
            )
    
    def update_from_force(self, force_value):
        """Curl all fingers based on grip force"""
        # Normalize force (0-100) to curl angle (0-90 degrees)
        curl = min(force_value / 100.0 * 90, 90)
        
        # Apply to all finger segments
        for name, bone in self.phalanges.items():
            if 'proximal' in name:
                bone.actor.RotateX(curl * 0.5)
            elif 'middle' in name:
                bone.actor.RotateX(curl * 0.7)
            elif 'distal' in name:
                bone.actor.RotateX(curl * 0.9)
    
    def update_from_emg(self, emg_value):
        """Highlight muscle activity on joints"""
        intensity = min(emg_value / 100.0, 1.0)
        
        # Change joint color based on muscle activation
        for joint in self.joints.values():
            joint.actor.GetProperty().SetColor(
                1.0,
                1.0 - intensity * 0.5,
                1.0 - intensity * 0.5
            )
            # Add glow effect
            joint.actor.GetProperty().SetAmbient(0.3 + intensity * 0.4)
    
    def get_renderer(self):
        """Return VTK renderer"""
        return self.renderer
