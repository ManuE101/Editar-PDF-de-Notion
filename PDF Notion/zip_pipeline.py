import os
import shutil
from pathlib import Path

from notion_zip_reader import leer_html_desde_zip
from notion_parser import parsear_html_notion
from smart_pdf_exporter_v2 import exportar_documento_pdf_v2


def convertir_zip_notion_a_pdf(ruta_zip, carpeta_salida, config):
    """
    Convierte un ZIP exportado desde Notion a PDF usando el motor nuevo.
    Mantiene configuración de header, footer, portada y logo.
    """

    if not os.path.exists(ruta_zip):
        raise FileNotFoundError(f"No existe el ZIP seleccionado: {ruta_zip}")

    os.makedirs(carpeta_salida, exist_ok=True)

    resultado = leer_html_desde_zip(ruta_zip)

    documento = parsear_html_notion(
        resultado["contenido_html"],
        resultado["html_principal"]
    )

    nombre_zip = Path(ruta_zip).stem
    nombre_salida = f"{nombre_zip}_convertido.pdf"
    ruta_salida = os.path.join(carpeta_salida, nombre_salida)

    exportar_documento_pdf_v2(
        documento=documento,
        ruta_salida=ruta_salida,
        config=config
    )

    carpeta_temporal = resultado.get("carpeta_temporal")

    if carpeta_temporal and os.path.exists(carpeta_temporal):
        shutil.rmtree(carpeta_temporal, ignore_errors=True)

    return ruta_salida

def convertir_carpeta_zips_notion_a_pdf(carpeta_zips, carpeta_salida, config, callback_estado=None, callback_progreso=None):
    if not os.path.exists(carpeta_zips):
        raise FileNotFoundError(f"No existe la carpeta: {carpeta_zips}")

    archivos_zip = [
        archivo for archivo in os.listdir(carpeta_zips)
        if archivo.lower().endswith(".zip")
    ]

    total = len(archivos_zip)

    if total == 0:
        return 0, 0, []

    errores = []
    convertidos = 0

    for index, archivo in enumerate(archivos_zip, start=1):
        ruta_zip = os.path.join(carpeta_zips, archivo)

        if callback_estado:
            callback_estado(f"Convirtiendo ZIP {index} de {total}: {archivo}")

        if callback_progreso:
            callback_progreso(index / total)

        try:
            convertir_zip_notion_a_pdf(
                ruta_zip=ruta_zip,
                carpeta_salida=carpeta_salida,
                config=config
            )
            convertidos += 1

        except Exception as error:
            errores.append(f"{archivo}: {error}")

    return convertidos, total, errores