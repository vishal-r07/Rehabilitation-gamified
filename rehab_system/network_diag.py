
import socket
import time
import sys

def check_ip(ip):
    print(f"Checking {ip}...")
    try:
        # Ping (fake ping using socket connect)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((ip, 81))
        if result == 0:
            print("✅ Port 81 is OPEN! (WebSocket Server Ready)")
            return True
        else:
            print(f"❌ Port 81 Closed (Error: {result})")
            return False
        s.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("running diagnostics...")
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("Enter ESP32 IP: ").strip()
    
    check_ip(ip)
    
    print("\nNetwork Interfaces:")
    print(socket.gethostbyname_ex(socket.gethostname()))
