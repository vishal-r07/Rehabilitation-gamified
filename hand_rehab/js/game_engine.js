/**
 * Game Engine - Manages 5 Rehabilitation Game Modes
 */

class GameEngine {
    constructor(handModel, websocketClient, sceneManager) {
        this.hand = handModel;
        this.ws = websocketClient;
        this.scene = sceneManager;
        this.currentGame = null;
        this.isPlaying = false;
        this.score = 0;
        this.level = 1;
        this.difficulty = 'medium';

        // Game state
        this.gameState = {
            startTime: 0,
            targetsPassed: 0,
            perfectAttempts: 0,
            totalAttempts: 0,
            currentTarget: null
        };

        // 3D objects for games
        this.gameObjects = [];

        this.setupGameCards();
    }

    setupGameCards() {
        const gameCards = document.querySelectorAll('.game-card');
        gameCards.forEach(card => {
            card.addEventListener('click', () => {
                const gameName = card.dataset.game;
                this.startGame(gameName);
            });
        });

        // Exit game button
        const exitBtn = document.getElementById('exit-game');
        if (exitBtn) {
            exitBtn.addEventListener('click', () => this.exitGame());
        }
    }

    /**
     * Start a rehabilitation game
     */
    startGame(gameName) {
        console.log(`[GameEngine] Starting game: ${gameName}`);
        this.currentGame = gameName;
        this.isPlaying = true;
        this.score = 0;
        this.gameState.startTime = Date.now();
        this.gameState.targetsPassed = 0;
        this.gameState.perfectAttempts = 0;
        this.gameState.totalAttempts = 0;

        // Show game overlay
        document.getElementById('game-selector').classList.add('hidden');
        document.getElementById('game-overlay').classList.remove('hidden');
        document.getElementById('form-indicators').classList.remove('hidden');

        // Update game title
        const titles = {
            rom: 'Range of Motion Trainer',
            grip: 'Grip Strength Challenge',
            coordination: 'Finger Coordination',
            manipulation: 'Object Manipulation',
            endurance: 'Endurance Mode'
        };
        document.getElementById('game-title').textContent = titles[gameName];

        // Start specific game
        switch (gameName) {
            case 'rom': this.startROMGame(); break;
            case 'grip': this.startGripGame(); break;
            case 'coordination': this.startCoordinationGame(); break;
            case 'manipulation': this.startManipulationGame(); break;
            case 'endurance': this.startEnduranceGame(); break;
        }

        // Start game loop
        this.gameLoop();
    }

    /**
     * Exit current game
     */
    exitGame() {
        this.isPlaying = false;
        this.currentGame = null;

        // Hide game overlay
        document.getElementById('game-overlay').classList.add('hidden');
        document.getElementById('game-selector').classList.remove('hidden');
        document.getElementById('form-indicators').classList.add('hidden');

        // Cleanup game objects
        this.gameObjects.forEach(obj => {
            this.scene.getScene().remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        });
        this.gameObjects = [];

        // Reset hand
        this.hand.resetPose();
    }

    /**
     * GAME 1: Range of Motion Trainer
     * Goal: Flex fingers to match target angles
     */
    startROMGame() {
        const instructions = `
            <h3>Match the target finger positions!</h3>
            <p>Bend your fingers to match the glowing target zones.</p>
            <p>Green = Perfect, Yellow = Close, Red = Off target</p>
        `;
        document.getElementById('game-instructions').innerHTML = instructions;

        // Create target visualization
        this.gameState.currentTarget = {
            thumb: Math.random() * 0.8 + 0.2,
            index: Math.random() * 0.8 + 0.2,
            middle: Math.random() * 0.8 + 0.2,
            ring: Math.random() * 0.8 + 0.2,
            pinky: Math.random() * 0.8 + 0.2
        };

        // Display target values
        this.updateROMFeedback();
    }

