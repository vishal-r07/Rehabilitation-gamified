"""
==========================================================================
  HYPERION SQUADRON — Ultra-Realistic 3D Space Flight Rehabilitation Game
  Ursina Engine | IMU Serial Real-Time Sync | Hackathon Edition
==========================================================================
"""
import sys, os, random, math, threading

# Path so we can find sensors/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── All Ursina imports first (they define `time`, `clamp`, `color`, etc.) ─
from ursina import (
    Ursina, Entity, Sky, Text, Vec3, color, window, camera,
    DirectionalLight, AmbientLight, destroy, held_keys,
    application, invoke, clamp
)

# NOTE: Do NOT import stdlib `time` after this – Ursina shadows `time.dt`
# We access it via `application.time_step` or just read ursina's `time` object
from ursina import time as ursina_time   # Ursina's time module (has `.dt`)
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
_serial_client = None
_simulator     = None

def _generic_cb(imu_or_dict, force=None, emg=None):
    """Handles both (dict_with_force) and (imu_dict, force, emg) signatures."""
    if isinstance(imu_or_dict, dict) and 'force' in imu_or_dict:
        SENSORS.push(imu_or_dict, imu_or_dict['force'], imu_or_dict['emg'])
    else:
        SENSORS.push(imu_or_dict, force or 0, emg or 0)

if args.com == "TEST" or args.test:
    from sensors.simulator import FlightPatternSimulator
    _simulator = FlightPatternSimulator(_generic_cb)
    _simulator.start()
    SENSORS.connected = True
    print("[HYPERION] ▶ TEST MODE – simulated IMU")
else:
    from sensors.serial_client import SerialClient
    _serial_client = SerialClient()
    _serial_client.set_data_callback(_generic_cb)
    _serial_client.connect(args.com)
    print(f"[HYPERION] Connecting to {args.com}…")

# ═════════════════════════════════════════════════════════════
#  URSINA SETUP
# ═════════════════════════════════════════════════════════════
app = Ursina(
    title      = "HYPERION SQUADRON – ARM REHAB",
    borderless = False,
    vsync      = True,
    fullscreen = False,
    size       = (1280, 720),
)

window.color               = color.black
window.fps_counter.enabled = True
window.exit_button.visible = True

# Background sky
sky = Sky()
sky.color = color.rgb(3, 4, 18)

camera.fov = 85

# ── Lighting ──────────────────────────────────────────────────────────────
sun                = DirectionalLight()
sun.look_at(Vec3(1, -1.5, -1))
sun.color          = color.rgb(255, 240, 200)

fill               = DirectionalLight()
fill.look_at(Vec3(-1, 0.5, 1))
fill.color         = color.rgb(50, 80, 160)

ambient            = AmbientLight()
ambient.color      = color.rgb(15, 20, 50)

# ── Starfield (3 depth layers) ────────────────────────────────────────────
_star_layers = []            # list of (entity, speed_factor)
for depth, (cnt, spd, sz_range) in enumerate([
        (1200, 0.10, (0.04, 0.12)),   # far
        ( 400, 0.25, (0.10, 0.22)),   # mid
        ( 120, 0.55, (0.20, 0.45)),   # near
]):
    for _ in range(cnt):
        b = random.randint(190, 255)
        star = Entity(
            model    = 'sphere',
            scale    = random.uniform(*sz_range),
            position = Vec3(random.uniform(-300, 300),
                            random.uniform(-180, 180),
                            random.uniform(50, 800)),
            color    = color.rgb(b - random.randint(0,40), b - random.randint(0,20), b),
            unlit    = True,
        )
        _star_layers.append((star, spd))

# ── Nebula clouds ─────────────────────────────────────────────────────────
_nebula_palette = [
    color.rgba(70, 30, 160, 18),
    color.rgba(20, 70, 210, 15),
    color.rgba(160, 25, 90, 15),
    color.rgba(0, 130, 160, 12),
]
for _ in range(20):
    Entity(
        model        = 'sphere',
        scale        = random.uniform(50, 140),
        position     = Vec3(random.uniform(-250, 250),
                            random.uniform(-100, 100),
                            random.uniform(100, 700)),
        color        = random.choice(_nebula_palette),
        double_sided = True,
        unlit        = True,
    )

