/**
 * USB Serial Client for Vega Aries Communication
 * Handles real-time sensor data streaming via Web Serial API
 */

class SerialClient {
    constructor() {
        this.port = null;
        this.reader = null;
        this.streamClosed = null;
        this.connected = false;
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
     * Connect to Vega Aries via Web Serial API
     */
    async connect() {
        try {
            this.port = await navigator.serial.requestPort();
            await this.port.open({ baudRate: 115200 });

            this.handleOpen();
            this.readLoop();
        } catch (error) {
            console.error('[Serial] Connection failed:', error);
            this.updateConnectionUI(false);
            if (this.onError) this.onError(error);
        }
    }

    handleOpen() {
        console.log('[Serial] Connected!');
        this.connected = true;
        this.updateConnectionUI(true);

        if (this.onConnect) this.onConnect();
    }

    async readLoop() {
        const textDecoder = new TextDecoderStream();
        this.streamClosed = this.port.readable.pipeTo(textDecoder.writable);
        this.reader = textDecoder.readable
            .pipeThrough(new TransformStream(new this.LineBreakTransformer()))
            .getReader();

        try {
            while (true) {
                const { value, done } = await this.reader.read();
                if (done) break;
                if (value) this.handleMessage(value);
            }
        } catch (error) {
            this.handleError(error);
        } finally {
            this.handleClose();
        }
    }

    LineBreakTransformer = class {
        constructor() {
            this.chunks = "";
        }
        transform(chunk, controller) {
            this.chunks += chunk;
            const lines = this.chunks.split('\n');
            this.chunks = lines.pop(); // Keep incomplete line
            lines.forEach(line => controller.enqueue(line));
        }
        flush(controller) {
            if (this.chunks !== "") controller.enqueue(this.chunks);
        }
    }

    handleMessage(messageLine) {
        try {
            const data = JSON.parse(messageLine);

            // Parse Vega Aries JSON format
            this.sensorData = {
                force: data.sensorValue || data.f || 0,
                emg: data.emgValue || data.e || 0,
                roll: data.roll || data.r || 0,
                pitch: data.pitch || data.p || 0,
                yaw: data.yaw || data.y || 0,
                accel: data.accel || data.a || 0,
                curlCount: data.curlCount || data.tc || 0,
                goodFormCurls: data.goodFormCurls || data.gc || 0,
                thresholdHigh: data.th || 0,
                thresholdLow: data.tl || 0,
                formWarning: data.formWarning || data.w || '',
                timestamp: Date.now()
            };

            // Calculate latency mock
            if (this.lastPingTime > 0) {
                this.latency = Date.now() - this.lastPingTime;
            }
            this.lastPingTime = Date.now();

            this.updateSensorUI();

            if (this.onData) this.onData(this.sensorData);

        } catch (error) {
            // Ignore format errors for simple text prints
        }
    }

    handleError(error) {
        console.error('[Serial] Error:', error);
        this.updateConnectionUI(false);
        if (this.onError) this.onError(error);
    }

    handleClose() {
        console.log('[Serial] Disconnected');
        this.connected = false;
        this.updateConnectionUI(false);

        if (this.onDisconnect) this.onDisconnect();
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
            text.textContent = isConnected ? 'Connected (USB)' : 'Disconnected';
        }

        if (btn) {
            btn.textContent = isConnected ? 'Disconnect' : 'Connect Vega Aries';
            btn.onclick = () => isConnected ? this.disconnect() : this.connect();
        }
    }

    /**
     * Update sensor data UI
     */
    updateSensorUI() {
        const imuStatus = document.getElementById('imu-status');
        if (imuStatus) {
            const imuConnected = Math.abs(this.sensorData.roll) > 0 ||
                Math.abs(this.sensorData.pitch) > 0 ||
                Math.abs(this.sensorData.yaw) > 0;
            imuStatus.textContent = imuConnected ? '✓' : '✗';
            imuStatus.style.color = imuConnected ? 'var(--success)' : 'var(--danger)';
        }

        const emgValue = document.getElementById('emg-value');
        if (emgValue) {
            const emgPercent = Math.round((this.sensorData.emg / 4095) * 100);
            emgValue.textContent = `${emgPercent}%`;
        }

        const latency = document.getElementById('latency');
        if (latency) {
            latency.textContent = `${this.latency}ms`;
            latency.style.color = 'var(--success)';
        }
    }

    /**
     * Disconnect from Serial Port
     */
    async disconnect() {
        if (this.reader) {
            await this.reader.cancel();
            await this.streamClosed.catch(() => { });
            this.reader = null;
        }
        if (this.port) {
            await this.port.close();
            this.port = null;
        }
        this.connected = false;
        this.updateConnectionUI(false);
        if (this.onDisconnect) this.onDisconnect();
    }

    /**
     * Send calibration command (stub for unidirectional serial for now, or bi-directional writes)
     */
    async calibrate() {
        if (this.connected && this.port && this.port.writable) {
            const encoder = new TextEncoder();
            const writer = this.port.writable.getWriter();
            await writer.write(encoder.encode("calibrate\n"));
            writer.releaseLock();
            console.log('[Serial] Calibration command sent');
        }
    }

    /**
     * Get normalized sensor values (0-1 range)
     */
    getNormalizedData() {
        return {
            thumbBend: Math.min((this.sensorData.force / 4095), 1.0),
            indexBend: Math.min((this.sensorData.force / 4095) * 0.9, 1.0),
            middleBend: Math.min((this.sensorData.force / 4095) * 0.95, 1.0),
            ringBend: Math.min((this.sensorData.force / 4095) * 0.85, 1.0),
            pinkyBend: Math.min((this.sensorData.force / 4095) * 0.8, 1.0),

            wristRoll: (this.sensorData.roll * Math.PI) / 180,
            wristPitch: (this.sensorData.pitch * Math.PI) / 180,
            wristYaw: (this.sensorData.yaw * Math.PI) / 180,

            muscleActivation: this.sensorData.emg / 4095,

            formWarning: this.sensorData.formWarning,
            isGoodForm: this.sensorData.formWarning === ''
        };
    }
}

window.WebSocketClient = SerialClient;
