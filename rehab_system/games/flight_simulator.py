"""
Flight Simulator Rehabilitation Game - FIXED VERSION
- Rings face the player correctly
- Camera follows aircraft
- Constrained movement within visible area
"""
import vtk
import numpy as np
import math
import random


class Cloud:
    """Simple cloud object"""
    def __init__(self, position, size=1.0):
        self.position = list(position)
        self.size = size
        self.actors = []
        self._create_cloud()
        
    def _create_cloud(self):
        """Create fluffy cloud from spheres"""
        offsets = [
            (0, 0, 0, 1.0),
            (0.8, 0.2, 0.1, 0.7),
            (-0.7, 0.1, 0.2, 0.8),
            (0.3, 0.4, -0.3, 0.6),
        ]
        
        for ox, oy, oz, scale in offsets:
            sphere = vtk.vtkSphereSource()
            sphere.SetRadius(self.size * scale)
            sphere.SetThetaResolution(8)
            sphere.SetPhiResolution(8)
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(1.0, 1.0, 1.0)
            actor.GetProperty().SetOpacity(0.8)
            actor.SetPosition(
                self.position[0] + ox * self.size,
                self.position[1] + oy * self.size,
                self.position[2] + oz * self.size
            )
            self.actors.append(actor)
            
    def add_to_renderer(self, renderer):
        for actor in self.actors:
            renderer.AddActor(actor)
            
    def remove_from_renderer(self, renderer):
        for actor in self.actors:
            renderer.RemoveActor(actor)
            
    def update_position(self, offset_z):
        """Move cloud towards camera"""
        self.position[2] += offset_z
        for actor in self.actors:
            pos = actor.GetPosition()
            actor.SetPosition(pos[0], pos[1], pos[2] + offset_z)


class Ring:
    """Collectible ring - FACES THE PLAYER correctly"""
    def __init__(self, position, radius=2.5, color=(1.0, 0.84, 0.0)):
        self.position = list(position)
        self.radius = radius
        self.color = color
        self.collected = False
        self.actor = None
        self.time = 0
        self._create_ring()
        
    def _create_ring(self):
        """Create a torus ring facing the player (Z direction)"""
        # Create torus
        torus = vtk.vtkParametricTorus()
        torus.SetRingRadius(self.radius)
        torus.SetCrossSectionRadius(0.35)
        
        source = vtk.vtkParametricFunctionSource()
        source.SetParametricFunction(torus)
        source.SetUResolution(32)
        source.SetVResolution(16)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(*self.color)
        self.actor.GetProperty().SetSpecular(0.9)
        self.actor.GetProperty().SetSpecularPower(50)
        self.actor.GetProperty().SetAmbient(0.4)
        self.actor.SetPosition(*self.position)
        
        # CORRECT ORIENTATION: Rotate so the hole faces the camera (along Z axis)
        # Default torus lies in XY plane with hole along Z - that's what we want!
        # Just rotate X by 90 to stand it up vertically
        self.actor.RotateX(90)
        
    def add_to_renderer(self, renderer):
        if self.actor:
            renderer.AddActor(self.actor)
            
    def remove_from_renderer(self, renderer):
        if self.actor:
            renderer.RemoveActor(self.actor)
            
    def update_position(self, offset_z):
        """Move ring towards camera"""
        self.position[2] += offset_z
        self.time += 0.1
        if self.actor:
            self.actor.SetPosition(*self.position)
            # Gentle shimmer effect
            glow = 0.4 + 0.1 * math.sin(self.time)
            self.actor.GetProperty().SetAmbient(glow)
            
    def check_collision(self, aircraft_pos, threshold=4.5):
        """Check if aircraft passed through ring"""
        if self.collected:
            return False
        dx = self.position[0] - aircraft_pos[0]
        dy = self.position[1] - aircraft_pos[1]
        dz = self.position[2] - aircraft_pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < threshold