# ═════════════════════════════════════════════════════════════
#  PLAYER SHIP
# ═════════════════════════════════════════════════════════════
ship = Entity()   # pivot / root

# Fuselage
Entity(parent=ship, model='cube', color=color.rgb(38, 50, 90),
       scale=Vec3(0.65, 0.28, 2.8))
# Cockpit dome
Entity(parent=ship, model='cube', color=color.rgb(15, 155, 230),
       scale=Vec3(0.32, 0.26, 0.55), position=Vec3(0, 0.20, 0.60))
# Left wing
Entity(parent=ship, model='cube', color=color.rgb(50, 62, 105),
       scale=Vec3(2.2, 0.07, 0.85), position=Vec3(-0.85, 0, -0.35))
# Right wing
Entity(parent=ship, model='cube', color=color.rgb(50, 62, 105),
       scale=Vec3(2.2, 0.07, 0.85), position=Vec3( 0.85, 0, -0.35))
# Tail fin
Entity(parent=ship, model='cube', color=color.rgb(38, 50, 90),
       scale=Vec3(0.07, 0.52, 0.72), position=Vec3(0, 0.32, -1.05))
# Belly stripe (accent)
Entity(parent=ship, model='cube', color=color.rgb(0, 200, 255),
       scale=Vec3(0.08, 0.05, 2.6), position=Vec3(0, -0.12, 0), unlit=True)

# Engine glow orbs
eng_L = Entity(parent=ship, model='sphere',
               color=color.rgb(0, 210, 255), scale=0.24,
               position=Vec3(-0.32, 0, -1.42), unlit=True)
eng_R = Entity(parent=ship, model='sphere',
               color=color.rgb(0, 210, 255), scale=0.24,
               position=Vec3( 0.32, 0, -1.42), unlit=True)

# Camera: chase cam
camera.parent   = ship
camera.position = Vec3(0, 2.8, -9)
camera.rotation_x = 12

# ═════════════════════════════════════════════════════════════
#  RING & ASTEROID OBJECT POOLS
# ═════════════════════════════════════════════════════════════
RING_POOL = []
ROCK_POOL = []

for _ in range(25):
    r = Entity(model='torus', color=color.rgba(0, 230, 255, 200),
               scale=Vec3(6, 6, 1.3), unlit=False)
    r.enabled = False
    r._live = False
    r._done = False
    RING_POOL.append(r)

for _ in range(18):
    a = Entity(model='cube', color=color.rgb(128, 85, 55))
    a.enabled = False
    a._live = False
    a._done = False
    ROCK_POOL.append(a)

# ═════════════════════════════════════════════════════════════
#  PARTICLE ENGINE
# ═════════════════════════════════════════════════════════════
_active_sparks = set()   # use a set for O(1) discard

class Spark(Entity):
    def __init__(self, pos, col, vel, life=None):
        super().__init__(
            model    = 'sphere',
            color    = col,
            scale    = random.uniform(0.06, 0.28),
            position = pos,
            unlit    = True,
        )
        self.vel      = vel
        self.life     = life or random.uniform(0.3, 1.2)
        self.max_life = self.life

    def update(self):                          # called by Ursina every frame
        dt           = ursina_time.dt
        self.vel.y  -= 1.0 * dt               # gravity
        self.position += self.vel * dt
        self.life    -= dt
        if self.life <= 0:
            _active_sparks.discard(self)
            destroy(self)
            return
        frac         = self.life / self.max_life
        self.scale_x = frac * 0.25
        self.scale_y = self.scale_x
        self.scale_z = self.scale_x

def explode(pos, col, count=35):
    for _ in range(count):
        vel = Vec3(random.uniform(-5, 5),
                   random.uniform(-5, 5),
                   random.uniform(-5, 5))
        sp = Spark(pos, col, vel)
        _active_sparks.add(sp)

