# Solar·Arch — Análisis Bioclimático

Herramienta web para análisis solar y bioclimático: diagrama solar interactivo, visor 3D de modelos arquitectónicos y visualización de datos climáticos desde archivos EPW.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+, Flask 3, Matplotlib, NumPy, Pandas |
| Frontend | HTML5, Three.js r128, Leaflet.js 1.9, PapaParse |
| Producción | Gunicorn, Linux (Ubuntu 22.04 / Amazon Linux 2) |

---

## Instalación en AWS / Linux

```bash
# 1. Clonar / copiar el proyecto
cd /home/ubuntu/solar_arch

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias (sin basemap, sin X11)
pip install -r requirements.txt

# 4. Crear carpetas necesarias
mkdir -p uploads static

# 5. Iniciar en producción
bash start.sh 5000
```

Para exponer detrás de **nginx** agrega un proxy pass a `http://127.0.0.1:5000`.

---

## Uso

### Diagrama solar
1. Abre la aplicación en el navegador.
2. Haz clic en cualquier punto del mapa o busca una dirección.
3. El diagrama solar polar se genera automáticamente para esa latitud.

### Modelo 3D
- Arrastra un archivo `.obj`, `.mtl` o `.stl` al visor, o usa el botón **Modelo 3D**.
- El modelo se coloca automáticamente **sobre el plano/tabla**.
- Ajusta la **orientación norte** con el slider o los botones +90° / −90°.
- Usa las vistas rápidas: **Top**, **Front**, **Iso**.

### Archivo EPW
1. Haz clic en **Cargar EPW** y selecciona un archivo `.epw`.
2. Se generan automáticamente:
   - **Mapa de calor** hora × mes con escala continua de temperatura.
   - **Tabla de confort térmico** por mes (frío / neutro / cálido).
   - **Esfera solar 3D** coloreada según confort.
3. Descarga las imágenes y el CSV con los botones de la franja inferior.

---

## Estructura del proyecto

```
solar_arch/
├── app.py              # Flask principal + cálculo solar
├── lectorEPW.py        # Blueprint EPW + generación de gráficas
├── wsgi.py             # Entry point gunicorn
├── start.sh            # Script de inicio producción
├── requirements.txt
├── templates/
│   └── index.html      # SPA principal
├── static/             # Imágenes generadas (diagrama solar)
└── uploads/            # Archivos EPW, CSV y tablas generadas
```
