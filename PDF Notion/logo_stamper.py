import os
import tempfile


def puede_estampar_logos():
    try:
        import fitz  # noqa: F401
        return True
    except Exception:
        return False


def estampar_logos_en_pdf(ruta_pdf, config, omitir_primera_pagina=False):
    if not config.get("mostrar_logo"):
        return False

    logos = [
        config.get("logo_izquierdo", ""),
        config.get("logo_central", ""),
        config.get("logo_derecho", ""),
    ]

    logos = [logo if logo and os.path.exists(logo) else "" for logo in logos]

    if not any(logos):
        return False

    import fitz

    margen_x = int(config.get("margen_x", 40))
    header_offset = int(config.get("header_offset", 35))
    logo_width = int(config.get("logo_width", 80))
    logo_height = int(config.get("logo_height", 30))

    top = max(0, header_offset - 15)
    bottom = top + logo_height

    doc = fitz.open(ruta_pdf)

    for index, page in enumerate(doc):
        if omitir_primera_pagina and index == 0:
            continue

        page_width = page.rect.width
        positions_x = [
            margen_x,
            (page_width - logo_width) / 2,
            page_width - margen_x - logo_width,
        ]

        for logo, x in zip(logos, positions_x):
            if not logo:
                continue

            rect = fitz.Rect(x, top, x + logo_width, bottom)
            page.insert_image(
                rect,
                filename=logo,
                keep_proportion=True,
                overlay=True,
            )

    directory = os.path.dirname(ruta_pdf)
    fd, temp_path = tempfile.mkstemp(suffix=".pdf", dir=directory)
    os.close(fd)

    try:
        doc.save(temp_path, garbage=4, deflate=True)
    finally:
        doc.close()

    os.replace(temp_path, ruta_pdf)
    return True