def exhaust_puff(pos, boosting):
    col = (color.rgb(255, 140, 20) if boosting
           else color.rgb(0, 140, 255))
    vel = Vec3(random.uniform(-0.3, 0.3),
               random.uniform(-0.3, 0.3),
               random.uniform(-9, -5))
    sp = Spark(pos, col, vel, life=random.uniform(0.15, 0.45))
    _active_sparks.add(sp)

# ═════════════════════════════════════════════════════════════
#  HUD
# ═════════════════════════════════════════════════════════════
def _txt(txt, x, y, c, sc=1.6):
    return Text(txt, position=(x, y), scale=sc, color=c)

hud_score  = _txt("SCORE: 0",        -0.87,  0.47, color.rgb(0, 255, 220), 2.0)
hud_health = _txt("HEALTH: 100%",    -0.87,  0.41, color.rgb(0, 255, 110))
hud_speed  = _txt("SPEED: 0 m/s",    -0.87,  0.36, color.rgb(255, 200, 0))
hud_boost  = _txt("BOOST: FULL",     -0.87,  0.31, color.rgb(0, 180, 255))
hud_imu    = _txt("IMU: --",          0.25,  0.47, color.rgb(160, 160, 255), 1.4)
hud_status = _txt("[*] CONNECTING",   0.25,  0.42, color.rgb(255, 200, 0),  1.4)
hud_level  = _txt("LEVEL 1",          0.25,  0.37, color.rgb(200, 200, 255), 1.4)

# Crosshair
Entity(model='quad', scale=0.025, color=color.rgba(0, 255, 200, 200),
       parent=camera.ui, z=-1)

# ═════════════════════════════════════════════════════════════
#  GAME STATE
# ═════════════════════════════════════════════════════════════
class GS:
    score     = 0
    health    = 100.0
    boost     = 100.0
    speed     = 0.0
    dist      = 0.0
    level     = 1
    game_over = False
    # smooth ship
    sx = sy = 0.0
    s_roll = s_pitch = 0.0
    # shake
    shake_t = 0.0
    shake_p = 0.0
    # spawn timers
    ring_t = 3.0
    rock_t = 5.5
    # exhaust timer
    exh_t  = 0.0

def _lerp(a, b, t):
    return a + (b - a) * clamp(t, 0, 1)

# ═════════════════════════════════════════════════════════════
#  SPAWN HELPERS
# ═════════════════════════════════════════════════════════════
def _spawn_ring():
    for r in RING_POOL:
        if not r._live:
            r.enabled  = True
            r._live    = True
            r._done    = False
            r.rotation = Vec3(90, 0, 0)
            r.scale    = random.uniform(5, 8)
            r.color    = color.rgb(0, random.randint(180, 255), 255)
            r.position = Vec3(
                random.uniform(-18, 18),
                random.uniform(-12, 12),
                ship.z + random.uniform(80, 130),
            )
            return

def _spawn_rock():
    for a in ROCK_POOL:
        if not a._live:
            a.enabled  = True
            a._live    = True
            a._done    = False
            sz = random.uniform(2, 7)
            a.scale    = Vec3(sz * random.uniform(0.7,1.3),
                               sz * random.uniform(0.7,1.3),
                               sz * random.uniform(0.7,1.3))
            a.rotation = Vec3(random.uniform(0,360),
                               random.uniform(0,360),
                               random.uniform(0,360))
            a.color    = color.rgb(random.randint(90,150),
                                   random.randint(60,100),
                                   random.randint(40,80))
            a.position = Vec3(
                random.uniform(-20, 20),
                random.uniform(-14, 14),
                ship.z + random.uniform(90, 150),
            )
            return

# ═════════════════════════════════════════════════════════════
#  GAME OVER OVERLAY
# ═════════════════════════════════════════════════════════════
_over_text = None

