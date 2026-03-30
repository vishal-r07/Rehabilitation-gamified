/**
 * Main Application Entry Point
 * Initializes all systems and starts the application
 */

class RehabiHandApp {
    constructor() {
        this.sceneManager = null;
        this.handModel = null;
        this.wsClient = null;
        this.animationController = null;
        this.gameEngine = null;
        this.gamificationSystem = null;
        this.feedbackSystem = null;

        this.init();
    }

    init() {
        console.log('[RehabiHand] Initializing application...');

        // Initialize Three.js scene
        this.sceneManager = new SceneManager('render-canvas');
        console.log('[RehabiHand] Scene manager initialized');

        // Create 3D hand model
        this.handModel = new HandModel(this.sceneManager.getScene());
        console.log('[RehabiHand] Hand model created');

        // Initialize WebSocket client
        this.wsClient = new WebSocketClient();
        this.wsClient.onConnect = () => this.onESP32Connected();
        this.wsClient.onDisconnect = () => this.onESP32Disconnected();
        this.wsClient.onData = (data) => this.onSensorData(data);
        console.log('[RehabiHand] WebSocket client initialized');

        // Initialize animation controller
        this.animationController = new AnimationController(this.handModel, this.wsClient);
        console.log('[RehabiHand] Animation controller initialized');

        // Initialize game engine
        this.gameEngine = new GameEngine(this.handModel, this.wsClient, this.sceneManager);
        console.log('[RehabiHand] Game engine initialized');

        // Initialize gamification system
        this.gamificationSystem = new GamificationSystem();
        this.gamificationSystem.updateProgressUI();
        console.log('[RehabiHand] Gamification system initialized');

        // Initialize feedback system
        this.feedbackSystem = new FeedbackSystem(this.wsClient);
        console.log('[RehabiHand] Feedback system initialized');

        // Setup UI event listeners
        this.setupUI();

        // Add floating particles for aesthetics
        this.sceneManager.addParticles();

        console.log('[RehabiHand] ✅ Application ready!');
        this.feedbackSystem.showToast('Welcome to RehabiHand! Connect your ESP32 to begin.', 'info');
    }

    setupUI() {
        // Connect button
        const connectBtn = document.getElementById('connect-btn');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => {
                if (!this.wsClient.connected) {
                    this.wsClient.connect();
                } else {
                    this.wsClient.disconnect();
                }
            });
        }

        // Settings toggle
        const settingsToggle = document.getElementById('settings-toggle');
        const settingsPanel = document.getElementById('settings-panel');
        if (settingsToggle && settingsPanel) {
            settingsToggle.addEventListener('click', () => {
                settingsPanel.classList.toggle('hidden');
            });
        }

        // Calibrate button
        const calibrateBtn = document.getElementById('calibrate-btn');
        if (calibrateBtn) {
            calibrateBtn.addEventListener('click', () => {
                this.wsClient.calibrate();
                this.feedbackSystem.showToast('Calibration started on ESP32', 'info');
            });
        }

        // Difficulty selector
        const difficultySelect = document.getElementById('difficulty');
        if (difficultySelect) {
            difficultySelect.addEventListener('change', (e) => {
                this.gameEngine.difficulty = e.target.value;
                this.feedbackSystem.showToast(`Difficulty set to ${e.target.value}`, 'success');
            });
        }

        // Quality selector
        const qualitySelect = document.getElementById('quality');
        if (qualitySelect) {
            qualitySelect.addEventListener('change', (e) => {
                this.updateQuality(e.target.value);
            });
        }

        // Auto-save IP address
        const ipInput = document.getElementById('esp32-ip');
        if (ipInput) {
            const savedIP = localStorage.getItem('esp32_ip');
            if (savedIP) {
                ipInput.value = savedIP;
            }

            ipInput.addEventListener('change', (e) => {
                localStorage.setItem('esp32_ip', e.target.value);
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Press 'C' to connect/disconnect
            if (e.key === 'c' || e.key === 'C') {
                if (!this.wsClient.connected) {
                    this.wsClient.connect();
                } else {
                    this.wsClient.disconnect();
                }
            }

            // Press 'R' to reset hand pose
            if (e.key === 'r' || e.key === 'R') {
                this.handModel.resetPose();
            }

            // Press 'ESC' to exit game
            if (e.key === 'Escape' && this.gameEngine.isPlaying) {
                this.gameEngine.exitGame();
            }
        });
    }

    updateQuality(quality) {
        const pixelRatios = {
            low: 1,
            medium: 1.5,
            high: 2,
            ultra: 2.5
        };

        this.sceneManager.renderer.setPixelRatio(pixelRatios[quality] || 2);
        this.feedbackSystem.showToast(`Quality set to ${quality}`, 'success');
    }

    onESP32Connected() {
        console.log('[RehabiHand] ESP32 connected!');
        this.feedbackSystem.showToast('ESP32 connected successfully!', 'success');
        this.feedbackSystem.playSuccess();

        // Start animation controller
        this.animationController.start();

        // Demo hand wave
        setTimeout(() => {
            this.handModel.animate('wave', 3000);
        }, 1000);
    }

    onESP32Disconnected() {
        console.log('[RehabiHand] ESP32 disconnected');
        this.feedbackSystem.showToast('ESP32 disconnected', 'warning');

        // Stop animation controller
        this.animationController.stop();

        // Reset hand to neutral
        this.handModel.resetPose();
    }

    onSensorData(data) {
        // This is called every time new sensor data arrives (50ms intervals)
        // Data is already being used by animation controller

        // Check for form warnings and play sounds
        if (data.formWarning && data.formWarning !== this.lastWarning) {
            this.feedbackSystem.playError();
            this.lastWarning = data.formWarning;
        } else if (data.formWarning === '' && this.lastWarning) {
            this.lastWarning = '';
        }
    }
}

// Initialize application when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.app = new RehabiHandApp();
});

// Prevent page reload on accidental gestures
window.addEventListener('beforeunload', (e) => {
    if (window.app && window.app.wsClient && window.app.wsClient.connected) {
        e.preventDefault();
        e.returnValue = 'Are you sure you want to leave? Your ESP32 connection will be lost.';
    }
});

console.log('[RehabiHand] Application script loaded. Waiting for DOM...');
