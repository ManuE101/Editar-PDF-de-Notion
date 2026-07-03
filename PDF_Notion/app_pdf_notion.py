from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog, messagebox


def formatear_titulo(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    nombre = nombre.replace("_", " ").replace("-", " ")
    return nombre.strip().title()


def crear_overlay(ancho, alto, titulo, footer_texto, version, logo, pagina_actual, total_paginas):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    margen_x = 40
    header_y = alto - 35
    footer_y = 25
    fecha = datetime.now().strftime("%d/%m/%Y")

    if logo and os.path.exists(logo):
        c.drawImage(
            ImageReader(logo),
            margen_x,
            alto - 50,
            width=80,
            height=30,
            preserveAspectRatio=True,
            mask="auto"
        )
        texto_x = margen_x + 95
    else:
        texto_x = margen_x

    c.setFont("Helvetica-Bold", 10)
    c.drawString(texto_x, header_y, titulo)

    c.setFont("Helvetica", 8)
    c.drawRightString(ancho - margen_x, header_y, fecha)

    c.line(margen_x, alto - 60, ancho - margen_x, alto - 60)

    c.setFont("Helvetica", 8)
    c.drawString(margen_x, footer_y, f"{footer_texto} | {version}")

    c.drawRightString(
        ancho - margen_x,
        footer_y,
        f"Página {pagina_actual} de {total_paginas}"
    )

    c.line(margen_x, 45, ancho - margen_x, 45)

    c.save()
    buffer.seek(0)

    return PdfReader(buffer).pages[0]


def procesar_pdf(ruta_pdf, ruta_salida, titulo, footer_texto, version, logo):
    reader = PdfReader(ruta_pdf)
    writer = PdfWriter()

    total_paginas = len(reader.pages)

    for i, pagina in enumerate(reader.pages, start=1):
        ancho = float(pagina.mediabox.width)
        alto = float(pagina.mediabox.height)

        overlay = crear_overlay(
            ancho,
            alto,
            titulo,
            footer_texto,
            version,
            logo,
            i,
            total_paginas
        )

        pagina.merge_page(overlay)
        writer.add_page(pagina)

    with open(ruta_salida, "wb") as f:
        writer.write(f)


def elegir_carpeta_entrada():
    carpeta = filedialog.askdirectory()
    if carpeta:
        entrada_var.set(carpeta)


def elegir_carpeta_salida():
    carpeta = filedialog.askdirectory()
    if carpeta:
        salida_var.set(carpeta)


def elegir_logo():
    archivo = filedialog.askopenfilename(
        filetypes=[
            ("Imágenes", "*.png *.jpg *.jpeg"),
            ("Todos los archivos", "*.*")
        ]
    )
    if archivo:
        logo_var.set(archivo)


def procesar_todos():
    carpeta_entrada = entrada_var.get()
    carpeta_salida = salida_var.get()
    footer_texto = footer_var.get()
    version = version_var.get()
    logo = logo_var.get()

    if not carpeta_entrada:
        messagebox.showerror("Error", "Seleccioná una carpeta de entrada.")
        return

    if not carpeta_salida:
        messagebox.showerror("Error", "Seleccioná una carpeta de salida.")
        return

    archivos_pdf = [
        archivo for archivo in os.listdir(carpeta_entrada)
        if archivo.lower().endswith(".pdf")
    ]

    if not archivos_pdf:
        messagebox.showwarning("Sin PDFs", "No se encontraron PDFs en la carpeta de entrada.")
        return

    procesados = 0

    for archivo in archivos_pdf:
        try:
            titulo = formatear_titulo(archivo)

            ruta_pdf = os.path.join(carpeta_entrada, archivo)
            nombre_sin_extension = os.path.splitext(archivo)[0]

            ruta_salida = os.path.join(
                carpeta_salida,
                f"{nombre_sin_extension}_con_header_footer.pdf"
            )

            procesar_pdf(
                ruta_pdf,
                ruta_salida,
                titulo,
                footer_texto,
                version,
                logo
            )

            procesados += 1

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo procesar el archivo:\n{archivo}\n\nDetalle:\n{e}"
            )

    messagebox.showinfo(
        "Proceso finalizado",
        f"Se procesaron {procesados} PDF(s).\n\nLos archivos están en la carpeta de salida."
    )


ventana = tk.Tk()
ventana.title("Notion PDF Processor")
ventana.geometry("620x420")
ventana.resizable(False, False)

entrada_var = tk.StringVar()
salida_var = tk.StringVar()
logo_var = tk.StringVar()
footer_var = tk.StringVar(value="Confidencial - Uso interno")
version_var = tk.StringVar(value="v1.0")


tk.Label(ventana, text="Notion PDF Processor", font=("Arial", 18, "bold")).pack(pady=15)

frame = tk.Frame(ventana)
frame.pack(padx=20, pady=10, fill="x")


tk.Label(frame, text="Carpeta de entrada:").grid(row=0, column=0, sticky="w")
tk.Entry(frame, textvariable=entrada_var, width=55).grid(row=1, column=0, padx=5, pady=5)
tk.Button(frame, text="Buscar", command=elegir_carpeta_entrada).grid(row=1, column=1, padx=5)


tk.Label(frame, text="Carpeta de salida:").grid(row=2, column=0, sticky="w", pady=(10, 0))
tk.Entry(frame, textvariable=salida_var, width=55).grid(row=3, column=0, padx=5, pady=5)
tk.Button(frame, text="Buscar", command=elegir_carpeta_salida).grid(row=3, column=1, padx=5)


tk.Label(frame, text="Logo:").grid(row=4, column=0, sticky="w", pady=(10, 0))
tk.Entry(frame, textvariable=logo_var, width=55).grid(row=5, column=0, padx=5, pady=5)
tk.Button(frame, text="Buscar", command=elegir_logo).grid(row=5, column=1, padx=5)


tk.Label(frame, text="Footer:").grid(row=6, column=0, sticky="w", pady=(10, 0))
tk.Entry(frame, textvariable=footer_var, width=55).grid(row=7, column=0, padx=5, pady=5)


tk.Label(frame, text="Versión:").grid(row=8, column=0, sticky="w", pady=(10, 0))
tk.Entry(frame, textvariable=version_var, width=20).grid(row=9, column=0, sticky="w", padx=5, pady=5)


tk.Button(
    ventana,
    text="Procesar PDFs",
    font=("Arial", 12, "bold"),
    command=procesar_todos,
    width=25,
    height=2
).pack(pady=20)


ventana.mainloop()