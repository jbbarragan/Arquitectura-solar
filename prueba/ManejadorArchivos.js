class ManejadorArchivos {
    constructor(visor) {
        this.visor = visor;
        document.getElementById('fileInput').addEventListener('change', (event) => this.procesarArchivos(event.target.files));
    }

    procesarArchivos(files) {
        for (let file of files) {
            if (file.name.endsWith('.obj')) {
                this.visor.cargarModelo(file);
            }
        }
    }
}
