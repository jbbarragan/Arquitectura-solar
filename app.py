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
<<<<<<< HEAD
# Meses representativos: 7 curvas únicas (simétricas alrededor del solsticio de verano)
# Día 21 de cada mes: Dic(355), Ene(21), Feb(52), Mar(80), Abr(111), May(141), Jun(172)
MESES_SOLAR = [
    ('Jun', 172, '#e63946'),   # solsticio verano — más alto
    ('May', 141, '#f4a261'),
    ('Abr', 111, '#e9c46a'),
    ('Mar',  80, '#2a9d8f'),   # equinoccio primavera
    ('Feb',  52, '#48cae4'),
    ('Ene',  21, '#4361ee'),
    ('Dic', 355, '#7209b7'),   # solsticio invierno — más bajo
]

def calcular_curva_mes(lat, dia_n):
    """Calcula altitud y azimut horarios para un día del año dado."""
    horas = np.arange(0, 25)          # 0..24 h
    H = (horas - 12) * 15            # ángulo horario en grados
    D = 23.45 * sind(360 * (284 + dia_n) / 365)   # declinación

    alts, azs = [], []
    for h in H:
        alt = arcsin_d(cosd(D) * cosd(lat) * cosd(h) + sind(D) * sind(lat))
        alts.append(alt)
        if alt <= 0:
            azs.append(None)
            continue
        denom = cosd(alt)
        if abs(denom) < 1e-6:
            azs.append(180.0)
        else:
            az = arccos_d((sind(D) * cosd(lat) - cosd(D) * sind(lat) * cosd(h)) / denom)
            azs.append(az if h <= 0 else 360 - az)
    return alts, azs, H


def _puntos_mes(lat, dia_n):
    """Devuelve lista de (az_deg, alt_deg, hora_int) sobre el horizonte."""
    alts, azs, H = calcular_curva_mes(lat, dia_n)
    pts = []
    for i in range(len(alts)):
        if alts[i] > 0 and azs[i] is not None:
            pts.append((azs[i], alts[i], int(round((H[i] / 15) + 12))))
    return pts


def equation_of_time(N):
    """Ecuación del tiempo en minutos para el día N (1..365). Fórmula de Spencer."""
    B = np.deg2rad((360 / 365) * (N - 81))
    return 9.87 * np.sin(2 * B) - 7.53 * np.cos(B) - 1.5 * np.sin(B)


def solar_pos_clock_hour(lat, day_n, clock_hour):
    """
    Posición solar (altitud, azimut en grados) para hora civil clock_hour,
    aplicando la ecuación del tiempo.
    """
    eot = equation_of_time(day_n)                   # minutos
    solar_min = clock_hour * 60 + eot               # minutos desde medianoche
    h_deg = (solar_min / 60 - 12) * 15             # ángulo horario en grados
    D = 23.45 * sind(360 * (284 + day_n) / 365)    # declinación

    alt = arcsin_d(cosd(D) * cosd(lat) * cosd(h_deg) + sind(D) * sind(lat))
    if alt <= 0:
        return None, None
    denom = cosd(alt)
    if abs(denom) < 1e-6:
        az = 180.0
    else:
        az = arccos_d((sind(D) * cosd(lat) - cosd(D) * sind(lat) * cosd(h_deg)) / denom)
        if h_deg > 0:
            az = 360 - az
    return alt, az