class Obstacle:
    """Obstacle to avoid"""
    def __init__(self, position, size=2.0):
        self.position = list(position)
        self.size = size
        self.actor = None
        self.rotation = 0
        self._create_obstacle()
        
    def _create_obstacle(self):
        """Create obstacle"""
        source = vtk.vtkCubeSource()
        source.SetXLength(self.size)
        source.SetYLength(self.size)
        source.SetZLength(self.size)
            
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(0.9, 0.2, 0.2)
        self.actor.GetProperty().SetOpacity(0.9)
        self.actor.SetPosition(*self.position)
        
    def add_to_renderer(self, renderer):
        if self.actor:
            renderer.AddActor(self.actor)
            
    def remove_from_renderer(self, renderer):
        if self.actor:
            renderer.RemoveActor(self.actor)
            
    def update_position(self, offset_z):
        """Move obstacle towards camera"""
        self.position[2] += offset_z
        self.rotation += 2
        if self.actor:
            self.actor.SetPosition(*self.position)
            self.actor.SetOrientation(self.rotation, self.rotation * 0.7, 0)
            
    def check_collision(self, aircraft_pos, threshold=2.5):
        """Check collision"""
        dx = self.position[0] - aircraft_pos[0]
        dy = self.position[1] - aircraft_pos[1]
        dz = self.position[2] - aircraft_pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < threshold


class Aircraft:
    """Player aircraft with BETTER CONTROLS"""
    
    # Play area bounds (visible on screen)
    BOUNDS_X = 10  # Left/Right limit
    BOUNDS_Y_MIN = -5  # Bottom limit  
    BOUNDS_Y_MAX = 8   # Top limit
    
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.throttle = 0.0
        self.boost = False
        self.boost_fuel = 100.0
        self.health = 100.0
        
        self.assembly = vtk.vtkAssembly()
        self._create_aircraft()
        
    def _create_aircraft(self):
        """Create simple aircraft"""
        # Fuselage
        fuselage = vtk.vtkCylinderSource()
        fuselage.SetRadius(0.4)
        fuselage.SetHeight(3.0)
        fuselage.SetResolution(16)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(fuselage.GetOutputPort())
        
        body = vtk.vtkActor()
        body.SetMapper(mapper)
        body.GetProperty().SetColor(0.2, 0.4, 0.9)
        body.GetProperty().SetSpecular(0.6)
        body.RotateX(90)
        self.assembly.AddPart(body)
        
        # Nose
        nose = vtk.vtkConeSource()
        nose.SetRadius(0.4)
        nose.SetHeight(1.0)
        nose.SetResolution(16)
        
        mapper2 = vtk.vtkPolyDataMapper()
        mapper2.SetInputConnection(nose.GetOutputPort())
        
        nose_actor = vtk.vtkActor()
        nose_actor.SetMapper(mapper2)
        nose_actor.GetProperty().SetColor(0.95, 0.95, 0.95)
        nose_actor.SetPosition(0, 0, 2.0)
        nose_actor.RotateY(-90)
        nose_actor.RotateZ(90)
        self.assembly.AddPart(nose_actor)
        
        # Wings
        wing = vtk.vtkCubeSource()
        wing.SetXLength(5.0)
        wing.SetYLength(0.08)
        wing.SetZLength(0.6)
        
        mapper3 = vtk.vtkPolyDataMapper()
        mapper3.SetInputConnection(wing.GetOutputPort())
        
        wing_actor = vtk.vtkActor()
        wing_actor.SetMapper(mapper3)
        wing_actor.GetProperty().SetColor(0.15, 0.3, 0.8)
        wing_actor.SetPosition(0, 0, 0)
        self.assembly.AddPart(wing_actor)
        
        # Tail
        tail = vtk.vtkCubeSource()
        tail.SetXLength(2.0)
        tail.SetYLength(0.06)
        tail.SetZLength(0.4)
        
        mapper4 = vtk.vtkPolyDataMapper()
        mapper4.SetInputConnection(tail.GetOutputPort())
        
        tail_actor = vtk.vtkActor()
        tail_actor.SetMapper(mapper4)
        tail_actor.GetProperty().SetColor(0.15, 0.3, 0.8)
        tail_actor.SetPosition(0, 0, -1.3)
        self.assembly.AddPart(tail_actor)
        
        # Vertical stabilizer
        vstab = vtk.vtkCubeSource()
        vstab.SetXLength(0.08)
        vstab.SetYLength(0.8)
        vstab.SetZLength(0.5)
        
        mapper5 = vtk.vtkPolyDataMapper()
        mapper5.SetInputConnection(vstab.GetOutputPort())
        
        vstab_actor = vtk.vtkActor()
        vstab_actor.SetMapper(mapper5)
        vstab_actor.GetProperty().SetColor(0.15, 0.3, 0.8)
        vstab_actor.SetPosition(0, 0.4, -1.3)
        self.assembly.AddPart(vstab_actor)
        
        # Engine glow
        engine = vtk.vtkSphereSource()
        engine.SetRadius(0.25)
        engine.SetThetaResolution(12)
        engine.SetPhiResolution(12)
        
        mapper6 = vtk.vtkPolyDataMapper()
        mapper6.SetInputConnection(engine.GetOutputPort())
        
        self.engine_glow = vtk.vtkActor()
        self.engine_glow.SetMapper(mapper6)
        self.engine_glow.GetProperty().SetColor(1.0, 0.5, 0.0)
        self.engine_glow.GetProperty().SetOpacity(0.8)
        self.engine_glow.SetPosition(0, 0, -1.7)
        self.assembly.AddPart(self.engine_glow)
        
    def get_assembly(self):
        return self.assembly
        
    def update(self, roll, pitch, throttle, boost_active):
        """Update aircraft - SMOOTH and BOUNDED controls"""
        # Reduced sensitivity for smoother control
        target_roll = np.clip(roll * 0.8, -35, 35)
        target_pitch = np.clip(pitch * 0.6, -25, 25)
        
        # Smooth interpolation
        self.rotation[0] += (target_roll - self.rotation[0]) * 0.15
        self.rotation[1] += (target_pitch - self.rotation[1]) * 0.15
        
        # Throttle
        self.throttle = np.clip(throttle, 0, 100)
        
        # Boost
        if boost_active and self.boost_fuel > 0:
            self.boost = True
            self.boost_fuel = max(0, self.boost_fuel - 0.4)
        else:
            self.boost = False
            self.boost_fuel = min(100, self.boost_fuel + 0.2)
            
        # Movement speed based on rotation
        speed = 0.25 if self.boost else 0.18
        self.velocity[0] = math.sin(math.radians(self.rotation[0])) * speed
        self.velocity[1] = math.sin(math.radians(self.rotation[1])) * speed
        
        # Update position with STRICT BOUNDS
        new_x = self.position[0] + self.velocity[0]
        new_y = self.position[1] + self.velocity[1]
        
        # Clamp to visible play area
        self.position[0] = np.clip(new_x, -self.BOUNDS_X, self.BOUNDS_X)
        self.position[1] = np.clip(new_y, self.BOUNDS_Y_MIN, self.BOUNDS_Y_MAX)
        
        # Apply to assembly
        self.assembly.SetPosition(*self.position)
        self.assembly.SetOrientation(self.rotation[1], 0, self.rotation[0])
        
        # Engine glow
        if self.engine_glow:
            if self.boost:
                self.engine_glow.GetProperty().SetColor(0.0, 0.8, 1.0)
                self.engine_glow.GetProperty().SetOpacity(1.0)
            else:
                intensity = 0.4 + (self.throttle / 100) * 0.6
                self.engine_glow.GetProperty().SetColor(1.0, 0.4, 0.0)
                self.engine_glow.GetProperty().SetOpacity(intensity)
                
    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        return self.health <= 0


