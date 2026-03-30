import os, math, random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def generate_torus(filename, R=6.0, r=0.8, rings=36, segments=16):
    vertices = []
    for i in range(rings):
        u = i / rings * 2 * math.pi
        for j in range(segments):
            v = j / segments * 2 * math.pi
            x = (R + r * math.cos(v)) * math.cos(u)
            y = (R + r * math.cos(v)) * math.sin(u)
            z = r * math.sin(v)
            vertices.append((x,y,z))
    faces = []
    for i in range(rings):
        for j in range(segments):
            next_i = (i + 1) % rings
            next_j = (j + 1) % segments
            v1 = i * segments + j + 1
            v2 = next_i * segments + j + 1
            v3 = next_i * segments + next_j + 1
            v4 = i * segments + next_j + 1
            faces.append((v1, v2, v3, v4))
    with open(filename, 'w') as f:
        for v in vertices: f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in faces: f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n")

def generate_asteroid(filename, radius=2.0, rings=16, segments=16):
    vertices = []
    for i in range(rings + 1):
        v = i / rings
        phi = v * math.pi
        for j in range(segments):
            u = j / segments
            theta = u * 2 * math.pi
            # Add heavy noise to make it look like a jagged rock
            r_noise = radius + random.uniform(-radius*0.4, radius*0.3)
            x = r_noise * math.sin(phi) * math.cos(theta)
            y = r_noise * math.cos(phi)
            z = r_noise * math.sin(phi) * math.sin(theta)
            vertices.append((x,y,z))
    faces = []
    for i in range(rings):
        for j in range(segments):
            next_i = i + 1
            next_j = (j + 1) % segments
            v1 = i * segments + j + 1
            v2 = next_i * segments + j + 1
            v3 = next_i * segments + next_j + 1
            v4 = i * segments + next_j + 1
            if i == 0:
                faces.append((v1, v2, v3))
            elif i == rings - 1:
                faces.append((v1, v2, v4))
            else:
                faces.append((v1, v2, v3, v4))
    with open(filename, 'w') as f:
        for v in vertices: f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in faces:
            f.write("f " + " ".join(str(idx) for idx in face) + "\n")

def generate_spaceship(filename):
    # Sleek Sci-Fi Stealth interceptor (Procedural Mesh)
    v = [
        (0.0, 0.0, 6.0),     # 1: Nose tip
        (0.0, 0.5, 1.0),     # 2: Cockpit top
        (0.0, 0.2, 3.0),     # 3: Cockpit front glass
        (-0.5, -0.1, 2.0),   # 4: Left nose base
        (0.5, -0.1, 2.0),    # 5: Right nose base
        (-0.9, 0.2, -1.0),   # 6: Left fuselage top
        (0.9, 0.2, -1.0),    # 7: Right fuselage top
        (-0.7, -0.4, -2.0),  # 8: Left bottom
        (0.7, -0.4, -2.0),   # 9: Right bottom
        (0.0, 0.6, -3.0),    # 10: Engine top center
        (0.0, -0.5, -3.0),   # 11: Engine bottom center
        (-5.0, 0.0, -2.0),   # 12: Left Wing tip
        (5.0, 0.0, -2.0),    # 13: Right Wing tip
        (-1.2, 0.0, 1.0),    # 14: Left Wing root front
        (1.2, 0.0, 1.0),     # 15: Right Wing root front
        (-1.5, 0.0, -3.0),   # 16: Left Wing root back
        (1.5, 0.0, -3.0),    # 17: Right Wing root back
        (0.0, 1.8, -3.8),    # 18: Tail fin top
        (0.0, 0.6, -1.5),    # 19: Tail fin base front
    ]
    f_clean = [
        (1, 4, 3), (1, 3, 5),     # Nose top
        (1, 8, 4), (1, 5, 9), (1, 9, 8), # Nose bottom
        (3, 4, 14, 2), (3, 2, 15, 5), # cockpit window side
        (2, 14, 6, 19), (2, 19, 7, 15), # top fuselage
        (14, 12, 16), (15, 17, 13), # main wings
        (4, 8, 16, 14), (5, 15, 17, 9), # under wings / side
        (6, 16, 10), (7, 10, 17), # rear fuselage
        (10, 16, 8, 11), (10, 11, 9, 17), # engine block
        (19, 6, 10), (19, 10, 7), # tail base
        (19, 18, 10), # tail fin
        (8, 9, 11) # rear bottom
    ]
    with open(filename, 'w') as fh:
        for vert in v: fh.write(f"v {vert[0]:.4f} {vert[1]:.4f} {vert[2]:.4f}\n")
        for face in f_clean: fh.write("f " + " ".join(str(idx) for idx in face) + "\n")

if __name__ == '__main__':
    print("Generating High-Poly Procedural OBJs (100% Offline!)...")
    generate_torus(os.path.join(MODELS_DIR, 'torus.obj'))
    generate_asteroid(os.path.join(MODELS_DIR, 'asteroid.obj'))
    generate_spaceship(os.path.join(MODELS_DIR, 'spaceship.obj'))
    print("Assets generated successfully.")