def _dibujar_analemas(ax, lat, radio_func):
    """
    Dibuja los analemas en un eje polar usando segmentos continuos.
    Evita las líneas rectas que aparecen cuando el sol está bajo el horizonte.
    """
    HORAS_ANALEMA = range(6, 19)
    DIAS = np.arange(1, 366)
    color_analema = '#b91c1c'  # rojo oscuro — mismo que línea del día en simulación

    for hora in HORAS_ANALEMA:
        # Recoger puntos día a día, insertar None en gaps para cortar la línea
        azs_seg, rs_seg = [], []
        for N in DIAS:
            alt, az = solar_pos_clock_hour(lat, int(N), hora)
            if alt is None or alt <= 0.5:
                # Insertar None para cortar el segmento
                if azs_seg and azs_seg[-1] is not None:
                    azs_seg.append(None)
                    rs_seg.append(None)
            else:
                azs_seg.append(np.deg2rad(az))
                rs_seg.append(radio_func(alt))

        if len([x for x in azs_seg if x is not None]) < 10:
            continue

        # Dividir en segmentos continuos y dibujar cada uno
        seg_az, seg_r = [], []
        for az, r in zip(azs_seg, rs_seg):
            if az is None:
                if len(seg_az) >= 2:
                    ax.plot(seg_az, seg_r, color=color_analema,
                            linewidth=0.9, alpha=0.6, zorder=3)
                seg_az, seg_r = [], []
            else:
                seg_az.append(az)
                seg_r.append(r)
        if len(seg_az) >= 2:
            ax.plot(seg_az, seg_r, color=color_analema,
                    linewidth=0.9, alpha=0.6, zorder=3)


def _render_figura(fig, lat, tipo):
    """Guarda la figura y devuelve base64."""
    fig.suptitle(f'Diagrama Solar {tipo} — Lat {lat:.2f}°',
                 color='#e6edf3', fontsize=11, fontweight='bold', y=0.98)
    plt.tight_layout()
    os.makedirs('static', exist_ok=True)
    plt.savefig('static/sunpath_diagram.png', dpi=140,
                bbox_inches='tight', facecolor=fig.get_facecolor())
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=140,
=======
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
>>>>>>> 59da878b1171ddf1704a46f519fd727fd7dc6e9e
                bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close()
<<<<<<< HEAD
    return img_b64


def _leyenda_polar(ax):
    handles = [mpatches.Patch(color=c, label=n) for n, _, c in MESES_SOLAR]
    ax.legend(handles=handles,
              loc='lower left', bbox_to_anchor=(-0.20, -0.06),
              framealpha=0.3, labelcolor='#c9d1d9', fontsize=8,
              facecolor='#161b22', edgecolor='#30363d', ncol=1)


def _base_polar(horas_label=None):
    """Crea figura polar con estilo oscuro. Devuelve (fig, ax)."""
    if horas_label is None:
        horas_label = {6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.tick_params(axis='y', colors='#6e7f96')
    ax.grid(color='#252d3a', linewidth=0.7, linestyle='--', alpha=0.8)
    ax.spines['polar'].set_color('#30363d')
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                       color='#c9d1d9', fontsize=10, fontweight='bold')
    return fig, ax


# ── TIPO 1: Estereográfica (proyección igual-ángulo) ─────────────────────────
def diagrama_estereografico(lat):
    fig, ax = _base_polar()
    ax.set_ylim(0, 90)
    ax.set_yticks(range(0, 91, 15))
    ax.set_yticklabels([f'{90-v}°' for v in range(0, 91, 15)],
                       color='#6e7f96', fontsize=7)

    # ── Analemas ──────────────────────────────────────────────────────────────
    _dibujar_analemas(ax, lat, lambda alt: np.tan(np.deg2rad((90 - alt) / 2)) * 90)

    altitudes_all, azimuts_all = [], []

    for nombre, dia_n, color in MESES_SOLAR:
        alts, azs, H = calcular_curva_mes(lat, dia_n)
        altitudes_all.append([a if a == a else None for a in alts])
        azimuts_all.append([a if a is not None else None for a in azs])

        # Incluir TODOS los puntos sobre el horizonte (alt >= 0)
        # Radio estereográfico: horizonte = r=90, cénit = r=0
        theta_pts, r_pts = [], []
        for i in range(len(alts)):
            if alts[i] >= 0 and azs[i] is not None:
                theta_pts.append(np.deg2rad(azs[i]))
                r_pts.append(np.tan(np.deg2rad((90 - max(alts[i], 0)) / 2)) * 90)

        if len(theta_pts) < 2:
            continue

        ax.plot(theta_pts, r_pts, color=color, linewidth=2.2,
                solid_capstyle='round', zorder=4)
        # Solo puntos sin etiquetas de hora
        for t, rv in zip(theta_pts, r_pts):
            if rv < 89:  # no pintar puntos en el borde del horizonte
                ax.scatter(t, rv, color=color, s=10, zorder=6)

    ax.scatter([0], [0], color='#fbbf24', s=150, zorder=10, marker='*')
    _leyenda_polar(ax)
    return fig, altitudes_all, azimuts_all


