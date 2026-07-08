import errno
import os
import zipfile


def describir_error(error, accion="completar la operación", ruta=None):
    nombre = error.__class__.__name__
    detalle = str(error).strip()
    titulo = "No se pudo completar la operación"
    causa = detalle or "Se produjo un error inesperado."
    sugerencia = "Revisá el archivo seleccionado e intentá nuevamente."

    if isinstance(error, PermissionError):
        titulo = "Acceso denegado"
        causa = "Windows no permitió leer o escribir uno de los archivos."
        sugerencia = (
            "Cerrá el archivo si está abierto en otra aplicación y verificá "
            "que tengas permisos sobre la carpeta."
        )
    elif isinstance(error, FileNotFoundError):
        titulo = "Archivo o carpeta no encontrado"
        causa = "La ruta dejó de estar disponible o fue movida."
        sugerencia = "Volvé a seleccionar el archivo o la carpeta."
    elif isinstance(error, zipfile.BadZipFile) or nombre == "BadZipFile":
        titulo = "ZIP dañado o incompleto"
        causa = "El archivo no se puede abrir como un ZIP válido."
        sugerencia = "Exportá nuevamente el contenido desde Notion."
    elif nombre in {"PdfReadError", "EmptyFileError"}:
        titulo = "PDF dañado o no compatible"
        causa = "No se pudo leer la estructura interna del PDF."
        sugerencia = "Abrí el PDF para comprobarlo o generá una copia nueva."
    elif nombre == "ZipNotionInvalido":
        titulo = "ZIP de Notion inválido"
        sugerencia = "Exportá la página desde Notion incluyendo el contenido HTML."
    elif nombre in {"UnidentifiedImageError", "DecompressionBombError"}:
        titulo = "Logo no compatible"
        causa = "No se pudo leer una de las imágenes configuradas como logo."
        sugerencia = "Usá una imagen PNG o JPG válida."
    elif isinstance(error, OSError):
        if getattr(error, "errno", None) == errno.ENOSPC:
            titulo = "Espacio insuficiente"
            causa = "No queda espacio disponible para generar el archivo."
            sugerencia = "Liberá espacio o elegí otra carpeta de salida."
        elif getattr(error, "errno", None) == errno.ENAMETOOLONG:
            titulo = "Nombre de archivo demasiado largo"
            sugerencia = "Elegí un nombre de salida más corto."

    partes = [f"No se pudo {accion}."]
    if ruta:
        partes.extend(["", f"Archivo: {os.path.basename(ruta)}"])
    partes.extend(["", f"Causa: {causa}", "", f"Qué podés hacer: {sugerencia}"])
    return titulo, "\n".join(partes)


def resumir_error(error, ruta=None):
    titulo, mensaje = describir_error(error, ruta=ruta)
    causa = next(
        (linea[7:] for linea in mensaje.splitlines() if linea.startswith("Causa: ")),
        str(error),
    )
    archivo = os.path.basename(ruta) if ruta else "Archivo desconocido"
    return f"{archivo}: {titulo}. {causa}"
