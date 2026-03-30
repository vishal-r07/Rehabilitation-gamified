/**
 * Animation Controller - Maps sensor data to hand animations
 */

class AnimationController {
    constructor(handModel, websocketClient) {
        this.hand = handModel;
        this.ws = websocketClient;
        this.isActive = false;
        this.lerpFactor = 0.15; // Smoothing factor
    }

    /**
     * Start animation loop
     */
    start() {
        this.isActive = true;
        this.update();
    }

    /**
     * Stop animation loop
     */
    stop() {
        this.isActive = false;
    }

    /**
     * Update hand pose from sensor data
     */
    update() {
        if (!this.isActive) return;

        // Get normalized sensor data
        const data = this.ws.getNormalizedData();

        // Update hand model
        if (this.hand) {
            this.hand.updatePose(data);
        }

        // Continue loop
        requestAnimationFrame(() => this.update());
    }

    /**
     * Play predefined animation sequence
     */
    playSequence(sequence, onComplete) {
        const gestures = sequence.split(',');
        let currentIndex = 0;

        const playNext = () => {
            if (currentIndex < gestures.length) {
                const gesture = gestures[currentIndex].trim();
                this.hand.performGesture(gesture);
                currentIndex++;
                setTimeout(playNext, 1000);
            } else {
                if (onComplete) onComplete();
            }
        };

        playNext();
    }
}

window.AnimationController = AnimationController;
