function actualizarSkyDome(altitudes, azimuts) {
    console.log("Actualizando Sky Dome...");
    crearAnillos(altitudes, azimuts);
}

function crearAnillos(altitudes, azimuts) {
    const colores = [0xADD8E6, 0x800080, 0x008000, 0xFF0000, 0x00008B];

    scene.traverse(child => {
        if (child.isMesh) scene.remove(child);
    });

    for (let i = 0; i < altitudes.length; i++) {
        for (let j = 0; j < azimuts[i].length; j++) {
            const altura = altitudes[i][j] * 2;
            const azimut = azimuts[i][j] * (Math.PI / 180) * 2;

            const geometry = new THREE.SphereGeometry(0.5, 16, 16);
            const material = new THREE.MeshBasicMaterial({ color: colores[i % colores.length] });
            const punto = new THREE.Mesh(geometry, material);

            const x = Math.cos(azimut) * altura;
            const z = Math.sin(azimut) * altura;
            const y = altura;

            punto.position.set(x, y, z);
            scene.add(punto);
        }
    }
}
