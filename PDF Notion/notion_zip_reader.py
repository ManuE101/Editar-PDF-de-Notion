import os
import zipfile
import tempfile
from pathlib import Path


def extraer_zip_notion(ruta_zip):
    """
    Extrae un ZIP exportado desde Notion en una carpeta temporal.
    Devuelve la ruta de la carpeta temporal.
    """
    if not os.path.exists(ruta_zip):
        raise FileNotFoundError(f"No existe el archivo ZIP: {ruta_zip}")

    carpeta_temporal = tempfile.mkdtemp(prefix="pdf_notion_")

    with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
        zip_ref.extractall(carpeta_temporal)

    # Notion a veces mete otro ZIP adentro
    extraer_zips_internos(carpeta_temporal)

    return carpeta_temporal


def extraer_zips_internos(carpeta):
    """
    Busca ZIPs internos dentro de la exportación y los extrae.
    Esto pasa a veces con exportaciones grandes de Notion.
    """
    for root, _, files in os.walk(carpeta):
        for file in files:
            if file.lower().endswith(".zip"):
                ruta_zip = os.path.join(root, file)
                destino = os.path.join(root, Path(file).stem)

                os.makedirs(destino, exist_ok=True)

                with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
                    zip_ref.extractall(destino)


def buscar_html_principal(carpeta):
    """
    Busca el HTML principal dentro de la exportación.
    Por ahora toma el HTML más grande, que normalmente es la página principal.
    """
    htmls = []

    for root, _, files in os.walk(carpeta):
        for file in files:
            if file.lower().endswith(".html"):
                ruta = os.path.join(root, file)
                tamanio = os.path.getsize(ruta)
                htmls.append((ruta, tamanio))

    if not htmls:
        raise FileNotFoundError("No se encontró ningún archivo HTML dentro del ZIP.")

    htmls.sort(key=lambda item: item[1], reverse=True)

    return htmls[0][0]


def leer_html_desde_zip(ruta_zip):
    """
    Función principal:
    ZIP → carpeta temporal → HTML principal.
    """
    carpeta_temporal = extraer_zip_notion(ruta_zip)
    html_principal = buscar_html_principal(carpeta_temporal)

    with open(html_principal, "r", encoding="utf-8") as file:
        contenido_html = file.read()

    return {
        "carpeta_temporal": carpeta_temporal,
        "html_principal": html_principal,
        "contenido_html": contenido_html
    }