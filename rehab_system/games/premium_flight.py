"""
==========================================================================
  HYPERION SQUADRON V2: ULTRA-HD EDITION
  Ursina Engine | AAA Graphics | PBR Shaders | Serial Sync
==========================================================================
"""
import sys, os, random, threading

# Path so we can find sensors/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ursina import (
    Ursina, Entity, Sky, Text, Vec3, color, window, camera,
    DirectionalLight, AmbientLight, destroy, 
    application, clamp, load_model, Texture
)
from ursina import time as ursina_time
from ursina.shaders import lit_with_shadows_shader, colored_shader

# ── Thread-safe sensor store ──────────────────────────────────────────────
class SensorStore:
    def __init__(self):
        self._lock = threading.Lock()
        self.roll = self.pitch = self.yaw = 0.0
        self.force = self.emg = 0.0
        self.connected = False

    def push(self, imu: dict, force: float, emg: float):
        with self._lock:
            self.roll  = float(imu.get('roll',  0))
            self.pitch = float(imu.get('pitch', 0))
            self.yaw   = float(imu.get('yaw',   0))
            self.force = float(force)
            self.emg   = float(emg)
            self.connected = True

    def read(self):
        with self._lock:
            return self.roll, self.pitch, self.yaw, self.force, self.emg

SENSORS = SensorStore()

# ── CLI arguments ─────────────────────────────────────────────────────────
import argparse
ap = argparse.ArgumentParser(add_help=False)
ap.add_argument("--com",  default="TEST")
ap.add_argument("--test", action="store_true")
args, _ = ap.parse_known_args()

# ── Connect sensor source ─────────────────────────────────────────────────
def _generic_cb(imu_or_dict, force=None, emg=None):
    if isinstance(imu_or_dict, dict) and 'force' in imu_or_dict:
        SENSORS.push(imu_or_dict, imu_or_dict['force'], imu_or_dict['emg'])
    else:
        SENSORS.push(imu_or_dict, force or 0, emg or 0)

if args.com == "TEST" or args.test:
    from sensors.simulator import FlightPatternSimulator
    _simulator = FlightPatternSimulator(_generic_cb)
    _simulator.start()
    SENSORS.connected = True
    print("[HD-ENGINE] ▶ TEST MODE (Simulated Hardware)")
else:
    from sensors.serial_client import SerialClient
    _serial_client = SerialClient()
    _serial_client.set_data_callback(_generic_cb)
    _serial_client.connect(args.com)
    print(f"[HD-ENGINE] Connecting to {args.com}...")

# ═════════════════════════════════════════════════════════════
#  URSINA SETUP & SHADERS
# ═════════════════════════════════════════════════════════════
# Must set antialiasing before init
window.cog_button.enabled = False
window.exit_button.visible = True

app = Ursina(
    title      = "HYPERION SQUADRON : HD REMASTER",
    borderless = False,
    vsync      = True,
    size       = (1440, 810),
)
window.color = color.black

# Cinematic HD Skybox (using high-res stars texture instead of spheres)
sky = Sky()
sky.color = color.rgb(8, 12, 35)

camera.fov = 85

# ── HD Lighting Pipeline ──────────────────────────────────────────────────
# Main sun (casts shadows if enabled on objects)
sun = DirectionalLight(shadows=True)
sun.look_at(Vec3(1, -1.5, -1))
sun.color = color.rgb(255, 230, 200)

# Colored rim light for cinematic space feel (purple/blue)
rim = DirectionalLight()
rim.look_at(Vec3(-1, 0.5, 2))
rim.color = color.rgb(60, 40, 180)

ambient = AmbientLight()
ambient.color = color.rgb(25, 30, 45)

# ═════════════════════════════════════════════════════════════
#  HD ASSETS (Imported .obj files with procedural shaders)
# ═════════════════════════════════════════════════════════════
# Build paths relative to this file
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "models")
SHIP_OBJ = os.path.join(ASSETS_DIR, "spaceship.obj")
ROCK_OBJ = os.path.join(ASSETS_DIR, "asteroid.obj")
TORUS_OBJ = os.path.join(ASSETS_DIR, "torus.obj")

# ── PLAYER SHIP ──────────────────────────────────────────────────────────
# We use a pivot to handle rotation without displacing the mesh center
ship = Entity()

