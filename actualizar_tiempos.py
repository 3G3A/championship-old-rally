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
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)

            tables = await page.query_selector_all("table")
            print(f"Tablas totales encontradas: {len(tables)}")

            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            for t_idx, table in enumerate(tables):
                rows = await table.query_selector_all("tr")
                if len(rows) < 2:
                    continue

                for r_idx, row in enumerate(rows):
                    cells = await row.query_selector_all("td, th")
                    cell_texts = [((await c.text_content()) or "").strip() for c in cells]

                    if len(cell_texts) < 2:
                        continue

                    # Imprimir en consola las filas que parezcan tener datos de rally
                    texto_fila = " | ".join(cell_texts)
                    
                    # Filtrar menús obvios
                    if any(m in texto_fila.lower() for m in ['home', 'hotlap', 'download', 'championships', 'discord', 'facebook']):
                        continue

                    print(f"Tabla {t_idx} - Fila {r_idx}: {cell_texts}")

                    # Si la fila tiene al menos 3 celdas y no es un encabezado
                    if len(cell_texts) >= 3:
                        # Si no es la fila de títulos (Pos, Driver, Car...)
                        if "driver" in cell_texts[1].lower() or "piloto" in cell_texts[1].lower() or "pos" in cell_texts[0].lower():
                            continue

                        piloto = cell_texts[1]
                        coche = cell_texts[2] if len(cell_texts) > 2 else "N/A"
                        tiempo = cell_texts[-1] if len(cell_texts) > 3 else "--:--.--"

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
                        print(f"   --> PILOTO CAPTURADO #{posicion_real}: {piloto} | {coche} | {tiempo}")
                        posicion_real += 1

        except Exception as e:
            print(f"Error extrayendo datos: {e}")
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

    if not resultados and 'pilotos_manuales' in config:
        print("Cargando datos de respaldo en config.json")
        resultados = config.get('pilotos_manuales', [])

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Total guardados en resultados.json: {len(resultados)} pilotos.")

if __name__ == "__main__":
    main()
