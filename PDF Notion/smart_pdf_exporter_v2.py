import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from PIL import Image as PILImage

from layout_engine import dividir_en_paginas
from logo_stamper import estampar_logos_en_pdf, puede_estampar_logos


PAGE_WIDTH, PAGE_HEIGHT = A4

MARGIN_LEFT = 1.8 * cm
MARGIN_RIGHT = 1.8 * cm
MARGIN_TOP = 2.2 * cm
MARGIN_BOTTOM = 2.0 * cm

CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
INDICE_LINEAS_POR_PAGINA = 34


FUENTES_PDF = {
    "Helvetica",
    "Helvetica-Bold",
    "Helvetica-Oblique",
    "Times-Roman",
    "Times-Bold",
    "Courier",
    "Courier-Bold",
}


def fuente_pdf(config, clave, fallback):
    fuente = config.get(clave, fallback)
    return fuente if fuente in FUENTES_PDF else fallback


def draw_header_footer(c, config, page_number, titulo_pdf):
    c.saveState()

    footer = config.get("footer", "Confidencial - Uso interno")
    version = config.get("version", "v1.0")
    margen_x = int(config.get("margen_x", MARGIN_LEFT))
    header_y = PAGE_HEIGHT - int(config.get("header_offset", 35))
    footer_y = int(config.get("footer_offset", 25))
    logo_width = int(config.get("logo_width", 80))
    logo_height = int(config.get("logo_height", 30))
    header_text_offset_x = int(config.get("header_text_offset_x", 0))
    footer_text_offset_x = int(config.get("footer_text_offset_x", 0))
    fuente_header = fuente_pdf(config, "fuente_header", "Helvetica-Bold")
    fuente_footer = fuente_pdf(config, "fuente_footer", "Helvetica")
    tamano_header = int(config.get("tamano_fuente_header", 10))
    tamano_footer = int(config.get("tamano_fuente_footer", 8))
    texto_x = margen_x + header_text_offset_x
    logo_izquierdo = config.get("logo_izquierdo", "")
    logo_central = config.get("logo_central", "")
    logo_derecho = config.get("logo_derecho", "")

    omitir_logos_overlay = config.get("_omitir_logos_overlay", False)

    if config.get("mostrar_logo") and logo_izquierdo and os.path.exists(logo_izquierdo):
        texto_x = margen_x + logo_width + 15 + header_text_offset_x

    if config.get("mostrar_logo") and not omitir_logos_overlay:
        if logo_izquierdo and os.path.exists(logo_izquierdo):
            c.drawImage(
                ImageReader(logo_izquierdo),
                margen_x,
                header_y - 15,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )

        if logo_central and os.path.exists(logo_central):
            c.drawImage(
                ImageReader(logo_central),
                (PAGE_WIDTH - logo_width) / 2,
                header_y - 15,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )

        if logo_derecho and os.path.exists(logo_derecho):
            c.drawImage(
                ImageReader(logo_derecho),
                PAGE_WIDTH - margen_x - logo_width,
                header_y - 15,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )

    c.setFont(fuente_header, tamano_header)
    header_texto = config.get("header", "") or titulo_pdf
    c.drawString(texto_x, header_y, header_texto)

    c.setFont("Helvetica", max(6, min(14, tamano_footer)))
    c.drawRightString(PAGE_WIDTH - margen_x, header_y, version)

    if config.get("mostrar_lineas_separadoras", True):
        c.line(
            margen_x,
            header_y - 25,
            PAGE_WIDTH - margen_x,
            header_y - 25
        )

    c.setFont(fuente_footer, tamano_footer)
    c.drawString(margen_x + footer_text_offset_x, footer_y, footer)
    #c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, 1 * cm, f"Página {page_number}")
    if config.get("numerar_paginas", True):
        formato = config.get("formato_numeracion", "Página {pagina}")

        if formato != "Sin numeración":
            texto_pagina = formato.format(
                pagina=page_number,
                total=config.get("total_paginas", "")
            )

            c.drawRightString(PAGE_WIDTH - margen_x, footer_y, texto_pagina)

    if config.get("mostrar_lineas_separadoras", True):
        c.line(margen_x, footer_y + 20, PAGE_WIDTH - margen_x, footer_y + 20)
    c.restoreState()


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


def collect_indice_entries(paginas, primera_pagina_contenido):
    entries = []

    for page_index, pagina in enumerate(paginas, start=primera_pagina_contenido):
        for seccion in pagina.secciones:
            for bloque in seccion.bloques:
                if bloque.tipo == "heading" and bloque.texto:
                    entries.append({
                        "texto": bloque.texto,
                        "nivel": bloque.nivel,
                        "pagina": page_index,
                    })

    return entries


