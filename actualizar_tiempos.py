import json
import re
import urllib.request
import urllib.parse

def obtener_tiempos(rally_id):
    if not rally_id:
        return []

    # Probar petición POST y GET directa al endpoint de resultados
    url_base = "https://www.rallysimfans.hu/rbr/rally_results.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Datos de formulario POST
    data = urllib.parse.urlencode({'rally_id': rally_id}).encode('utf-8')

    try:
        req = urllib.request.Request(url_base, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')

        print(f"--- RESPUESTA SERVIDOR RSF (POST) ---")
        print(f"Tamaño HTML: {len(html)} bytes")
        
        # Buscar palabras clave o pilotos en el HTML
        filas = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        print(f"Total filas <tr> en respuesta: {len(filas)}")

        for i, fila in enumerate(filas[:10]):
            celdas = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.DOTALL | re.IGNORECASE)
            textos = [re.sub(r'<[^>]+>', '', c).strip() for c in celdas]
            if textos:
                print(f"Fila {i}: {textos}")

        print("--------------------------------------")
        return []

    except Exception as e:
        print(f"Error en petición POST: {e}")
        return []

def main():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error cargando config.json: {e}")
        return

    rally_id = config.get('rally_actual_id', '')
    obtener_tiempos(rally_id)

if __name__ == "__main__":
    main()
