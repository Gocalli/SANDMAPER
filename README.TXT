================================================================
SANDMAPER - Topografía Interactiva AR
================================================================

Bienvenido a SandMapper. Este sistema transforma una caja de arena convencional en un paisaje topográfico interactivo utilizando un sensor Kinect v1 y un proyector digital.

## Requisitos del Sistema

- Hardware:
  - Sensor Microsoft Kinect v1 (Modelo 1414/1473).
  - Proyector (Resolución recomendada: 1280x800).
  - Computadora con Linux.
  - Caja de arena (dimensiones sugeridas: 60x40 cm).

- Software:
  - Python 3.
  - Librerías: `freenect`, `opencv-python`, `numpy`.

## Configuración Inicial y Calibración

Sigue estos pasos la primera vez que instales el sistema o si mueves el Kinect de posición.

### 1. Calibración de Profundidad
Para que el sistema mida correctamente la altura de la arena en centímetros:

1.  Activa el entorno:
    `source sandmapper_env/bin/activate`
2.  Ejecuta el recolector de datos:
    `python3 recolector_datos.py`
3.  Coloca un objeto plano frente al Kinect a una distancia conocida (mide con cinta métrica).
4.  Apunta el cursor al objeto y presiona `Espacio`.
5.  Ingresa la distancia real en cm y presiona `Enter`.
6.  Repite para al menos 5-10 distancias diferentes (ej: entre 40cm y 80cm).
7.  Presiona `q` para salir.
8.  Genera la configuración automática:
    `python3 analisis_calibracion.py`
    Esto creará/actualizará el archivo `config.json`.

### 2. Configuración Geométrica (Ajuste de Imagen)
Para alinear la proyección exactamente con tu caja de arena:

1.  Ejecuta el programa principal:
    `python3 sandmapper_final.py`
2.  Presiona la tecla **'M'** para entrar en el **Modo de Ajuste**.
3.  Verás un recuadro amarillo. Úsalo para encuadrar tu arena:
    - **W / S**: Mover recuadro Arriba/Abajo.
    - **A / D**: Mover recuadro Izquierda/Derecha.
    - **I / K**: Aumentar/Disminuir Altura del recuadro.
    - **J / L**: Aumentar/Disminuir Ancho del recuadro.
4.  Una vez alineado, presiona **'G'** para **Guardar**.
5.  Presiona **'M'** de nuevo para salir del modo ajuste.

### 3. Inclinación del Kinect
Si necesitas ajustar el ángulo físico del sensor:
- Usa las **Flechas Arriba / Abajo** del teclado para mover el motor del Kinect.

## Guía de Uso Diario

Una vez calibrado, solo necesitas ejecutar:

```bash
source sandmapper_env/bin/activate
python3 sandmapper_final.py
```

### Controles de Visualización
Controla cómo se ve el mapa mientras interactúas con la arena:

- **W / S**: Ajusta la **Altura Máxima** (Color rojo/blanco). Si tu montaña se ve "cortada", aumenta este valor.
- **A / D**: Ajusta la **Altura Mínima** (Color azul). Ajusta esto al fondo de tu caja.
- **C**: Cambia la **Paleta de Colores** (Topográfico, Arcoíris, Volcán, etc.).
- **H**: Activa/Desactiva las **Sombras 3D** (Hillshading) para dar relieve.
- **R**: Resetea los valores de visualización a los predeterminados.
- **Q**: Salir del programa.

### Consejos
- Para el mejor efecto, mantén el cuarto con luz tenue.
- Alisa la arena para calibrar la "Altura Mínima" (color azul) correctamente.
- Si el mapa parpadea o no detecta bien, asegúrate de que no haya luz solar directa sobre el sensor Kinect.

## Solución de Problemas
- **Error "Kinect not found"**: Desconecta y reconecta el USB del Kinect. Asegúrate de usar el adaptador de corriente del Kinect.
- **La imagen no llena la pantalla**: El programa está diseñado para proyectores de 1280x800. Si usas otra resolución, el sistema operativo o el proyector deberían escalar la imagen, o puedes editar el código en `cv2.resize`.
