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

        print(f"--- INICIO DIAGNÓSTICO RSF (Longitud HTML: {len(html)}) ---")

        # Buscar cualquier tabla o patrón que contenga filas
        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        print(f"Total de filas <tr> encontradas: {len(filas)}")

        resultados = []
        posicion_real = 1
        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        for idx, fila in enumerate(filas):
            celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

            # Si la fila tiene al menos 2 columnas, la imprimimos en los logs para ver qué contiene
            if len(textos) >= 2:
                print(f"Fila {idx}: {textos[:4]}")

            if len(textos) < 3:
                continue

            pos_limpia = textos[0].replace('.', '').strip()

            if not pos_limpia.isdigit():
                continue

            nombre_piloto = textos[1]
            coche = textos[2] if len(textos) > 2 else "N/A"
            tiempo = textos[-1] if len(textos) > 3 else "--:--.--"

            if not nombre_piloto or len(nombre_piloto) < 2:
                continue

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

        print(f"Total de pilotos procesados: {len(resultados)}")
        print("--- FIN DIAGNÓSTICO RSF ---")
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

if __name__ == "__main__":
    main()
