"""Cliente mínimo de datos.gov.co (Socrata): pide por páginas y reintenta cuando el servidor se demora."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

URL = "https://www.datos.gov.co/resource/{}.json?{}"


def http(dataset, params, intentos=3):
    url = URL.format(dataset, urllib.parse.urlencode(params))
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=120) as respuesta:
                return json.load(respuesta)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if intento == intentos - 1:
                raise
            time.sleep(15 * (intento + 1))


def paginas(dataset, params, tam=10_000, fetch=http):
    """Páginas de hasta `tam` filas. `params` debe traer $order para que el paginado sea estable."""
    offset = 0
    while True:
        filas = fetch(dataset, {**params, "$limit": tam, "$offset": offset})
        if filas:
            yield filas
        if len(filas) < tam:
            return
        offset += tam
