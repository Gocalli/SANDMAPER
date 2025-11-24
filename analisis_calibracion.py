import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit

# 1. CARGAR DATOS
try:
    df = pd.read_csv("calibracion_kinect.csv")
    x_raw = df["Valor_Kinect_Raw"].values
    y_cm = df["Distancia_Real_CM"].values
except FileNotFoundError:
    print("ERROR: No encuentro el archivo 'calibracion_kinect.csv'. Asegúrate de que esté en la misma carpeta.")
    exit()

# 2. DEFINIR LA FUNCION DE CALIBRACION (Modelo Inverso)
# La teoría dice que Distancia = 1 / (m * Raw + b)
def modelo_kinect(raw, m, b):
    return 1.0 / (m * raw + b)

# 3. CALCULAR LOS COEFICIENTES (REGRESION)
# Usamos Scipy para encontrar los mejores 'm' y 'b'
popt, pcov = curve_fit(modelo_kinect, x_raw, y_cm, p0=[-0.00001, 0.1]) # Valores iniciales estimados
m_calculada, b_calculada = popt

print("="*40)
print("      RESULTADOS DE LA CALIBRACIÓN")
print("="*40)
print(f"Ecuación encontrada: Distancia = 1 / ({m_calculada:.6f} * Raw + {b_calculada:.6f})")
print("-" * 40)
print("COPIA ESTA LÍNEA PARA TU CÓDIGO PRINCIPAL:")
print(f"dist_cm = 1.0 / ({m_calculada:.8f} * raw_val + {b_calculada:.8f})")
print("="*40)

# 4. GENERAR GRAFICAS PARA EL INFORME
plt.figure(figsize=(10, 6))

# Puntos reales (Tus mediciones)
plt.scatter(x_raw, y_cm, color='red', label='Datos Medidos (Experimental)')

# Curva teórica (La fórmula)
x_rango = np.linspace(min(x_raw), max(x_raw), 100)
y_predicha = modelo_kinect(x_rango, m_calculada, b_calculada)
plt.plot(x_rango, y_predicha, color='blue', linewidth=2, label=f'Ajuste Teórico: $d = 1/({m_calculada:.2e} \cdot raw + {b_calculada:.2f})$')

plt.title("Curva de Calibración del Sensor Kinect v1")
plt.xlabel("Valor Crudo (Raw 11-bit)")
plt.ylabel("Distancia Real (cm)")
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.legend()
plt.savefig("grafica_calibracion.png") # Guarda la imagen automáticamente
plt.show()