# HYPERION Clinical Portal Backend
# Lightweight SQLite + HTTP API to manage Patients and Therapy Sessions
import sqlite3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_FILE = os.path.join(os.path.dirname(__file__), "hyp_clinical.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            pid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            condition TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            sid INTEGER PRIMARY KEY AUTOINCREMENT,
            pid TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exercise_type TEXT,
            difficulty TEXT,
            duration INTEGER,
            score INTEGER,
            success_rate INTEGER,
            rings_collected INTEGER,
            rings_spawned INTEGER,
            max_speed REAL,
            FOREIGN KEY(pid) REFERENCES patients(pid)
        )
    ''')
    conn.commit()
    conn.close()

# Ensure DB exists
init_db()

class ClinicalAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Crucial for local dev bridging
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        try:
            if path == '/api/patients':
                c.execute("SELECT * FROM patients ORDER BY date_added DESC")
                rows = [dict(r) for r in c.fetchall()]
                self.send_json({"status": "ok", "data": rows})

            elif path.startswith('/api/sessions'):
                qs = parse_qs(parsed.query)
                pid = qs.get('pid', [None])[0]
                if pid:
                    c.execute("SELECT * FROM sessions WHERE pid=? ORDER BY date DESC", (pid,))
                    rows = [dict(r) for r in c.fetchall()]
                    self.send_json({"status": "ok", "data": rows})
                else:
                    self.send_json({"status": "error", "message": "Missing pid parameter"}, 400)
            else:
                self.send_json({"status": "error", "message": "Not found"}, 404)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, 500)
        finally:
            conn.close()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        parsed = urlparse(self.path)
        path = parsed.path
        
        try:
            body = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json({"status": "error", "message": "Invalid JSON"}, 400)
            return

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Must be set BEFORE creating cursor
        c = conn.cursor()

        try:
            if path == '/api/signup':
                pid = body.get('pid')
                name = body.get('name')
                age = body.get('age', 0)
                condition = body.get('condition', 'Rehabilitation')
                
                if not pid or not name:
                    self.send_json({"status": "error", "message": "Missing Patient ID or Name"}, 400)
                    return

                c.execute("SELECT * FROM patients WHERE pid=?", (pid,))
                if c.fetchone():
                    self.send_json({"status": "error", "message": "Patient ID already exists. Please login instead."}, 409)
                    return

                c.execute("INSERT INTO patients (pid, name, age, condition) VALUES (?, ?, ?, ?)", 
                         (pid, name, age, condition))
                conn.commit()
                
                c.execute("SELECT * FROM patients WHERE pid=?", (pid,))
                patient = dict(c.fetchone())
                self.send_json({"status": "ok", "message": "Patient registered successfully", "data": patient})

            elif path == '/api/login':
                pid = body.get('pid')
                
                if not pid:
                    self.send_json({"status": "error", "message": "Please enter a Patient ID"}, 400)
                    return

                c.execute("SELECT * FROM patients WHERE pid=?", (pid,))
                row = c.fetchone()
                if not row:
                    self.send_json({"status": "error", "message": "Patient ID not found. Please register first."}, 404)
                    return
                
                patient = dict(row)
                self.send_json({"status": "ok", "data": patient})

            elif path == '/api/sessions':
                pid = body.get('pid')
                # Optional details
                ex_type = body.get('exercise_type', 'unknown')
                diff = body.get('difficulty', 'medium')
                dur = body.get('duration', 0)
                score = body.get('score', 0)
                rate = body.get('success_rate', 0)
                collected = body.get('rings_collected', 0)
                spawned = body.get('rings_spawned', 0)
                max_spd = body.get('max_speed', 0.0)

                if not pid:
                     self.send_json({"status": "error", "message": "Missing pid"}, 400)
                     return

                c.execute('''
                    INSERT INTO sessions (pid, exercise_type, difficulty, duration, score, success_rate, rings_collected, rings_spawned, max_speed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pid, ex_type, diff, dur, score, rate, collected, spawned, max_spd))
                conn.commit()
                self.send_json({"status": "ok", "message": "Session recorded successfully", "sid": c.lastrowid})

            else:
                self.send_json({"status": "error", "message": "Not found"}, 404)

        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, 500)
        finally:
            conn.close()

if __name__ == "__main__":
    import sys
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    httpd = HTTPServer(("", PORT), ClinicalAPIHandler)
    print(f"[CLINICAL-DB] Database connected: {DB_FILE}")
    print(f"[CLINICAL-DB] API serving on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[CLINICAL-DB] Shutdown")
