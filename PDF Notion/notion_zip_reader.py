import os
import zipfile
import tempfile
import shutil
from pathlib import Path

from bs4 import BeautifulSoup


class ZipNotionInvalido(ValueError):
    pass


def validar_archivo_zip(ruta_zip):
    if not ruta_zip or not os.path.exists(ruta_zip):
        raise ZipNotionInvalido("No existe el archivo ZIP seleccionado.")

    if not os.path.isfile(ruta_zip):
        raise ZipNotionInvalido("La ruta seleccionada no es un archivo ZIP.")

    if not ruta_zip.lower().endswith(".zip"):
        raise ZipNotionInvalido("El archivo seleccionado no tiene extensión .zip.")

    if not zipfile.is_zipfile(ruta_zip):
        raise ZipNotionInvalido("El archivo seleccionado no es un ZIP válido o está dañado.")


def extraer_zip_notion(ruta_zip):
    """
    Extrae un ZIP exportado desde Notion en una carpeta temporal.
    Devuelve la ruta de la carpeta temporal.
    """
    validar_archivo_zip(ruta_zip)

    carpeta_temporal = tempfile.mkdtemp(prefix="pdf_notion_")

    try:
        with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
            zip_ref.extractall(carpeta_temporal)
    except zipfile.BadZipFile as error:
        shutil.rmtree(carpeta_temporal, ignore_errors=True)
        raise ZipNotionInvalido("El ZIP está dañado o no se pudo abrir.") from error

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

                try:
                    with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
                        zip_ref.extractall(destino)
                except zipfile.BadZipFile:
                    continue


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
        raise ZipNotionInvalido("No se encontró ningún archivo HTML dentro del ZIP.")

    htmls.sort(key=lambda item: item[1], reverse=True)

    return htmls[0][0]


def leer_html(ruta_html):
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            with open(ruta_html, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            pass

    with open(ruta_html, "r", encoding="utf-8", errors="replace") as file:
        return file.read()


def validar_contenido_html_exportado(contenido_html):
    if not contenido_html or not contenido_html.strip():
        raise ZipNotionInvalido("El HTML principal está vacío.")

    soup = BeautifulSoup(contenido_html, "lxml")

    if not soup.find(["html", "body", "h1", "h2", "h3", "p", "li", "img"]):
        raise ZipNotionInvalido("El HTML encontrado no parece ser una exportación convertible.")

    if not (soup.title or soup.find(["h1", "h2", "h3", "p", "li", "img"])):
        raise ZipNotionInvalido("No se detectó contenido útil dentro del HTML exportado.")


def validar_zip_notion(ruta_zip):
    carpeta_temporal = None

    try:
        carpeta_temporal = extraer_zip_notion(ruta_zip)
        html_principal = buscar_html_principal(carpeta_temporal)
        contenido_html = leer_html(html_principal)
        validar_contenido_html_exportado(contenido_html)
        return True
    finally:
        if carpeta_temporal and os.path.exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal, ignore_errors=True)


def leer_html_desde_zip(ruta_zip):
    """
    Función principal:
    ZIP → carpeta temporal → HTML principal.
    """
    carpeta_temporal = extraer_zip_notion(ruta_zip)
    try:
        html_principal = buscar_html_principal(carpeta_temporal)
        contenido_html = leer_html(html_principal)
        validar_contenido_html_exportado(contenido_html)

        return {
            "carpeta_temporal": carpeta_temporal,
            "html_principal": html_principal,
            "contenido_html": contenido_html
        }
    except Exception:
        shutil.rmtree(carpeta_temporal, ignore_errors=True)
        raise
