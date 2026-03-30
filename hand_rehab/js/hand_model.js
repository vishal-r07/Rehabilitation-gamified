/**
 * 3D Hand Model with Anatomical Structure
 * Creates a realistic hand with proper bone hierarchy and IK
 */

class HandModel {
    constructor(scene) {
        this.scene = scene;
        this.hand = new THREE.Group();
        this.bones = {};
        this.fingers = {
            thumb: [],
            index: [],
            middle: [],
            ring: [],
            pinky: []
        };

        // Materials
        this.skinMaterial = new THREE.MeshStandardMaterial({
            color: 0xFFD4B2,
            roughness: 0.6,
            metalness: 0.1,
            emissive: 0x000000
        });

        this.jointMaterial = new THREE.MeshStandardMaterial({
            color: 0xFFB088,
            roughness: 0.5,
            metalness: 0.2
        });

        // Build hand
        this.createHand();
        this.scene.add(this.hand);
    }

    /**
     * Create anatomically accurate hand structure
     */
    createHand() {
        // Palm (center)
        const palmGeometry = new THREE.BoxGeometry(2, 0.5, 3);
        const palm = new THREE.Mesh(palmGeometry, this.skinMaterial);
        palm.castShadow = true;
        palm.receiveShadow = true;
        this.hand.add(palm);
        this.bones.palm = palm;

        // Wrist
        const wristGeometry = new THREE.CylinderGeometry(0.8, 0.9, 0.8, 16);
        const wrist = new THREE.Mesh(wristGeometry, this.skinMaterial);
        wrist.position.set(0, -0.65, 0);
        wrist.castShadow = true;
        wrist.receiveShadow = true;
        this.hand.add(wrist);
        this.bones.wrist = wrist;

        // Create fingers
        this.createFinger('thumb', { x: -1.2, y: 0, z: 0.8 }, -0.5, [1.2, 1.0]);
        this.createFinger('index', { x: -0.9, y: 0, z: 1.7 }, 0, [1.5, 1.2, 1.0]);
        this.createFinger('middle', { x: -0.3, y: 0, z: 1.8 }, 0, [1.6, 1.3, 1.1]);
        this.createFinger('ring', { x: 0.3, y: 0, z: 1.7 }, 0, [1.4, 1.2, 1.0]);
        this.createFinger('pinky', { x: 0.9, y: 0, z: 1.5 }, 0.2, [1.1, 0.9, 0.8]);

        // Position hand in scene
        this.hand.position.set(0, 0, 0);
        this.hand.rotation.set(0, 0, 0);
    }

    /**
     * Create a finger with multiple phalanges
     * @param {string} name - Finger name
     * @param {object} startPos - Starting position {x, y, z}
     * @param {number} angle - Base rotation angle
     * @param {array} lengths - Length of each phalanx [proximal, middle, distal]
     */
    createFinger(name, startPos, angle, lengths) {
        const fingerGroup = new THREE.Group();
        fingerGroup.position.set(startPos.x, startPos.y, startPos.z);
        fingerGroup.rotation.z = angle;

        let currentY = 0;
        const phalanges = [];

        lengths.forEach((length, index) => {
            // Phalanx (finger segment)
            const radius = 0.25 - (index * 0.05);
            const phalanxGeometry = new THREE.CapsuleGeometry(radius, length, 8, 16);
            const phalanx = new THREE.Mesh(phalanxGeometry, this.skinMaterial);
            phalanx.position.y = currentY + length / 2;
            phalanx.castShadow = true;
            phalanx.receiveShadow = true;

            // Joint (sphere at connection point)
            if (index > 0) {
                const jointGeometry = new THREE.SphereGeometry(radius * 1.1, 16, 16);
                const joint = new THREE.Mesh(jointGeometry, this.jointMaterial);
                joint.position.y = currentY;
                joint.castShadow = true;
                fingerGroup.add(joint);
            }

            // Create a pivot point for rotation
            const pivot = new THREE.Group();
            pivot.position.y = currentY;
            pivot.add(phalanx);

            if (index === 0) {
                fingerGroup.add(pivot);
            } else {
                phalanges[index - 1].add(pivot);
            }

            phalanges.push(pivot);
            currentY += length;
        });

        this.fingers[name] = phalanges;
        this.bones.palm.add(fingerGroup);
    }