    updateROMFeedback() {
        const data = this.ws.getNormalizedData();
        const target = this.gameState.currentTarget;

        let totalError = 0;
        let feedback = '<h4>Finger Targets:</h4><div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;">';

        ['thumb', 'index', 'middle', 'ring', 'pinky'].forEach(finger => {
            const current = data[finger + 'Bend'] || 0;
            const targetVal = target[finger];
            const error = Math.abs(current - targetVal);
            totalError += error;

            let color = '#FF4444';
            if (error < 0.1) color = '#00FF88';
            else if (error < 0.2) color = '#FFB800';

            feedback += `<div style="text-align: center;">
                <div style="font-size: 0.8rem; color: #A0AEC0; text-transform: uppercase;">${finger}</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: ${color};">
                    ${Math.round(current * 100)}%
                </div>
                <div style="font-size: 0.7rem; color: #666;">Target: ${Math.round(targetVal * 100)}%</div>
            </div>`;
        });

        feedback += '</div>';

        // Check if target achieved
        if (totalError < 0.3) {
            this.score += 100;
            this.gameState.perfectAttempts++;
            this.scene.createSuccessEffect(new THREE.Vector3(0, 2, 0));

            // New target
            setTimeout(() => {
                this.gameState.currentTarget = {
                    thumb: Math.random() * 0.8 + 0.2,
                    index: Math.random() * 0.8 + 0.2,
                    middle: Math.random() * 0.8 + 0.2,
                    ring: Math.random() * 0.8 + 0.2,
                    pinky: Math.random() * 0.8 + 0.2
                };
            }, 500);
        }

        document.getElementById('game-feedback').innerHTML = feedback;
    }

    /**
     * GAME 2: Grip Strength Challenge
     * Goal: Maintain target EMG level
     */
    startGripGame() {
        const instructions = `
            <h3>Grip Strength Challenge!</h3>
            <p>Maintain the target muscle activation level.</p>
            <p>Hold steady to earn points!</p>
        `;
        document.getElementById('game-instructions').innerHTML = instructions;

        this.gameState.targetEMG = 0.5 + (this.level * 0.05);
        this.gameState.holdTime = 0;
    }

    updateGripFeedback() {
        const data = this.ws.getNormalizedData();
        const targetEMG = this.gameState.targetEMG;
        const currentEMG = data.muscleActivation;
        const error = Math.abs(currentEMG - targetEMG);

        let color = '#FF4444';
        let status = 'Too weak';

        if (error < 0.1) {
            color = '#00FF88';
            status = 'Perfect! Hold it!';
            this.gameState.holdTime += 50; // Add time
            this.score += 10;
        } else if (currentEMG > targetEMG) {
            status = 'Too strong';
        }

        const holdProgress = Math.min((this.gameState.holdTime / 3000) * 100, 100);

        const feedback = `
            <h4>Muscle Activation</h4>
            <div style="font-size: 3rem; font-weight: bold; color: ${color};">
                ${Math.round(currentEMG * 100)}%
            </div>
            <div style="font-size: 1.2rem; margin: 10px 0;">Target: ${Math.round(targetEMG * 100)}%</div>
            <div style="font-size: 1rem; color: ${color}; margin-bottom: 10px;">${status}</div>
            <div style="width: 100%; background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; overflow: hidden;">
                <div style="width: ${holdProgress}%; background: linear-gradient(90deg, #00FFFF, #9D4EDD); height: 100%; transition: width 0.1s;"></div>
            </div>
            <div style="font-size: 0.8rem; color: #A0AEC0; margin-top: 5px;">Hold ${(this.gameState.holdTime / 1000).toFixed(1)}s / 3.0s</div>
        `;

        document.getElementById('game-feedback').innerHTML = feedback;

        // Check if target achieved
        if (this.gameState.holdTime >= 3000) {
            this.score += 500;
            this.scene.createSuccessEffect(new THREE.Vector3(0, 2, 0));
            this.gameState.holdTime = 0;
            this.gameState.targetEMG = Math.min(0.5 + (Math.random() * 0.3), 0.9);
        }
    }

