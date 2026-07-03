import os


def formatear_titulo(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    nombre = nombre.replace("_", " ").replace("-", " ")
    return nombre.strip().title()


def listar_pdfs(carpeta):
    if not os.path.exists(carpeta):
        return []

    return [
        archivo for archivo in os.listdir(carpeta)
        if archivo.lower().endswith(".pdf")
    ]


def crear_nombre_salida(nombre_archivo):
    nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
    return f"{nombre_sin_extension}_con_header_footer.pdf"