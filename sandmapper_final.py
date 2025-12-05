import cv2
import numpy as np
import freenect
import json
import sys
import time

"""
SandMapper Final - Aplicación de Realidad Aumentada para Caja de Arena
-----------------------------------------------------------------------
Este script captura datos de profundidad de un sensor Kinect v1, aplica una
calibración personalizada para convertir los datos crudos a centímetros, y 
proyecta un mapa topográfico interactivo sobre la arena en tiempo real.

Características:
- Calibración automática cargada desde config.json.
- Recorte de Área de Interés (ROI) ajustable en tiempo real.
- Control de inclinación del motor del Kinect.
- Múltiples paletas de color, incluyendo una topográfica personalizada.
- Simulación de sombras (Hillshading) para efecto 3D.
- Salida optimizada para proyector (1280x800).

Autor: Santiago & Gemini Agent
Fecha: Diciembre 2025
"""

# ==============================
#  CONFIGURACIÓN DE CALIBRACIÓN Y VARIABLES GLOBALES
# ==============================
CONFIG_FILE = "config.json"

# Variables globales para el manejo de Freenect asíncrono
ctx = None
dev = None
last_depth = None

def display_depth_callback(dev, data, timestamp):
    """
    Callback asíncrono que recibe los datos de profundidad del Kinect.
    
    Se ejecuta cada vez que el Kinect tiene un nuevo frame de profundidad disponible.
    Actualiza la variable global 'last_depth' para ser procesada por el hilo principal.

    Args:
        dev: Puntero al dispositivo Kinect.
        data: Array numpy (uint16 o similar) con los datos de profundidad crudos.
        timestamp: Marca de tiempo del frame.
    """
    global last_depth
    last_depth = data

# Carga de configuración
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        M_CALIB = config["calibration"]["m"]
        B_CALIB = config["calibration"]["b"]
        DISTANCIA_FONDO_CAJA = config["box_geometry"]["distancia_fondo_caja"]
        ALTURA_MINIMA = config["visualization"]["altura_minima"]
        ALTURA_MAXIMA = config["visualization"]["altura_maxima"]
        # Cargar ROI
        ROI_X = config.get("roi", {}).get("x", 0)
        ROI_Y = config.get("roi", {}).get("y", 0)
        ROI_W = config.get("roi", {}).get("w", 640)
        ROI_H = config.get("roi", {}).get("h", 480)
        
        print(f"Configuración cargada desde {CONFIG_FILE}")
except FileNotFoundError:
    print(f"ERROR CRÍTICO: No se encontró el archivo '{CONFIG_FILE}'.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Fallo al cargar configuración: {e}")
    sys.exit(1)

def guardar_config_roi(x, y, w, h):
    """
    Guarda la configuración actual de la Región de Interés (ROI) en el archivo JSON.

    Args:
        x (int): Coordenada X de la esquina superior izquierda.
        y (int): Coordenada Y de la esquina superior izquierda.
        w (int): Ancho del ROI.
        h (int): Alto del ROI.

    Returns:
        bool: True si se guardó correctamente, False si hubo error.
    """
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        
        data["roi"] = {
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h)
        }
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("Configuración ROI guardada exitosamente.")
        return True
    except Exception as e:
        print(f"Error al guardar config: {e}")
        return False

def calcular_distancia_cm(depth_raw):
    """
    Convierte una matriz de profundidad 'raw' (cruda) del Kinect a centímetros.

    Utiliza la fórmula de calibración hiperbólica derivada:
    d = 1 / (m * raw + b)

    Args:
        depth_raw (numpy.ndarray): Matriz de profundidad raw del Kinect.

    Returns:
        numpy.ndarray: Matriz de distancias en centímetros. Retorna None si input es None.
    """
    if depth_raw is None:
        return None
    
    # Convertimos a float para precisión
    depth_raw = depth_raw.astype(np.float32)

    # Fórmula de calibración
    denominador = (M_CALIB * depth_raw) + B_CALIB
    
    # Evitar división por cero
    denominador[np.abs(denominador) < 0.0001] = 0.0001 
    
    distancia_cm = np.reciprocal(denominador)
    return distancia_cm

