import os
import shutil
import tempfile
from pathlib import Path

from notion_zip_reader import leer_html_desde_zip
from notion_parser import parsear_html_notion
from smart_pdf_exporter_v2 import exportar_documento_pdf_v2
from error_messages import resumir_error
from process_control import ProcesoCancelado


def convertir_zip_notion_a_pdf(
    ruta_zip,
    carpeta_salida,
    config,
    nombre_salida=None,
    callback_estado=None,
    callback_progreso=None,
):
    """
    Convierte un ZIP exportado desde Notion a PDF usando el motor nuevo.
    Mantiene configuración de header, footer, portada y logo.
    """

    if callback_estado:
        callback_estado("Validando el ZIP...")
    if callback_progreso:
        callback_progreso(0.05)

    if not os.path.exists(ruta_zip):
        raise FileNotFoundError(f"No existe el ZIP seleccionado: {ruta_zip}")

    os.makedirs(carpeta_salida, exist_ok=True)

    if callback_estado:
        callback_estado("Extrayendo el contenido de Notion...")
    if callback_progreso:
        callback_progreso(0.15)
    resultado = leer_html_desde_zip(ruta_zip)
    carpeta_temporal = resultado.get("carpeta_temporal")
    if callback_progreso:
        callback_progreso(0.35)

    try:
        if callback_estado:
            callback_estado("Analizando títulos, textos e imágenes...")
        documento = parsear_html_notion(
            resultado["contenido_html"],
            resultado["html_principal"]
        )
        if callback_progreso:
            callback_progreso(0.52)

        nombre_zip = Path(ruta_zip).stem
        nombre_salida = nombre_salida or f"{nombre_zip}_convertido.pdf"
        ruta_salida = os.path.join(carpeta_salida, nombre_salida)
        descriptor, ruta_temporal_pdf = tempfile.mkstemp(
            prefix="pdf_notion_zip_",
            suffix=".pdf",
            dir=os.path.abspath(carpeta_salida),
        )
        os.close(descriptor)

        try:
            if callback_estado:
                callback_estado("Generando páginas y aplicando el diseño...")
            if callback_progreso:
                callback_progreso(0.62)

            def progreso_exportacion(valor):
                if callback_progreso:
                    callback_progreso(0.62 + (valor * 0.36))

            exportar_documento_pdf_v2(
                documento=documento,
                ruta_salida=ruta_temporal_pdf,
                config=config,
                callback_estado=callback_estado,
                callback_progreso=progreso_exportacion,
            )
            if callback_estado:
                callback_estado("Finalizando el PDF...")
            if callback_progreso:
                callback_progreso(0.99)
            os.replace(ruta_temporal_pdf, ruta_salida)
            return ruta_salida
        finally:
            try:
                if os.path.exists(ruta_temporal_pdf):
                    os.remove(ruta_temporal_pdf)
            except OSError:
                pass
    finally:
        if carpeta_temporal and os.path.exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal, ignore_errors=True)

def convertir_carpeta_zips_notion_a_pdf(carpeta_zips, carpeta_salida, config, callback_estado=None, callback_progreso=None, callback_sobrescritura=None):
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
        nombre_salida = f"{os.path.splitext(archivo)[0]}_convertido.pdf"
        ruta_salida = os.path.join(carpeta_salida, nombre_salida)

        if callback_estado:
            callback_estado(f"Convirtiendo ZIP {index} de {total}: {archivo}")

        if callback_progreso:
            callback_progreso((index - 1) / total)

        if os.path.exists(ruta_salida) and callback_sobrescritura:
            if not callback_sobrescritura(ruta_salida):
                if callback_progreso:
                    callback_progreso(index / total)
                continue

        def progreso_archivo(valor):
            if callback_progreso:
                callback_progreso(((index - 1) + valor) / total)

        def estado_archivo(etapa):
            if callback_estado:
                callback_estado(f"{archivo} · {etapa}")

        try:
            convertir_zip_notion_a_pdf(
                ruta_zip=ruta_zip,
                carpeta_salida=carpeta_salida,
                config=config,
                nombre_salida=nombre_salida,
                callback_estado=estado_archivo,
                callback_progreso=progreso_archivo,
            )
            convertidos += 1

        except ProcesoCancelado:
            raise
        except Exception as error:
            errores.append(resumir_error(error, ruta_zip))

    return convertidos, total, errores
