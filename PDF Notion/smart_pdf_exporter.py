import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    KeepTogether,
    ListFlowable,
    ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT


def crear_estilos():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TituloDocumento",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        spaceAfter=18,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name="Heading1Custom",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="Heading2Custom",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        spaceBefore=14,
        spaceAfter=7,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="Heading3Custom",
        parent=styles["Heading3"],
        fontSize=13,
        leading=17,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="ParrafoCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=7
    ))

    styles.add(ParagraphStyle(
        name="BulletCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        leftIndent=6,
        spaceAfter=4
    ))

    return styles


def header_footer(canvas, doc, config):
    canvas.saveState()

    ancho, alto = A4
    margen_x = 1.8 * cm

    titulo = config.get("titulo_pdf", "")
    footer = config.get("footer", "Confidencial - Uso interno")
    version = config.get("version", "v1.0")

    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(margen_x, alto - 1.1 * cm, titulo)

    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(ancho - margen_x, alto - 1.1 * cm, version)

    canvas.line(margen_x, alto - 1.35 * cm, ancho - margen_x, alto - 1.35 * cm)

    canvas.setFont("Helvetica", 8)
    canvas.drawString(margen_x, 1 * cm, footer)
    canvas.drawRightString(ancho - margen_x, 1 * cm, f"Página {doc.page}")

    canvas.line(margen_x, 1.3 * cm, ancho - margen_x, 1.3 * cm)

    canvas.restoreState()


def crear_portada_story(documento, config, styles):
    story = []

    story.append(Spacer(1, 3 * cm))

    logo = config.get("logo", "")
    if logo and os.path.exists(logo):
        story.append(Image(logo, width=4 * cm, height=2 * cm))
        story.append(Spacer(1, 1 * cm))

    story.append(Paragraph(config.get("titulo_portada", "Documentación"), styles["TituloDocumento"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(documento.titulo, styles["Heading1Custom"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(config.get("subtitulo_portada", ""), styles["ParrafoCustom"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f'Versión: {config.get("version", "v1.0")}', styles["ParrafoCustom"]))
    story.append(Paragraph(f'Área: {config.get("area_portada", "Uso interno")}', styles["ParrafoCustom"]))

    story.append(PageBreak())

    return story


def imagen_ajustada(ruta_imagen, max_width):
    try:
        img = Image(ruta_imagen)
        ratio = img.imageHeight / float(img.imageWidth)

        width = min(max_width, img.imageWidth)
        height = width * ratio

        if height > 12 * cm:
            height = 12 * cm
            width = height / ratio

        return Image(ruta_imagen, width=width, height=height)

    except Exception:
        return None


def crear_lista_bullets(items, styles):
    list_items = [
        ListItem(
            Paragraph(item, styles["BulletCustom"]),
            leftIndent=12
        )
        for item in items
    ]

    return ListFlowable(
        list_items,
        bulletType="bullet",
        start="circle",
        leftIndent=18,
        bulletFontSize=8
    )


def heading_style(bloque, styles):
    if bloque.nivel == 1:
        return styles["Heading1Custom"]

    if bloque.nivel == 2:
        return styles["Heading2Custom"]

    return styles["Heading3Custom"]


def exportar_documento_pdf(documento, ruta_salida, config):
    styles = crear_estilos()
    config["titulo_pdf"] = documento.titulo

    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm
    )

    story = []

    if config.get("agregar_portada", True):
        story.extend(crear_portada_story(documento, config, styles))

    bloques = documento.bloques
    i = 0

    while i < len(bloques):
        bloque = bloques[i]

        if bloque.tipo == "heading":
            elementos = [
                Paragraph(bloque.texto, heading_style(bloque, styles))
            ]

            # Adjunta el primer contenido después del título para que no quede solo.
            if i + 1 < len(bloques) and bloques[i + 1].tipo != "heading":
                siguiente = bloques[i + 1]

                if siguiente.tipo == "paragraph":
                    elementos.append(Paragraph(siguiente.texto, styles["ParrafoCustom"]))
                    i += 1

                elif siguiente.tipo == "bullet":
                    bullets = []

                    j = i + 1
                    while j < len(bloques) and bloques[j].tipo == "bullet":
                        bullets.append(bloques[j].texto)
                        j += 1

                    elementos.append(crear_lista_bullets(bullets, styles))
                    i = j - 1

                elif siguiente.tipo == "image":
                    img = imagen_ajustada(siguiente.imagen, doc.width)
                    if img:
                        elementos.append(img)
                    i += 1

            story.append(KeepTogether(elementos))

        elif bloque.tipo == "paragraph":
            # Si un párrafo funciona como etiqueta de lista, por ejemplo "Ventajas",
            # lo mantiene junto con los bullets que vienen después.
            if i + 1 < len(bloques) and bloques[i + 1].tipo == "bullet":
                elementos = [
                    Paragraph(bloque.texto, styles["ParrafoCustom"])
                ]

                bullets = []
                j = i + 1

                while j < len(bloques) and bloques[j].tipo == "bullet":
                    bullets.append(bloques[j].texto)
                    j += 1

                elementos.append(crear_lista_bullets(bullets, styles))

                story.append(KeepTogether(elementos))
                i = j - 1

            else:
                story.append(Paragraph(bloque.texto, styles["ParrafoCustom"]))

        elif bloque.tipo == "bullet":
            bullets = []
            j = i

            while j < len(bloques) and bloques[j].tipo == "bullet":
                bullets.append(bloques[j].texto)
                j += 1

            story.append(KeepTogether([crear_lista_bullets(bullets, styles)]))
            i = j - 1

        elif bloque.tipo == "image":
            img = imagen_ajustada(bloque.imagen, doc.width)
            if img:
                story.append(Spacer(1, 0.2 * cm))
                story.append(KeepTogether([img]))
                story.append(Spacer(1, 0.3 * cm))

        i += 1

    doc.build(
        story,
        onFirstPage=lambda c, d: header_footer(c, d, config),
        onLaterPages=lambda c, d: header_footer(c, d, config)
    )