# ── TIPO 2: Equidistante (proyección igual-distancia) ────────────────────────
def diagrama_equidistante(lat):
    fig, ax = _base_polar()
    ax.set_ylim(0, 90)
    ax.set_yticks(range(0, 91, 15))
    ax.set_yticklabels([f'{90-v}°' for v in range(0, 91, 15)],
                       color='#6e7f96', fontsize=7)

    HL = {6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
    altitudes_all, azimuts_all = [], []

    for nombre, dia_n, color in MESES_SOLAR:
        alts, azs, H = calcular_curva_mes(lat, dia_n)
        altitudes_all.append([a if a == a else None for a in alts])
        azimuts_all.append([a if a is not None else None for a in azs])
        pts = _puntos_mes(lat, dia_n)
        if not pts: continue
        azs_v, alts_v, hrs_v = zip(*pts)

        # Radio equidistante: distancia cenital directa (lineal)
        r = [90 - a for a in alts_v]
        theta = np.deg2rad(list(azs_v))
        ax.plot(theta, r, color=color, linewidth=2.2, solid_capstyle='round', zorder=4)
        for t, rv, h in zip(theta, r, hrs_v):
            ax.scatter(t, rv, color=color, s=14, zorder=6)
            if h in HL:
                ax.annotate(str(h), xy=(t, rv), xytext=(t, rv + 2.5),
                            color=color, fontsize=6, ha='center', va='center',
                            fontweight='bold', textcoords='data', zorder=7)

    ax.scatter([0], [0], color='#fbbf24', s=150, zorder=10, marker='*')
    _leyenda_polar(ax)
    return fig, altitudes_all, azimuts_all


# ── TIPO 3: Esférica (proyección igual-área / Lambert) ───────────────────────
def diagrama_esferico(lat):
    fig, ax = _base_polar()
    ax.set_ylim(0, 90)
    ax.set_yticks(range(0, 91, 15))
    ax.set_yticklabels([f'{90-v}°' for v in range(0, 91, 15)],
                       color='#6e7f96', fontsize=7)

    HL = {6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
    altitudes_all, azimuts_all = [], []

    for nombre, dia_n, color in MESES_SOLAR:
        alts, azs, H = calcular_curva_mes(lat, dia_n)
        altitudes_all.append([a if a == a else None for a in alts])
        azimuts_all.append([a if a is not None else None for a in azs])
        pts = _puntos_mes(lat, dia_n)
        if not pts: continue
        azs_v, alts_v, hrs_v = zip(*pts)

        # Radio Lambert (igual-área): sqrt(2)*sin(zenith/2)*90
        r = [np.sqrt(2) * np.sin(np.deg2rad((90 - a) / 2)) * 90 for a in alts_v]
        theta = np.deg2rad(list(azs_v))
        ax.plot(theta, r, color=color, linewidth=2.2, solid_capstyle='round', zorder=4)
        for t, rv, h in zip(theta, r, hrs_v):
            ax.scatter(t, rv, color=color, s=14, zorder=6)
            if h in HL:
                ax.annotate(str(h), xy=(t, rv), xytext=(t, rv + 2.5),
                            color=color, fontsize=6, ha='center', va='center',
                            fontweight='bold', textcoords='data', zorder=7)

    ax.scatter([0], [0], color='#fbbf24', s=150, zorder=10, marker='*')
    _leyenda_polar(ax)
    return fig, altitudes_all, azimuts_all


# ── TIPO 4: Cartesiana (azimut X, altitud Y) ─────────────────────────────────
def diagrama_cartesiano(lat):
    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')
    ax.tick_params(colors='#6e7f96')
    ax.spines[:].set_color('#30363d')
    ax.grid(color='#252d3a', linewidth=0.6, linestyle='--', alpha=0.8)

    # Eje X: azimut 0–360 con etiquetas cardinales
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 90)
    ax.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'],
                       color='#c9d1d9', fontsize=9, fontweight='bold')
    ax.set_yticks(range(0, 91, 10))
    ax.set_yticklabels([f'{v}°' for v in range(0, 91, 10)],
                       color='#6e7f96', fontsize=7)
    ax.set_xlabel('Azimut', color='#6e7f96', fontsize=9)
    ax.set_ylabel('Altitud solar', color='#6e7f96', fontsize=9)

    # Línea de horizonte
    ax.axhline(0, color='#30363d', linewidth=1)
    # Línea N central
    ax.axvline(180, color='#252d3a', linewidth=0.8, linestyle=':')

    HL = {6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
    altitudes_all, azimuts_all = [], []

    for nombre, dia_n, color in MESES_SOLAR:
        alts, azs, H = calcular_curva_mes(lat, dia_n)
        altitudes_all.append([a if a == a else None for a in alts])
        azimuts_all.append([a if a is not None else None for a in azs])
        pts = _puntos_mes(lat, dia_n)
        if not pts: continue
        azs_v, alts_v, hrs_v = zip(*pts)

        ax.plot(list(azs_v), list(alts_v), color=color, linewidth=2.0,
                solid_capstyle='round', zorder=4)
        for az, al, h in zip(azs_v, alts_v, hrs_v):
            ax.scatter(az, al, color=color, s=14, zorder=6)
            if h in HL:
                ax.annotate(str(h), xy=(az, al), xytext=(az, al + 1.8),
                            color=color, fontsize=6, ha='center', va='bottom',
                            fontweight='bold', zorder=7)

    handles = [mpatches.Patch(color=c, label=n) for n, _, c in MESES_SOLAR]
    ax.legend(handles=handles, loc='upper left',
              framealpha=0.3, labelcolor='#c9d1d9', fontsize=8,
              facecolor='#161b22', edgecolor='#30363d', ncol=1)

    return fig, altitudes_all, azimuts_all


def generar_diagrama_solar(lat, tipo='stereographic'):
    altitudes_all, azimuts_all = [], []
    if tipo == 'cartesian':
        fig, altitudes_all, azimuts_all = diagrama_cartesiano(lat)
        img_b64 = _render_figura(fig, lat, 'Cartesiano')
    elif tipo == 'equidistant':
        fig, altitudes_all, azimuts_all = diagrama_equidistante(lat)
        img_b64 = _render_figura(fig, lat, 'Equidistante')
    elif tipo == 'spherical':
        fig, altitudes_all, azimuts_all = diagrama_esferico(lat)
        img_b64 = _render_figura(fig, lat, 'Esférico')
    else:  # stereographic (default)
        fig, altitudes_all, azimuts_all = diagrama_estereografico(lat)
        img_b64 = _render_figura(fig, lat, 'Estereográfico')
    return img_b64, altitudes_all, azimuts_all
=======

    return img_b64, altitudes, azimuts
>>>>>>> 59da878b1171ddf1704a46f519fd727fd7dc6e9e


# ── Rutas ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/procesar-latitud', methods=['POST'])
def procesar_latitud():
    data = request.get_json()
    latitud = float(data['latitud'])
<<<<<<< HEAD
    tipo = data.get('tipo', 'stereographic')
    img_b64, altitudes, azimuts = generar_diagrama_solar(latitud, tipo)
=======
    img_b64, altitudes, azimuts = generar_diagrama_solar_polar(latitud)
>>>>>>> 59da878b1171ddf1704a46f519fd727fd7dc6e9e
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
