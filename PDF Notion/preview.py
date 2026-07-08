import os
from datetime import datetime

import fitz
from PIL import Image, ImageDraw, ImageFont


def obtener_primer_pdf(carpeta):
    if not os.path.exists(carpeta):
        return None

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            return os.path.join(carpeta, archivo)

    return None


def cargar_fuente(tamano, bold=False):
    nombres = ["arialbd.ttf", "arial.ttf"] if bold else ["arial.ttf"]

    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except Exception:
            pass

    return ImageFont.load_default()


def ancho_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0]


def ajustar_texto(draw, texto, font, ancho_maximo):
    if ancho_texto(draw, texto, font) <= ancho_maximo:
        return texto

    sufijo = "..."
    disponible = max(0, ancho_maximo - ancho_texto(draw, sufijo, font))
    resultado = ""

    for caracter in texto:
        candidato = resultado + caracter
        if ancho_texto(draw, candidato, font) > disponible:
            break
        resultado = candidato

    return f"{resultado.rstrip()}{sufijo}" if resultado else sufijo


def pegar_logo(imagen, ruta_logo, x, y, ancho, alto):
    if not ruta_logo or not os.path.exists(ruta_logo):
        return

    try:
        logo = Image.open(ruta_logo).convert("RGBA")
        logo.thumbnail((max(1, ancho), max(1, alto)), Image.Resampling.LANCZOS)
        imagen.paste(logo, (int(x), int(y)), logo)
    except Exception:
        return


def formatear_numeracion(config):
    if not config.get("numerar_paginas", True):
        return ""

    formato = config.get("formato_numeracion", "Página {pagina}")

    if formato == "Sin numeración":
        return ""

    try:
        return formato.format(pagina=1, total="...")
    except Exception:
        return "Página 1"


def generar_preview_pdf(ruta_pdf, config, ancho_preview=360, alto_preview=None):
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        return None

    documento = fitz.open(ruta_pdf)
    pagina = documento[0]

    pix = pagina.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
    imagen = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    escala_ancho = ancho_preview / imagen.width
    escala_alto = alto_preview / imagen.height if alto_preview else escala_ancho
    escala = min(escala_ancho, escala_alto)
    ancho_preview = int(imagen.width * escala)
    nuevo_alto = int(imagen.height * escala)

    imagen = imagen.resize((ancho_preview, nuevo_alto))

    draw = ImageDraw.Draw(imagen)

    header_y = int(config.get("header_offset", 35) * escala)
    footer_y = nuevo_alto - int(config.get("footer_offset", 25) * escala)
    margen_x = int(config.get("margen_x", 40) * escala)
    logo_width = int(config.get("logo_width", 80) * escala)
    logo_height = int(config.get("logo_height", 30) * escala)
    logo_top = max(0, int((config.get("header_offset", 35) - 15) * escala))

    font_header = cargar_fuente(10, bold=True)
    font_small = cargar_fuente(8)

    logo_izquierdo = config.get("logo_izquierdo", "")
    logo_central = config.get("logo_central", "")
    logo_derecho = config.get("logo_derecho", "")

    if config.get("mostrar_logo"):
        pegar_logo(imagen, logo_izquierdo, margen_x, logo_top, logo_width, logo_height)
        pegar_logo(
            imagen,
            logo_central,
            (ancho_preview - logo_width) / 2,
            logo_top,
            logo_width,
            logo_height
        )
        pegar_logo(
            imagen,
            logo_derecho,
            ancho_preview - margen_x - logo_width,
            logo_top,
            logo_width,
            logo_height
        )

    texto_x = margen_x
    if config.get("mostrar_logo") and logo_izquierdo and os.path.exists(logo_izquierdo):
        texto_x = margen_x + logo_width + int(15 * escala)

    titulo_fallback = os.path.splitext(os.path.basename(ruta_pdf))[0]
    header_texto = config.get("header", "") or titulo_fallback
    header_text_y = max(0, header_y - 10)
    fecha = datetime.now().strftime("%d/%m/%Y")
    fecha_w = ancho_texto(draw, fecha, font_small) if config.get("mostrar_fecha") else 0
    header_limite = ancho_preview - margen_x - fecha_w - int(10 * escala)
    header_texto = ajustar_texto(draw, header_texto, font_header, header_limite - texto_x)
    draw.text((texto_x, header_text_y), header_texto, fill=(25, 25, 25), font=font_header)

    if config.get("mostrar_fecha"):
        draw.text(
            (ancho_preview - margen_x - fecha_w, header_text_y),
            fecha,
            fill=(45, 45, 45),
            font=font_small
        )

    linea_color = (90, 90, 90)
    guia_color = (220, 40, 40)

    draw.line(
        [(margen_x, header_y + int(25 * escala)), (ancho_preview - margen_x, header_y + int(25 * escala))],
        fill=linea_color,
        width=1
    )
    draw.line(
        [(margen_x, header_y), (ancho_preview - margen_x, header_y)],
        fill=guia_color,
        width=1
    )

    footer_texto = f'{config.get("footer", "")} | {config.get("version", "")}'.strip(" |")
    if footer_texto:
        draw.text((margen_x, footer_y), footer_texto, fill=(45, 45, 45), font=font_small)

    texto_pagina = formatear_numeracion(config)
    if texto_pagina:
        pagina_w = ancho_texto(draw, texto_pagina, font_small)
        draw.text(
            (ancho_preview - margen_x - pagina_w, footer_y),
            texto_pagina,
            fill=(45, 45, 45),
            font=font_small
        )

    footer_line_y = max(0, footer_y - int(20 * escala))
    draw.line(
        [(margen_x, footer_line_y), (ancho_preview - margen_x, footer_line_y)],
        fill=linea_color,
        width=1
    )
    draw.line(
        [(margen_x, footer_y), (ancho_preview - margen_x, footer_y)],
        fill=guia_color,
        width=1
    )

    documento.close()

    return imagen
