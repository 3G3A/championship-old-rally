import json
import re
import urllib.request

def obtener_tiempos(rally_id):
    if not rally_id:
        return []

    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    try:
        with urllib.request.urlopen(req) as response:
            raw_html = response.read()
            # Probar decodificaciones típicas de servidores php/hungaros
            try:
                html = raw_html.decode('utf-8')
            except:
                html = raw_html.decode('iso-8859-1', errors='ignore')

        print(f"--- TAMAÑO HTML RECIBIDO: {len(html)} bytes ---")

        # Extraer todas las filas de tabla
        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        print(f"Filas totales encontradas: {len(filas)}")

        resultados = []
        posicion_real = 1
        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        for idx, fila in enumerate(filas):
            # Extraer celdas td o th
            celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

            # Si la fila no tiene al menos 3 celdas, continuar
            if len(textos) < 3:
                continue

            # Limpiar la primera columna para ver si es una posición (1, 2, 3...)
            pos_candidate = textos[0].replace('.', '').strip()

            # Si la celda es numérica o la fila contiene tiempos formateados (00:00)
            es_posicion = pos_candidate.isdigit()
            tiene_tiempo = any(re.search(r'\d+:\d{2}', t) for t in textos)

            if es_posicion or tiene_tiempo:
                # Comprobar que no sea fila de encabezado
                texto_unido = " ".join(textos).lower()
                if any(bad in texto_unido for bad in ['hotlap', 'home', 'download', 'championship', 'menu', 'driver', 'piloto']):
                    continue

                piloto = textos[1] if len(textos) > 1 else "Piloto"
                coche = textos[2] if len(textos) > 2 else "N/A"
                
                # Extraer tiempo (la última celda que tenga formato de tiempo)
                tiempo = "--:--.--"
                for t in reversed(textos):
                    if re.search(r'\d+:\d{2}', t):
                        tiempo = t
                        break

                pts_rally = puntos_escala[posicion_real - 1] if posicion_real <= len(puntos_escala) else 1
                pts_ps = 0

                resultados.append({
                    "posicion": posicion_real,
                    "nombre": piloto,
                    "coche": coche,
                    "tiempo": tiempo,
                    "puntos_rally": pts_rally,
                    "puntos_ps": pts_ps,
                    "puntos_totales": pts_rally + pts_ps
                })
                print(f"-> Piloto detectado (#{posicion_real}): {piloto} - {coche} ({tiempo})")
                posicion_real += 1

        print(f"Total pilotos guardados: {len(resultados)}")
        return resultados

    except Exception as e:
        print(f"Error accediendo a RSF: {e}")
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

if __name__ == "__main__":
    main()