    /**
     * GAME 3: Finger Coordination (Simon Says)
     * Goal: Match specific hand gestures
     */
    startCoordinationGame() {
        const instructions = `
            <h3>Finger Coordination!</h3>
            <p>Match the gesture shown on screen.</p>
            <p>Quick and accurate = bonus points!</p>
        `;
        document.getElementById('game-instructions').innerHTML = instructions;

        this.gameState.targetGesture = this.getRandomGesture();
        this.gameState.gestureStartTime = Date.now();
        this.hand.performGesture(this.gameState.targetGesture);

        setTimeout(() => this.hand.resetPose(), 2000);
    }

    getRandomGesture() {
        const gestures = ['fist', 'open', 'point', 'peace', 'thumbsUp', 'pinch'];
        return gestures[Math.floor(Math.random() * gestures.length)];
    }

    updateCoordinationFeedback() {
        const data = this.ws.getNormalizedData();
        const elapsed = (Date.now() - this.gameState.gestureStartTime) / 1000;

        const feedback = `
            <h4>Match This Gesture:</h4>
            <div style="font-size: 3rem; margin: 20px 0;">
                ${this.getGestureEmoji(this.gameState.targetGesture)}
            </div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #00FFFF;">
                ${this.gameState.targetGesture.toUpperCase()}
            </div>
            <div style="font-size: 0.9rem; color: #A0AEC0; margin-top: 10px;">
                Time: ${elapsed.toFixed(1)}s
            </div>
        `;

        document.getElementById('game-feedback').innerHTML = feedback;

        // Gesture detection (simplified - check if matches)
        if (this.matchesGesture(data, this.gameState.targetGesture)) {
            const bonus = Math.max(0, 500 - (elapsed * 50));
            this.score += Math.round(200 + bonus);
            this.scene.createSuccessEffect(new THREE.Vector3(0, 2, 0));

            // Next gesture
            this.gameState.targetGesture = this.getRandomGesture();
            this.gameState.gestureStartTime = Date.now();
            this.hand.performGesture(this.gameState.targetGesture);
            setTimeout(() => this.hand.resetPose(), 2000);
        }
    }

    getGestureEmoji(gesture) {
        const emojis = {
            fist: '✊',
            open: '🖐️',
            point: '☝️',
            peace: '✌️',
            thumbsUp: '👍',
            pinch: '🤏'
        };
        return emojis[gesture] || '🤚';
    }

    matchesGesture(data, gesture) {
        // Simplified gesture matching
        const gestures = {
            fist: () => data.thumbBend > 0.8 && data.indexBend > 0.8 && data.middleBend > 0.8,
            open: () => data.thumbBend < 0.2 && data.indexBend < 0.2 && data.middleBend < 0.2,
            point: () => data.indexBend < 0.3 && data.middleBend > 0.7 && data.ringBend > 0.7,
            peace: () => data.indexBend < 0.3 && data.middleBend < 0.3 && data.ringBend > 0.7,
            thumbsUp: () => data.thumbBend < 0.3 && data.indexBend > 0.7 && data.middleBend > 0.7,
            pinch: () => data.thumbBend > 0.6 && data.indexBend > 0.6 && data.middleBend < 0.3
        };

        return gestures[gesture] ? gestures[gesture]() : false;
    }

    /**
     * GAME 4: Object Manipulation
     * Goal: Pick up and move virtual objects
     */
    startManipulationGame() {
        const instructions = `
            <h3>Object Manipulation!</h3>
            <p>Grab and place the virtual cubes in the target zone.</p>
            <p>Precision matters!</p>
        `;
        document.getElementById('game-instructions').innerHTML = instructions;

        // Create virtual objects
        this.createManipulationObjects();
    }

    createManipulationObjects() {
        // Create a cube to manipulate
        const geometry = new THREE.BoxGeometry(1, 1, 1);
        const material = new THREE.MeshStandardMaterial({
            color: 0x00FFFF,
            emissive: 0x00FFFF,
            emissiveIntensity: 0.3
        });
        const cube = new THREE.Mesh(geometry, material);
        cube.position.set(3, 0, 0);
        cube.castShadow = true;

        this.scene.getScene().add(cube);
        this.gameObjects.push(cube);
        this.gameState.grabbedObject = null;

        // Create target zone
        const targetGeometry = new THREE.RingGeometry(1, 1.2, 32);
        const targetMaterial = new THREE.MeshBasicMaterial({
            color: 0x9D4EDD,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.5
        });
        const target = new THREE.Mesh(targetGeometry, targetMaterial);
        target.rotation.x = -Math.PI / 2;
        target.position.set(-3, -0.5, 0);

        this.scene.getScene().add(target);
        this.gameObjects.push(target);
    }