def _show_game_over():
    global _over_text
    GS.game_over = True
    GS.health    = 0
    _over_text   = Text(
        text       = f"✦ GAME OVER ✦\nSCORE: {int(GS.score):,}\n\nPress [R] to restart",
        origin     = (0, 0),
        scale      = 2.8,
        color      = color.rgb(255, 55, 55),
        background = True,
    )

def _reset():
    global _over_text
    GS.score     = 0
    GS.health    = 100.0
    GS.boost     = 100.0
    GS.speed     = 0.0
    GS.dist      = 0.0
    GS.level     = 1
    GS.game_over = False
    GS.sx = GS.sy = GS.s_roll = GS.s_pitch = 0.0
    GS.ring_t    = 3.0
    GS.rock_t    = 5.5
    ship.position = Vec3(0, 0, 0)
    for r in RING_POOL:
        r._live = False; r.enabled = False
    for a in ROCK_POOL:
        a._live = False; a.enabled = False
    if _over_text:
        destroy(_over_text)
        _over_text = None

# ═════════════════════════════════════════════════════════════
#  MAIN UPDATE   (Ursina calls this every frame)
# ═════════════════════════════════════════════════════════════
_CAM_BASE_POS = Vec3(0, 2.8, -9)
_CAM_BASE_ROT = Vec3(12, 0, 0)

