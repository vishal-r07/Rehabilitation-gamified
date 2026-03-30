"""
==========================================================================
  HYPERION SQUADRON : PHOTOREALISTIC ASSET DOWNLOADER
  Downloads highly reliable Three.js CDN models for the Rehab Environment.
==========================================================================
"""
import os
import urllib.request

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ASSETS_DIR, "models")

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)

# Using the ultra-reliable MrDoob Three.js core repository for assets.
# A gracefully animated flying bird is infinitely better for rehab than a fighter jet.
ASSETS = {
    "bird.glb": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Flamingo.glb"
}

def download_assets():
    print(f"[ASSET-MGR] Downloading Calming GLB Models to {MODELS_DIR}...")
    for filename, url in ASSETS.items():
        filepath = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(filepath):
            try:
                print(f"[ASSET-MGR] DOWNLOADING: {filename}")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"[ASSET-MGR] ✔ SUCCESS: {filename}")
            except Exception as e:
                print(f"[ASSET-MGR] ❌ FAILED {filename}: {e}")
        else:
            print(f"[ASSET-MGR] CACHED: {filename}")

if __name__ == "__main__":
    download_assets()
