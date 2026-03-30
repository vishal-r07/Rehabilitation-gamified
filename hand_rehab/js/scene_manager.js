/**
 * Scene Manager - Sets up Three.js scene with lighting and effects
 */

class SceneManager {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = new THREE.Scene();
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.lights = [];

        this.init();
        this.setupLighting();
        this.setupPostProcessing();
        this.animate();
    }

    init() {
        // Camera setup
        const aspect = window.innerWidth / window.innerHeight;
        this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
        this.camera.position.set(0, 5, 15);
        this.camera.lookAt(0, 0, 0);

        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;

        // Scene background
        this.scene.background = null; // Transparent for CSS background
        this.scene.fog = new THREE.Fog(0x0A0E27, 20, 50);

        // Orbit controls
        this.controls = new THREE.OrbitControls(this.camera, this.canvas);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 5;
        this.controls.maxDistance = 30;
        this.controls.target.set(0, 0, 0);

        // Handle window resize
        window.addEventListener('resize', () => this.onResize());
    }

    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);

        // Main key light (cyan tint)
        const keyLight = new THREE.DirectionalLight(0x00FFFF, 1.5);
        keyLight.position.set(5, 10, 5);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        keyLight.shadow.camera.near = 0.5;
        keyLight.shadow.camera.far = 50;
        keyLight.shadow.camera.left = -10;
        keyLight.shadow.camera.right = 10;
        keyLight.shadow.camera.top = 10;
        keyLight.shadow.camera.bottom = -10;
        this.scene.add(keyLight);
        this.lights.push(keyLight);

        // Fill light (purple tint)
        const fillLight = new THREE.DirectionalLight(0x9D4EDD, 0.8);
        fillLight.position.set(-5, 5, -5);
        this.scene.add(fillLight);
        this.lights.push(fillLight);

        // Rim light (back light)
        const rimLight = new THREE.DirectionalLight(0xFFFFFF, 0.6);
        rimLight.position.set(0, 5, -10);
        this.scene.add(rimLight);
        this.lights.push(rimLight);

        // Hemisphere light for realistic ambient
        const hemiLight = new THREE.HemisphereLight(0x87CEEB, 0x1A1A2E, 0.3);
        this.scene.add(hemiLight);
        this.lights.push(hemiLight);

        // Add grid floor
        this.addGridFloor();
    }

    addGridFloor() {
        // Subtle grid plane
        const gridSize = 50;
        const gridDivisions = 50;
        const gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x00FFFF, 0x444466);
        gridHelper.position.y = -5;
        gridHelper.material.opacity = 0.2;
        gridHelper.material.transparent = true;
        this.scene.add(gridHelper);
    }

    setupPostProcessing() {
        // This would use EffectComposer for bloom, etc.
        // Simplified for now - can be expanded with UnrealBloomPass
    }

    /**
     * Add particle system for visual effects
     */
    addParticles() {
        const particleCount = 200;
        const particles = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 50;     // x
            positions[i + 1] = Math.random() * 30;         // y
            positions[i + 2] = (Math.random() - 0.5) * 50; // z
        }

        particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const particleMaterial = new THREE.PointsMaterial({
            color: 0x00FFFF,
            size: 0.1,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
        });

        const particleSystem = new THREE.Points(particles, particleMaterial);
        this.scene.add(particleSystem);

        // Animate particles
        this.particleSystem = particleSystem;
    }

    /**
     * Create success celebration effect
     */
    createSuccessEffect(position = new THREE.Vector3(0, 0, 0)) {
        const particleCount = 50;
        const particles = [];

        for (let i = 0; i < particleCount; i++) {
            const geometry = new THREE.SphereGeometry(0.1, 8, 8);
            const material = new THREE.MeshBasicMaterial({
                color: Math.random() > 0.5 ? 0x00FFFF : 0x9D4EDD,
                transparent: true,
                opacity: 1
            });

            const particle = new THREE.Mesh(geometry, material);
            particle.position.copy(position);

            // Random velocity
            particle.velocity = new THREE.Vector3(
                (Math.random() - 0.5) * 0.2,
                Math.random() * 0.3,
                (Math.random() - 0.5) * 0.2
            );

            this.scene.add(particle);
            particles.push(particle);
        }

        // Animate particles
        const startTime = Date.now();
        const duration = 1500;

        const animateParticles = () => {
            const elapsed = Date.now() - startTime;
            const progress = elapsed / duration;

            if (progress < 1) {
                particles.forEach(particle => {
                    particle.position.add(particle.velocity);
                    particle.velocity.y -= 0.01; // Gravity
                    particle.material.opacity = 1 - progress;
                });
                requestAnimationFrame(animateParticles);
            } else {
                // Cleanup
                particles.forEach(particle => {
                    this.scene.remove(particle);
                    particle.geometry.dispose();
                    particle.material.dispose();
                });
            }
        };
        animateParticles();
    }

    onResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Update controls
        this.controls.update();

        // Animate particles if present
        if (this.particleSystem) {
            this.particleSystem.rotation.y += 0.001;
        }

        // Render
        this.renderer.render(this.scene, this.camera);
    }

    getScene() {
        return this.scene;
    }

    getCamera() {
        return this.camera;
    }
}

window.SceneManager = SceneManager;
