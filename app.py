from flask import Flask, request, render_template, jsonify, send_from_directory
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import os
import io
import base64
from lectorEPW import lector_epw_bp

app = Flask(__name__)
app.register_blueprint(lector_epw_bp)

# ── Trigonometría en grados ──────────────────────────────────────────────────
def sind(x):  return np.sin(np.deg2rad(x))
def cosd(x):  return np.cos(np.deg2rad(x))
def arcsin_d(x): return np.degrees(np.arcsin(np.clip(x, -1, 1)))
def arccos_d(x): return np.degrees(np.arccos(np.clip(x, -1, 1)))

# ── Cálculo solar ─────────────────────────────────────────────────────────────
def calcular_posicion_solar(lat):
    """Devuelve (altitudes, azimuts) para 5 fechas representativas."""
    horas = np.arange(0, 25)
    H = (horas - 12) * 15               # ángulo horario

    # Días del año: solsticios, equinoccios y solsticio de verano sur
    dias_N = [172, 355, 81, 264, 355]
    etiquetas = ['Jun 21', 'Dic 21', 'Mar 21', 'Sep 21', 'Dic 21 b']
    # Simplificado: usamos 5 fechas clave
    dias_N = [172.25, 354.75, 81.0, 264.0, 111.25]

    declinaciones = [23.45 * sind(360 * (284 + n) / 365) for n in dias_N]

    altitudes, azimuts = [], []
    for D in declinaciones:
        alt = [arcsin_d(cosd(D) * cosd(lat) * cosd(h) + sind(D) * sind(lat)) for h in H]
        az_list = []
        for i, h in enumerate(H):
            denom = cosd(alt[i])
            if abs(denom) < 1e-6:
                az_list.append(180.0)
            else:
                az = arccos_d((sind(D) * cosd(lat) - cosd(D) * sind(lat) * cosd(h)) / denom)
                az_list.append(az if h <= 0 else 360 - az)
        altitudes.append(alt)
        azimuts.append(az_list)

    return altitudes, azimuts


def generar_diagrama_solar_polar(lat):
    """
    Genera el diagrama solar en proyección polar estereográfica
    usando matplotlib puro (sin basemap).
    El resultado se guarda como PNG y también se devuelve en base64.
    """
    altitudes, azimuts = calcular_posicion_solar(lat)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    # Configuración de la grilla polar
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)           # sentido horario = E a la derecha
    ax.set_ylim(0, 90)
    ax.set_yticks(range(0, 91, 15))
    ax.set_yticklabels([f'{90-v}°' for v in range(0, 91, 15)],
                       color='#8892a4', fontsize=7)
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                       color='#c9d1d9', fontsize=9, fontweight='bold')
    ax.tick_params(axis='y', colors='#8892a4')
    ax.grid(color='#30363d', linewidth=0.6, linestyle='--')
    ax.spines['polar'].set_color('#30363d')

    colores = ['#f97316', '#3b82f6', '#22c55e', '#a855f7', '#ec4899']
    etiquetas = ['Jun 21', 'Dic 21', 'Equinoccio Mar', 'Equinoccio Sep', 'Nov/Ene']

    for i, (alts, azs) in enumerate(zip(altitudes, azimuts)):
        # Convertir altitud a radio en proyección (90 - alt = distancia al cénit)
        validos = [(az, alt) for az, alt in zip(azs, alts) if alt > 0]
        if not validos:
            continue
        azs_v, alts_v = zip(*validos)
        r = [90 - a for a in alts_v]
        theta = np.deg2rad(azs_v)
        ax.plot(theta, r, color=colores[i], linewidth=2, label=etiquetas[i],
                solid_capstyle='round')
        ax.scatter(theta, r, color=colores[i], s=15, zorder=5)

    # Punto cénit
    ax.scatter([0], [0], color='#fbbf24', s=120, zorder=10, marker='*')

    ax.legend(loc='lower left', bbox_to_anchor=(-0.18, -0.05),
              framealpha=0.2, labelcolor='#c9d1d9', fontsize=8,
              facecolor='#161b22', edgecolor='#30363d')
    ax.set_title(f'Diagrama Solar — Latitud {lat:.2f}°',
                 color='#e6edf3', fontsize=11, pad=15, fontweight='bold')

    plt.tight_layout()

    # Guardar a disco y a buffer base64
    os.makedirs('static', exist_ok=True)
    plt.savefig('static/sunpath_diagram.png', dpi=130,
                bbox_inches='tight', facecolor=fig.get_facecolor())

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130,
                bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close()

    return img_b64, altitudes, azimuts


# ── Rutas ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/procesar-latitud', methods=['POST'])
def procesar_latitud():
    data = request.get_json()
    latitud = float(data['latitud'])
    img_b64, altitudes, azimuts = generar_diagrama_solar_polar(latitud)
    return jsonify({
        'mensaje': 'Diagrama solar generado',
        'latitud': latitud,
        'imagen_b64': img_b64,
        'altitudes': altitudes,
        'azimuts': azimuts
    })


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