def calcular_paginas_indice(entries):
    if not entries:
        return 0

    return max(1, (len(entries) + INDICE_LINEAS_POR_PAGINA - 1) // INDICE_LINEAS_POR_PAGINA)


def draw_indice_pages(c, entries, config, documento, primera_pagina_indice):
    if not entries:
        return 0

    paginas_indice = calcular_paginas_indice(entries)

    for page_idx in range(paginas_indice):
        inicio = page_idx * INDICE_LINEAS_POR_PAGINA
        fin = inicio + INDICE_LINEAS_POR_PAGINA
        entries_pagina = entries[inicio:fin]

        y = PAGE_HEIGHT - MARGIN_TOP
        c.setFont("Helvetica-Bold", 22)
        c.drawString(MARGIN_LEFT, y, "Índice")
        y -= 1.2 * cm

        for entry in entries_pagina:
            nivel = max(1, min(3, int(entry.get("nivel", 1))))
            indent = (nivel - 1) * 0.45 * cm
            font_name = "Helvetica-Bold" if nivel == 1 else "Helvetica"
            font_size = 10 if nivel == 1 else 9
            page_text = str(entry["pagina"])
            text_x = MARGIN_LEFT + indent
            page_w = c.stringWidth(page_text, "Helvetica", 9)
            max_text_w = CONTENT_WIDTH - indent - page_w - 0.5 * cm
            texto = entry["texto"]

            while texto and c.stringWidth(texto + "...", font_name, font_size) > max_text_w:
                texto = texto[:-1]

            if texto != entry["texto"]:
                texto = texto.rstrip() + "..."

            c.setFont(font_name, font_size)
            c.drawString(text_x, y, texto)

            text_w = c.stringWidth(texto, font_name, font_size)
            dots_start = text_x + text_w + 0.15 * cm
            dots_end = PAGE_WIDTH - MARGIN_RIGHT - page_w - 0.15 * cm

            if dots_end > dots_start:
                c.setDash(1, 2)
                c.line(dots_start, y + 2, dots_end, y + 2)
                c.setDash()

            c.setFont("Helvetica", 9)
            c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y, page_text)
            y -= 0.5 * cm

        if not config.get("_omitir_header_footer", False):
            draw_header_footer(c, config, primera_pagina_indice + page_idx, documento.titulo)
        c.showPage()

    return paginas_indice


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
    logos = [
        config.get("logo_izquierdo", ""),
        config.get("logo_central", ""),
        config.get("logo_derecho", ""),
    ]
    if not any(logos):
        logos = [config.get("logo", "")]

    if config.get("mostrar_header_portada", False):
        header = config.get("header_portada", "") or documento.titulo
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 1.1 * cm, header)
        c.line(MARGIN_LEFT, PAGE_HEIGHT - 1.35 * cm, PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 1.35 * cm)

    y = PAGE_HEIGHT - 3 * cm

    logo_width = int(config.get("logo_width", 80))
    logo_height = int(config.get("logo_height", 30))
    posiciones_x = [
        MARGIN_LEFT,
        (PAGE_WIDTH - logo_width) / 2,
        PAGE_WIDTH - MARGIN_RIGHT - logo_width,
    ]
    logos_dibujados = False

    if config.get("mostrar_logo"):
        for logo, x in zip(logos, posiciones_x):
            if logo and os.path.exists(logo):
                c.drawImage(
                    ImageReader(logo),
                    x,
                    y - logo_height,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    mask="auto"
                )
                logos_dibujados = True

    if logos_dibujados:
        y -= logo_height + 1 * cm

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


def exportar_documento_pdf_v2(
    documento,
    ruta_salida,
    config,
    callback_estado=None,
    callback_progreso=None,
):
    usar_estampado_logos = puede_estampar_logos()
    config_pdf = config.copy()

    if usar_estampado_logos:
        config_pdf["_omitir_logos_overlay"] = True

    if callback_estado:
        callback_estado("Distribuyendo el contenido en páginas...")
    if callback_progreso:
        callback_progreso(0.05)
    paginas = dividir_en_paginas(documento)
    paginas_portada = 1 if config_pdf.get("agregar_portada", True) else 0
    agregar_indice = bool(config_pdf.get("agregar_indice", False))
    entries_indice = []
    paginas_indice = 0

    if agregar_indice:
        entries_base = collect_indice_entries(paginas, paginas_portada + 1)
        paginas_indice = calcular_paginas_indice(entries_base)
        primera_pagina_contenido = paginas_portada + paginas_indice + 1
        entries_indice = collect_indice_entries(paginas, primera_pagina_contenido)

    total_paginas = len(paginas) + paginas_portada + paginas_indice
    config_pdf["total_paginas"] = total_paginas

    c = canvas.Canvas(ruta_salida, pagesize=A4)

    page_number = 1

    if config_pdf.get("agregar_portada", True):
        if callback_estado:
            callback_estado("Generando portada...")
        draw_portada(c, documento, config_pdf)
        c.showPage()
        page_number += 1

    if entries_indice:
        if callback_estado:
            callback_estado("Generando índice automático...")
        draw_indice_pages(
            c,
            entries_indice,
            config_pdf,
            documento,
            primera_pagina_indice=page_number
        )
        page_number += paginas_indice

    total_contenido = len(paginas)
    for indice_pagina, pagina in enumerate(paginas, start=1):
        if callback_estado:
            callback_estado(
                f"Generando página de contenido {indice_pagina} de {total_contenido}..."
            )
        y = PAGE_HEIGHT - MARGIN_TOP

        for seccion in pagina.secciones:
            for bloque in seccion.bloques:
                y = draw_bloque(c, bloque, MARGIN_LEFT, y, config_pdf)

            y -= 6

        if not config_pdf.get("_omitir_header_footer", False):
            draw_header_footer(c, config_pdf, page_number, documento.titulo)
        c.showPage()
        page_number += 1
        if callback_progreso:
            callback_progreso(0.15 + (0.70 * indice_pagina / max(total_contenido, 1)))

    if callback_estado:
        callback_estado("Guardando el documento...")
    if callback_progreso:
        callback_progreso(0.88)
    c.save()

    if usar_estampado_logos:
        if callback_estado:
            callback_estado("Aplicando logos...")
        if callback_progreso:
            callback_progreso(0.93)
        estampar_logos_en_pdf(
            ruta_salida,
            config,
            omitir_primera_pagina=bool(config_pdf.get("agregar_portada", True)),
        )
    if callback_progreso:
        callback_progreso(1.0)
