from io import BytesIO
from datetime import datetime
import os

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from portada import crear_portada
from utils import formatear_titulo, crear_nombre_salida


def crear_overlay(ancho, alto, titulo, config, pagina_actual, total_paginas):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    margen_x = int(config.get("margen_x", 40))
    header_y = alto - int(config.get("header_offset", 35))
    footer_y = int(config.get("footer_offset", 25))

    logo = config.get("logo", "")
    texto_x = margen_x

    if config.get("mostrar_logo") and logo and os.path.exists(logo):
        c.drawImage(
            ImageReader(logo),
            margen_x,
            header_y - 15,
            width=int(config.get("logo_width", 80)),
            height=int(config.get("logo_height", 30)),
            preserveAspectRatio=True,
            mask="auto"
        )
        texto_x = margen_x + int(config.get("logo_width", 80)) + 15

    c.setFont("Helvetica-Bold", 10)
    c.drawString(texto_x, header_y, titulo)

    if config.get("mostrar_fecha"):
        fecha = datetime.now().strftime("%d/%m/%Y")
        c.setFont("Helvetica", 8)
        c.drawRightString(ancho - margen_x, header_y, fecha)

    c.line(margen_x, header_y - 25, ancho - margen_x, header_y - 25)

    c.setFont("Helvetica", 8)
    c.drawString(
        margen_x,
        footer_y,
        f'{config.get("footer", "")} | {config.get("version", "")}'
    )

    if config.get("numerar_paginas"):
        c.drawRightString(
            ancho - margen_x,
            footer_y,
            f"Página {pagina_actual} de {total_paginas}"
        )

    c.line(margen_x, footer_y + 20, ancho - margen_x, footer_y + 20)

    c.save()
    buffer.seek(0)

    return PdfReader(buffer).pages[0]


def procesar_pdf(ruta_pdf, ruta_salida, titulo, config):
    reader = PdfReader(ruta_pdf)
    writer = PdfWriter()

    total_original = len(reader.pages)
    total_final = total_original + (1 if config.get("agregar_portada") else 0)

    if config.get("agregar_portada"):
        writer.add_page(crear_portada(titulo, config))

    for i, pagina in enumerate(reader.pages, start=1):
        pagina_final = i + (1 if config.get("agregar_portada") else 0)

        ancho = float(pagina.mediabox.width)
        alto = float(pagina.mediabox.height)

        overlay = crear_overlay(
            ancho,
            alto,
            titulo,
            config,
            pagina_final,
            total_final
        )

        pagina.merge_page(overlay)
        writer.add_page(pagina)

    with open(ruta_salida, "wb") as file:
        writer.write(file)


def procesar_carpeta(config, callback_estado=None, callback_progreso=None):
    entrada = config.get("entrada", "Entrada")
    salida = config.get("salida", "Salida")

    os.makedirs(entrada, exist_ok=True)
    os.makedirs(salida, exist_ok=True)

    archivos_pdf = [
        archivo for archivo in os.listdir(entrada)
        if archivo.lower().endswith(".pdf")
    ]

    total = len(archivos_pdf)

    if total == 0:
        return 0, 0

    procesados = 0

    for index, archivo in enumerate(archivos_pdf, start=1):
        if callback_estado:
            callback_estado(f"Procesando {index} de {total}: {archivo}")

        if callback_progreso:
            callback_progreso(index / total)

        ruta_pdf = os.path.join(entrada, archivo)
        titulo = formatear_titulo(archivo)
        nombre_salida = crear_nombre_salida(archivo)
        ruta_salida = os.path.join(salida, nombre_salida)

        procesar_pdf(ruta_pdf, ruta_salida, titulo, config)

        procesados += 1

    return procesados, total