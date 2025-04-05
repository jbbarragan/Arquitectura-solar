// Inicializar el mapa
var map = L.map('map').setView([20, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var marker;

// Función de búsqueda de dirección
function searchAddress() {
    var address = document.getElementById('searchInput').value;
    if (address.trim() === "") {
        alert("Por favor, ingrese una dirección para buscar.");
        return;
    }

    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                var result = data[0];
                var latLng = [result.lat, result.lon];

                if (marker) {
                    map.removeLayer(marker);
                }

                marker = L.marker(latLng).addTo(map)
                    .bindPopup(result.display_name)
                    .openPopup();

                map.setView(latLng, 15);
            } else {
                alert("No se encontraron resultados.");
            }
        })
        .catch(error => console.error('Error:', error));
}

// Eventos
document.getElementById('searchButton').addEventListener('click', searchAddress);
document.getElementById('searchInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') searchAddress();
});

// Evento de clic en el mapa para agregar marcador
map.on('click', function (e) {
    if (marker) {
        map.removeLayer(marker);
    }
    marker = L.marker(e.latlng).addTo(map)
        .bindPopup(`Lat: ${e.latlng.lat.toFixed(4)}, Lon: ${e.latlng.lng.toFixed(4)}`)
        .openPopup();

    enviarLatitud(e.latlng.lat);
});

// Enviar latitud al servidor
function enviarLatitud(latitud) {
    fetch('/procesar-latitud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitud: latitud })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Respuesta:', data);
        document.getElementById('solarImage').src = '/static/sunpath_diagram.png';
        actualizarSkyDome(data.altitudes, data.azimuts);
        crearArco(latitud);
    })
    .catch(error => console.error('Error:', error));
}
