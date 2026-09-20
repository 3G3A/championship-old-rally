import json
import re
import requests
from bs4 import BeautifulSoup

def obtener_tiempos(rally_id):
    if not rally_id:
        return []
        
    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar la tabla que contiene los tiempos (evitando menús)
        tablas = soup.find_all('table')
        tabla_resultados = None
        
        for t in tablas:
            # La tabla correcta contiene encabezados típicos de resultados
            texto = t.get_text().lower()
            if 'pos' in texto or 'driver' in texto or 'car' in texto or 'stage' in texto:
                tabla_resultados = t
                break
                
        if not tabla_resultados and len(tablas) > 0:
            tabla_resultados = tablas[-1] # Probar con la última tabla si no se detecta por texto

        if not tabla_resultados:
            return []

        filas = tabla_resultados.find_all('tr')
        resultados = []
        posicion = 1

        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        for fila in filas:
            celdas = fila.find_all(['td', 'th'])
            textos = [c.get_text().strip() for c in celdas]

            # Omitir encabezados y filas vacías o con textos de menú
            if not textos or len(textos) < 4 or 'Hotlap' in textos[0] or 'Download' in textos[0]:
                continue
                
            # Validar que la primera celda sea una posición numérica
            if not textos[0].isdigit():
                continue

            nombre_piloto = textos[1]
            coche = textos[2]
            tiempo = textos[-1] # El tiempo total suele ser la última columna

            pts_rally = puntos_escala[posicion - 1] if posicion <= len(puntos_escala) else 1
            pts_ps = 0 # Reservado para la Power Stage

            resultados.append({
                "posicion": posicion,
                "nombre": nombre_piloto,
                "coche": coche,
                "tiempo": tiempo,
                "puntos_rally": pts_rally,
                "puntos_ps": pts_ps,
                "puntos_totales": pts_rally + pts_ps
            })
            posicion += 1

        return resultados

    except Exception as e:
        print(f"Error extrayendo datos: {e}")
        return []

def main():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error cargando config.json: {e}")
        return

    rally_id = config.get('rally_actual_id', '')
    resultados = obtener_tiempos(rally_id)

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Procesados {len(resultados)} pilotos correctamente.")

if __name__ == "__main__":
    main()
