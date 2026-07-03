from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import os


CARPETA_ENTRADA = "Entrada"
CARPETA_SALIDA = "Salida"

LOGO = "logo.png.png"

FOOTER_TEXTO = "Confidencial - Uso interno"
VERSION = "v1.0"
FECHA = datetime.now().strftime("%d/%m/%Y")


def formatear_titulo(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    nombre = nombre.replace("_", " ").replace("-", " ")
    return nombre.strip().title()


def crear_overlay(ancho, alto, titulo, pagina_actual, total_paginas):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    margen_x = 40
    header_y = alto - 35
    footer_y = 25

    if LOGO and os.path.exists(LOGO):
        c.drawImage(
            ImageReader(LOGO),
            margen_x,
            alto - 50,
            width=80,
            height=30,
            preserveAspectRatio=True,
            mask="auto"
        )
        texto_x = margen_x + 95
    else:
        texto_x = margen_x

    c.setFont("Helvetica-Bold", 10)
    c.drawString(texto_x, header_y, titulo)

    c.setFont("Helvetica", 8)
    c.drawRightString(ancho - margen_x, header_y, FECHA)

    c.line(margen_x, alto - 60, ancho - margen_x, alto - 60)

    c.setFont("Helvetica", 8)
    c.drawString(
        margen_x,
        footer_y,
        f"{FOOTER_TEXTO} | {VERSION}"
    )

    c.drawRightString(
        ancho - margen_x,
        footer_y,
        f"Página {pagina_actual} de {total_paginas}"
    )

    c.line(margen_x, 45, ancho - margen_x, 45)

    c.save()
    buffer.seek(0)

    return PdfReader(buffer).pages[0]


def procesar_pdf(ruta_pdf, ruta_salida, titulo):
    reader = PdfReader(ruta_pdf)
    writer = PdfWriter()

    total_paginas = len(reader.pages)

    for i, pagina in enumerate(reader.pages, start=1):
        ancho = float(pagina.mediabox.width)
        alto = float(pagina.mediabox.height)

        overlay = crear_overlay(ancho, alto, titulo, i, total_paginas)
        pagina.merge_page(overlay)

        writer.add_page(pagina)

    with open(ruta_salida, "wb") as f:
        writer.write(f)


def procesar_todos_los_pdfs():
    os.makedirs(CARPETA_ENTRADA, exist_ok=True)
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    archivos_pdf = [
        archivo for archivo in os.listdir(CARPETA_ENTRADA)
        if archivo.lower().endswith(".pdf")
    ]

    if not archivos_pdf:
        print(f"No se encontraron PDFs en la carpeta {CARPETA_ENTRADA}.")
        return

    for archivo in archivos_pdf:
        titulo = formatear_titulo(archivo)

        ruta_pdf = os.path.join(CARPETA_ENTRADA, archivo)
        nombre_sin_extension = os.path.splitext(archivo)[0]

        ruta_salida = os.path.join(
            CARPETA_SALIDA,
            f"{nombre_sin_extension}_con_header_footer.pdf"
        )

        print(f"Procesando: {archivo}")
        procesar_pdf(ruta_pdf, ruta_salida, titulo)

    print("Listo. PDFs generados en la carpeta Salida.")


if __name__ == "__main__":
    procesar_todos_los_pdfs()