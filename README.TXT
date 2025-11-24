================================================================
# Sandmapper - Caja de Arena de Realidad Aumentada con Kinect v1
================================================================

Este proyecto utiliza un sensor Kinect de Xbox 360 para crear un mapa topográfico interactivo sobre una caja de arena. La profundidad de la arena se convierte en un mapa de colores con curvas de nivel, proyectando una topografía virtual que cambia en tiempo real según se moldea la arena.

## Estructura del Proyecto

El proyecto se compone de varios archivos clave:

- `recolector_datos.py`:
  - **Propósito**: Herramienta para capturar los datos necesarios para calibrar el sensor.
  - **Funcionamiento**: Muestra la vista de profundidad del Kinect y permite guardar pares de valores: la distancia real (medida manualmente en cm) y el valor "crudo" (raw) que entrega el sensor para esa distancia. Los datos se guardan en `calibracion_kinect.csv`.

- `analisis_calibracion.py`:
  - **Propósito**: Analiza los datos recolectados y calcula la fórmula matemática para convertir el valor raw del Kinect a centímetros.
  - **Funcionamiento**: Lee `calibracion_kinect.csv`, aplica una regresión no lineal para encontrar los coeficientes de la ecuación de calibración, muestra la ecuación resultante por consola y guarda una gráfica (`grafica_calibracion.png`) que visualiza la curva de ajuste.

- `sandmapper_final.py`:
  - **Propósito**: Es la aplicación principal que corre el mapa topográfico.
  - **Funcionamiento**: Usa la fórmula de calibración para obtener mediciones de distancia en cm. Luego, calcula la altura de la arena basándose en la distancia al fondo de la caja y genera un mapa de colores (de azul para lo más bajo a rojo para lo más alto) con curvas de nivel que se actualiza en tiempo real.

- `calibracion_kinect.csv`:
  - Archivo generado por `recolector_datos.py`. Contiene las mediciones para la calibración.

- `grafica_calibracion.png`:
  - Imagen generada por `analisis_calibracion.py` que muestra la calidad del ajuste de la calibración.

- `README.TXT`:
  - Este mismo archivo, con la documentación del proyecto.

## ¿Cómo Usarlo?

Sigue estos pasos en orden para poner en marcha el sistema.

### Paso 1: Recolectar Datos para Calibración

Este es el paso más importante para que las mediciones sean precisas.

1.  **Ejecuta el script de recolección**:
    ```bash
    python3 recolector_datos.py
    ```
2.  **Prepara la caja**: Coloca un objeto plano (como una tabla o la propia base de la caja vacía) a una distancia conocida del Kinect. Mide esta distancia con una cinta métrica.
3.  **Captura los datos**:
    - En la ventana que aparece, apunta el centro (marcado con un rectángulo) al objeto.
    - Presiona la **barra espaciadora**. El script promediará varias lecturas para mayor precisión.
    - Introduce en la terminal la distancia real que mediste (en cm) y presiona Enter.
4.  **Repite**: Repite el proceso para diferentes distancias (se recomienda un mínimo de 10 puntos, cubriendo el rango de alturas de tu caja, por ejemplo, desde 40 cm hasta 60 cm).
5.  **Finaliza**: Presiona la tecla `q` para cerrar el recolector. Esto habrá creado o actualizado el archivo `calibracion_kinect.csv`.

### Paso 2: Analizar y Obtener la Ecuación de Calibración

Una vez que tienes los datos, necesitas la fórmula.

1.  **Ejecuta el script de análisis**:
    ```bash
    python3 analisis_calibracion.py
    ```
2.  **Observa los resultados**: El script imprimirá en la consola la ecuación de calibración encontrada. Algo como:
    `dist_cm = 1.0 / (-0.00002918 * raw_val + 0.03172860)`
3.  **Actualiza el código principal**: Copia la línea de la ecuación y pégala en el script `sandmapper_final.py`, reemplazando los valores de las constantes `M_CALIB` y `B_CALIB` con los nuevos. El script también guarda la gráfica `grafica_calibracion.png` para que compruebes visualmente que los puntos se ajustan bien a la curva.

### Paso 3: Ejecutar el Sandmapper

¡Es hora de ver la magia!

1.  **Asegúrate de que la calibración esté actualizada** en `sandmapper_final.py`.
2.  **Ejecuta el script principal**:
    ```bash
    python3 sandmapper_final.py
    ```
3.  **Disfruta**: Apunta el Kinect a tu caja de arena. Verás cómo se forma un mapa topográfico de colores sobre la superficie. Moldea la arena y observa cómo el mapa cambia en tiempo real.
4.  **Finaliza**: Presiona `q` para cerrar la aplicación.

========================================
      RESULTADOS DE LA CALIBRACIÓN (Ejemplo)
========================================
Ecuación encontrada: Distancia = 1 / (-0.000029 * Raw + 0.031729)
----------------------------------------
COPIA ESTA LÍNEA PARA TU CÓDIGO PRINCIPAL:
dist_cm = 1.0 / (-0.00002918 * raw_val + 0.03172860)
========================================