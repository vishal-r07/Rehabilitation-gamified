/*
 * ESP32 Bicep Trainer - WebSocket Value Monitor
 * This adds WiFi WebSocket server for real-time value graphing
 * Run this HTML page in a browser to see live sensor values
 */

#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>

// WiFi credentials - UPDATE THESE!
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

WebServer server(80);
WebSocketsServer webSocket = WebSocketsServer(81);

// External variables from main firmware (declare as extern)
extern int rawValue;
extern int smoothedValue;
extern int emgRaw;
extern int emgSmoothed;
extern float roll, pitch, yaw;
extern float accelMagnitude;
extern int curlCount, goodFormCurls;
extern bool imuConnected, isCalibrated;
extern int THRESHOLD_HIGH, THRESHOLD_LOW;
extern String formWarning;

// HTML page for WebSocket client
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML>
<html>
<head>
    <title>ESP32 Bicep Trainer Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #0a0a0f; 
            color: #fff; 
            padding: 20px;
            margin: 0;
        }
        h1 { color: #00f5ff; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0,245,255,0.2);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }
        .card h3 { color: #00f5ff; margin-top: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .stat {
            background: rgba(0,245,255,0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value { font-size: 28px; font-weight: bold; color: #00f5ff; }
        .stat-label { font-size: 12px; color: #888; text-transform: uppercase; }
        canvas { 
            width: 100%; 
            height: 150px; 
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
        }
        .warning { background: rgba(255,100,100,0.2); border-color: #ff6464; }
        .good { background: rgba(100,255,100,0.2); border-color: #64ff64; }
        #status { 
            padding: 10px; 
            text-align: center; 
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .connected { background: rgba(0,255,100,0.2); color: #0f0; }
        .disconnected { background: rgba(255,0,0,0.2); color: #f00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏋️ ESP32 Bicep Trainer Monitor</h1>
        <div id="status" class="disconnected">Connecting...</div>
        
        <div class="card">
            <h3>📊 Live Sensors</h3>
            <div class="grid">
                <div class="stat">
                    <div class="stat-value" id="force">0</div>
                    <div class="stat-label">Force Sensor</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="emg">0</div>
                    <div class="stat-label">EMG Signal</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="curls">0/0</div>
                    <div class="stat-label">Curls (Good/Total)</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="threshold">-/-</div>
                    <div class="stat-label">Thresholds (H/L)</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🎯 IMU Orientation</h3>
            <div class="grid">
                <div class="stat">
                    <div class="stat-value" id="roll">0°</div>
                    <div class="stat-label">Roll</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="pitch">0°</div>
                    <div class="stat-label">Pitch</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="yaw">0°</div>
                    <div class="stat-label">Yaw</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="accel">0</div>
                    <div class="stat-label">Accel (m/s²)</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>📈 Force Sensor Graph</h3>
            <canvas id="forceChart"></canvas>
        </div>

        <div class="card">
            <h3>💪 EMG Signal Graph</h3>
            <canvas id="emgChart"></canvas>
        </div>

        <div class="card" id="warningCard">
            <h3>⚠️ Form Warning</h3>
            <div id="warning" style="font-size: 20px; text-align: center;">None</div>
        </div>
    </div>

    <script>
        let forceData = new Array(200).fill(0);
        let emgData = new Array(200).fill(0);
        
        const forceCanvas = document.getElementById('forceChart');
        const emgCanvas = document.getElementById('emgChart');
        const forceCtx = forceCanvas.getContext('2d');
        const emgCtx = emgCanvas.getContext('2d');

        function resizeCanvas() {
            forceCanvas.width = forceCanvas.offsetWidth;
            forceCanvas.height = 150;
            emgCanvas.width = emgCanvas.offsetWidth;
            emgCanvas.height = 150;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        function drawGraph(ctx, data, color, maxVal = 4095) {
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            const step = ctx.canvas.width / data.length;
            data.forEach((val, i) => {
                const x = i * step;
                const y = ctx.canvas.height - (val / maxVal * ctx.canvas.height);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
            
            // Draw current value line
            ctx.strokeStyle = 'rgba(255,255,255,0.3)';
            ctx.setLineDash([5, 5]);
            const lastY = ctx.canvas.height - (data[data.length-1] / maxVal * ctx.canvas.height);
            ctx.beginPath();
            ctx.moveTo(0, lastY);
            ctx.lineTo(ctx.canvas.width, lastY);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        let ws;
        function connect() {
            ws = new WebSocket('ws://' + window.location.hostname + ':81');
            
            ws.onopen = () => {
                document.getElementById('status').className = 'connected';
                document.getElementById('status').textContent = '✅ Connected to ESP32';
            };
            
            ws.onclose = () => {
                document.getElementById('status').className = 'disconnected';
                document.getElementById('status').textContent = '❌ Disconnected - Reconnecting...';
                setTimeout(connect, 2000);
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Update values
                    document.getElementById('force').textContent = data.force || 0;
                    document.getElementById('emg').textContent = data.emg || 0;
                    document.getElementById('curls').textContent = 
                        (data.goodCurls || 0) + '/' + (data.totalCurls || 0);
                    document.getElementById('threshold').textContent = 
                        (data.threshHigh || '-') + '/' + (data.threshLow || '-');
                    
                    document.getElementById('roll').textContent = (data.roll || 0).toFixed(1) + '°';
                    document.getElementById('pitch').textContent = (data.pitch || 0).toFixed(1) + '°';
                    document.getElementById('yaw').textContent = (data.yaw || 0).toFixed(1) + '°';
                    document.getElementById('accel').textContent = (data.accel || 0).toFixed(1);
                    
                    // Update warning
                    const warning = data.warning || 'None';
                    document.getElementById('warning').textContent = warning;
                    const warnCard = document.getElementById('warningCard');
                    warnCard.className = warning !== 'None' && warning !== '' ? 'card warning' : 'card good';
                    
                    // Update graphs
                    forceData.push(data.force || 0);
                    forceData.shift();
                    emgData.push(data.emg || 0);
                    emgData.shift();
                    
                    drawGraph(forceCtx, forceData, '#00f5ff');
                    drawGraph(emgCtx, emgData, '#ff00ff');
                    
                } catch(e) { console.log('Parse error:', e); }
            };
        }
        connect();
    </script>
</body>
</html>
)rawliteral";

void setupWebSocket() {
  // Connect to WiFi
  Serial.println("\n[WIFI] Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected!");
    Serial.print("[WIFI] IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.println("[WIFI] Open this IP in browser for live graphs!");
    
    // Serve HTML page
    server.on("/", []() {
      server.send(200, "text/html", index_html);
    });
    server.begin();
    
    // Start WebSocket server
    webSocket.begin();
    webSocket.onEvent([](uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
      if (type == WStype_CONNECTED) {
        Serial.printf("[WS] Client #%u connected\n", num);
      } else if (type == WStype_DISCONNECTED) {
        Serial.printf("[WS] Client #%u disconnected\n", num);
      }
    });
    
    Serial.println("[WS] WebSocket server started on port 81");
  } else {
    Serial.println("\n[WIFI] Failed to connect! WebSocket disabled.");
  }
}

void loopWebSocket() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  server.handleClient();
  webSocket.loop();
  
  // Broadcast data at ~20Hz
  static unsigned long lastWsBroadcast = 0;
  if (millis() - lastWsBroadcast >= 50) {
    lastWsBroadcast = millis();
    
    String json = "{";
    json += "\"force\":" + String(smoothedValue) + ",";
    json += "\"emg\":" + String(emgSmoothed) + ",";
    json += "\"roll\":" + String(roll, 1) + ",";
    json += "\"pitch\":" + String(pitch, 1) + ",";
    json += "\"yaw\":" + String(yaw, 1) + ",";
    json += "\"accel\":" + String(accelMagnitude, 1) + ",";
    json += "\"totalCurls\":" + String(curlCount) + ",";
    json += "\"goodCurls\":" + String(goodFormCurls) + ",";
    json += "\"threshHigh\":" + String(THRESHOLD_HIGH) + ",";
    json += "\"threshLow\":" + String(THRESHOLD_LOW) + ",";
    json += "\"warning\":\"" + formWarning + "\"";
    json += "}";
    
    webSocket.broadcastTXT(json);
  }
}