def apply_hillshade(height_map_uint8, azimuth=315.0, altitude=45.0):
    """
    Genera un mapa de sombras (Hillshade) para simular relieve 3D.

    Calcula la iluminación de la superficie basándose en gradientes de altura.

    Args:
        height_map_uint8 (numpy.ndarray): Mapa de alturas normalizado (0-255).
        azimuth (float): Dirección de la fuente de luz en grados (0-360).
        altitude (float): Altura de la fuente de luz en grados (0-90).

    Returns:
        numpy.ndarray: Mapa de sombras normalizado (0.0 a 1.0).
    """
    grad_x, grad_y = np.gradient(height_map_uint8.astype(float))
    azimuth_rad = np.radians(azimuth)
    altitude_rad = np.radians(altitude)
    
    # Cálculo de pendiente y aspecto
    slope = np.pi/2.0 - np.arctan(np.sqrt(grad_x**2 + grad_y**2))
    aspect = np.arctan2(-grad_x, grad_y)
    
    # Cálculo de iluminación (Lambertiana)
    shaded = np.sin(altitude_rad) * np.sin(slope) + \
             np.cos(altitude_rad) * np.cos(slope) * \
             np.cos(azimuth_rad - aspect)
             
    # Normalizar a rango 0-1
    shaded = (shaded + 1) / 2.0
    return np.clip(shaded, 0, 1)

def crear_paleta_cartografica():
    """
    Genera una tabla de búsqueda de colores (LUT) personalizada con estilo topográfico.

    Interpola linealmente entre una serie de colores clave (Azul, Cyan, Arena, Verde, Marrón, Blanco)
    para crear una transición suave que represente diferentes elevaciones geográficas.

    Returns:
        numpy.ndarray: LUT de 256 colores con forma (256, 3) tipo uint8.
    """
    # Hitos: (Indice 0-255, (B, G, R))
    key_colors = [
        (0,   (128, 0, 0)),      # Azul Oscuro (Profundo)
        (90,  (255, 255, 0)),    # Cyan (Agua baja)
        (100, (180, 228, 255)),  # Arena (Beige)
        (150, (34, 139, 34)),    # Verde Bosque
        (200, (19, 69, 139)),    # Marron Tierra
        (240, (100, 100, 100)),  # Gris Roca
        (255, (255, 255, 255))   # Blanco Nieve
    ]
    
    lut = np.zeros((256, 3), dtype=np.uint8)
    
    prev_idx, prev_color = key_colors[0]
    lut[0] = prev_color # Asegurar inicio
    
    for idx, color in key_colors[1:]:
        len_tramo = idx - prev_idx
        for i in range(3): # Canales B, G, R
            lut[prev_idx:idx, i] = np.linspace(prev_color[i], color[i], len_tramo, endpoint=False)
        prev_idx = idx
        prev_color = color
        
    lut[255] = key_colors[-1][1] # Asegurar final
    return lut

# Generamos la paleta custom al iniciar
LUT_CARTOGRAFICA = crear_paleta_cartografica()

PALETAS = [
    ("Topografico (Custom)", LUT_CARTOGRAFICA),
    ("Jet (Clasico)", cv2.COLORMAP_JET),
    ("Oceano", cv2.COLORMAP_OCEAN),
    ("Magma (Volcan)", cv2.COLORMAP_MAGMA),
    ("Invierno", cv2.COLORMAP_WINTER),
    ("Arcoiris", cv2.COLORMAP_RAINBOW),
    ("Hueso (Gris)", cv2.COLORMAP_BONE)
]

def generar_mapa_topografico(distancia_cm, min_h, max_h, paleta_idx=0, hillshade=False):
    """
    Procesa la matriz de distancias y genera la visualización topográfica final.

    Pasos:
    1. Calcula la altura de la arena respecto al fondo.
    2. Recorta y normaliza los valores al rango [min_h, max_h].
    3. Aplica suavizado gaussiano.
    4. Colorea usando la paleta seleccionada.
    5. Opcionalmente aplica sombreado (hillshade).
    6. Dibuja curvas de nivel (contornos).

    Args:
        distancia_cm (numpy.ndarray): Matriz de distancias reales.
        min_h (float): Altura mínima de visualización (cm).
        max_h (float): Altura máxima de visualización (cm).
        paleta_idx (int): Índice de la paleta de colores a usar.
        hillshade (bool): Si aplicar o no el efecto de sombreado.

    Returns:
        tuple: (imagen_coloreada, nombre_paleta)
    """
    # 1. Calcular altura de la arena (Fondo - Distancia medida)
    altura_arena = DISTANCIA_FONDO_CAJA - distancia_cm
    
    # 2. Clipping para asegurar rango válido
    np.maximum(altura_arena, min_h, out=altura_arena)
    np.minimum(altura_arena, max_h, out=altura_arena)
    
    # 3. Normalización a 8-bit (0-255)
    rango = max_h - min_h
    if rango < 1.0: rango = 1.0
    
    altura_norm = (altura_arena - min_h) / rango
    altura_uint8 = (altura_norm * 255).astype(np.uint8)
    
    # 4. Suavizado para reducir ruido y mejorar curvas
    altura_blur = cv2.GaussianBlur(altura_uint8, (5, 5), 0)
    
    # 5. Aplicación de Color
    nombre_paleta, id_paleta_o_lut = PALETAS[paleta_idx % len(PALETAS)]
    
    if isinstance(id_paleta_o_lut, int):
        # Paleta estándar de OpenCV
        mapa_color = cv2.applyColorMap(altura_blur, id_paleta_o_lut)
    else:
        # LUT Custom (numpy array)
        mapa_color = id_paleta_o_lut[altura_blur]
    
    # 6. Aplicación de Hillshading (opcional)
    if hillshade:
        shading = apply_hillshade(altura_blur)
        shading_3d = np.dstack((shading, shading, shading))
        # Mezclar color con sombras
        mapa_color = (mapa_color.astype(float) * shading_3d).astype(np.uint8)

    # 7. Dibujado de Curvas de Nivel
    # Se dibujan contornos en intervalos regulares de altura (intensidad de pixel)
    for i in range(10, 250, 40):
        _, thresh = cv2.threshold(altura_blur, i, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mapa_color, contours, -1, (0, 0, 0), 1)

    return mapa_color, nombre_paleta

