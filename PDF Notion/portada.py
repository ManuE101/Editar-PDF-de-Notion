from io import BytesIO
from datetime import datetime
import os

from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4


def crear_portada(titulo_documento, config):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    ancho, alto = A4
    margen_x = 70

    logo = config.get("logo", "")

    if config.get("mostrar_logo") and logo and os.path.exists(logo):
        c.drawImage(
            ImageReader(logo),
            margen_x,
            alto - 130,
            width=150,
            height=70,
            preserveAspectRatio=True,
            mask="auto"
        )

    c.setFont("Helvetica-Bold", 24)
    c.drawString(margen_x, alto - 230, config.get("titulo_portada", ""))

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margen_x, alto - 270, titulo_documento)

    c.setFont("Helvetica", 12)
    c.drawString(margen_x, alto - 315, config.get("subtitulo_portada", ""))

    c.setFont("Helvetica", 10)
    c.drawString(margen_x, alto - 370, f'Versión: {config.get("version", "")}')
    c.drawString(margen_x, alto - 390, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}')
    c.drawString(margen_x, alto - 410, f'Área: {config.get("area_portada", "")}')

    c.line(margen_x, alto - 450, ancho - margen_x, alto - 450)

    c.setFont("Helvetica", 9)
    c.drawString(margen_x, 60, config.get("footer", ""))

    c.save()
    buffer.seek(0)

    return PdfReader(buffer).pages[0]