    updateManipulationFeedback() {
        const data = this.ws.getNormalizedData();

        const feedback = `
            <h4>Grab & Move!</h4>
            <p style="font-size: 0.9rem; color: #A0AEC0;">
                Close your fist to grab the cube<br>
                Move it to the purple target zone
            </p>
            <div style="margin-top: 15px;">
                <div style="font-size: 0.8rem; color: #00FFFF;">Grip: ${Math.round(data.indexBend * 100)}%</div>
            </div>
        `;

        document.getElementById('game-feedback').innerHTML = feedback;

        // Simple grab mechanics
        const cube = this.gameObjects[0];
        if (cube && data.indexBend > 0.8) {
            // Object follows hand
            const fingerTips = this.hand.getFingerTipPositions();
            if (fingerTips.index) {
                cube.position.copy(fingerTips.index);
            }

            // Check if in target zone
            const target = this.gameObjects[1];
            const distance = cube.position.distanceTo(target.position);
            if (distance < 1.5) {
                this.score += 300;
                this.scene.createSuccessEffect(cube.position);

                // Reset object
                cube.position.set(3, 0, 0);
            }
        }
    }

    /**
     * GAME 5: Endurance Mode
     * Goal: Sustained repetitive exercises
     */
    startEnduranceGame() {
        const instructions = `
            <h3>Endurance Training!</h3>
            <p>Perform repetitive hand open/close exercises.</p>
            <p>Keep a steady rhythm for maximum points!</p>
        `;
        document.getElementById('game-instructions').innerHTML = instructions;

        this.gameState.reps = 0;
        this.gameState.lastState = 'open';
    }

    updateEnduranceFeedback() {
        const data = this.ws.getNormalizedData();
        const avgBend = (data.thumbBend + data.indexBend + data.middleBend) / 3;

        // Detect open/close cycles
        const currentState = avgBend > 0.6 ? 'closed' : 'open';
        if (currentState !== this.gameState.lastState) {
            if (currentState === 'closed') {
                this.gameState.reps++;
                this.score += 50;

                if (this.gameState.reps % 10 === 0) {
                    this.scene.createSuccessEffect(new THREE.Vector3(0, 2, 0));
                }
            }
            this.gameState.lastState = currentState;
        }

        const elapsed = (Date.now() - this.gameState.startTime) / 1000;
        const pace = this.gameState.reps > 0 ? (elapsed / this.gameState.reps).toFixed(1) : '0.0';

        const feedback = `
            <h4>Repetitions</h4>
            <div style="font-size: 4rem; font-weight: bold; color: #00FFFF;">
                ${this.gameState.reps}
            </div>
            <div style="font-size: 1rem; color: #A0AEC0; margin: 10px 0;">
                Time: ${elapsed.toFixed(1)}s | Pace: ${pace}s/rep
            </div>
            <div style="font-size: 0.9rem; color: ${currentState === 'closed' ? '#00FF88' : '#FFB800'};">
                ${currentState === 'closed' ? '✊ CLOSED' : '🖐️ OPEN'}
            </div>
        `;

        document.getElementById('game-feedback').innerHTML = feedback;
    }

    /**
     * Main game loop
     */
    gameLoop() {
        if (!this.isPlaying) return;

        // Update appropriate game
        switch (this.currentGame) {
            case 'rom': this.updateROMFeedback(); break;
            case 'grip': this.updateGripFeedback(); break;
            case 'coordination': this.updateCoordinationFeedback(); break;
            case 'manipulation': this.updateManipulationFeedback(); break;
            case 'endurance': this.updateEnduranceFeedback(); break;
        }

        // Update score display
        document.getElementById('current-score').textContent = this.score;

        // Continue loop
        setTimeout(() => this.gameLoop(), 50);
    }
}

window.GameEngine = GameEngine;
