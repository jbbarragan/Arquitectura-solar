from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import csv
import io
import base64

lector_epw_bp = Blueprint('lector_epw', __name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Paletas refinadas
AZULES = ["#dbeafe", "#93c5fd", "#3b82f6", "#1d4ed8", "#1e3a5f"]
NARANJAS = ["#fef3c7", "#fbbf24", "#f97316", "#dc2626", "#7f1d1d"]
BG_DARK = '#0d1117'
TEXT_COLOR = '#e6edf3'
GRID_COLOR = '#21262d'


def fig_a_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def generar_heatmap(tabla_completa, temperatura_neutra, nombre_archivo):
    """Genera heatmap hora×mes con escala de color continua."""
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_DARK)

    # Construir matriz numérica
    matrix = np.array([[tabla_completa[h, m] for m in range(12)] for h in range(24)])

    # Colormap personalizado: azul→blanco→naranja
    cmap = LinearSegmentedColormap.from_list(
        'thermal', ['#1e3a5f', '#3b82f6', '#dbeafe', '#ffffff',
                    '#fef3c7', '#f97316', '#7f1d1d'], N=256)

    # Temperatura neutra promedio para normalizar
    t_neutra_med = np.nanmean(list(temperatura_neutra.values()))
    t_min = np.nanmin(matrix)
    t_max = np.nanmax(matrix)
    norm = mcolors.TwoSlopeNorm(vmin=t_min, vcenter=t_neutra_med, vmax=t_max)

    im = ax.imshow(matrix, aspect='auto', cmap=cmap, norm=norm, origin='upper')

    # Etiquetas de ejes
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    ax.set_xticks(range(12))
    ax.set_xticklabels(meses, color=TEXT_COLOR, fontsize=9)
    ax.set_yticks(range(24))
    ax.set_yticklabels([f'{h:02d}:00' for h in range(24)],
                       color=TEXT_COLOR, fontsize=7)

    # Valores en celdas
    for h in range(24):
        for m in range(12):
            val = matrix[h, m]
            if not np.isnan(val):
                text_c = 'white' if abs(val - t_neutra_med) > 4 else '#0d1117'
                ax.text(m, h, f'{val:.1f}', ha='center', va='center',
                        fontsize=5.5, color=text_c, fontweight='bold')

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
    cbar.outline.set_edgecolor(GRID_COLOR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_COLOR, fontsize=8)
    cbar.set_label('°C', color=TEXT_COLOR, fontsize=9)

    ax.set_title('Temperatura Promedio por Hora y Mes', color=TEXT_COLOR,
                 fontsize=13, fontweight='bold', pad=12)
    ax.spines[:].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_COLOR)

    plt.tight_layout()
    fig.savefig(nombre_archivo, dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    b64 = fig_a_b64(fig)
    plt.close(fig)
    return b64


def generar_tabla_mensual(df, temperatura_neutra, promedio_por_mes, nombre_archivo, neutral_half=2.5, step=2.5):
    """Genera la tabla de rangos térmicos por mes con diseño oscuro."""
    fig, axes = plt.subplots(3, 4, figsize=(16, 10))
    fig.patch.set_facecolor(BG_DARK)
    axes = axes.flatten()

    for mes in range(1, 13):
        ax = axes[mes - 1]
        ax.set_facecolor(BG_DARK)

        neutra = temperatura_neutra.get(mes, 20)
        t_min = df[df["Mes"] == mes]["Temperatura_Aire"].min()
        t_max = df[df["Mes"] == mes]["Temperatura_Aire"].max()
        t_med = promedio_por_mes.get(mes, 20)

        rangos = []
        # Subcalentamiento — bands below comfort zone, fixed step=2.5
        t = neutra - neutral_half
        for color in reversed(AZULES):
            if t < t_min - step: break
            rangos.insert(0, (t - step, t, color, 'frio'))
            t -= step
        # Zona de confort
        rangos.append((neutra - neutral_half, neutra + neutral_half, '#1e4d3a', 'neutro'))
        # Sobrecalentamiento — bands above comfort zone, fixed step=2.5
        t = neutra + neutral_half
        for color in NARANJAS:
            if t > t_max + step: break
            rangos.append((t, t + step, color, 'calido'))
            t += step

        meses_nombres = ['Ene','Feb','Mar','Abr','May','Jun',
                         'Jul','Ago','Sep','Oct','Nov','Dic']

        # Dibujar filas como barras horizontales
        for idx, (t0, t1, color, tipo) in enumerate(rangos):
            rect = plt.Rectangle((0, idx), 1, 1, color=color,
                                  transform=ax.transData)
            ax.add_patch(rect)
            label_color = 'white' if tipo != 'neutro' else '#9ca3af'
            ax.text(0.5, idx + 0.5, f'{t0:.1f}–{t1:.1f}°C',
                    ha='center', va='center', fontsize=7.5,
                    color=label_color, fontweight='bold')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, len(rangos))
        ax.axis('off')
        ax.set_title(meses_nombres[mes - 1], color=TEXT_COLOR,
                     fontsize=10, fontweight='bold', pad=4)
        ax.text(0.5, -0.06,
                f'Media: {t_med:.1f}°C  |  T.Neutra: {neutra:.1f}°C',
                ha='center', va='top', fontsize=6.5,
                color='#8892a4', transform=ax.transAxes)

    fig.suptitle('Rangos de Confort Térmico por Mes', color=TEXT_COLOR,
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig.savefig(nombre_archivo, dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    b64 = fig_a_b64(fig)
    plt.close(fig)
    return b64


# ── Blueprint routes ──────────────────────────────────────────────────────────
@lector_epw_bp.route('/procesar-epw', methods=['POST'])
def procesar_epw():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se envió ningún archivo'}), 400

        file = request.files['file']
        if not file.filename.lower().endswith('.epw'):
            return jsonify({'error': 'El archivo debe tener extensión .epw'}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Acceptability mode: 90% = ±2.5°C half-range, 80% = ±3.5°C
        accept_mode_raw = request.form.get('accept_mode', '90')
        # neutral_half = half-width of comfort zone only
        # step is ALWAYS 2.5°C for all bands outside comfort
        if accept_mode_raw == '80':
            neutral_half = 3.5
        elif accept_mode_raw == 'micro':
            neutral_half = 1.25
        else:
            neutral_half = 2.5
        step = 2.5
        half_range = neutral_half  # kept for compatibility

        # Leer metadatos de la primera línea
        with open(filepath, 'r', encoding='latin-1') as f:
            primera_linea = f.readline()
        partes = primera_linea.strip().split(',')
        latitud  = float(partes[6]) if len(partes) > 6 else 0.0
        longitud = float(partes[7]) if len(partes) > 7 else 0.0
        ciudad   = partes[1] if len(partes) > 1 else 'Desconocida'
        pais     = partes[3] if len(partes) > 3 else ''

        # Leer datos climáticos
        df = pd.read_csv(filepath, skiprows=8, header=None, encoding='latin-1')
        if df.empty:
            return jsonify({'error': 'No se pudo leer el EPW'}), 500

        col_indices = {"Mes": 1, "Dia": 2, "Hora": 3,
                       "Temperatura_Aire": 6, "Humedad_Relativa": 8}
        df = df.iloc[:, list(col_indices.values())]
        df.columns = list(col_indices.keys())
        df["Hora"] = df["Hora"].apply(lambda x: x - 1 if x == 24 else x)

        # Cálculos estadísticos
        promedio_por_mes      = df.groupby("Mes")["Temperatura_Aire"].mean()
        temperatura_neutra    = promedio_por_mes.apply(lambda x: 17.8 + 0.31 * x)
        promedio_por_hora_mes = df.groupby(["Mes", "Hora"])["Temperatura_Aire"].mean().reset_index()

        # Construir matriz hora×mes
        tabla_completa = np.full((24, 12), np.nan)
        for _, row in promedio_por_hora_mes.iterrows():
            tabla_completa[int(row["Hora"]), int(row["Mes"]) - 1] = row["Temperatura_Aire"]

        # Construir tabla de colores (step always 2.5, neutral_half defines comfort zone)
        tabla_colores = []
        for hora in range(24):
            fila_colores = []
            for mes in range(1, 13):
                temp = tabla_completa[hora, mes - 1]
                neutra = temperatura_neutra.get(mes, 20)
                if np.isnan(temp):
                    fila_colores.append('#374151')
                else:
                    diff = temp - neutra
                    if abs(diff) <= neutral_half:
                        fila_colores.append('white')
                    elif diff < -neutral_half:
                        idx = min(4, int((abs(diff) - neutral_half) // step))
                        fila_colores.append(AZULES[idx])
                    else:
                        idx = min(4, int((abs(diff) - neutral_half) // step))
                        fila_colores.append(NARANJAS[idx])
            tabla_colores.append(fila_colores)

        # Generar imágenes
        path_heatmap = os.path.join(UPLOAD_FOLDER, 'tabla_hora_mes.png')
        path_mensual = os.path.join(UPLOAD_FOLDER, 'tabla_temperaturas.png')

        b64_heatmap = generar_heatmap(tabla_completa, temperatura_neutra.to_dict(), path_heatmap)
        b64_mensual = generar_tabla_mensual(df, temperatura_neutra.to_dict(),
                                            promedio_por_mes.to_dict(), path_mensual, neutral_half, step)

        # Guardar CSV de colores (incluye latitud)
        csv_path = os.path.join(UPLOAD_FOLDER, 'pintar_celeste.csv')
        with open(csv_path, 'w', newline='') as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow(["MES", "HORA", "COLOR"])
            writer.writerow([f"Latitud: {latitud}", "", ""])
            for hora in range(24):
                for mes in range(1, 13):
                    writer.writerow([mes, hora, tabla_colores[hora][mes - 1]])

        # CSV completo procesado
        archivo_csv = filepath.replace('.epw', '.csv')
        df_res = df.merge(promedio_por_hora_mes, on=["Mes", "Hora"], how="left",
                          suffixes=("", "_Prom"))
        df_res["Temperatura_Promedio_Mes"] = df_res["Mes"].map(promedio_por_mes)
        df_res["Temperatura_Neutra_Mes"] = df_res["Mes"].map(temperatura_neutra)
        df_res = df_res[["Mes", "Dia", "Hora", "Temperatura_Aire_Prom",
                         "Temperatura_Promedio_Mes", "Temperatura_Neutra_Mes"]]
        df_res.columns = ["Mes", "Dia", "Hora", "TempPromedioHora",
                          "TempPromedioMes", "TempNeutraMes"]
        df_res.to_csv(archivo_csv, index=False)

        return jsonify({
            'mensaje': 'EPW procesado correctamente',
            'ciudad': ciudad,
            'pais': pais,
            'latitud': latitud,
            'longitud': longitud,
            'imagen_heatmap_b64': b64_heatmap,
            'imagen_mensual_b64': b64_mensual,
            'imagen_heatmap_url': f'/uploads/tabla_hora_mes.png',
            'imagen_mensual_url': f'/uploads/tabla_temperaturas.png',
            'csv_url': f'/uploads/{os.path.basename(archivo_csv)}',
            'promedio_temperaturas': {str(k): round(v, 2)
                                      for k, v in promedio_por_mes.items()},
            'temperatura_neutra': {str(k): round(v, 2)
                                   for k, v in temperatura_neutra.items()},
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500


# ── Rutas de descarga ─────────────────────────────────────────────────────────
@lector_epw_bp.route('/descargar/<filename>')
def descargar(filename):
    """Permite descargar cualquier archivo generado en uploads/."""
    safe_name = os.path.basename(filename)
    path = os.path.join(UPLOAD_FOLDER, safe_name)
    if not os.path.exists(path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(path, as_attachment=True, download_name=safe_name)
