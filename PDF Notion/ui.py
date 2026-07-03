import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from config import cargar_config, guardar_config
from pdf_processor import procesar_carpeta
from preview import obtener_primer_pdf, generar_preview_pdf


class PDFNotionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("PDF Notion")
        self.geometry("1100x760")
        self.resizable(False, False)

        self.config_data = cargar_config()

        self.entrada_var = ctk.StringVar(value=self.config_data["entrada"])
        self.salida_var = ctk.StringVar(value=self.config_data["salida"])
        self.logo_var = ctk.StringVar(value=self.config_data["logo"])
        self.footer_var = ctk.StringVar(value=self.config_data["footer"])
        self.version_var = ctk.StringVar(value=self.config_data["version"])

        self.header_offset_var = ctk.IntVar(value=int(self.config_data["header_offset"]))
        self.footer_offset_var = ctk.IntVar(value=int(self.config_data["footer_offset"]))
        self.margen_x_var = ctk.IntVar(value=int(self.config_data["margen_x"]))
        self.logo_width_var = ctk.IntVar(value=int(self.config_data["logo_width"]))
        self.logo_height_var = ctk.IntVar(value=int(self.config_data["logo_height"]))

        self.titulo_portada_var = ctk.StringVar(value=self.config_data["titulo_portada"])
        self.subtitulo_portada_var = ctk.StringVar(value=self.config_data["subtitulo_portada"])
        self.area_portada_var = ctk.StringVar(value=self.config_data["area_portada"])

        self.mostrar_logo_var = ctk.BooleanVar(value=self.config_data["mostrar_logo"])
        self.mostrar_fecha_var = ctk.BooleanVar(value=self.config_data["mostrar_fecha"])
        self.numerar_paginas_var = ctk.BooleanVar(value=self.config_data["numerar_paginas"])
        self.agregar_portada_var = ctk.BooleanVar(value=self.config_data["agregar_portada"])

        self.preview_image_tk = None

        self.crear_interfaz()
        self.actualizar_preview()

    def crear_interfaz(self):
        header = ctk.CTkFrame(self, height=70, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="PDF Notion",
            font=("Arial", 28, "bold")
        ).pack(side="left", padx=30, pady=20)

        ctk.CTkLabel(
            header,
            text="Procesador de PDFs exportados desde Notion",
            font=("Arial", 13)
        ).pack(side="left", padx=10, pady=25)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)

        panel_config = ctk.CTkScrollableFrame(body, width=520, height=620, corner_radius=18)
        panel_config.pack(side="left", fill="y", padx=(0, 20))

        panel_preview = ctk.CTkFrame(body, width=520, height=620, corner_radius=18)
        panel_preview.pack(side="right", fill="both", expand=True)

        self.crear_panel_config(panel_config)
        self.crear_panel_preview(panel_preview)

    def crear_panel_config(self, panel):
        ctk.CTkLabel(
            panel,
            text="Configuración",
            font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.crear_selector(panel, "Carpeta de entrada", self.entrada_var, self.elegir_entrada)
        self.crear_selector(panel, "Carpeta de salida", self.salida_var, self.elegir_salida)
        self.crear_selector(panel, "Logo", self.logo_var, self.elegir_logo)

        self.crear_entry(panel, "Footer", self.footer_var)
        self.crear_entry(panel, "Versión", self.version_var, width=160)

        self.crear_slider(panel, "Header desde arriba", self.header_offset_var, 10, 150)
        self.crear_slider(panel, "Footer desde abajo", self.footer_offset_var, 10, 150)
        self.crear_slider(panel, "Margen izquierdo/derecho", self.margen_x_var, 10, 120)
        self.crear_slider(panel, "Ancho del logo", self.logo_width_var, 30, 200)
        self.crear_slider(panel, "Alto del logo", self.logo_height_var, 15, 100)

        opciones = ctk.CTkFrame(panel, fg_color="transparent")
        opciones.pack(fill="x", padx=20, pady=10)

        ctk.CTkCheckBox(
            opciones,
            text="Mostrar logo",
            variable=self.mostrar_logo_var,
            command=self.actualizar_preview
        ).grid(row=0, column=0, sticky="w", pady=5)

        ctk.CTkCheckBox(
            opciones,
            text="Mostrar fecha",
            variable=self.mostrar_fecha_var,
            command=self.actualizar_preview
        ).grid(row=1, column=0, sticky="w", pady=5)

        ctk.CTkCheckBox(
            opciones,
            text="Numerar páginas",
            variable=self.numerar_paginas_var,
            command=self.actualizar_preview
        ).grid(row=2, column=0, sticky="w", pady=5)

        ctk.CTkCheckBox(
            opciones,
            text="Agregar portada",
            variable=self.agregar_portada_var,
            command=self.actualizar_preview
        ).grid(row=3, column=0, sticky="w", pady=5)

        ctk.CTkLabel(
            panel,
            text="Portada",
            font=("Arial", 17, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.crear_entry(panel, "Título de portada", self.titulo_portada_var)
        self.crear_entry(panel, "Subtítulo de portada", self.subtitulo_portada_var)
        self.crear_entry(panel, "Área / Empresa", self.area_portada_var)

        self.estado_label = ctk.CTkLabel(
            panel,
            text="Estado: listo para procesar.",
            font=("Arial", 12)
        )
        self.estado_label.pack(anchor="w", padx=20, pady=(20, 5))

        self.progress = ctk.CTkProgressBar(panel, width=420)
        self.progress.pack(anchor="w", padx=20, pady=10)
        self.progress.set(0)

        ctk.CTkButton(
            panel,
            text="Procesar PDFs",
            font=("Arial", 16, "bold"),
            height=48,
            command=self.procesar
        ).pack(fill="x", padx=20, pady=(10, 25))

    def crear_panel_preview(self, panel):
        ctk.CTkLabel(
            panel,
            text="Vista previa real",
            font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        ctk.CTkLabel(
            panel,
            text="Usa las líneas guía para ajustar header y footer antes de procesar.",
            font=("Arial", 12)
        ).pack(anchor="w", padx=20, pady=(0, 15))

        self.preview_label = ctk.CTkLabel(panel, text="")
        self.preview_label.pack(padx=20, pady=10)

        ctk.CTkButton(
            panel,
            text="Actualizar vista previa",
            command=self.actualizar_preview,
            width=220
        ).pack(pady=(10, 5))

        self.preview_info = ctk.CTkLabel(
            panel,
            text="",
            font=("Arial", 12)
        )
        self.preview_info.pack(pady=5)

    def crear_selector(self, panel, texto, variable, comando):
        ctk.CTkLabel(panel, text=texto).pack(anchor="w", padx=20, pady=(12, 2))

        fila = ctk.CTkFrame(panel, fg_color="transparent")
        fila.pack(fill="x", padx=20)

        ctk.CTkEntry(fila, textvariable=variable, width=340).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            fila,
            text="Buscar",
            width=80,
            command=comando
        ).pack(side="left")

    def crear_entry(self, panel, texto, variable, width=420):
        ctk.CTkLabel(panel, text=texto).pack(anchor="w", padx=20, pady=(12, 2))
        ctk.CTkEntry(panel, textvariable=variable, width=width).pack(anchor="w", padx=20)

    def crear_slider(self, panel, texto, variable, minimo, maximo):
        frame = ctk.CTkFrame(panel, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=(14, 0))

        label = ctk.CTkLabel(frame, text=f"{texto}: {variable.get()} px")
        label.pack(anchor="w")

        def actualizar(valor):
            variable.set(int(float(valor)))
            label.configure(text=f"{texto}: {variable.get()} px")
            self.actualizar_preview()

        ctk.CTkSlider(
            frame,
            from_=minimo,
            to=maximo,
            variable=variable,
            command=actualizar,
            width=420
        ).pack(anchor="w", pady=4)

    def elegir_entrada(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.entrada_var.set(carpeta)
            self.actualizar_preview()

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
            self.actualizar_preview()

    def obtener_config_actual(self):
        return {
            "entrada": self.entrada_var.get(),
            "salida": self.salida_var.get(),
            "logo": self.logo_var.get(),
            "footer": self.footer_var.get(),
            "version": self.version_var.get(),
            "mostrar_logo": self.mostrar_logo_var.get(),
            "mostrar_fecha": self.mostrar_fecha_var.get(),
            "numerar_paginas": self.numerar_paginas_var.get(),
            "agregar_portada": self.agregar_portada_var.get(),
            "header_offset": self.header_offset_var.get(),
            "footer_offset": self.footer_offset_var.get(),
            "margen_x": self.margen_x_var.get(),
            "logo_width": self.logo_width_var.get(),
            "logo_height": self.logo_height_var.get(),
            "titulo_portada": self.titulo_portada_var.get(),
            "subtitulo_portada": self.subtitulo_portada_var.get(),
            "area_portada": self.area_portada_var.get()
        }

    def actualizar_preview(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        primer_pdf = obtener_primer_pdf(config["entrada"])

        if not primer_pdf:
            self.preview_label.configure(text="No hay PDFs en la carpeta de entrada.")
            self.preview_info.configure(text="")
            return

        imagen = generar_preview_pdf(primer_pdf, config, ancho_preview=430)

        if imagen is None:
            self.preview_label.configure(text="No se pudo generar la vista previa.")
            self.preview_info.configure(text="")
            return

        self.preview_image_tk = ImageTk.PhotoImage(imagen)
        self.preview_label.configure(image=self.preview_image_tk, text="")

        nombre_pdf = os.path.basename(primer_pdf)
        self.preview_info.configure(text=f"Vista previa: {nombre_pdf}")

    def procesar(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        if not os.path.exists(config["entrada"]):
            messagebox.showerror("Error", "La carpeta de entrada no existe.")
            return

        os.makedirs(config["salida"], exist_ok=True)

        def estado(texto):
            self.estado_label.configure(text=texto)
            self.update_idletasks()

        def progreso(valor):
            self.progress.set(valor)
            self.update_idletasks()

        try:
            procesados, total = procesar_carpeta(
                config,
                callback_estado=estado,
                callback_progreso=progreso
            )

            if total == 0:
                messagebox.showwarning("Sin PDFs", "No se encontraron PDFs en la carpeta de entrada.")
                return

            self.estado_label.configure(text=f"Proceso finalizado: {procesados}/{total} PDFs procesados.")
            self.progress.set(1)

            messagebox.showinfo(
                "Listo",
                f"Se procesaron {procesados} PDF(s).\n\nRevisá la carpeta de salida."
            )

        except Exception as error:
            messagebox.showerror("Error", f"Ocurrió un error:\n\n{error}")


def iniciar_app():
    app = PDFNotionApp()
    app.mainloop()