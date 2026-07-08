import os
import re
import shutil

from utils import formatear_titulo


CARACTERES_INVALIDOS = r'[<>:"/\\|?*\x00-\x1f]'


def limpiar_nombre_archivo(texto, fallback="documento"):
    nombre = re.sub(CARACTERES_INVALIDOS, " ", texto or "")
    nombre = re.sub(r"\s+", " ", nombre).strip(" .")
    return nombre or fallback


def nombre_pdf_desde_titulo(titulo, fallback="documento"):
    return f"{limpiar_nombre_archivo(titulo, fallback)}.pdf"


def _titulo_valido(texto):
    texto = " ".join((texto or "").split()).strip()
    if not texto:
        return ""
    if len(texto) < 3:
        return ""
    return texto


def detectar_titulo_zip(ruta_zip):
    from notion_parser import parsear_html_notion
    from notion_zip_reader import leer_html_desde_zip

    resultado = leer_html_desde_zip(ruta_zip)
    carpeta_temporal = resultado.get("carpeta_temporal")

    try:
        documento = parsear_html_notion(
            resultado["contenido_html"],
            resultado["html_principal"]
        )

        for bloque in documento.bloques:
            if bloque.tipo == "heading" and bloque.nivel == 1:
                titulo = _titulo_valido(bloque.texto)
                if titulo:
                    return titulo

        return _titulo_valido(documento.titulo) or formatear_titulo(os.path.basename(ruta_zip))

    finally:
        if carpeta_temporal and os.path.exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal, ignore_errors=True)


def detectar_titulo_pdf(ruta_pdf):
    try:
        import fitz

        doc = fitz.open(ruta_pdf)

        try:
            metadata_title = _titulo_valido(doc.metadata.get("title", ""))
            if metadata_title and metadata_title.lower() not in {"untitled", "sin titulo", "sin título"}:
                return metadata_title

            if len(doc) == 0:
                return formatear_titulo(os.path.basename(ruta_pdf))

            page = doc[0]
            blocks = page.get_text("dict").get("blocks", [])
            candidates = []

            for block in blocks:
                for line in block.get("lines", []):
                    spans = [span for span in line.get("spans", []) if _titulo_valido(span.get("text", ""))]
                    if not spans:
                        continue

                    texto = _titulo_valido(" ".join(span.get("text", "") for span in spans))
                    if not texto:
                        continue

                    max_size = max(float(span.get("size", 0)) for span in spans)
                    y0 = min(float(span.get("bbox", [0, 9999])[1]) for span in spans)
                    candidates.append((max_size, -y0, texto))

            if candidates:
                candidates.sort(reverse=True)
                return candidates[0][2]

        finally:
            doc.close()

    except Exception:
        pass

    return formatear_titulo(os.path.basename(ruta_pdf))
