import json
import re
import urllib.request

def obtener_tiempos(rally_id):
    if not rally_id:
        return []
        
    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Buscar las filas de la tabla de resultados mediante expresiones regulares
        # Filtra únicamente filas que contengan celdas TD de tablas
        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        
        resultados = []
        posicion = 1
        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        for fila in filas:
            # Extraer el texto limpio dentro de cada TD
            celdas = re.findall(r'<td[^>]*>(.*?)</td>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

            # Requerimos al menos 4 columnas útiles y descartar enlaces del menú lateral
            if len(textos) < 4 or any(w in textos[0] for w in ['Hotlap', 'Download', 'Menu', 'Profile', 'Home']):
                continue

            # Verificar que el primer dato o posición empiece por un número
            if not re.match(r'^\d+', textos[0]):
                continue

            piloto = textos[1] if len(textos) > 1 else "Piloto"
            coche = textos[2] if len(textos) > 2 else "N/A"
            tiempo = textos[-1] if len(textos) > 3 else "--:--.--"

            # Evitar filtrado de falsos positivos
            if not piloto or len(piloto) < 2:
                continue

            pts_rally = puntos_escala[posicion - 1] if posicion <= len(puntos_escala) else 1
            pts_ps = 0

            resultados.append({
                "posicion": posicion,
                "nombre": piloto,
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
