from flask import Flask, request, render_template, jsonify
from flask import send_from_directory
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend sin interfaz gráfica
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.patches as mpatches
from lectorEPW import lector_epw_bp 
import os
# Crear la aplicación Flask
app = Flask(__name__)
app.register_blueprint(lector_epw_bp)

pi = np.pi

# Funciones trigonométricas en grados
def sin(x):
    return np.sin(np.deg2rad(x))

def cos(x):
    return np.cos(np.deg2rad(x))

def arcsin(x):
    return np.arcsin(x) * (180.0 / pi)

def arccos(x):
    return np.rad2deg(np.arccos(x))

# Función para generar el diagrama solar y devolver altitud y azimut
def generar_diagrama_solar(L):
    # Horas del día
    T = range(0, 25, 1)
    
    # Ángulo horario (15° por cada hora desde el mediodía)
    H = [15 * (x - 12) for x in T]

    # Días del año (en diferentes meses)
    N = [354.75, 293.75, 81, 111.25, 172.25]

    # Declinaciones solares para los días seleccionados
    D = [23.4 * sin((360.0 * (284.0 + x)) / 365.0) for x in N]

    # Función para calcular altitud solar
    def calcular_altitud(D, L, H):
        return [arcsin(cos(D) * cos(L) * cos(h) + sin(D) * sin(L)) for h in H]

    # Cálculo de altitudes para los diferentes días
    altitudes = [calcular_altitud(D[i], L, H) for i in range(len(D))]

    np.seterr(divide='ignore', invalid='ignore')

    # Función para calcular el azimut solar
    def calcular_azimuth(altitud, declinacion_index):
        n = 0
        m_az = []
        e_az = []
        while n < len(altitud):
            morn_az = arccos((sin(D[declinacion_index]) * cos(L) - cos(D[declinacion_index]) * sin(L) * cos(H[n])) / cos(altitud[n]))
            evenin_az = 360 - morn_az
            n += 1
            m_az.append(morn_az)
            e_az.append(evenin_az)

        morning_az_list = m_az[:((len(m_az) + 1) // 2)]
        evening_az_list = e_az[(((len(e_az)) - 1) // 2):]
        az_list = morning_az_list + evening_az_list
        del(az_list[13])
        az_list = [0.0 if np.isnan(x) else x for x in az_list]

        if abs(az_list[12] - az_list[11]) > 100:
            del(az_list[12])
            az_list.insert(12, 180.0)

        if L < 0:
            del(az_list[0])
            az_list.insert(0, 180)
            del(az_list[24])
            az_list.insert(24, 180)
        return az_list

    # Azimuts para cada altitud
    azimuts = [calcular_azimuth(altitudes[i], i) for i in range(len(D))]

    # Crear el diagrama solar base
    plt.figure(1, figsize=(13, 8))
    Diagram = Basemap(projection='spstere', boundinglat=0, lon_0=180, resolution='l', round=True, suppress_ticks=True)
    gridX, gridY = 10.0, 15.0
    parallelGrid = np.arange(-90.0, 90.0, gridX)
    meridianGrid = np.arange(-180.0, 180.0, gridY)

    Diagram.drawparallels(parallelGrid, labels=[False, False, False, False])
    Diagram.drawmeridians(meridianGrid, labels=[False, False, False, False], labelstyle='+/-', fmt='%i')

    ax = plt.gca()
    ax.text(0.5, 1.025, 'N', transform=ax.transAxes, horizontalalignment='center', verticalalignment='bottom', size=25)

    # Función para graficar altitud y azimut
    def plot(azimuth, altitude, color):
        azi_list = []
        alt_list = []
        offset = 0.5 if color in ['bo-', 'co-'] else 0
        for n in range(len(azimuth)):
            azi, alt = Diagram(azimuth[n], -(altitude[n] + offset))
            azi_list.append(azi)
            alt_list.append(alt)
        Diagram.plot(azi_list, alt_list, color)

    # Colores para las curvas
    colores = ['bo-', 'ro-', 'go-', 'mo-', 'co-']
    for i in range(len(azimuts)):
        plot(azimuts[i], altitudes[i], colores[i])

    # Guardar en un archivo
    plt.savefig('static/sunpath_diagram.png')
    plt.close()

    # Devolver los datos calculados (altitudes y azimuts)
    return {
        'altitudes': altitudes,
        'azimuts': azimuts
    }

# Ruta principal que sirve la página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para procesar la latitud desde el mapa interactivo
@app.route('/procesar-latitud', methods=['POST'])
def procesar_latitud():
    data = request.get_json()
    latitud = float(data['latitud'])

    # Llamada a la función para generar el diagrama solar con la latitud proporcionada y obtener datos
    resultado = generar_diagrama_solar(latitud)
    
    return jsonify({
        'mensaje': 'Diagrama solar generado correctamente',
        'latitud': latitud,
        'altitudes': resultado['altitudes'],
        'azimuts': resultado['azimuts']
    })

@app.route('/uploads/pintar_celeste.csv')
def get_csv():
    uploads_dir = os.path.join(app.root_path, 'uploads')
    return send_from_directory(uploads_dir, 'pintar_celeste.csv')
 
if __name__ == '__main__':
    app.run(debug=True)
