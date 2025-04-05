class Visor3D {
    constructor() {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('viewer').appendChild(this.renderer.domElement);

        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        this.camera.position.z = 5;
        this.scene.add(new THREE.GridHelper(100, 100));

        this.animate();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    cargarModelo(file) {
        const loader = new THREE.OBJLoader();
        loader.load(URL.createObjectURL(file), (object) => {
            this.scene.add(object);
            object.scale.set(1, 1, 1);
        });
    }
}