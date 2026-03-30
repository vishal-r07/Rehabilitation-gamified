# -*- coding: utf-8 -*-
"""
Diagnostic wrapper — run this to capture errors from ursina_flight.py
It writes full traceback to game_error.log
"""
import sys, os, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

log_path = os.path.join(os.path.dirname(__file__), 'game_error.log')

try:
    exec(open(os.path.join(os.path.dirname(__file__), 'games', 'ursina_flight.py'), encoding='utf-8').read())
except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(traceback.format_exc())
    print(f"ERROR captured to {log_path}")
    print(traceback.format_exc())
    raise