try:
    # Attempt to load the realistic model
    hull = Entity(
        parent=ship,
        model=SHIP_OBJ,
        scale=2.5,
        rotation=Vec3(0, 180, 0), # Face forward
        shader=lit_with_shadows_shader,
        color=color.rgb(180, 190, 210) # metallic silver base
    )
except Exception as e:
    print(f"[HD-ENGINE] Failed to load {SHIP_OBJ}, using proxy. ({e})")
    hull = Entity(parent=ship, model='cube', shader=lit_with_shadows_shader, scale=Vec3(1.5, 0.5, 3), color=color.gray)

# Engine glow thrusters
eng_L = Entity(parent=ship, model='sphere', color=color.rgb(0, 230, 255), scale=0.35, position=Vec3(-0.6, 0.2, -1.5), unlit=True)
eng_R = Entity(parent=ship, model='sphere', color=color.rgb(0, 230, 255), scale=0.35, position=Vec3( 0.6, 0.2, -1.5), unlit=True)

# Post-process glow (simulated using larger transparent spheres)
glow_L = Entity(parent=eng_L, model='sphere', color=color.rgba(0, 200, 255, 100), scale=2.0, unlit=True)
glow_R = Entity(parent=eng_R, model='sphere', color=color.rgba(0, 200, 255, 100), scale=2.0, unlit=True)

# Cinematic Chase Camera
camera.parent   = ship
camera.position = Vec3(0, 4.0, -12)
camera.rotation_x = 10

# ═════════════════════════════════════════════════════════════
#  HD OBSTACLES (Asteroids & Target Rings)
# ═════════════════════════════════════════════════════════════
RING_POOL = []
ROCK_POOL = []

for _ in range(25):
    # Rings glow, so they are unlit (emissive)
    try:
        r = Entity(model=TORUS_OBJ, color=color.rgba(0, 255, 200, 220), scale=Vec3(1.2, 1.2, 1.2), unlit=True)
    except:
        r = Entity(model='torus', color=color.rgba(0, 255, 200, 220), scale=Vec3(8, 8, 1.5), unlit=True)
    r.enabled = False; r._live = False; r._done = False
    RING_POOL.append(r)

for _ in range(20):
    try:
        a = Entity(model=ROCK_OBJ, shader=lit_with_shadows_shader, color=color.rgb(90, 80, 75))
    except:
        a = Entity(model='cube', shader=lit_with_shadows_shader, color=color.rgb(90, 80, 75))
    a.enabled = False; a._live = False; a._done = False
    ROCK_POOL.append(a)

# ═════════════════════════════════════════════════════════════
#  GPU PARTICLE SYSTEM
# ═════════════════════════════════════════════════════════════
_active_sparks = set()

class Spark(Entity):
    def __init__(self, pos, col, vel, life, scale_start):
        super().__init__(
            model='sphere', color=col, scale=scale_start, position=pos, unlit=True
        )
        self.vel = vel
        self.life = life
        self.max_life = life
        self.scale_start = scale_start

    def update(self):
        dt = ursina_time.dt
        self.position += self.vel * dt
        self.life -= dt
        if self.life <= 0:
            _active_sparks.discard(self)
            destroy(self)
            return
        
        # Fade scale and add drag
        frac = self.life / self.max_life
        self.scale = Vec3(1,1,1) * (self.scale_start * frac)
        self.vel *= (1 - dt * 2) # drag

def fx_explosion(pos, col):
    for _ in range(45):
        vel = Vec3(random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)).normalized() * random.uniform(5, 25)
        sp = Spark(pos, col, vel, life=random.uniform(0.4, 0.9), scale_start=random.uniform(0.2, 0.8))
        _active_sparks.add(sp)

def fx_exhaust(pos, is_boost):
    col = color.rgb(255, 100, 0) if is_boost else color.rgb(0, 180, 255)
    vel = Vec3(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(-15, -8))
    sp = Spark(pos, col, vel, life=random.uniform(0.15, 0.35), scale_start=0.4)
    _active_sparks.add(sp)

# ═════════════════════════════════════════════════════════════
#  HD USER INTERFACE (HUD)
# ═════════════════════════════════════════════════════════════
def _ui_txt(txt, px, py, col, sc=1.5):
    t = Text(txt, position=(px, py), scale=sc, color=col)
    t.font = 'VeraMono.ttf' # ensure fixed-width for alignment
    return t

