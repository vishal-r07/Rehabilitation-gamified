"""
Simple 3D Hand Model
Basic implementation using VTK for visualization
"""
import vtk
import numpy as np


class HandModel:
    def __init__(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.1, 0.15)
        
        # Create basic hand structure
        self.bones = {}
        self.joints = {}
        self._create_basic_hand()
        
    def _create_basic_hand(self):
        """Create simplified hand model"""
        
        # Palm (base)
        palm = self._create_cube(1.5, 0.3, 2.0, color=(1.0, 0.86, 0.68))
        palm.SetPosition(0, 0, 0)
        self.bones['palm'] = palm
        self.renderer.AddActor(palm)
        
        # Fingers (simplified as cylinders for now)
        fingers = [
            ('thumb', -0.6, 0.2, 1.0),
            ('index', -0.4, 0.2, 1.5),
            ('middle', 0.0, 0.2, 1.6),
            ('ring', 0.4, 0.2, 1.5),
            ('pinky', 0.7, 0.2, 1.2)
        ]
        
        for name, x, y, length in fingers:
            finger = self._create_cylinder(0.15, length, color=(1.0, 0.86, 0.68))
            finger.SetPosition(x, y, length/2 + 1.0)
            self.bones[name] = finger
            self.renderer.AddActor(finger)
            
            # Joint sphere
            joint = self._create_sphere(0.2, color=(1.0, 0.4, 0.4))
            joint.SetPosition(x, y, 1.0)
            self.joints[name] = joint
            self.renderer.AddActor(joint)
        
        # Add axes for reference
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(3, 3, 3)
        self.renderer.AddActor(axes)
        
    def _create_cube(self, width, height, depth, color=(1, 1, 1)):
        """Create a cube actor"""
        source = vtk.vtkCubeSource()
        source.SetXLength(width)
        source.SetYLength(height)
        source.SetZLength(depth)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        
        return actor
        
    def _create_cylinder(self, radius, height, color=(1, 1, 1)):
        """Create a cylinder actor"""
        source = vtk.vtkCylinderSource()
        source.SetRadius(radius)
        source.SetHeight(height)
        source.SetResolution(16)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        
        return actor
        
    def _create_sphere(self, radius, color=(1, 1, 1)):
        """Create a sphere actor"""
        source = vtk.vtkSphereSource()
        source.SetRadius(radius)
        source.SetThetaResolution(16)
        source.SetPhiResolution(16)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        
        return actor
        
    def update_from_imu(self, roll, pitch, yaw):
        """Update hand orientation from IMU data"""
        # Convert degrees to radians
        roll_rad = np.radians(roll)
        pitch_rad = np.radians(pitch)
        yaw_rad = np.radians(yaw)
        
        # Apply rotation to palm
        if 'palm' in self.bones:
            self.bones['palm'].SetOrientation(
                np.degrees(pitch_rad),
                np.degrees(yaw_rad),
                np.degrees(roll_rad)
            )
            
    def update_from_force(self, force_value):
        """Update finger curl based on force sensor"""
        # Normalize force (0-100) to curl angle (0-90 degrees)
        curl_angle = (force_value / 100.0) * 90.0
        
        # Apply to all fingers
        for name in ['index', 'middle', 'ring', 'pinky']:
            if name in self.bones:
                # Simple rotation for now
                self.bones[name].RotateX(curl_angle * 0.01)
                
    def update_from_emg(self, emg_value):
        """Update muscle visualization based on EMG"""
        # Change joint color based on muscle activity
        intensity = min(emg_value / 100.0, 1.0)
        
        for joint in self.joints.values():
            joint.GetProperty().SetColor(
                1.0,
                1.0 - intensity * 0.6,
                1.0 - intensity * 0.6
            )
            
    def get_renderer(self):
        """Get VTK renderer for display"""
        return self.renderer
