import requests
from bs4 import BeautifulSoup
import json
import os

# Reparto de puntos
PUNTOS_RALLY = [50, 45, 42, 40]
p = 38
while p > 0:
    PUNTOS_RALLY.append(p)
    p -= 2

PUNTOS_PS = [8, 7, 6, 5, 4, 3, 2, 1]

def Cargar_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def extraer_resultados_rsf(rally_id):
    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        pilotos = []
        
        # Buscar la tabla principal de resultados
        filas = soup.find_all('tr')
        pos = 1
        for fila in filas:
            cols = fila.find_all('td')
            if len(cols) >= 5:
                nombre = cols[1].text.strip()
                coche = cols[2].text.strip() if len(cols) > 2 else ""
                tiempo = cols[4].text.strip() if len(cols) > 4 else ""
                
                # Descartar cabeceras o filas vacías
                if nombre and tiempo and "Driver" not in nombre and "Piloto" not in nombre:
                    pts_rally = PUNTOS_RALLY[pos - 1] if pos <= len(PUNTOS_RALLY) else 0
                    
                    pilotos.append({
                        "posicion": pos,
                        "nombre": nombre,
                        "coche": coche,
                        "tiempo": tiempo,
                        "puntos_rally": pts_rally,
                        "puntos_ps": 0,
                        "puntos_totales": pts_rally
                    })
                    pos += 1
        return pilotos
    except Exception as e:
        print(f"Error procesando rally {rally_id}: {e}")
        return []

def main():
    config = Cargar_config()
    if not config or not config.get('rally_actual_id'):
        print("No se encontró ID de rally activo en config.json")
        return

    rally_id = config['rally_actual_id']
    print(f"Obteniendo tiempos del Rally ID: {rally_id}")
    
    resultados_actuales = extraer_resultados_rsf(rally_id)
    
    # Cargar datos históricos existentes para calcular la general
    historico = {}
    if os.path.exists('resultados.json'):
        with open('resultados.json', 'r', encoding='utf-8') as f:
            datos_previos = json.load(f)
            historico = datos_previos.get('clasificacion_general', {})

    # Guardar los nuevos resultados
    salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados_actuales,
        "clasificacion_general": historico # Se irá acumulando
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(salida, f, indent=2, ensure_ascii=False)
        
    print("Resultados actualizados correctamente en resultados.json")

if __name__ == "__main__":
    main()