class FlightSimulator:
    """Flight Simulator Game - FIXED VERSION"""
    
    def __init__(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.4, 0.65, 0.95)  # Sky blue
        
        # Game state
        self.is_running = False
        self.is_paused = False
        self.score = 0
        self.distance = 0.0
        self.level = 1
        self.game_speed = 0.8
        
        # Callbacks
        self.on_score_update = None
        self.on_game_over = None
        self.on_ring_collected = None
        self.on_collision = None
        
        # Game objects
        self.aircraft = Aircraft()
        self.clouds = []
        self.rings = []
        self.obstacles = []
        
        # Camera
        self.camera = self.renderer.GetActiveCamera()
        
        # Setup
        self._setup_scene()
        self._setup_camera()
        self._setup_lighting()
        self._spawn_initial_objects()
        
    def _setup_scene(self):
        """Setup scene"""
        # Add aircraft
        self.renderer.AddActor(self.aircraft.get_assembly())
        
        # Ground plane
        ground = vtk.vtkPlaneSource()
        ground.SetXResolution(20)
        ground.SetYResolution(20)
        ground.SetOrigin(-200, -15, -50)
        ground.SetPoint1(200, -15, -50)
        ground.SetPoint2(-200, -15, 300)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(ground.GetOutputPort())
        
        ground_actor = vtk.vtkActor()
        ground_actor.SetMapper(mapper)
        ground_actor.GetProperty().SetColor(0.3, 0.6, 0.3)
        ground_actor.GetProperty().SetOpacity(0.7)
        self.renderer.AddActor(ground_actor)
        
    def _setup_camera(self):
        """Setup FOLLOWING camera behind aircraft"""
        # Camera positioned behind and above aircraft
        self.camera.SetPosition(0, 8, -25)
        self.camera.SetFocalPoint(0, 0, 30)
        self.camera.SetViewUp(0, 1, 0)
        self.camera.SetClippingRange(0.1, 500)
        self.camera.SetViewAngle(60)  # Wider FOV
        
    def _update_camera(self):
        """Update camera to follow aircraft smoothly"""
        # Camera follows aircraft position with offset
        target_x = self.aircraft.position[0] * 0.5  # Reduced following
        target_y = self.aircraft.position[1] * 0.3 + 6
        
        current_pos = list(self.camera.GetPosition())
        current_focal = list(self.camera.GetFocalPoint())
        
        # Smooth camera movement
        new_cam_x = current_pos[0] + (target_x - current_pos[0]) * 0.08
        new_cam_y = current_pos[1] + (target_y - current_pos[1]) * 0.08
        
        self.camera.SetPosition(new_cam_x, new_cam_y, -25)
        self.camera.SetFocalPoint(new_cam_x, target_y - 4, 30)
        
    def _setup_lighting(self):
        """Setup lighting"""
        sun = vtk.vtkLight()
        sun.SetPositional(False)
        sun.SetPosition(50, 100, 0)
        sun.SetFocalPoint(0, 0, 0)
        sun.SetColor(1.0, 0.98, 0.9)
        sun.SetIntensity(1.0)
        self.renderer.AddLight(sun)
        
        fill = vtk.vtkLight()
        fill.SetPositional(False)
        fill.SetColor(0.5, 0.6, 0.8)
        fill.SetIntensity(0.4)
        self.renderer.AddLight(fill)
        
    def _spawn_initial_objects(self):
        """Spawn initial objects"""
        # Clouds
        for i in range(10):
            x = random.uniform(-30, 30)
            y = random.uniform(8, 18)
            z = random.uniform(20, 150)
            cloud = Cloud([x, y, z], random.uniform(2, 4))
            cloud.add_to_renderer(self.renderer)
            self.clouds.append(cloud)
            
        # Initial rings - spaced out
        for i in range(4):
            self._spawn_ring(40 + i * 25)
            
    def _spawn_ring(self, z_pos):
        """Spawn ring in VISIBLE area"""
        # Keep rings within aircraft movement bounds
        x = random.uniform(-8, 8)
        y = random.uniform(-3, 6)
        ring = Ring([x, y, z_pos])
        ring.add_to_renderer(self.renderer)
        self.rings.append(ring)
        
    def _spawn_obstacle(self, z_pos):
        """Spawn obstacle"""
        x = random.uniform(-8, 8)
        y = random.uniform(-3, 6)
        size = random.uniform(1.5, 2.5)
        obs = Obstacle([x, y, z_pos], size)
        obs.add_to_renderer(self.renderer)
        self.obstacles.append(obs)
        
    def _spawn_cloud(self, z_pos):
        """Spawn cloud"""
        x = random.uniform(-30, 30)
        y = random.uniform(8, 18)
        cloud = Cloud([x, y, z_pos], random.uniform(2, 4))
        cloud.add_to_renderer(self.renderer)
        self.clouds.append(cloud)
        
    def start(self):
        """Start game"""
        self.is_running = True
        self.is_paused = False
        self.score = 0
        self.distance = 0.0
        self.aircraft.health = 100.0
        self.aircraft.boost_fuel = 100.0
        self.aircraft.position = [0.0, 0.0, 0.0]
        print("[FlightSim] 🛫 Game Started!")
        
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
        
    def stop(self):
        self.is_running = False
        print(f"[FlightSim] Game Over! Score: {self.score}")
        
    def reset(self):
        """Reset game"""
        for ring in self.rings:
            ring.remove_from_renderer(self.renderer)
        for obs in self.obstacles:
            obs.remove_from_renderer(self.renderer)
        for cloud in self.clouds:
            cloud.remove_from_renderer(self.renderer)
            
        self.rings.clear()
        self.obstacles.clear()
        self.clouds.clear()
        
        self.score = 0
        self.distance = 0.0
        self.level = 1
        self.game_speed = 0.8
        self.aircraft.health = 100.0
        self.aircraft.boost_fuel = 100.0
        self.aircraft.position = [0.0, 0.0, 0.0]
        
        self._spawn_initial_objects()
        self._setup_camera()
        print("[FlightSim] 🔄 Reset")
        
    def update(self, imu_data, force_value, emg_value, dt=0.016):
        """Update game"""
        if not self.is_running or self.is_paused:
            return
            
        # Sensor input
        roll = imu_data.get('roll', 0)
        pitch = imu_data.get('pitch', 0)
        throttle = force_value
        boost_active = emg_value > 50
        
        # Update aircraft
        self.aircraft.update(roll, pitch, throttle, boost_active)
        
        # Update camera to follow
        self._update_camera()
        
        # Game speed
        base_speed = 0.6 + (throttle / 100) * 0.4
        if self.aircraft.boost:
            base_speed *= 1.3
        self.game_speed = base_speed * (1 + self.level * 0.05)
        
        # Distance
        self.distance += self.game_speed
        
        # Move objects
        move_speed = -self.game_speed
        
        # Clouds
        for cloud in self.clouds[:]:
            cloud.update_position(move_speed)
            if cloud.position[2] < -30:
                cloud.remove_from_renderer(self.renderer)
                self.clouds.remove(cloud)
                self._spawn_cloud(random.uniform(120, 160))
                
        # Rings
        for ring in self.rings[:]:
            ring.update_position(move_speed)
            
            if ring.check_collision(self.aircraft.position):
                ring.collected = True
                ring.remove_from_renderer(self.renderer)
                self.rings.remove(ring)
                points = 100 + self.level * 25
                self.score += points
                print(f"[FlightSim] 🎯 +{points} pts! Total: {self.score}")
                if self.on_ring_collected:
                    self.on_ring_collected()
                self._spawn_ring(random.uniform(70, 100))
                
            elif ring.position[2] < -15:
                ring.remove_from_renderer(self.renderer)
                self.rings.remove(ring)
                self._spawn_ring(random.uniform(70, 100))
                
        # Obstacles
        for obs in self.obstacles[:]:
            obs.update_position(move_speed)
            
            if obs.check_collision(self.aircraft.position):
                game_over = self.aircraft.take_damage(25)
                obs.remove_from_renderer(self.renderer)
                self.obstacles.remove(obs)
                print(f"[FlightSim] 💥 Hit! Health: {self.aircraft.health}")
                if self.on_collision:
                    self.on_collision(self.aircraft.health)
                if game_over:
                    self.stop()
                    if self.on_game_over:
                        self.on_game_over(self.score)
                else:
                    self._spawn_obstacle(random.uniform(100, 130))
                    
            elif obs.position[2] < -15:
                obs.remove_from_renderer(self.renderer)
                self.obstacles.remove(obs)
                self.score += 15  # Dodged!
                
        # Level up
        new_level = int(self.distance / 400) + 1
        if new_level > self.level:
            self.level = new_level
            print(f"[FlightSim] 🎉 LEVEL {self.level}!")
            self._spawn_obstacle(random.uniform(80, 110))
            
        # Random obstacles
        if self.level > 1 and random.random() < 0.008 * self.level:
            self._spawn_obstacle(random.uniform(90, 120))
            
        # Score callback
        if self.on_score_update:
            self.on_score_update(self.score, self.distance, self.level)
            
    def get_renderer(self):
        return self.renderer
        
    def get_game_state(self):
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'score': self.score,
            'distance': self.distance,
            'level': self.level,
            'health': self.aircraft.health,
            'boost_fuel': self.aircraft.boost_fuel,
            'throttle': self.aircraft.throttle,
            'position': self.aircraft.position.copy(),
        }
