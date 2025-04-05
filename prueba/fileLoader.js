function loadOBJWithMTL(objFile, mtlFile) {
    var mtlLoader = new THREE.MTLLoader();
    mtlLoader.load(URL.createObjectURL(mtlFile), function (materials) {
        materials.preload();
        var objLoader = new THREE.OBJLoader();
        objLoader.setMaterials(materials);
        objLoader.load(URL.createObjectURL(objFile), function (object) {
            scene.add(object);
            object.scale.set(1, 1, 1);
        });
    });
}

function loadOBJ(objFile) {
    var objLoader = new THREE.OBJLoader();
    objLoader.load(URL.createObjectURL(objFile), function (object) {
        scene.add(object);
        object.scale.set(1, 1, 1);
    });
}

function loadSTL(file) {
    var loader = new THREE.STLLoader();
    loader.load(URL.createObjectURL(file), function (geometry) {
        var material = new THREE.MeshPhongMaterial({ color: 0x999999 });
        var mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
        mesh.scale.set(1, 1, 1);
    });
}

document.getElementById('fileInput').addEventListener('change', function (event) {
    var files = event.target.files;
    var objFile, mtlFile, stlFile;

    for (var i = 0; i < files.length; i++) {
        if (files[i].name.endsWith('.obj')) objFile = files[i];
        else if (files[i].name.endsWith('.mtl')) mtlFile = files[i];
        else if (files[i].name.endsWith('.stl')) stlFile = files[i];
    }

    if (objFile && mtlFile) loadOBJWithMTL(objFile, mtlFile);
    else if (objFile) loadOBJ(objFile);
    if (stlFile) loadSTL(stlFile);
});
