class Mapa {
    constructor() {
        this.map = L.map('map').setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
        this.marker = null;
        this.initEventListeners();
    }

    searchAddress() {
        const address = document.getElementById('searchInput').value;
        if (!address.trim()) {
            alert("Por favor, ingrese una dirección para buscar.");
            return;
        }

        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
            .then(response => response.json())
            .then(data => {
                if (data.length > 0) {
                    const result = data[0];
                    const latLng = [result.lat, result.lon];

                    if (this.marker) this.map.removeLayer(this.marker);
                    
                    this.marker = L.marker(latLng).addTo(this.map)
                        .bindPopup(result.display_name)
                        .openPopup();
                    this.map.setView(latLng, 15);
                } else {
                    alert("No se encontraron resultados.");
                }
            })
            .catch(error => console.error('Error:', error));
    }

    initEventListeners() {
        document.getElementById('searchButton').addEventListener('click', () => this.searchAddress());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchAddress();
        });
    }
}