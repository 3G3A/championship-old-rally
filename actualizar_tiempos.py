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
            await page.wait_for_timeout(4000)

            # Si RSF carga la tabla dentro de un iframe o frame secundario
            target_frame = page
            for frame in page.frames:
                if "rally_results.php" in frame.url or "rally_id" in frame.url:
                    target_frame = frame
                    print(f"Iframe detected: {frame.url}")
                    break

            # Extraer las filas directamente desde el DOM
            rows = await target_frame.query_selector_all("tr")
            print(f"Filas de tabla encontradas en el DOM: {len(rows)}")

            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            for row in rows:
                text_content = await row.text_content()
                if not text_content or "hotlap" in text_content.lower() or "download" in text_content.lower():
                    continue

                cells = await row.query_selector_all("td, th")
                cell_texts = []
                for cell in cells:
                    txt = await cell.text_content()
                    cell_texts.append(txt.strip() if txt else "")

                if len(cell_texts) < 3:
                    continue

                pos_candidate = cell_texts[0].replace('.', '').strip()

                if pos_candidate.isdigit():
                    piloto = cell_texts[1]
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
                    print(f"  [+] Piloto #{posicion_real}: {piloto} | {coche} | {tiempo}")
                    posicion_real += 1

        except Exception as e:
            print(f"Error extrayendo con Playwright: {e}")
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

    # Resguardo si no se capturan filas
    if not resultados and 'pilotos_manuales' in config:
        print("Usando datos de respaldo en config.json")
        resultados = config.get('pilotos_manuales', [])

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Guardados {len(resultados)} pilotos en resultados.json.")

if __name__ == "__main__":
    main()
