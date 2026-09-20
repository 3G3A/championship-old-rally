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
        # Lanzar navegador Chrome en modo headless
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Cargando página RSF con navegador virtual: {url}")
        try:
            # Navegar a la página y esperar a que el DOM y las peticiones red se completen
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Esperar un par de segundos adicionales por si hay renders asíncronos
            await page.wait_for_timeout(3000)

            # Obtener el contenido HTML completamente renderizado
            html = await page.content()
            print(f"HTML renderizado capturado ({len(html)} bytes).")

            filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
            posicion_real = 1
            puntos_escala = [50, 45, 42, 40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 12, 10, 8, 6, 4, 2, 1]

            for fila in filas:
                celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
                textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]

                if len(textos) < 3:
                    continue

                pos_str = textos[0].replace('.', '').strip()

                if pos_str.isdigit():
                    texto_unido = " ".join(textos).lower()
                    if any(bad in texto_unido for bad in ['hotlap', 'home', 'download', 'championship', 'menu', 'driver']):
                        continue

                    piloto = textos[1] if len(textos) > 1 else "Piloto"
                    coche = textos[2] if len(textos) > 2 else "N/A"
                    tiempo = "--:--.--"
                    
                    for t in reversed(textos):
                        if re.search(r'\d+:\d{2}', t):
                            tiempo = t
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
                    print(f"  [+] Piloto detectado #{posicion_real}: {piloto} | {coche} | {tiempo}")
                    posicion_real += 1

        except Exception as e:
            print(f"Error durante la navegación con Playwright: {e}")
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
    
    # Ejecutar la extracción asíncrona
    resultados = asyncio.run(obtener_tiempos_playwright(rally_id))

    datos_salida = {
        "rally_actual_id": rally_id,
        "resultados_rally": resultados,
        "historico_rallies": {}
    }

    with open('resultados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_salida, f, ensure_ascii=False, indent=2)

    print(f"Procesados {len(resultados)} pilotos exitosamente.")

if __name__ == "__main__":
    main()
