# Solar·Arch — Análisis Bioclimático

<<<<<<< HEAD
Herramienta web para análisis solar y bioclimático: diagrama solar interactivo, visor 3D de modelos arquitectónicos y visualización de datos climáticos desde archivos EPW.
=======
![image](https://github.com/user-attachments/assets/fdbe7ee6-5f10-463d-9ff3-00fa38ca5f37)

In this code, tables and files will be generated allowing you to visualize the 3D solar chart alongside your architectural model, as well as the various temperature data extracted from the EPW file. This program uses the dry bulb temperature as a reference and applies the adaptive comfort temperature equation.

![image](https://github.com/user-attachments/assets/aca72b33-249d-4d87-bd34-75cd0921fc5b)

Based on this reference, a change in temperature or color in the indicators is considered every 2 to 2.5 degrees Celsius.

![image](https://github.com/user-attachments/assets/82d75cd6-d4c0-4989-a68d-09c74f4d205b)

Finally, the solar chart is constructed in both 3D and 2D by making the appropriate projections and considering a bimonthly average of temperatures to generate the color samples in the 3D chart composed of 6x24 panels. This results in an average hourly temperature for each of the 12 months.

![image](https://github.com/user-attachments/assets/7036916c-7af7-4319-a743-bd72700fd1cf)

Results:

![image](https://github.com/user-attachments/assets/91972808-a8b5-4a7b-9cf1-99c109300ff3)

![image](https://github.com/user-attachments/assets/b0e61e28-57f1-4c54-9d21-0b07d63307ea)

![image](https://github.com/user-attachments/assets/5644cc4b-96ea-495d-ab42-34a1874c5c8c)

![image](https://github.com/user-attachments/assets/ab25d1c8-5cb3-485d-9dc8-08f6069867eb)

USE: 
This page is very simple to use, feel free to play around with it. You just need to clone the repository and run app.py, which will start the page and all its features.
Make sure to have all the Python libraries installed by running the following command: pip install -r requirements.txt
>>>>>>> c940b88bbc6cef2fccfae8f25bc3fd3a2edc896e

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
