import json
import re
import asyncio
from playwright.async_api import async_playwright

async def obtener_tiempos_playwright(rally_id):
    if not rally_id:
        return []

    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Cargando RSF en navegador virtual: {url}")
        try:
            # Ir a la URL y esperar carga de red completa
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Esperar a que aparezca cualquier tabla en la página
            try:
                await page.wait_for_selector("table", timeout=10000)
            except Exception:
                print("Tiempo de espera para selector 'table' agotado.")

            # Esperar 5 segundos adicionales para renderizado de JS
            await page.wait_for_timeout(5000)

            # Buscar todas las tablas presentes en el documento
            tables = await page.query_selector_all("table")
            print(f"Tablas totales encontradas en la página: {len(tables)}")

            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            for t_idx, table in enumerate(tables):
                rows = await table.query_selector_all("tr")
                
                # Evaluar únicamente tablas que tengan densidad de filas (posibles resultados)
                if len(rows) < 2:
                    continue

                for row in rows:
                    cells = await row.query_selector_all("td, th")
                    cell_texts = [((await c.text_content()) or "").strip() for c in cells]

                    if len(cell_texts) < 3:
                        continue

                    # Comprobar si la fila contiene formato de tiempos (ej: 12:34.56 o 01:23:45)
                    tiene_tiempo = any(re.search(r'\d+:\d{2}', t) for t in cell_texts)
                    
                    pos_limpia = re.sub(r'\D', '', cell_texts[0])

                    if pos_limpia.isdigit() and tiene_tiempo:
                        piloto = cell_texts[1] if len(cell_texts) > 1 else "Piloto"
                        coche = cell_texts[2] if len(cell_texts) > 2 else "N/A"
                        tiempo = "--:--.--"

                        for txt in reversed(cell_texts):
                            if re.search(r'\d+:\d{2}', txt):
                                tiempo = txt
                                break

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
                        print(f"  [+] ¡PILOTO DETECTADO! #{posicion_real}: {piloto} | {coche} | {tiempo}")
                        posicion_real += 1

        except Exception as e:
            print(f"Error extrayendo datos con Playwright: {e}")
        finally:
            await browser.close()

    return resultados

def main():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error cargando config.json: {e}")
        return

    rally_id = config.get('rally_actual_id', '')
    resultados = asyncio.run(obtener_tiempos_playwright(rally_id))

    # Sistema de respaldo
    if not resultados and 'pilotos_manuales' in config:
        print("Cargando datos de respaldo desde config.json")
        resultados = config.get('pilotos_manuales', [])

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Proceso finalizado. Total guardados: {len(resultados)} pilotos.")

if __name__ == "__main__":
    main()