u_hdr    = _ui_txt("HYPERION HD", -0.87,  0.47, color.rgb(255, 255, 255), 2.2)
u_score  = _ui_txt("SCORE : 0",   -0.87,  0.41, color.rgb(0, 255, 200), 1.8)
u_hp     = _ui_txt("HULL  : 100%",-0.87,  0.36, color.rgb(0, 255, 100))
u_spd    = _ui_txt("SPEED : 0",   -0.87,  0.31, color.rgb(255, 220, 0))
u_bst    = _ui_txt("BOOST : |||", -0.87,  0.26, color.rgb(0, 180, 255))
u_stat   = _ui_txt("[LIVE]",       0.30,  0.47, color.rgb(0, 255, 100))
u_imu    = _ui_txt("IMU R:0 P:0",  0.30,  0.42, color.rgb(180, 180, 255))

crosshair = Entity(model='quad', parent=camera.ui, scale=0.015, color=color.rgba(255,255,255,150))

# ═════════════════════════════════════════════════════════════
#  CORE GAME LOGIC
# ═════════════════════════════════════════════════════════════
class State:
    score = 0
    hp = 100.0
    boost = 100.0
    speed = 0.0
    dist = 0.0
    over = False
    
    # smoothing params
    sx = sy = sroll = spitch = 0.0
    
    # timers
    ring_t = 2.5
    rock_t = 4.0
    exh_t = 0.0
    
    # fx
    shake = 0.0

def _spawn_ring():
    for r in RING_POOL:
        if not r._live:
            r.enabled = True; r._live = True; r._done = False
            r.scale = random.uniform(8, 12)
            r.position = Vec3(random.uniform(-25, 25), random.uniform(-15, 15), ship.z + random.uniform(150, 200))
            r.rotation = Vec3(90, 0, 0)
            return

def _spawn_rock():
    for a in ROCK_POOL:
        if not a._live:
            a.enabled = True; a._live = True; a._done = False
            sz = random.uniform(4, 15)
            a.scale = Vec3(sz, sz, sz)
            a.position = Vec3(random.uniform(-30, 30), random.uniform(-20, 20), ship.z + random.uniform(180, 250))
            a.rotation = Vec3(random.uniform(0,360), random.uniform(0,360), random.uniform(0,360))
            return

_over_ui = None
def _trigger_gameover():
    global _over_ui
    State.over = True
    State.hp = 0
    _over_ui = Text(
        text=f"CRITICAL HULL FAILURE\nFINAL SCORE: {int(State.score):,}\n\n[R] RESTART SYSTEMS",
        origin=(0,0), scale=2.5, color=color.rgb(255,50,50), background=True
    )

def input(key):
    global _over_ui
    if key == 'r' and State.over:
        State.score = 0; State.hp = 100.0; State.boost = 100.0; State.speed = 0; State.dist = 0; State.over = False
        State.sx = State.sy = State.sroll = State.spitch = 0
        ship.position = Vec3(0,0,0)
        for e in RING_POOL + ROCK_POOL: e._live = False; e.enabled = False
        if _over_ui: destroy(_over_ui); _over_ui = None

_CAM_ORIG = Vec3(0, 4.0, -12)
_CAM_ROT  = Vec3(10, 0, 0)

