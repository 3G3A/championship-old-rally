import json
import re
import urllib.request

def obtener_tiempos(rally_id):
    if not rally_id:
        return []
        
    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Extraer todas las filas <tr> de las tablas
        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        
        resultados = []
        posicion_real = 1
        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        # Palabras clave de menús para descartar
        palabras_basura = ['hotlap', 'download', 'menu', 'profile', 'home', 'discord', 'facebook', 'instagram', 'championships', 'stats', 'logout']

        for fila in filas:
            # Extraer celdas <td> o <th>
            celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

            # Si no tiene al menos 3 celdas, se descarta
            if len(textos) < 3:
                continue

            # Comprobar si alguna celda contiene palabras de menú
            texto_unido = " ".join(textos).lower()
            if any(basura in texto_unido for basura in palabras_basura):
                continue

            # La primera celda DEBE ser exclusivamente un número (la posición: 1, 2, 3...)
            pos_str = textos[0].replace('.', '').strip()
            if not pos_str.isdigit():
                continue

            # Extraer los datos reales
            nombre_piloto = textos[1]
            coche = textos[2] if len(textos) > 2 else "N/A"
            tiempo = textos[-1] if len(textos) > 3 else "--:--.--"

            pts_rally = puntos_escala[posicion_real - 1] if posicion_real <= len(puntos_escala) else 1
            pts_ps = 0

            resultados.append({
                "posicion": posicion_real,
                "nombre": nombre_piloto,
                "coche": coche,
                "tiempo": tiempo,
                "puntos_rally": pts_rally,
                "puntos_ps": pts_ps,
                "puntos_totales": pts_rally + pts_ps
            })
            posicion_real += 1

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
