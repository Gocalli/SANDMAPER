import freenect
import cv2
import numpy as np
import csv
import time

# Nombre del archivo donde se guardarán los datos
ARCHIVO_SALIDA = "calibracion_kinect.csv"

def get_depth():
    """Obtiene una imagen de profundidad del Kinect"""
    depth, _ = freenect.sync_get_depth()
    if depth is None:
        return None
    return depth

def medir_centro(depth_map, radio=10):
    """
    Calcula el promedio de profundidad en el centro de la imagen.
    """
    h, w = depth_map.shape
    cy, cx = h // 2, w // 2
    
    # Recortar la zona central (ROI)
    zona_central = depth_map[cy-radio:cy+radio, cx-radio:cx+radio]
    
    # Calcular promedio ignorando ceros (zonas sin datos)
    # Los valores 2047 suelen ser error también, los filtramos si es necesario
    datos_validos = zona_central[zona_central < 2047]
    
    if len(datos_validos) == 0:
        return 0
    
    return np.mean(datos_validos)

def guardar_dato(distancia_real, valor_raw):
    with open(ARCHIVO_SALIDA, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([distancia_real, valor_raw])
    print(f"--> Guardado: {distancia_real} cm = {valor_raw:.2f} raw")

def main():
    print("--- RECOLECTOR DE DATOS KINECT ---")
    print("1. Coloca la caja.")
    print("2. Mide la distancia real con una cinta métrica.")
    print("3. Presiona 'ESPACIO' para capturar y guardar el dato.")
    print("4. Presiona 'q' para salir.")
    
    # Crear archivo CSV con encabezados
    with open(ARCHIVO_SALIDA, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Distancia_Real_CM", "Valor_Kinect_Raw"])

    while True:
        depth = get_depth()
        if depth is None:
            continue
            
        # Convertir a 8-bit para visualizar.
        depth_visual = (depth / 2048.0 * 255).astype(np.uint8)
        
        # Dibujar un cuadro en el centro.
        h, w = depth_visual.shape
        cv2.rectangle(depth_visual, (w//2 - 10, h//2 - 10), (w//2 + 10, h//2 + 10), (255), 2)
        
        # Mostrar valor en tiempo real en pantalla
        valor_actual = medir_centro(depth)
        cv2.putText(depth_visual, f"Raw: {valor_actual:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255), 2)

        cv2.imshow('Apunta al centro de la caja', depth_visual)
        
        key = cv2.waitKey(10) & 0xFF
        
        # CAPTURAR DATO (TECLA ESPACIO)
        if key == 32:  # 32 es Espacio
            # Promediar 30 cuadros para mayor precisión
            print("Promediando 30 cuadros... no muevas la caja.")
            acumulador = []
            for _ in range(30):
                d = get_depth()
                val = medir_centro(d)
                if val > 0: acumulador.append(val)
                time.sleep(0.01)
            
            if len(acumulador) > 0:
                promedio_raw = np.mean(acumulador)
                try:
                    dist_real = input("Introduce la distancia REAL en cm (ej: 50): ")
                    guardar_dato(dist_real, promedio_raw)
                except ValueError:
                    print("Error: Introduce un número válido.")
            else:
                print("Error: No se detectó profundidad válida (Zona ciega o muy lejos).")

        # SALIR
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()