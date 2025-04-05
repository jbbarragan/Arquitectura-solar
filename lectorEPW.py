from flask import Blueprint, request, jsonify
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

lector_epw_bp = Blueprint('lector_epw', __name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@lector_epw_bp.route('/procesar-epw', methods=['POST'])
def procesar_epw():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se envió ningún archivo'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        print(f"Archivo guardado en: {filepath}")

        if not os.path.exists(filepath):
            return jsonify({'error': 'Error al guardar el archivo'}), 500

        # Procesar el archivo EPW
        archivo_csv = filepath.replace('.epw', '.csv')
        df = pd.read_csv(filepath, skiprows=8, header=None)

        if df.empty:
            return jsonify({'error': 'No se pudo leer el archivo EPW correctamente'}), 500

        columnas = {
            "Mes": 1,
            "Día": 2,
            "Hora": 3,
            "Temperatura_Aire": 6,
            "Sensación_Térmica": 25
        }

        df = df.iloc[:, list(columnas.values())]
        df.columns = columnas.keys()
        df["Hora"] = df["Hora"].apply(lambda x: x - 1 if x == 24 else x)
        
        # Calcular el promedio de temperatura del aire por mes
        promedio_por_mes = df.groupby("Mes")["Temperatura_Aire"].mean()
        
        # Calcular la temperatura neutra del mes
        temperatura_neutra = promedio_por_mes.apply(lambda x: 17.8 + (0.31 * x))
        
        # Calcular el promedio de temperaturas por hora de cada mes entre 6AM y 6PM
        df_dia = df[(df["Hora"] >= 6) & (df["Hora"] <= 18)]
        promedio_por_hora_mes = df_dia.groupby(["Mes", "Hora"])["Temperatura_Aire"].mean().reset_index()

        # Tonos personalizados
        colores_azules = ["#cce5ff", "#99ccff", "#66b2ff", "#3399ff", "#0073e6"]
        colores_naranjas = ["#ffe0cc", "#ffb366", "#ff9933", "#ff8000", "#cc6600"]

        # Tabla por mes (como antes)
        fig, axes = plt.subplots(3, 4, figsize=(15, 10))
        axes = axes.flatten()
        
        for mes in range(1, 13):
            temp_neutra = temperatura_neutra.get(mes, 0)
            temp_min = df[df["Mes"] == mes]["Temperatura_Aire"].min()
            temp_max = df[df["Mes"] == mes]["Temperatura_Aire"].max()
            
            rangos = []

            # Frías
            temp_actual = temp_neutra
            for i in range(len(colores_azules)):
                temp_actual -= 2
                if temp_actual < temp_min:
                    break
                rangos.insert(0, (temp_actual, temp_actual + 2, colores_azules[i]))

            # Neutra
            rangos.append((temp_neutra - 1, temp_neutra + 1, "white"))

            # Cálidas
            temp_actual = temp_neutra + 2
            for i in range(len(colores_naranjas)):
                if temp_actual > temp_max:
                    break
                rangos.append((temp_actual, temp_actual + 2, colores_naranjas[i]))
                temp_actual += 2
            
            ax = axes[mes - 1]
            table_data = [["", f"{r[0]:.1f}-{r[1]:.1f}°C", ""] for r in rangos]
            table = ax.table(cellText=table_data, colLabels=["", f"Mes {mes}", ""], loc='center', cellLoc='center')
            
            for i, (_, _, color) in enumerate(rangos):
                for j in range(3):
                    table[(i + 1, j)].set_facecolor(color)
            
            ax.text(0.5, -0.1, f"Min: {temp_min:.1f}°C | Max: {temp_max:.1f}°C",
                    fontsize=8, ha='center', transform=ax.transAxes)
            
            ax.axis("off")
        
        plt.tight_layout()
        plt.savefig("uploads/tabla_temperaturas.png")
        print("Imagen de tablas de temperaturas generada en uploads/tabla_temperaturas.png")

        # NUEVA FUNCIÓN: tabla completa de 24h x 12 meses
        tabla_completa = np.full((24, 12), np.nan)
        for _, row in promedio_por_hora_mes.iterrows():
            tabla_completa[int(row["Hora"]), int(row["Mes"]) - 1] = row["Temperatura_Aire"]

        fig, ax = plt.subplots(figsize=(12, 8))
        col_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                      "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        row_labels = [f"{h:02d}:00" for h in range(24)]

        tabla_datos = []
        tabla_colores = []

        for hora in range(24):
            fila_datos = []
            fila_colores = []
            for mes in range(1, 13):
                temp = tabla_completa[hora, mes - 1]
                neutra = temperatura_neutra.get(mes, 0)
                if pd.isna(temp):
                    fila_datos.append("")
                    fila_colores.append("grey")
                else:
                    fila_datos.append(f"{temp:.1f}")
                    diff = temp - neutra
                    if abs(diff) <= 1:
                        fila_colores.append("white")
                    elif diff < -1:
                        idx = min(4, int(abs(diff) // 2))
                        fila_colores.append(colores_azules[idx])
                    elif diff > 1:
                        idx = min(4, int(abs(diff) // 2))
                        fila_colores.append(colores_naranjas[idx])
            tabla_datos.append(fila_datos)
            tabla_colores.append(fila_colores)

        tabla = ax.table(cellText=tabla_datos, rowLabels=row_labels, colLabels=col_labels,
                         cellLoc='center', loc='center')
        tabla.scale(1, 1.5)

        for i in range(24):
            for j in range(12):
                tabla[(i+1, j)].set_facecolor(tabla_colores[i][j])

        ax.axis("off")
        plt.tight_layout()
        plt.savefig("uploads/tabla_hora_mes.png")
        print("Imagen hora-mes generada en uploads/tabla_hora_mes.png")

        # Crear CSV procesado
        df_resultado = df.merge(promedio_por_hora_mes, on=["Mes", "Hora"], how="left", suffixes=("", "_Promedio_Hora"))
        df_resultado["Temperatura_Promedio_Mes"] = df_resultado["Mes"].map(promedio_por_mes)
        df_resultado["Temperatura_Neutra_Mes"] = df_resultado["Mes"].map(temperatura_neutra)
        df_resultado = df_resultado[["Mes", "Día", "Hora", "Temperatura_Aire_Promedio_Hora", "Temperatura_Promedio_Mes", "Temperatura_Neutra_Mes"]]
        df_resultado.columns = ["Mes", "Día", "Hora", "TemperaturaPromedioHora", "TemperaturaPromedioDelMes", "TemperaturaNeutraDelMes"]
        
        df_resultado.to_csv(archivo_csv, index=False)
        print(f"Archivo CSV generado en: {archivo_csv}")
        df_dia_21 = df_resultado[df_resultado["Día"] == 21]
        
        return jsonify({
            'mensaje': 'Archivo procesado correctamente',
            'csv_path': archivo_csv,
            'imagen_temperaturas': 'uploads/tabla_temperaturas.png',
            'imagen_hora_mes': 'uploads/tabla_hora_mes.png',
            'promedio_temperaturas': promedio_por_mes.to_dict(),
            'temperatura_neutra': temperatura_neutra.to_dict(),
            'promedio_temperaturas_horas': promedio_por_hora_mes.set_index(["Mes", "Hora"]).to_dict()["Temperatura_Aire"],
            'datos_dia_21': df_dia_21.to_dict(orient='records')
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500
