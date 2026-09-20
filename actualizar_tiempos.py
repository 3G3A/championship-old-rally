import json
import re
import asyncio
from playwright.async_api import async_playwright

async def obtener_tiempos_playwright(rally_id):
    if not rally_id:
        return []

    # Añadimos &cg=7 para forzar la tabla de Final Standings (Clasificación General)
    url = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}&cg=7"
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Cargando Clasificación General en RSF: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(4000)

            tables = await page.query_selector_all("table")
            print(f"Tablas encontradas en pantalla: {len(tables)}")

            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            for t_idx, table in enumerate(tables):
                rows = await table.query_selector_all("tr")
                
                # Ignorar tablas pequeñas (menús, pies de página)
                if len(rows) < 3:
                    continue

                for row in rows:
                    cells = await row.query_selector_all("td, th")
                    cell_texts = [((await c.text_content()) or "").strip() for c in cells]

                    if len(cell_texts) < 3:
                        continue

                    # Verificar si la fila tiene formato de tiempo (mm:ss.ms o hh:mm:ss)
                    tiene_tiempo = any(re.search(r'\d+:\d{2}', t) for t in cell_texts)
                    
                    # Limpiar la primera celda para obtener el número de posición
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
                        print(f"  [+] ¡PILOTO REGISTRADO! #{posicion_real}: {piloto} | {coche} | {tiempo}")
                        posicion_real += 1

        except Exception as e:
            print(f"Error procesando RSF con Playwright: {e}")
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
        print("Usando datos de respaldo de config.json")
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
