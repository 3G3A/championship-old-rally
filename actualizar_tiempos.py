import json
import re
import asyncio
from playwright.async_api import async_playwright

async def obtener_tiempos_playwright(rally_id):
    if not rally_id:
        return []

    # Cargar directamente el frame central de la tabla de resultados
    url_directa = f"https://www.rallysimfans.hu/rbr/rally_results.php?rally_id={rally_id}"
    url_contenedor = f"https://www.rallysimfans.hu/rbr/rally_online.php?centerbox=rally_results.php&rally_id={rally_id}"
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Cargando navegador en página contenedora: {url_contenedor}")
        try:
            await page.goto(url_contenedor, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)

            # Buscar si hay un <iframe> dentro de la página
            iframes = page.frames
            print(f"Total de frames/iframes detectados: {len(iframes)}")
            
            target_page = page
            for frame in iframes:
                print(f" - Evaluando frame: {frame.url}")
                if "rally_results.php" in frame.url:
                    target_page = frame
                    print(f"--> ¡Iframe central de resultados encontrado! {frame.url}")
                    break

            # Si no hay iframe explícito, intentar navegar directamente en la pestaña activa
            if target_page == page and len(iframes) <= 1:
                print(f"Navegando directamente al módulo de resultados: {url_directa}")
                await page.goto(url_directa, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                target_page = page

            rows = await target_page.query_selector_all("tr")
            print(f"Filas a analizar en el módulo de resultados: {len(rows)}")

            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            # Palabras clave a ignorar (menús y administradores)
            palabras_descarte = [
                'hotlap', 'home', 'download', 'championship', 'menu', 'driver', 'piloto', 
                'coche', 'car', 'chrisx', 'falcon77', 'lacka6', 'sebgutkopf', 'discord', 
                'facebook', 'instagram', 'admins', 'links', 'hirdetés'
            ]

            for idx, row in enumerate(rows):
                cells = await row.query_selector_all("td, th")
                cell_texts = []
                for cell in cells:
                    txt = await cell.text_content()
                    cell_texts.append(txt.strip() if txt else "")

                if len(cell_texts) < 3:
                    continue

                texto_completo_fila = " ".join(cell_texts).lower()

                # Descartar si contiene palabras del menú o admins
                if any(bad in texto_completo_fila for bad in palabras_descarte):
                    continue

                # La primera celda debe tener un número de posición (ej: 1, 2, 3...)
                pos_limpia = re.sub(r'\D', '', cell_texts[0])

                # Buscar formato de tiempo en las celdas (ej: 12:34.56 o 1:23:45)
                tiene_tiempo = any(re.search(r'\d+:\d{2}', t) for t in cell_texts)

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
                    print(f"  [+] ¡PILOTO EXTRAÍDO! #{posicion_real}: {piloto} | {coche} | {tiempo}")
                    posicion_real += 1

        except Exception as e:
            print(f"Error procesando con Playwright: {e}")
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
        print("Usando datos de respaldo en config.json")
        resultados = config.get('pilotos_manuales', [])

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Procesado finalizado. Total guardados: {len(resultados)} pilotos.")

if __name__ == "__main__":
    main()
