import json
import re
import urllib.request

def obtener_tiempos(rally_id):
    if not rally_id:
        return []

    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Buscar todas las filas de tabla <tr> en la página
        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        
        resultados = []
        posicion_real = 1
        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        for fila in filas:
            # Extraer el texto de todas las celdas (<td> o <th>)
            celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

            # Las filas de tiempos de RSF suelen tener al menos 4-5 columnas:
            # Pos, Piloto, Coche, Categ, Tiempo, etc.
            if len(textos) < 4:
                continue

            # Buscar si alguna de las celdas tiene un formato de tiempo típico de rally (ej: 12:34.56 o 1:23:45.67)
            tiene_tiempo = any(re.search(r'\d+:\d{2}\.\d{2}', t) for t in textos)
            
            # La primera celda debe ser la posición o número
            pos_str = textos[0].replace('.', '').strip()

            if pos_str.isdigit() and (tiene_tiempo or len(textos) >= 5):
                # Descartar filas que contengan textos de navegación o encabezados
                primer_texto = textos[1].lower() if len(textos) > 1 else ""
                if any(bad in primer_texto for bad in ['driver', 'piloto', 'coche', 'car', 'hotlap', 'home', 'download']):
                    continue

                nombre_piloto = textos[1]
                coche = textos[2] if len(textos) > 2 else "N/A"
                
                # Buscar la celda que contiene el tiempo total
                tiempo = "--:--.--"
                for t in reversed(textos):
                    if re.search(r'\d+:\d{2}', t):
                        tiempo = t
                        break

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

        print(f"Pilotos encontrados en RSF: {len(resultados)}")
        return resultados

    except Exception as e:
        print(f"Error procesando RSF: {e}")
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

    print(f"Total de pilotos guardados en resultados.json: {len(resultados)}")

if __name__ == "__main__":
    main()
