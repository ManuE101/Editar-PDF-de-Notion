import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from PIL import Image as PILImage

from layout_engine import dividir_en_paginas


PAGE_WIDTH, PAGE_HEIGHT = A4

MARGIN_LEFT = 1.8 * cm
MARGIN_RIGHT = 1.8 * cm
MARGIN_TOP = 2.2 * cm
MARGIN_BOTTOM = 2.0 * cm

CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT


def draw_header_footer(c, config, page_number, titulo_pdf):
    footer = config.get("footer", "Confidencial - Uso interno")
    version = config.get("version", "v1.0")

    c.setFont("Helvetica-Bold", 8)
    header_texto = config.get("header", "") or titulo_pdf
    c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 1.1 * cm, header_texto)

    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 1.1 * cm, version)

    c.line(
        MARGIN_LEFT,
        PAGE_HEIGHT - 1.35 * cm,
        PAGE_WIDTH - MARGIN_RIGHT,
        PAGE_HEIGHT - 1.35 * cm
    )

    c.setFont("Helvetica", 8)
    c.drawString(MARGIN_LEFT, 1 * cm, footer)
    #c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, 1 * cm, f"Página {page_number}")
    if config.get("numerar_paginas", True):
        formato = config.get("formato_numeracion", "Página {pagina}")

        if formato != "Sin numeración":
            texto_pagina = formato.format(
                pagina=page_number,
                total=config.get("total_paginas", "")
            )

            c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, 1 * cm, texto_pagina)

    c.line(MARGIN_LEFT, 1.3 * cm, PAGE_WIDTH - MARGIN_RIGHT, 1.3 * cm)


def draw_wrapped_text(c, text, x, y, max_width, font_name, font_size, leading):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if c.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    c.setFont(font_name, font_size)

    for line in lines:
        c.drawString(x, y, line)
        y -= leading

    return y


def draw_bloque(c, bloque, x, y, config):
    if bloque.tipo == "heading":
        if bloque.nivel == 1:
            font_name = "Helvetica-Bold"
            font_size = 18
            leading = 24
            y -= 8
        elif bloque.nivel == 2:
            font_name = "Helvetica-Bold"
            font_size = 15
            leading = 21
            y -= 7
        else:
            font_name = "Helvetica-BoldOblique"
            font_size = 13
            leading = 18
            y -= 6

        y = draw_wrapped_text(
            c,
            bloque.texto,
            x,
            y,
            CONTENT_WIDTH,
            font_name,
            font_size,
            leading
        )

        y -= 8
        return y

    if bloque.tipo == "paragraph":
        y = draw_wrapped_text(
            c,
            bloque.texto,
            x,
            y,
            CONTENT_WIDTH,
            "Helvetica",
            10,
            15
        )

        y -= 7
        return y

    if bloque.tipo == "bullet":
        bullet_x = x
        text_x = x + 0.45 * cm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(bullet_x, y, "•")

        y = draw_wrapped_text(
            c,
            bloque.texto,
            text_x,
            y,
            CONTENT_WIDTH - 0.45 * cm,
            "Helvetica",
            10,
            15
        )

        y -= 5
        return y

    if bloque.tipo == "image":
        ruta = bloque.imagen

        if not ruta or not os.path.exists(ruta):
            return y

        try:
            img = PILImage.open(ruta)
            w, h = img.size

            max_w = CONTENT_WIDTH
            max_h = 11 * cm

            scale = min(max_w / w, max_h / h, 1)
            draw_w = w * scale
            draw_h = h * scale

            if y - draw_h < MARGIN_BOTTOM + 1.5 * cm:
                y = PAGE_HEIGHT - MARGIN_TOP

            c.drawImage(
                ImageReader(ruta),
                x,
                y - draw_h,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=True,
                mask="auto"
            )

            y -= draw_h + 12
            return y

        except Exception:
            return y

    return y


def draw_portada(c, documento, config):
    logo = config.get("logo", "")

    if config.get("mostrar_header_portada", False):
        header = config.get("header_portada", "") or documento.titulo
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 1.1 * cm, header)
        c.line(MARGIN_LEFT, PAGE_HEIGHT - 1.35 * cm, PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 1.35 * cm)

    y = PAGE_HEIGHT - 3 * cm

    if logo and os.path.exists(logo):
        c.drawImage(
            ImageReader(logo),
            MARGIN_LEFT,
            y - 2 * cm,
            width=4 * cm,
            height=2 * cm,
            preserveAspectRatio=True,
            mask="auto"
        )
        y -= 3 * cm

    c.setFont("Helvetica-Bold", 24)
    c.drawString(MARGIN_LEFT, y, config.get("titulo_portada", "Documentación"))
    y -= 1.2 * cm

    c.setFont("Helvetica-Bold", 17)
    c.drawString(MARGIN_LEFT, y, documento.titulo)
    y -= 1.2 * cm

    c.setFont("Helvetica", 11)
    c.drawString(MARGIN_LEFT, y, config.get("subtitulo_portada", ""))
    y -= 1.5 * cm

    c.setFont("Helvetica", 10)
    c.drawString(MARGIN_LEFT, y, f'Versión: {config.get("version", "v1.0")}')
    y -= 0.6 * cm
    c.drawString(MARGIN_LEFT, y, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}')
    y -= 0.6 * cm
    c.drawString(MARGIN_LEFT, y, f'Área: {config.get("area_portada", "Uso interno")}')

    c.line(MARGIN_LEFT, y - 1 * cm, PAGE_WIDTH - MARGIN_RIGHT, y - 1 * cm)

    if config.get("mostrar_footer_portada", False):
        footer = config.get("footer_portada", "") or config.get("footer", "")
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN_LEFT, 1 * cm, footer)
        c.line(MARGIN_LEFT, 1.3 * cm, PAGE_WIDTH - MARGIN_RIGHT, 1.3 * cm)


def exportar_documento_pdf_v2(documento, ruta_salida, config):
    paginas = dividir_en_paginas(documento)
    total_paginas = len(paginas) + (1 if config.get("agregar_portada", True) else 0)
    config["total_paginas"] = total_paginas

    c = canvas.Canvas(ruta_salida, pagesize=A4)

    page_number = 1

    if config.get("agregar_portada", True):
        draw_portada(c, documento, config)
        c.showPage()
        page_number += 1

    for pagina in paginas:
        draw_header_footer(c, config, page_number, documento.titulo)

        y = PAGE_HEIGHT - MARGIN_TOP

        for seccion in pagina.secciones:
            for bloque in seccion.bloques:
                y = draw_bloque(c, bloque, MARGIN_LEFT, y, config)

            y -= 6

        c.showPage()
        page_number += 1

    c.save()