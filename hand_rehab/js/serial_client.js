/**
 * WebSocket Client for ESP32 Communication
 * Handles real-time sensor data streaming from ESP32
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.latency = 0;
        this.lastPingTime = 0;
        
        // Sensor data
        this.sensorData = {
            force: 0,                    // Force sensor (0-4095)
            emg: 0,                      // EMG sensor (0-4095)
            roll: 0,                     // IMU roll (degrees)
            pitch: 0,                    // IMU pitch (degrees)
            yaw: 0,                      // IMU yaw (degrees)
            accel: 0,                    // Acceleration magnitude
            curlCount: 0,                // Total curls
            goodFormCurls: 0,            // Perfect form curls
            thresholdHigh: 0,            // Calibrated high threshold
            thresholdLow: 0,             // Calibrated low threshold
            formWarning: '',             // Form warning message
            timestamp: 0                 // Timestamp
        };
        
        // Callbacks
        this.onConnect = null;
        this.onDisconnect = null;
        this.onData = null;
        this.onError = null;
    }
    
    /**
     * Connect to ESP32 WebSocket server
     * @param {string} ip - ESP32 IP address
     * @param {number} port - WebSocket port (default: 81)
     */
    connect(ip = null, port = 81) {
        // Get IP from input or default
        if (!ip) {
            const ipInput = document.getElementById('esp32-ip');
            ip = ipInput ? ipInput.value : '192.168.1.100';
        }
        
        const wsUrl = `ws://${ip}:${port}`;
        console.log(`[WebSocket] Connecting to ${wsUrl}...`);
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (error) => this.handleError(error);
            this.ws.onclose = () => this.handleClose();
            
        } catch (error) {
            console.error('[WebSocket] Connection failed:', error);
            this.updateConnectionUI(false);
            if (this.onError) this.onError(error);
        }
    }
    
    handleOpen() {
        console.log('[WebSocket] Connected!');
        this.connected = true;
        this.reconnectAttempts = 0;
        this.updateConnectionUI(true);
        
        if (this.onConnect) this.onConnect();
    }
    
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Parse ESP32 JSON format
            // {"f":1234,"e":567,"r":12.3,"p":45.6,"y":78.9,"a":2.1,"tc":5,"gc":4,"th":2500,"tl":800,"w":""}
            this.sensorData = {
                force: data.f || 0,
                emg: data.e || 0,
                roll: data.r || 0,
                pitch: data.p || 0,
                yaw: data.y || 0,
                accel: data.a || 0,
                curlCount: data.tc || 0,
                goodFormCurls: data.gc || 0,
                thresholdHigh: data.th || 0,
                thresholdLow: data.tl || 0,
                formWarning: data.w || '',
                timestamp: Date.now()
            };
            
            // Calculate latency
            if (this.lastPingTime > 0) {
                this.latency = Date.now() - this.lastPingTime;
            }
            this.lastPingTime = Date.now();
            
            // Update UI
            this.updateSensorUI();
            
            // Callback
            if (this.onData) this.onData(this.sensorData);
            
        } catch (error) {
            console.error('[WebSocket] Parse error:', error);
        }
    }
    
    handleError(error) {
        console.error('[WebSocket] Error:', error);
        this.updateConnectionUI(false);
        if (this.onError) this.onError(error);
    }
    
    handleClose() {
        console.log('[WebSocket] Disconnected');
        this.connected = false;
        this.updateConnectionUI(false);
        
        if (this.onDisconnect) this.onDisconnect();
        
        // Auto-reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
            console.log(`[WebSocket] Reconnecting in ${delay}ms...`);
            
            setTimeout(() => {
                this.reconnectAttempts++;
                this.connect();
            }, delay);
        } else {
            console.log('[WebSocket] Max reconnect attempts reached');
        }
    }
    
    /**
     * Update connection status UI
     */
    updateConnectionUI(isConnected) {
        const dot = document.getElementById('connection-dot');
        const text = document.getElementById('connection-text');
        const btn = document.getElementById('connect-btn');
        
        if (dot) {
            dot.className = isConnected ? 'dot connected' : 'dot disconnected';
        }
        
        if (text) {
            text.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
        
        if (btn) {
            btn.textContent = isConnected ? 'Disconnect' : 'Connect ESP32';
            btn.onclick = () => isConnected ? this.disconnect() : this.connect();
        }
    }
    
    /**
     * Update sensor data UI
     */
    updateSensorUI() {
        // IMU status
        const imuStatus = document.getElementById('imu-status');
        if (imuStatus) {
            const imuConnected = Math.abs(this.sensorData.roll) > 0 || 
                               Math.abs(this.sensorData.pitch) > 0 || 
                               Math.abs(this.sensorData.yaw) > 0;
            imuStatus.textContent = imuConnected ? '✓' : '✗';
            imuStatus.style.color = imuConnected ? 'var(--success)' : 'var(--danger)';
        }
        
        // EMG value (normalized to percentage)
        const emgValue = document.getElementById('emg-value');
        if (emgValue) {
            const emgPercent = Math.round((this.sensorData.emg / 4095) * 100);
            emgValue.textContent = `${emgPercent}%`;
        }
        
        // Latency
        const latency = document.getElementById('latency');
        if (latency) {
            latency.textContent = `${this.latency}ms`;
            latency.style.color = this.latency < 100 ? 'var(--success)' : 'var(--warning)';
        }
    }
    
    /**
     * Disconnect from ESP32
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
        this.updateConnectionUI(false);
    }
    
    /**
     * Send calibration command
     */
    calibrate() {
        if (this.connected && this.ws) {
            this.ws.send(JSON.stringify({ cmd: 'calibrate' }));
            console.log('[WebSocket] Calibration command sent');
        }
    }
    
    /**
     * Get normalized sensor values (0-1 range)
     */
    getNormalizedData() {
        return {
            // Finger simulation based on force sensor
            // In future, replace with individual flex sensor values
            thumbBend: Math.min((this.sensorData.force / this.sensorData.thresholdHigh), 1.0),
            indexBend: Math.min((this.sensorData.force / this.sensorData.thresholdHigh) * 0.9, 1.0),
            middleBend: Math.min((this.sensorData.force / this.sensorData.thresholdHigh) * 0.95, 1.0),
            ringBend: Math.min((this.sensorData.force / this.sensorData.thresholdHigh) * 0.85, 1.0),
            pinkyBend: Math.min((this.sensorData.force / this.sensorData.thresholdHigh) * 0.8, 1.0),
            
            // Hand orientation (radians)
            wristRoll: (this.sensorData.roll * Math.PI) / 180,
            wristPitch: (this.sensorData.pitch * Math.PI) / 180,
            wristYaw: (this.sensorData.yaw * Math.PI) / 180,
            
            // Muscle activation (0-1)
            muscleActivation: this.sensorData.emg / 4095,
            
            // Form data
            formWarning: this.sensorData.formWarning,
            isGoodForm: this.sensorData.formWarning === ''
        };
    }
}

// Export for use in other modules
window.WebSocketClient = WebSocketClient;