    /**
     * Update hand pose based on sensor data
     * @param {object} data - Normalized sensor data
     */
    updatePose(data) {
        if (!data) return;

        // Update wrist orientation (from IMU)
        this.hand.rotation.x = data.wristPitch;
        this.hand.rotation.y = data.wristYaw;
        this.hand.rotation.z = data.wristRoll;

        // Update finger bending
        this.bendFinger('thumb', data.thumbBend);
        this.bendFinger('index', data.indexBend);
        this.bendFinger('middle', data.middleBend);
        this.bendFinger('ring', data.ringBend);
        this.bendFinger('pinky', data.pinkyBend);

        // Update material based on muscle activation
        if (data.muscleActivation > 0.5) {
            this.skinMaterial.emissive.setHex(0x00FFFF);
            this.skinMaterial.emissiveIntensity = (data.muscleActivation - 0.5) * 0.3;
        } else {
            this.skinMaterial.emissiveIntensity = 0;
        }

        // Visual feedback for form
        if (!data.isGoodForm) {
            this.skinMaterial.color.setHex(0xFFAAAA); // Red tint for bad form
        } else {
            this.skinMaterial.color.setHex(0xFFD4B2); // Normal skin color
        }
    }

    /**
     * Bend finger using simple IK
     * @param {string} fingerName - Name of finger
     * @param {number} bendAmount - Bend amount (0-1)
     */
    bendFinger(fingerName, bendAmount) {
        const phalanges = this.fingers[fingerName];
        if (!phalanges) return;

        // Clamp bend amount
        bendAmount = Math.max(0, Math.min(1, bendAmount));

        // Natural finger curl angles (in radians)
        // Each joint bends progressively more
        const maxBendAngles = [
            Math.PI / 3,    // Proximal phalanx (60°)
            Math.PI / 2.5,  // Middle phalanx (72°)
            Math.PI / 4     // Distal phalanx (45°)
        ];

        phalanges.forEach((phalanx, index) => {
            if (index < maxBendAngles.length) {
                // Smooth interpolation with easing
                const targetAngle = -maxBendAngles[index] * bendAmount;

                // LERP for smooth animation
                phalanx.rotation.x = THREE.MathUtils.lerp(
                    phalanx.rotation.x,
                    targetAngle,
                    0.15
                );
            }
        });
    }

    /**
     * Reset hand to neutral pose
     */
    resetPose() {
        this.hand.rotation.set(0, 0, 0);

        Object.keys(this.fingers).forEach(fingerName => {
            this.bendFinger(fingerName, 0);
        });
    }

    /**
     * Perform predefined gesture
     * @param {string} gestureName - Name of gesture
     */
    performGesture(gestureName) {
        const gestures = {
            fist: { thumb: 1, index: 1, middle: 1, ring: 1, pinky: 1 },
            open: { thumb: 0, index: 0, middle: 0, ring: 0, pinky: 0 },
            point: { thumb: 0, index: 0, middle: 1, ring: 1, pinky: 1 },
            peace: { thumb: 1, index: 0, middle: 0, ring: 1, pinky: 1 },
            thumbsUp: { thumb: 0, index: 1, middle: 1, ring: 1, pinky: 1 },
            pinch: { thumb: 0.7, index: 0.7, middle: 0, ring: 0, pinky: 0 }
        };

        const gesture = gestures[gestureName];
        if (gesture) {
            Object.keys(gesture).forEach(finger => {
                this.bendFinger(finger, gesture[finger]);
            });
        }
    }

    /**
     * Get current hand position for collision detection
     */
    getFingerTipPositions() {
        const positions = {};

        Object.keys(this.fingers).forEach(fingerName => {
            const phalanges = this.fingers[fingerName];
            if (phalanges.length > 0) {
                const lastPhalanx = phalanges[phalanges.length - 1];
                const worldPos = new THREE.Vector3();
                lastPhalanx.getWorldPosition(worldPos);
                positions[fingerName] = worldPos;
            }
        });

        return positions;
    }

    /**
     * Animate hand (for tutorials/demos)
     */
    animate(animationName, duration = 2000) {
        const animations = {
            wave: () => {
                const startY = this.hand.rotation.y;
                const startTime = Date.now();

                const waveLoop = () => {
                    const elapsed = Date.now() - startTime;
                    if (elapsed < duration) {
                        const progress = (elapsed / duration) * Math.PI * 4;
                        this.hand.rotation.y = startY + Math.sin(progress) * 0.5;
                        requestAnimationFrame(waveLoop);
                    } else {
                        this.hand.rotation.y = startY;
                    }
                };
                waveLoop();
            },

            flex: () => {
                let flexing = true;
                const startTime = Date.now();

                const flexLoop = () => {
                    const elapsed = Date.now() - startTime;
                    if (elapsed < duration) {
                        const bendAmount = flexing ? 1 : 0;
                        Object.keys(this.fingers).forEach(finger => {
                            this.bendFinger(finger, bendAmount);
                        });

                        if (elapsed % 1000 < 50) {
                            flexing = !flexing;
                        }

                        requestAnimationFrame(flexLoop);
                    } else {
                        this.resetPose();
                    }
                };
                flexLoop();
            }
        };

        if (animations[animationName]) {
            animations[animationName]();
        }
    }
}

// Export for use in other modules
window.HandModel = HandModel;