def update():
    if GS.game_over:
        return

    dt = ursina_time.dt
    if dt <= 0:
        return

    # ── Read sensors ──────────────────────────────────────────
    roll, pitch, yaw, force, emg = SENSORS.read()

    # ── HUD: sensor status ───────────────────────────────────
    hud_imu.text    = f"IMU  R:{roll:+.1f}°  P:{pitch:+.1f}°"
    connected       = SENSORS.connected
    hud_status.text = "[LIVE]" if connected else "[OFFLINE]"
    hud_status.color = color.rgb(0, 255, 100) if connected else color.rgb(255, 60, 60)

    # ── Boost / Speed ─────────────────────────────────────────
    boosting = (emg > 50) and (GS.boost > 0)
    if boosting:
        tgt_speed  = 55 + (emg / 100) * 45
        GS.boost   = max(0.0, GS.boost - 28 * dt)
        camera.fov = _lerp(camera.fov, 108, dt * 3)
        eng_L.color = eng_R.color = color.rgb(255, 150, 0)
        eng_L.scale = eng_R.scale = _lerp(eng_L.scale_x, 0.52, dt * 7)
    else:
        tgt_speed  = 18 + (force / 100) * 35
        GS.boost   = min(100.0, GS.boost + 12 * dt)
        camera.fov = _lerp(camera.fov, 85, dt * 3)
        eng_L.color = eng_R.color = color.rgb(0, 210, 255)
        eng_L.scale = eng_R.scale = _lerp(eng_L.scale_x, 0.24, dt * 5)

    GS.speed = _lerp(GS.speed, tgt_speed, dt * 2.5)

    # ── IMU → ship XY + banking visuals ───────────────────────
    tx = clamp(roll  / 45.0, -1, 1) * 22.0
    ty = clamp(pitch / 35.0, -1, 1) * 16.0

    GS.sx      = _lerp(GS.sx,      tx,          dt * 4.5)
    GS.sy      = _lerp(GS.sy,      ty,          dt * 4.5)
    GS.s_roll  = _lerp(GS.s_roll,  -roll * 0.6, dt * 5)
    GS.s_pitch = _lerp(GS.s_pitch,  pitch * 0.4, dt * 5)

    ship.x        = GS.sx
    ship.y        = GS.sy
    ship.z       += GS.speed * dt
    ship.rotation  = Vec3(GS.s_pitch, 0, GS.s_roll)
    GS.dist        = ship.z
    GS.level       = 1 + int(GS.dist / 1000)

    # ── Recycle stars ─────────────────────────────────────────
    for star, spd in _star_layers:
        if star.z < ship.z - 150:
            star.z += 750
            star.x  = random.uniform(-300, 300)
            star.y  = random.uniform(-180, 180)

    # ── Spawn ─────────────────────────────────────────────────
    GS.ring_t -= dt
    if GS.ring_t <= 0:
        _spawn_ring()
        GS.ring_t = random.uniform(2.2, 3.8)

    GS.rock_t -= dt
    if GS.rock_t <= 0:
        _spawn_rock()
        GS.rock_t = random.uniform(2.8, 5.0)

    # ── Rings ─────────────────────────────────────────────────
    for r in RING_POOL:
        if not r._live:
            continue
        r.rotation_z += 45 * dt

        if r.z < ship.z - 8:
            r._live = False; r.enabled = False; continue

        if not r._done:
            dx   = abs(ship.x - r.x)
            dy   = abs(ship.y - r.y)
            dz   = abs(ship.z - r.z)
            half = r.scale_x * 0.52
            if dz < 3.5 and dx < half and dy < half:
                r._done = True
                r._live = False
                r.enabled = False
                pts         = int(300 * max(1, GS.speed / 25))
                GS.score   += pts
                explode(r.world_position, color.rgb(0, 230, 255), 45)

    # ── Asteroids ─────────────────────────────────────────────
    for a in ROCK_POOL:
        if not a._live:
            continue
        a.rotation_x += 12 * dt
        a.rotation_y += 18 * dt

        if a.z < ship.z - 8:
            a._live = False; a.enabled = False; continue

        if not a._done:
            dx  = abs(ship.x - a.x)
            dy  = abs(ship.y - a.y)
            dz  = abs(ship.z - a.z)
            rad = max(a.scale_x, a.scale_y) * 0.52
            if dz < 3.0 and dx < rad + 0.9 and dy < rad + 0.9:
                a._done  = True
                a._live  = False
                a.enabled = False
                GS.health -= 20
                GS.shake_p = 0.8
                GS.shake_t = 0.55
                explode(ship.world_position, color.rgb(255, 80, 20), 55)
                if GS.health <= 0:
                    _show_game_over()
                    return

    # ── Exhaust ───────────────────────────────────────────────
    GS.exh_t += dt
    threshold  = 0.02 if boosting else 0.06
    if GS.exh_t >= threshold:
        GS.exh_t = 0
        wp = ship.world_position
        exhaust_puff(wp + Vec3(-0.32, 0, -1.42), boosting)
        exhaust_puff(wp + Vec3( 0.32, 0, -1.42), boosting)

    # ── Screen shake ──────────────────────────────────────────
    if GS.shake_t > 0:
        GS.shake_t    -= dt
        ox = random.uniform(-GS.shake_p, GS.shake_p)
        oy = random.uniform(-GS.shake_p, GS.shake_p)
        camera.position = _CAM_BASE_POS + Vec3(ox, oy, 0)
        camera.rotation = _CAM_BASE_ROT + Vec3(oy * 6, ox * 6, 0)
    else:
        camera.position = _CAM_BASE_POS
        camera.rotation = _CAM_BASE_ROT

    # ── HUD refresh ───────────────────────────────────────────
    hud_score.text  = f"SCORE:   {int(GS.score):,}"
    hp              = int(GS.health)
    hud_health.text = f"HEALTH:  {hp}%"
    # green → yellow → red
    if hp > 60:
        hud_health.color = color.rgb(0, 255, 100)
    elif hp > 30:
        hud_health.color = color.rgb(255, 220, 0)
    else:
        hud_health.color = color.rgb(255, 60, 60)

    hud_speed.text  = f"SPEED:   {int(GS.speed)} m/s"
    bars            = "|" * int(GS.boost / 10)
    hud_boost.text  = f"BOOST:   {bars}"
    hud_boost.color = color.rgb(255, 150, 0) if boosting else color.rgb(0, 180, 255)
    hud_level.text  = f"LEVEL {GS.level}  DIST {int(GS.dist):,}m"


def input(key):
    if key == 'r' and GS.game_over:
        _reset()


app.run()