def update():
    if State.over: return
    dt = ursina_time.dt
    if dt <= 0: return

    # 1. READ SERIAL DATA (Thread-safe)
    roll, pitch, yaw, force, emg = SENSORS.read()

    # 2. HUD UPDATES
    u_stat.text = "[LIVE SENSOR LINK]" if SENSORS.connected else "[NO SIGNAL]"
    u_stat.color = color.rgb(0, 255, 100) if SENSORS.connected else color.rgb(255, 50, 50)
    u_imu.text = f"IMU  R:{roll:+.1f}  P:{pitch:+.1f}"

    # 3. THRUSTERS & BOOST LOGIC (EMG + Force)
    is_boosting = (emg > 50) and (State.boost > 0)
    if is_boosting:
        t_spd = 80 + (emg / 100) * 40
        State.boost = max(0, State.boost - 30 * dt)
        camera.fov = camera.fov + (110 - camera.fov) * dt * 4
        c_eng = color.rgb(255, 120, 0)
        s_eng = 0.6
    else:
        t_spd = 25 + (force / 100) * 45
        State.boost = min(100, State.boost + 8 * dt)
        camera.fov = camera.fov + (85 - camera.fov) * dt * 4
        c_eng = color.rgb(0, 230, 255)
        s_eng = 0.35

    eng_L.color = eng_R.color = c_eng
    glow_L.color = glow_R.color = color.rgba(*c_eng.tint(0.5), 100)
    eng_L.scale = eng_R.scale = eng_L.scale_x + (s_eng - eng_L.scale_x) * dt * 8
    
    State.speed += (t_spd - State.speed) * dt * 3

    # 4. FLIGHT PHYSICS (IMU Roll/Pitch)
    tx = clamp(roll  / 45.0, -1, 1) * 28.0
    ty = clamp(pitch / 35.0, -1, 1) * 20.0
    
    State.sx += (tx - State.sx) * dt * 5
    State.sy += (ty - State.sy) * dt * 5
    State.sroll += (-roll * 0.7 - State.sroll) * dt * 6
    State.spitch += (pitch * 0.5 - State.spitch) * dt * 6

    ship.x = State.sx
    ship.y = State.sy
    ship.z += State.speed * dt
    ship.rotation = Vec3(State.spitch, 0, State.sroll)
    hull.rotation = Vec3(0, 180, -State.sroll * 0.5) # Dynamic visual banking on hull
    State.dist = ship.z

    # 5. SPAWNING
    State.ring_t -= dt
    if State.ring_t <= 0: _spawn_ring(); State.ring_t = random.uniform(1.8, 3.5)
    
    State.rock_t -= dt
    if State.rock_t <= 0: _spawn_rock(); State.rock_t = random.uniform(2.0, 4.5)

    # 6. COLLISION (Rings)
    for r in RING_POOL:
        if not r._live: continue
        r.rotation_z += 60 * dt
        if r.z < ship.z - 15:
            r._live = False; r.enabled = False; continue
        if not r._done:
            dx, dy, dz = abs(ship.x - r.x), abs(ship.y - r.y), abs(ship.z - r.z)
            rad = r.scale_x * 0.5
            if dz < 5 and dx < rad and dy < rad:
                r._done = True; r._live = False; r.enabled = False
                State.score += int(450 * max(1, State.speed/30))
                fx_explosion(r.world_position, color.rgba(0, 255, 200, 200))

    # 7. COLLISION (Asteroids)
    for a in ROCK_POOL:
        if not a._live: continue
        a.rotation_x += 20 * dt; a.rotation_y += 15 * dt
        if a.z < ship.z - 15:
            a._live = False; a.enabled = False; continue
        if not a._done:
            dx, dy, dz = abs(ship.x - a.x), abs(ship.y - a.y), abs(ship.z - a.z)
            rad = a.scale_x * 0.6
            if dz < 4 and dx < rad + 1.5 and dy < rad + 1.5:
                a._done = True; a._live = False; a.enabled = False
                State.hp -= 25
                State.shake = 0.6
                fx_explosion(ship.world_position, color.rgb(255, 80, 0))
                if State.hp <= 0:
                    _trigger_gameover()
                    return

    # 8. POST-PROCESS FX
    State.exh_t += dt
    if State.exh_t >= (0.015 if is_boosting else 0.05):
        State.exh_t = 0
        wp = ship.world_position
        fx_exhaust(wp + Vec3(-0.6, 0.2, -1.5), is_boosting)
        fx_exhaust(wp + Vec3( 0.6, 0.2, -1.5), is_boosting)

    if State.shake > 0:
        State.shake -= dt
        sp = 1.2
        camera.position = _CAM_ORIG + Vec3(random.uniform(-sp,sp), random.uniform(-sp,sp), 0)
    else:
        camera.position = _CAM_ORIG

    # 9. UI UPDATE
    u_score.text = f"SCORE: {int(State.score):,}"
    u_hp.text = f"HULL : {int(State.hp)}%"
    u_hp.color = color.rgb(0,255,100) if State.hp > 50 else color.rgb(255,100,50)
    u_spd.text = f"SPEED: {int(State.speed)} m/s"
    u_bst.text = "BOOST: " + "|" * int(State.boost / 5)
    u_bst.color = color.rgb(255,150,0) if is_boosting else color.rgb(0,200,255)

app.run()
