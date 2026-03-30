"""
==========================================================================
  HYPERION SQUADRON : UDP -> WEBSOCKET BRIDGE
  Receives 60Hz UDP Telemetry from the Qt Launcher and broadcasts to 
  the ThreeJS WebGL frontend, avoiding any COM port locking conflicts.
==========================================================================
"""
import sys
import asyncio
import websockets
import json
import socket

# Thread-safe global for latest telemetry
LATEST_JSON = json.dumps({"r":0, "p":0, "y":0, "f":0, "e":0, "c":False})

class DatagramServerProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr):
        global LATEST_JSON
        LATEST_JSON = data.decode('utf-8')

connected_clients = set()

async def telemetry_handler(websocket, path):
    print(f"[UDP-WS-BRIDGE] Frontend Connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    # Send UDP events coming from frontend
    udp_return_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    async def listen_to_browser():
        try:
            async for message in websocket:
                # Forward everything back to python launcher via UDP
                udp_return_sock.sendto(message.encode('utf-8'), ("127.0.0.1", 9001))
        except websockets.exceptions.ConnectionClosed:
            pass

    async def stream_to_browser():
        try:
            while True:
                await websocket.send(LATEST_JSON)
                await asyncio.sleep(1/60)
        except websockets.exceptions.ConnectionClosed:
            pass

    try:
        await asyncio.gather(listen_to_browser(), stream_to_browser())
    finally:
        print(f"[UDP-WS-BRIDGE] Frontend Disconnected: {websocket.remote_address}")
        connected_clients.remove(websocket)
        udp_return_sock.close()

async def main():
    print("[UDP-WS-BRIDGE] Starting UDP Listener on 127.0.0.1:9000")
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DatagramServerProtocol(),
        local_addr=('127.0.0.1', 9000)
    )

    print("[UDP-WS-BRIDGE] Starting WebSocket Server on ws://localhost:8080")
    try:
        async with websockets.serve(telemetry_handler, "localhost", 8080):
            await asyncio.Future()  # run forever
    except Exception as e:
        print(f"[UDP-WS-BRIDGE] Failed to start WebSocket server: {e}")
    finally:
        transport.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[UDP-WS-BRIDGE] Shutting down.")
