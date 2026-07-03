import os
from PIL import Image, ImageDraw, ImageFont
import fitz


def obtener_primer_pdf(carpeta):
    if not os.path.exists(carpeta):
        return None

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            return os.path.join(carpeta, archivo)

    return None


def generar_preview_pdf(ruta_pdf, config, ancho_preview=360):
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        return None

    documento = fitz.open(ruta_pdf)
    pagina = documento[0]

    pix = pagina.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
    imagen = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    escala = ancho_preview / imagen.width
    nuevo_alto = int(imagen.height * escala)

    imagen = imagen.resize((ancho_preview, nuevo_alto))

    draw = ImageDraw.Draw(imagen)

    header_y = int(config.get("header_offset", 35) * escala)
    footer_y = nuevo_alto - int(config.get("footer_offset", 25) * escala)
    margen_x = int(config.get("margen_x", 40) * escala)

    # Líneas guía visuales
    color_guia = (255, 0, 0)

    draw.line(
        [(margen_x, header_y), (ancho_preview - margen_x, header_y)],
        fill=color_guia,
        width=3
    )

    draw.line(
        [(margen_x, footer_y), (ancho_preview - margen_x, footer_y)],
        fill=color_guia,
        width=3
    )

    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()

    draw.text((margen_x, max(header_y - 16, 5)), "HEADER", fill=color_guia, font=font)
    draw.text((margen_x, min(footer_y + 5, nuevo_alto - 20)), "FOOTER", fill=color_guia, font=font)

    documento.close()

    return imagen