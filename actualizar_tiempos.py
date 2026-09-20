import json
import re
import urllib.request

def obtener_tiempos_rsf(rally_id):
    if not rally_id:
        return []

    # Probar endpoint interno de iframe/resultados que usa RSF
    url = f"https://www.rallysimfans.hu/rbr/rally_results.php?rally_id={rally_id}&stage=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')

        print(f"--- PRUEBA IFRAME RSF (Longitud: {len(html)}) ---")

        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        resultados = []
        posicion_real = 1
        puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

        for fila in filas:
            celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

            if len(textos) < 3:
                continue

            pos_str = textos[0].replace('.', '').strip()

            if pos_str.isdigit():
                piloto = textos[1] if len(textos) > 1 else "Piloto"
                coche = textos[2] if len(textos) > 2 else "N/A"
                tiempo = textos[-1] if len(textos) > 3 else "--:--.--"

                pts_rally = puntos_escala[posicion_real - 1] if posicion_real <= len(puntos_escala) else 1

                resultados.append({
                    "posicion": posicion_real,
                    "nombre": piloto,
                    "coche": coche,
                    "tiempo": tiempo,
                    "puntos_rally": pts_rally,
                    "puntos_ps": 0,
                    "puntos_totales": pts_rally
                })
                posicion_real += 1

        print(f"Pilotos procesados desde iframe: {len(resultados)}")
        return resultados

    except Exception as e:
        print(f"Error consultando iframe RSF: {e}")
        return []

def main():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error cargando config.json: {e}")
        return

    rally_id = config.get('rally_actual_id', '')
    
    # 1. Intentar obtener tiempos desde RSF
    resultados = obtener_tiempos_rsf(rally_id)

    # 2. Si RSF bloquea la extracción automática, usar datos manuales/locales declarados en config.json si existen
    if not resultados and 'pilotos_manuales' in config:
        print("Usando datos de copia de respaldo desde config.json")
        resultados = config.get('pilotos_manuales', [])

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Resultado final guardado en resultados.json: {len(resultados)} pilotos")

if __name__ == "__main__":
    main()