def main():
    """
    Función principal. Configura el Kinect, inicializa ventanas y ejecuta el bucle de visualización.
    """
    global ctx, dev, last_depth

    print(f"Iniciando SandMapper Calibrado...")
    print(f"Usando fórmula: d = 1 / ({M_CALIB:.5f} * raw + {B_CALIB:.3f})")
    print("CONTROLES: [W/S] Max Altura | [A/D] Min Altura | [C] Color | [H] Sombra | [R] Reset | [Q] Salir")
    print("AJUSTE ROI: [M] Modo Ajuste | [G] Guardar ROI")
    print("CONTROL KINECT: [Flechas Arriba/Abajo] Inclinacion")

    # --- INICIALIZACIÓN KINECT (Modo Manual para soportar Motor) ---
    try:
        ctx = freenect.init()
        # Seleccionamos el primer dispositivo (índice 0)
        dev = freenect.open_device(ctx, 0)
        
        # Configurar modo de profundidad
        freenect.set_depth_mode(dev, freenect.RESOLUTION_MEDIUM, freenect.DEPTH_11BIT)
        freenect.set_depth_callback(dev, display_depth_callback)
        freenect.start_depth(dev)
        
        print("Kinect inicializado correctamente.")
        
        # Obtener ángulo inicial del motor
        freenect.update_tilt_state(dev)
        state = freenect.get_tilt_state(dev)
        kinect_tilt_angle = freenect.get_tilt_degs(state)
        print(f"Angulo inicial: {kinect_tilt_angle} grados")
        
    except Exception as e:
        print(f"ERROR CRÍTICO al inicializar Kinect: {e}")
        print("Asegurate de que el Kinect esta conectado y no esta siendo usado por otro programa.")
        if dev: freenect.close_device(dev)
        if ctx: freenect.shutdown(ctx)
        sys.exit(1)

    # Variables de estado de visualización
    cur_min_h = ALTURA_MINIMA
    cur_max_h = ALTURA_MAXIMA
    cur_paleta = 0
    usar_hillshade = False
    
    # Variables de ROI (Región de Interés)
    roi_x, roi_y = ROI_X, ROI_Y
    roi_w, roi_h = ROI_W, ROI_H
    modo_ajuste = False
    
    tilt_step = 1 # Grados por pulsación

    try:
        while True:
            # Procesar eventos de freenect (crítico para callbacks y motor)
            freenect.process_events(ctx)
            
            if last_depth is None:
                continue
            
            # Copiamos el frame para procesarlo sin bloqueos
            d_raw = last_depth.copy()
            d_cm = calcular_distancia_cm(d_raw)
            
            # --- APLICAR RECORTE (ROI) ---
            # Aseguramos que las coordenadas estén dentro de los límites de la imagen
            max_h_img, max_w_img = d_cm.shape
            roi_x = max(0, min(roi_x, max_w_img - 10))
            roi_y = max(0, min(roi_y, max_h_img - 10))
            roi_w = max(10, min(roi_w, max_w_img - roi_x))
            roi_h = max(10, min(roi_h, max_h_img - roi_y))
            
            d_cm_recortado = d_cm[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            
            # Generar mapa
            imagen_final, nombre_paleta = generar_mapa_topografico(d_cm_recortado, cur_min_h, cur_max_h, cur_paleta, usar_hillshade)
            
            # Redimensionar a resolución nativa del proyector (1280x800)
            imagen_final = cv2.resize(imagen_final, (1280, 800), interpolation=cv2.INTER_CUBIC)
            
            # --- OSD (On Screen Display) ---
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            if modo_ajuste:
                info_txt = [
                    "--- MODO AJUSTE GEOMETRICO ---",
                    f"X: {roi_x} Y: {roi_y} (WASD Mover)",
                    f"W: {roi_w} H: {roi_h} (J/L Ancho, I/K Alto)",
                    "Presiona [G] para Guardar, [M] Salir"
                ]
                color_texto = (0, 255, 255) # Amarillo
                # Dibujar marco guía
                cv2.rectangle(imagen_final, (0,0), (1279, 799), (0, 255, 255), 4)
            else:
                info_txt = [
                    f"Min H: {cur_min_h:.1f} cm (A/D)",
                    f"Max H: {cur_max_h:.1f} cm (W/S)",
                    f"Paleta: {nombre_paleta} (C)",
                    f"Sombra 3D: {'ON' if usar_hillshade else 'OFF'} (H)",
                    f"Inclinacion: {kinect_tilt_angle:.1f} deg (Flechas)",
                    f"[M] Ajustar Area ({roi_w}x{roi_h})"
                ]
                color_texto = (255, 255, 255) # Blanco

            y_pos = 30
            for txt in info_txt:
                cv2.putText(imagen_final, txt, (10, y_pos), font, 0.6, color_texto, 2)
                cv2.putText(imagen_final, txt, (10, y_pos), font, 0.6, (0, 0, 0), 1)
                y_pos += 30
            
            # Mostrar altura en el centro de la ROI
            h_rec, w_rec = d_cm_recortado.shape
            centro_val = d_cm_recortado[h_rec//2, w_rec//2]
            altura_centro = DISTANCIA_FONDO_CAJA - centro_val
            cv2.putText(imagen_final, f"Centro: {altura_centro:.1f} cm", (10, y_pos + 10), font, 0.6, (100, 255, 100), 2)
            
            # Ventana Fullscreen
            cv2.namedWindow('SandMapper Final', cv2.WINDOW_NORMAL)
            cv2.setWindowProperty('SandMapper Final', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow('SandMapper Final', imagen_final)
            
            # Manejo de teclado
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('m'):
                modo_ajuste = not modo_ajuste
            elif key == ord('g') and modo_ajuste:
                guardar_config_roi(roi_x, roi_y, roi_w, roi_h)
                
            if modo_ajuste:
                # Controles de geometría (ROI)
                step_pos = 2
                step_size = 2
                if key == ord('w'): roi_y -= step_pos
                elif key == ord('s'): roi_y += step_pos
                elif key == ord('a'): roi_x -= step_pos
                elif key == ord('d'): roi_x += step_pos
                elif key == ord('i'): roi_h -= step_size
                elif key == ord('k'): roi_h += step_size
                elif key == ord('j'): roi_w -= step_size
                elif key == ord('l'): roi_w += step_size
            else:
                # Controles de visualización y motor
                if key == ord('w'): cur_max_h += 0.5
                elif key == ord('s'): cur_max_h -= 0.5
                elif key == ord('d'): cur_min_h += 0.5
                elif key == ord('a'): cur_min_h -= 0.5
                elif key == ord('c'): cur_paleta += 1
                elif key == ord('h'): usar_hillshade = not usar_hillshade
                elif key == ord('r'):
                    cur_min_h = ALTURA_MINIMA
                    cur_max_h = ALTURA_MAXIMA
                    cur_paleta = 0
                    usar_hillshade = False
                elif key == 82 or key == 2490368: # Flecha Arriba
                    kinect_tilt_angle = min(28, kinect_tilt_angle + tilt_step)
                    freenect.set_tilt_degs(dev, kinect_tilt_angle)
                elif key == 84 or key == 2621440: # Flecha Abajo
                    kinect_tilt_angle = max(-28, kinect_tilt_angle - tilt_step)
                    freenect.set_tilt_degs(dev, kinect_tilt_angle)

    except KeyboardInterrupt:
        print("Deteniendo por interrupción de teclado...")
    finally:
        print("Cerrando conexión Kinect y liberando recursos...")
        if dev:
            freenect.stop_depth(dev)
            freenect.close_device(dev)
        if ctx:
            freenect.shutdown(ctx)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()