from io import BytesIO
from datetime import datetime
import os
import tempfile

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from logo_stamper import estampar_logos_en_pdf, puede_estampar_logos
from portada import crear_portada
from utils import formatear_titulo, crear_nombre_salida
from error_messages import resumir_error
from process_control import ProcesoCancelado


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


def crear_overlay(ancho, alto, titulo, config, pagina_actual, total_paginas, area_visible=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    visible_x = 0
    visible_y = 0
    visible_ancho = ancho
    visible_alto = alto

    if area_visible:
        visible_x, visible_y, visible_ancho, visible_alto = area_visible

    margen_x = int(config.get("margen_x", 40))
    header_y = visible_y + visible_alto - int(config.get("header_offset", 35))
    footer_y = visible_y + int(config.get("footer_offset", 25))
    header_text_offset_x = int(config.get("header_text_offset_x", 0))
    footer_text_offset_x = int(config.get("footer_text_offset_x", 0))
    fuente_header = fuente_pdf(config, "fuente_header", "Helvetica-Bold")
    fuente_footer = fuente_pdf(config, "fuente_footer", "Helvetica")
    tamano_header = int(config.get("tamano_fuente_header", 10))
    tamano_footer = int(config.get("tamano_fuente_footer", 8))

    texto_x = visible_x + margen_x + header_text_offset_x

    # if config.get("mostrar_logo") and logo and os.path.exists(logo):
    #     c.drawImage(
    #         ImageReader(logo),
    #         margen_x,
    #         header_y - 15,
    #         width=int(config.get("logo_width", 80)),
    #         height=int(config.get("logo_height", 30)),
    #         preserveAspectRatio=True,
    #         mask="auto"
    #     )
    #     texto_x = margen_x + int(config.get("logo_width", 80)) + 15

    # c.setFont("Helvetica-Bold", 10)
    # c.drawString(texto_x, header_y, titulo)

    logo_width = int(config.get("logo_width", 80))
    logo_height = int(config.get("logo_height", 30))

    logo_izquierdo = config.get("logo_izquierdo", "")
    logo_central = config.get("logo_central", "")
    logo_derecho = config.get("logo_derecho", "")

    omitir_logos_overlay = config.get("_omitir_logos_overlay", False)

    if config.get("mostrar_logo") and logo_izquierdo and os.path.exists(logo_izquierdo):
        texto_x = visible_x + margen_x + logo_width + 15 + header_text_offset_x

    if config.get("mostrar_logo") and not omitir_logos_overlay:

        if logo_izquierdo and os.path.exists(logo_izquierdo):
            c.drawImage(
                ImageReader(logo_izquierdo),
                visible_x + margen_x,
                header_y - 15,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )

        if logo_central and os.path.exists(logo_central):
            c.drawImage(
                ImageReader(logo_central),
                visible_x + (visible_ancho - logo_width) / 2,
                header_y - 15,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )

        if logo_derecho and os.path.exists(logo_derecho):
            c.drawImage(
                ImageReader(logo_derecho),
                visible_x + visible_ancho - margen_x - logo_width,
                header_y - 15,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )

    c.setFont(fuente_header, tamano_header)
    c.drawString(texto_x, header_y, titulo)

    if config.get("mostrar_fecha"):
        fecha = datetime.now().strftime("%d/%m/%Y")
        c.setFont("Helvetica", max(6, min(14, tamano_footer)))
        c.drawRightString(visible_x + visible_ancho - margen_x, header_y, fecha)

    if config.get("mostrar_lineas_separadoras", True):
        c.line(
            visible_x + margen_x,
            header_y - 25,
            visible_x + visible_ancho - margen_x,
            header_y - 25
        )

    c.setFont(fuente_footer, tamano_footer)
    c.drawString(
        visible_x + margen_x + footer_text_offset_x,
        footer_y,
        f'{config.get("footer", "")} | {config.get("version", "")}'
    )

    if config.get("numerar_paginas", True):
        formato = config.get("formato_numeracion", "Página {pagina}")

        if formato != "Sin numeración":
            texto_pagina = formato.format(
                pagina=pagina_actual,
                total=total_paginas
            )

            c.drawRightString(
                visible_x + visible_ancho - margen_x,
                footer_y,
                texto_pagina
            )

    if config.get("mostrar_lineas_separadoras", True):
        c.line(
            visible_x + margen_x,
            footer_y + 20,
            visible_x + visible_ancho - margen_x,
            footer_y + 20
        )

    c.save()
    buffer.seek(0)

    return PdfReader(buffer).pages[0]


def procesar_pdf(
    ruta_pdf,
    ruta_salida,
    titulo,
    config,
    callback_estado=None,
    callback_progreso=None,
):
    if callback_estado:
        callback_estado("Leyendo y validando el PDF...")
    if callback_progreso:
        callback_progreso(0.05)

    reader = PdfReader(ruta_pdf)
    writer = PdfWriter()
    usar_estampado_logos = puede_estampar_logos()
    config_overlay = config.copy()

    if usar_estampado_logos:
        config_overlay["_omitir_logos_overlay"] = True

    total_original = len(reader.pages)
    total_final = total_original + (1 if config.get("agregar_portada") else 0)

    if config.get("agregar_portada"):
        if callback_estado:
            callback_estado("Generando portada...")
        writer.add_page(crear_portada(titulo, config))
    if callback_progreso:
        callback_progreso(0.12)

    for i, pagina in enumerate(reader.pages, start=1):
        if callback_estado:
            callback_estado(f"Aplicando diseño a la página {i} de {total_original}...")
        pagina_final = i + (1 if config.get("agregar_portada") else 0)

        if getattr(pagina, "rotation", 0) and hasattr(pagina, "transfer_rotation_to_content"):
            pagina.transfer_rotation_to_content()

        media_box = pagina.mediabox
        crop_box = pagina.cropbox

        ancho = float(media_box.width)
        alto = float(media_box.height)
        area_visible = (
            float(crop_box.left),
            float(crop_box.bottom),
            float(crop_box.width),
            float(crop_box.height),
        )

        overlay = crear_overlay(
            ancho,
            alto,
            titulo,
            config_overlay,
            pagina_final,
            total_final,
            area_visible
        )

        try:
            pagina.merge_page(overlay, over=True)
        except TypeError:
            pagina.merge_page(overlay)

        writer.add_page(pagina)
        if callback_progreso:
            avance_paginas = i / max(total_original, 1)
            callback_progreso(0.12 + (avance_paginas * 0.70))

    descriptor, ruta_temporal = tempfile.mkstemp(
        prefix="pdf_notion_",
        suffix=".pdf",
        dir=os.path.dirname(os.path.abspath(ruta_salida)),
    )
    os.close(descriptor)
    try:
        if callback_estado:
            callback_estado("Guardando el PDF...")
        if callback_progreso:
            callback_progreso(0.86)
        with open(ruta_temporal, "wb") as file:
            writer.write(file)

        if usar_estampado_logos:
            if callback_estado:
                callback_estado("Aplicando logos...")
            if callback_progreso:
                callback_progreso(0.92)
            estampar_logos_en_pdf(
                ruta_temporal,
                config,
                omitir_primera_pagina=bool(config.get("agregar_portada")),
            )

        if callback_estado:
            callback_estado("Finalizando el PDF...")
        if callback_progreso:
            callback_progreso(0.99)
        os.replace(ruta_temporal, ruta_salida)
    finally:
        try:
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)
        except OSError:
            pass


def procesar_carpeta(config, callback_estado=None, callback_progreso=None, callback_sobrescritura=None):
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
        return 0, 0, []

    procesados = 0
    errores = []

    for index, archivo in enumerate(archivos_pdf, start=1):
        if callback_estado:
            callback_estado(f"Procesando {index} de {total}: {archivo}")

        if callback_progreso:
            callback_progreso((index - 1) / total)

        ruta_pdf = os.path.join(entrada, archivo)
        titulo = formatear_titulo(archivo)
        nombre_salida = crear_nombre_salida(archivo)
        ruta_salida = os.path.join(salida, nombre_salida)

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
            procesar_pdf(
                ruta_pdf,
                ruta_salida,
                titulo,
                config,
                callback_estado=estado_archivo,
                callback_progreso=progreso_archivo,
            )
            procesados += 1
        except ProcesoCancelado:
            raise
        except Exception as error:
            errores.append(resumir_error(error, ruta_pdf))

    return procesados, total, errores
