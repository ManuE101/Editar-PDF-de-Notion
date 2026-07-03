import os
import json
from io import BytesIO
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4


CONFIG_FILE = "config_pdf_notion.json"


def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    defaults = {
        "entrada": "",
        "salida": "",
        "logo": "",
        "footer": "Confidencial - Uso interno",
        "version": "v1.0",
        "mostrar_logo": True,
        "mostrar_fecha": True,
        "numerar_paginas": True,
        "header_offset": 35,
        "footer_offset": 25,
        "agregar_portada": True,
        "titulo_portada": "Documentación WalkMe",
        "subtitulo_portada": "Documento generado desde Notion",
        "area_portada": "Uso interno"
    }

    defaults.update(config)
    return defaults


def guardar_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def formatear_titulo(nombre_archivo):
    nombre = os.path.splitext(nombre_archivo)[0]
    nombre = nombre.replace("_", " ").replace("-", " ")
    return nombre.strip().title()


def crear_overlay(ancho, alto, titulo, config, pagina_actual, total_paginas):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))

    margen_x = 40
    header_y = alto - int(config["header_offset"])
    footer_y = int(config["footer_offset"])

    texto_x = margen_x

    if config["mostrar_logo"] and config["logo"] and os.path.exists(config["logo"]):
        c.drawImage(
            ImageReader(config["logo"]),
            margen_x,
            header_y - 15,
            width=80,
            height=30,
            preserveAspectRatio=True,
            mask="auto"
        )
        texto_x = margen_x + 95

    c.setFont("Helvetica-Bold", 10)
    c.drawString(texto_x, header_y, titulo)

    if config["mostrar_fecha"]:
        fecha = datetime.now().strftime("%d/%m/%Y")
        c.setFont("Helvetica", 8)
        c.drawRightString(ancho - margen_x, header_y, fecha)

    c.line(margen_x, header_y - 25, ancho - margen_x, header_y - 25)

    c.setFont("Helvetica", 8)
    c.drawString(
        margen_x,
        footer_y,
        f'{config["footer"]} | {config["version"]}'
    )

    if config["numerar_paginas"]:
        c.drawRightString(
            ancho - margen_x,
            footer_y,
            f"Página {pagina_actual} de {total_paginas}"
        )

    c.line(margen_x, footer_y + 20, ancho - margen_x, footer_y + 20)

    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def crear_portada(titulo_documento, config):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    ancho, alto = A4
    margen_x = 70

    if config["mostrar_logo"] and config["logo"] and os.path.exists(config["logo"]):
        c.drawImage(
            ImageReader(config["logo"]),
            margen_x,
            alto - 130,
            width=150,
            height=70,
            preserveAspectRatio=True,
            mask="auto"
        )

    c.setFont("Helvetica-Bold", 24)
    c.drawString(margen_x, alto - 230, config["titulo_portada"])

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margen_x, alto - 270, titulo_documento)

    c.setFont("Helvetica", 12)
    c.drawString(margen_x, alto - 315, config["subtitulo_portada"])

    c.setFont("Helvetica", 10)
    c.drawString(margen_x, alto - 370, f'Versión: {config["version"]}')
    c.drawString(margen_x, alto - 390, f'Fecha: {datetime.now().strftime("%d/%m/%Y")}')
    c.drawString(margen_x, alto - 410, f'Área: {config["area_portada"]}')

    c.line(margen_x, alto - 450, ancho - margen_x, alto - 450)

    c.setFont("Helvetica", 9)
    c.drawString(margen_x, 60, config["footer"])

    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def procesar_pdf(ruta_pdf, ruta_salida, titulo, config):
    reader = PdfReader(ruta_pdf)
    writer = PdfWriter()

    total_paginas_originales = len(reader.pages)
    total_paginas = total_paginas_originales + (1 if config["agregar_portada"] else 0)

    if config["agregar_portada"]:
        portada = crear_portada(titulo, config)
        writer.add_page(portada)

    for i, pagina in enumerate(reader.pages, start=1):
        numero_pagina_final = i + (1 if config["agregar_portada"] else 0)

        ancho = float(pagina.mediabox.width)
        alto = float(pagina.mediabox.height)

        overlay = crear_overlay(
            ancho,
            alto,
            titulo,
            config,
            numero_pagina_final,
            total_paginas
        )

        pagina.merge_page(overlay)
        writer.add_page(pagina)

    with open(ruta_salida, "wb") as f:
        writer.write(f)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Notion PDF Processor")
        self.geometry("920x780")
        self.resizable(False, False)

        self.config_data = cargar_config()

        self.entrada_var = ctk.StringVar(value=self.config_data["entrada"])
        self.salida_var = ctk.StringVar(value=self.config_data["salida"])
        self.logo_var = ctk.StringVar(value=self.config_data["logo"])
        self.footer_var = ctk.StringVar(value=self.config_data["footer"])
        self.version_var = ctk.StringVar(value=self.config_data["version"])

        self.header_offset_var = ctk.StringVar(value=str(self.config_data["header_offset"]))
        self.footer_offset_var = ctk.StringVar(value=str(self.config_data["footer_offset"]))

        self.titulo_portada_var = ctk.StringVar(value=self.config_data["titulo_portada"])
        self.subtitulo_portada_var = ctk.StringVar(value=self.config_data["subtitulo_portada"])
        self.area_portada_var = ctk.StringVar(value=self.config_data["area_portada"])

        self.mostrar_logo_var = ctk.BooleanVar(value=self.config_data["mostrar_logo"])
        self.mostrar_fecha_var = ctk.BooleanVar(value=self.config_data["mostrar_fecha"])
        self.numerar_paginas_var = ctk.BooleanVar(value=self.config_data["numerar_paginas"])
        self.agregar_portada_var = ctk.BooleanVar(value=self.config_data["agregar_portada"])

        self.crear_interfaz()

    def crear_interfaz(self):
        titulo = ctk.CTkLabel(
            self,
            text="Notion PDF Processor",
            font=("Arial", 28, "bold")
        )
        titulo.pack(pady=(20, 5))

        subtitulo = ctk.CTkLabel(
            self,
            text="Agrega header, footer, portada, logo, fecha y numeración a PDFs exportados desde Notion",
            font=("Arial", 13)
        )
        subtitulo.pack(pady=(0, 15))

        contenedor = ctk.CTkScrollableFrame(self, corner_radius=18, width=860, height=610)
        contenedor.pack(padx=30, pady=10, fill="both", expand=True)

        self.crear_selector(contenedor, "Carpeta de entrada", self.entrada_var, self.elegir_entrada, 0)
        self.crear_selector(contenedor, "Carpeta de salida", self.salida_var, self.elegir_salida, 2)
        self.crear_selector(contenedor, "Logo", self.logo_var, self.elegir_logo, 4)

        ctk.CTkLabel(contenedor, text="Footer").grid(row=6, column=0, sticky="w", padx=25, pady=(15, 0))
        ctk.CTkEntry(contenedor, textvariable=self.footer_var, width=620).grid(row=7, column=0, padx=25, pady=6, sticky="w")

        ctk.CTkLabel(contenedor, text="Versión").grid(row=8, column=0, sticky="w", padx=25, pady=(15, 0))
        ctk.CTkEntry(contenedor, textvariable=self.version_var, width=160).grid(row=9, column=0, padx=25, pady=6, sticky="w")

        posiciones = ctk.CTkFrame(contenedor)
        posiciones.grid(row=10, column=0, columnspan=2, padx=25, pady=15, sticky="w")

        ctk.CTkLabel(posiciones, text="Posición header desde arriba").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        ctk.CTkEntry(posiciones, textvariable=self.header_offset_var, width=120).grid(row=1, column=0, padx=10, pady=8)

        ctk.CTkLabel(posiciones, text="Posición footer desde abajo").grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
        ctk.CTkEntry(posiciones, textvariable=self.footer_offset_var, width=120).grid(row=1, column=1, padx=10, pady=8)

        opciones = ctk.CTkFrame(contenedor, fg_color="transparent")
        opciones.grid(row=11, column=0, columnspan=2, padx=25, pady=10, sticky="w")

        ctk.CTkCheckBox(opciones, text="Mostrar logo", variable=self.mostrar_logo_var).grid(row=0, column=0, padx=(0, 25))
        ctk.CTkCheckBox(opciones, text="Mostrar fecha", variable=self.mostrar_fecha_var).grid(row=0, column=1, padx=(0, 25))
        ctk.CTkCheckBox(opciones, text="Numerar páginas", variable=self.numerar_paginas_var).grid(row=0, column=2, padx=(0, 25))
        ctk.CTkCheckBox(opciones, text="Agregar portada", variable=self.agregar_portada_var).grid(row=0, column=3)

        portada_frame = ctk.CTkFrame(contenedor)
        portada_frame.grid(row=12, column=0, columnspan=2, padx=25, pady=15, sticky="w")

        ctk.CTkLabel(portada_frame, text="Configuración de portada", font=("Arial", 15, "bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(portada_frame, text="Título de portada").grid(row=1, column=0, padx=10, sticky="w")
        ctk.CTkEntry(portada_frame, textvariable=self.titulo_portada_var, width=620).grid(row=2, column=0, padx=10, pady=6)

        ctk.CTkLabel(portada_frame, text="Subtítulo").grid(row=3, column=0, padx=10, sticky="w")
        ctk.CTkEntry(portada_frame, textvariable=self.subtitulo_portada_var, width=620).grid(row=4, column=0, padx=10, pady=6)

        ctk.CTkLabel(portada_frame, text="Área / Empresa").grid(row=5, column=0, padx=10, sticky="w")
        ctk.CTkEntry(portada_frame, textvariable=self.area_portada_var, width=620).grid(row=6, column=0, padx=10, pady=(6, 12))

        self.preview_label = ctk.CTkLabel(
            contenedor,
            text=self.generar_preview(),
            font=("Consolas", 12),
            justify="left"
        )
        self.preview_label.grid(row=13, column=0, padx=25, pady=15, sticky="w")

        ctk.CTkButton(
            contenedor,
            text="Actualizar vista previa",
            command=self.actualizar_preview,
            width=200
        ).grid(row=14, column=0, padx=25, pady=5, sticky="w")

        self.estado_label = ctk.CTkLabel(
            contenedor,
            text="Estado: listo para procesar.",
            font=("Arial", 12)
        )
        self.estado_label.grid(row=15, column=0, padx=25, pady=(15, 5), sticky="w")

        self.progress = ctk.CTkProgressBar(contenedor, width=620)
        self.progress.grid(row=16, column=0, padx=25, pady=10, sticky="w")
        self.progress.set(0)

        boton = ctk.CTkButton(
            contenedor,
            text="Procesar PDFs",
            font=("Arial", 16, "bold"),
            height=50,
            width=260,
            command=self.procesar_todos
        )
        boton.grid(row=17, column=0, columnspan=2, padx=25, pady=25)

    def crear_selector(self, padre, label, variable, comando, row):
        ctk.CTkLabel(padre, text=label).grid(row=row, column=0, sticky="w", padx=25, pady=(15, 0))

        ctk.CTkEntry(
            padre,
            textvariable=variable,
            width=620
        ).grid(row=row + 1, column=0, padx=25, pady=6, sticky="w")

        ctk.CTkButton(
            padre,
            text="Buscar",
            width=100,
            command=comando
        ).grid(row=row + 1, column=1, padx=(0, 25), pady=6)

    def elegir_entrada(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.entrada_var.set(carpeta)

    def elegir_salida(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.salida_var.set(carpeta)

    def elegir_logo(self):
        archivo = filedialog.askopenfilename(
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.logo_var.set(archivo)

    def generar_preview(self):
        return (
            "Vista previa aproximada:\n\n"
            "HEADER:\n"
            f"Logo | Título del PDF | Fecha\n"
            f"Posición desde arriba: {self.header_offset_var.get()} px\n\n"
            "FOOTER:\n"
            f'{self.footer_var.get()} | {self.version_var.get()} | Página X de Y\n'
            f"Posición desde abajo: {self.footer_offset_var.get()} px\n\n"
            "PORTADA:\n"
            f'{self.titulo_portada_var.get()}\n'
            f'{self.subtitulo_portada_var.get()}\n'
            f'{self.area_portada_var.get()}'
        )

    def actualizar_preview(self):
        self.preview_label.configure(text=self.generar_preview())

    def obtener_config_actual(self):
        try:
            header_offset = int(self.header_offset_var.get())
            footer_offset = int(self.footer_offset_var.get())
        except ValueError:
            messagebox.showerror("Error", "Las posiciones de header y footer deben ser números.")
            return None

        return {
            "entrada": self.entrada_var.get(),
            "salida": self.salida_var.get(),
            "logo": self.logo_var.get(),
            "footer": self.footer_var.get(),
            "version": self.version_var.get(),
            "mostrar_logo": self.mostrar_logo_var.get(),
            "mostrar_fecha": self.mostrar_fecha_var.get(),
            "numerar_paginas": self.numerar_paginas_var.get(),
            "header_offset": header_offset,
            "footer_offset": footer_offset,
            "agregar_portada": self.agregar_portada_var.get(),
            "titulo_portada": self.titulo_portada_var.get(),
            "subtitulo_portada": self.subtitulo_portada_var.get(),
            "area_portada": self.area_portada_var.get()
        }

    def procesar_todos(self):
        config = self.obtener_config_actual()

        if config is None:
            return

        guardar_config(config)

        entrada = config["entrada"]
        salida = config["salida"]

        if not entrada or not os.path.exists(entrada):
            messagebox.showerror("Error", "Seleccioná una carpeta de entrada válida.")
            return

        if not salida:
            messagebox.showerror("Error", "Seleccioná una carpeta de salida.")
            return

        os.makedirs(salida, exist_ok=True)

        archivos_pdf = [
            archivo for archivo in os.listdir(entrada)
            if archivo.lower().endswith(".pdf")
        ]

        if not archivos_pdf:
            messagebox.showwarning("Sin PDFs", "No se encontraron PDFs en la carpeta de entrada.")
            return

        total = len(archivos_pdf)
        procesados = 0

        for index, archivo in enumerate(archivos_pdf, start=1):
            try:
                self.estado_label.configure(text=f"Procesando {index} de {total}: {archivo}")
                self.progress.set(index / total)
                self.update_idletasks()

                ruta_pdf = os.path.join(entrada, archivo)
                nombre_sin_extension = os.path.splitext(archivo)[0]
                titulo = formatear_titulo(archivo)

                ruta_salida = os.path.join(
                    salida,
                    f"{nombre_sin_extension}_con_header_footer.pdf"
                )

                procesar_pdf(ruta_pdf, ruta_salida, titulo, config)
                procesados += 1

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"No se pudo procesar:\n{archivo}\n\nDetalle:\n{e}"
                )

        self.estado_label.configure(text=f"Proceso finalizado. PDFs procesados: {procesados}/{total}.")
        self.progress.set(1)

        messagebox.showinfo(
            "Listo",
            f"Se procesaron {procesados} PDF(s).\n\nLos archivos están en la carpeta de salida."
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()