import cv2
import numpy as np
import freenect

# ==============================
#  CONFIGURACIÓN DE CALIBRACIÓN
# ==============================

# 1. Valores de calibración obtenidos experimentalmente
M_CALIB = -0.00002918  
B_CALIB = 0.03172860

# 2. GEOMETRÍA DE LA CAJA
# Distancia desde el Kinect hasta el fondo de madera de la caja (en cm)
DISTANCIA_FONDO_CAJA = 60.0  

# Rango de alturas para colorear (en cm de arena)
ALTURA_MINIMA = 0.0   # Nivel del mar (fondo de la caja)
ALTURA_MAXIMA = 12.0  # Cima de la montaña más alta esperada

def obtener_profundidad_cm():
    """
    Obtiene raw depth y la convierte a centimetros.
    """
    depth_raw, _ = freenect.sync_get_depth()
    if depth_raw is None:
        return None

    # Convertimos a float para poder multiplicar con decimales
    depth_raw = depth_raw.astype(np.float32)

    # --- APLICAMOS LA FÓRMULA MATEMÁTICA ---
    # d = 1 / (m * raw + b)
    # Usamos np.reciprocal que es lo mismo que (1 / x) pero más rápido y seguro
    denominador = (M_CALIB * depth_raw) + B_CALIB
    
    # Evitamos división por cero (donde el denominador sea muy pequeño)
    denominador[np.abs(denominador) < 0.0001] = 0.0001 
    
    distancia_cm = np.reciprocal(denominador)

   
    return distancia_cm

def generar_mapa_topografico(distancia_cm):
    """
    Convierte la matriz de distancias en un mapa de colores por altura.
    """
    # 1. CALCULAR ALTURA DE LA ARENA
    # Altura = (Fondo) - (Lo que mide el sensor)
    altura_arena = DISTANCIA_FONDO_CAJA - distancia_cm
    
    # 2. LIMPIEZA DE RUIDO (CLIPPING)
    np.maximum(altura_arena, ALTURA_MINIMA, out=altura_arena)
    # Todo lo que sea más alto que el máximo, lo cortamos.
    np.minimum(altura_arena, ALTURA_MAXIMA, out=altura_arena)
    
    # 3. NORMALIZACIÓN PARA COLOR (0 a 255)
    # 0 = Altura Mínima (Azul), 255 = Altura Máxima (Rojo)
    altura_norm = (altura_arena - ALTURA_MINIMA) / (ALTURA_MAXIMA - ALTURA_MINIMA)
    altura_uint8 = (altura_norm * 255).astype(np.uint8)
    
    # 4. FILTRO DE SUAVIZADO (Importante para que no tiemble)
    altura_blur = cv2.GaussianBlur(altura_uint8, (5, 5), 0)
    
    # 5. COLOREADO
    # OpenCV usa BGR. El mapa 'JET' va de Azul(0) a Rojo(255)
    mapa_color = cv2.applyColorMap(altura_blur, cv2.COLORMAP_JET)
    
    # 6. CURVAS DE NIVEL
    # Usamos umbralización por pasos para dibujar contornos
    for i in range(10, 250, 40): # Dibuja una línea cada cierto intervalo
        _, thresh = cv2.threshold(altura_blur, i, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mapa_color, contours, -1, (0, 0, 0), 1)

    return mapa_color

def main():
    print(f"Iniciando SandMapper Calibrado...")
    print(f"Usando fórmula: d = 1 / ({M_CALIB:.5f} * raw + {B_CALIB:.3f})")
    
    while True:
        d_cm = obtener_profundidad_cm()
        if d_cm is None:
            continue
        

        # --- NUEVO: IMPRIMIR EL VALOR CENTRAL ---
        centro = d_cm[240, 320] # Pixel del centro
        print(f"Distancia detectada: {centro:.1f} cm")
        # ----------------------------------------


        imagen_final = generar_mapa_topografico(d_cm)
        
        cv2.imshow('SandMapper Final', imagen_final)
        
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
