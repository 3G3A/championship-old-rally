import json
import re
import asyncio
from playwright.async_api import async_playwright

async def obtener_tiempos_playwright(rally_id):
    if not rally_id:
        return []

    url_contenedor = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}&cg=7"
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"Cargando RSF: {url_contenedor}")
            await page.goto(url_contenedor, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)

            # Buscar y pulsar el botón de ver resultados si existe
            botones = await page.query_selector_all("input[type='submit'], button, a")
            for btn in botones:
                txt = (await btn.text_content() or "").lower()
                val = (await btn.get_attribute("value") or "").lower()
                if "result" in txt or "result" in val or "see" in txt or "see" in val:
                    await btn.click()
                    await page.wait_for_timeout(3000)
                    break

            rows = await page.query_selector_all("tr")
            print(f"Filas encontradas para procesar: {len(rows)}")

            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            for row in rows:
                cells = await row.query_selector_all("td, th")
                cell_texts = [((await c.text_content()) or "").strip() for c in cells]

                # Filtrar filas vacías o menús
                if len(cell_texts) < 3:
                    continue

                texto_completo = " ".join(cell_texts).lower()
                if any(bad in texto_completo for bad in ['home', 'hotlap', 'download', 'championship', 'menu', 'discord', 'facebook', 'admins']):
                    continue

                # Detectar si hay un tiempo en formato 00:00.00 o 0:00:00 en cualquier celda
                tiempo_encontrado = None
                for txt in reversed(cell_texts):
                    if re.search(r'\d+:\d{2}', txt):
                        tiempo_encontrado = txt
                        break

                if tiempo_encontrado:
                    # Extraer piloto y coche con flexibilidad
                    piloto = cell_texts[1] if len(cell_texts) > 1 else "Piloto Anónimo"
                    coche = cell_texts[2] if len(cell_texts) > 2 else "N/A"

                    # Limpiar si el nombre viene pegado con la posición
                    if re.match(r'^\d+', piloto) and len(cell_texts) > 2:
                        piloto = cell_texts[2]
                        coche = cell_texts[3] if len(cell_texts) > 3 else "N/A"

                    pts_rally = puntos_escala[posicion_real - 1] if posicion_real <= len(puntos_escala) else 1

                    resultados.append({
                        "posicion": posicion_real,
                        "nombre": piloto,
                        "coche": coche,
                        "tiempo": tiempo_encontrado,
                        "puntos_rally": pts_rally,
                        "puntos_ps": 0,
                        "puntos_totales": pts_rally
                    })
                    print(f"  [+] #{posicion_real}: {piloto} | {coche} | {tiempo_encontrado}")
                    posicion_real += 1

        except Exception as e:
            print(f"Error en extracción: {e}")
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

    # Si la extracción automática no devuelve resultados, se usan los manuales de config.json
    if not resultados and 'pilotos_manuales' in config:
        print("Usando lista manual de respaldo desde config.json")
        resultados = config.get('pilotos_manuales', [])

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Proceso finalizado. Guardados: {len(resultados)} pilotos.")

if __name__ == "__main__":
    main()
