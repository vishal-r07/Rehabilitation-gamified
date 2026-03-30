/**
 * Feedback System - Visual and Audio Feedback
 */

class FeedbackSystem {
    constructor(websocketClient) {
        this.ws = websocketClient;
        this.audioContext = null;
        this.sounds = {};

        // Try to initialize audio
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.setupSounds();
        } catch (e) {
            console.warn('[Audio] Audio context not available');
        }

        this.updateLoop();
    }

    /**
     * Setup procedural sounds
     */
    setupSounds() {
        // Create simple beep sounds
        this.sounds.success = () => this.playBeep(800, 0.1, 'sine');
        this.sounds.error = () => this.playBeep(200, 0.2, 'sawtooth');
        this.sounds.levelUp = () => {
            this.playBeep(600, 0.1, 'sine');
            setTimeout(() => this.playBeep(800, 0.15, 'sine'), 100);
            setTimeout(() => this.playBeep(1000, 0.2, 'sine'), 200);
        };
    }

    /**
     * Play a simple beep tone
     */
    playBeep(frequency, duration, type = 'sine') {
        if (!this.audioContext) return;

        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        oscillator.frequency.value = frequency;
        oscillator.type = type;

        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);

        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
    }

    /**
     * Update visual form indicators
     */
    updateLoop() {
        const data = this.ws.getNormalizedData();

        // Update form indicators
        const goodIndicator = document.getElementById('form-good');
        const warningIndicator = document.getElementById('form-warning');
        const warningText = document.getElementById('warning-text');

        if (data.isGoodForm) {
            if (goodIndicator) goodIndicator.style.display = 'flex';
            if (warningIndicator) warningIndicator.style.display = 'none';
        } else {
            if (goodIndicator) goodIndicator.style.display = 'none';
            if (warningIndicator) warningIndicator.style.display = 'flex';

            // Update warning text
            const warnings = {
                'WRIST_TWIST': '⚠️ Keep wrist straight!',
                'ELBOW_FLARE': '⚠️ Keep elbow close!',
                'JERKY_MOVE': '⚠️ Move smoothly!'
            };

            if (warningText && data.formWarning) {
                warningText.textContent = warnings[data.formWarning] || data.formWarning;
            }
        }

        // Continue loop
        requestAnimationFrame(() => this.updateLoop());
    }

    /**
     * Play success sound
     */
    playSuccess() {
        if (this.sounds.success) {
            this.sounds.success();
        }
    }

    /**
     * Play error sound
     */
    playError() {
        if (this.sounds.error) {
            this.sounds.error();
        }
    }

    /**
     * Play level up sound
     */
    playLevelUp() {
        if (this.sounds.levelUp) {
            this.sounds.levelUp();
        }
    }

    /**
     * Show custom toast message
     */
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: rgba(20, 25, 45, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px 20px;
            color: white;
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        // Color based on type
        const colors = {
            success: '#00FF88',
            error: '#FF4444',
            warning: '#FFB800',
            info: '#00FFFF'
        };
        toast.style.borderLeftColor = colors[type];
        toast.style.borderLeftWidth = '4px';

        toast.textContent = message;
        document.body.appendChild(toast);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

window.FeedbackSystem = FeedbackSystem;
