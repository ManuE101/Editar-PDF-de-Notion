from logging import config
import os
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from config import cargar_config, guardar_config
# from pdf_processor import procesar_carpeta
# from preview import obtener_primer_pdf, generar_preview_pdf
try:
    from preview import obtener_primer_pdf, generar_preview_pdf
    PREVIEW_DISPONIBLE = True
except Exception:
    PREVIEW_DISPONIBLE = False

from zip_pipeline import convertir_zip_notion_a_pdf, convertir_carpeta_zips_notion_a_pdf

from pdf_processor import procesar_carpeta, procesar_pdf
from utils import formatear_titulo, crear_nombre_salida


class PDFNotionApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        ctk.CTk._windows_set_titlebar_color = lambda *args, **kwargs: None

        self.title("PDF Notion")
        self.geometry("1100x760")
        self.resizable(False, False)

        self.config_data = cargar_config()

        self.entrada_var = ctk.StringVar(value=self.config_data["entrada"])
        self.salida_var = ctk.StringVar(value=self.config_data["salida"])
        self.logo_var = ctk.StringVar(value=self.config_data["logo"])
        self.zip_var = ctk.StringVar(value="")

        self.zip_folder_var = ctk.StringVar(value="")
        self.pdf_unico_var = ctk.StringVar(value="")

        self.header_var = ctk.StringVar(value=self.config_data["header"])
        self.footer_var = ctk.StringVar(value=self.config_data["footer"])
        self.version_var = ctk.StringVar(value=self.config_data["version"])

        self.formato_numeracion_var = ctk.StringVar(
            value=self.config_data.get("formato_numeracion", "Página {pagina}")
        )

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

        self.mostrar_header_portada_var = ctk.BooleanVar(value=self.config_data["mostrar_header_portada"])
        self.mostrar_footer_portada_var = ctk.BooleanVar(value=self.config_data["mostrar_footer_portada"])
        self.header_portada_var = ctk.StringVar(value=self.config_data["header_portada"])
        self.footer_portada_var = ctk.StringVar(value=self.config_data["footer_portada"])


        self.preview_image_tk = None
        self.ultimo_pdf_generado = None

        self.crear_interfaz()
        self.actualizar_preview()

        self.formato_numeracion_var = ctk.StringVar(
            value=self.config_data.get("formato_numeracion", "Página {pagina}")
        )

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

        drop_frame = ctk.CTkFrame(panel, corner_radius=16, border_width=2)
        drop_frame.pack(fill="x", padx=20, pady=(5, 20))

        ctk.CTkLabel(
            drop_frame,
            text="Arrastrá aquí un PDF, ZIP o carpeta",
            font=("Arial", 15, "bold")
        ).pack(pady=(18, 5))

        ctk.CTkLabel(
            drop_frame,
            text="PDF → procesa archivo | ZIP → convierte Notion | Carpeta → detecta archivos",
            font=("Arial", 11)
        ).pack(pady=(0, 18))

        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", self.procesar_drop)

        # self.crear_selector(panel, "Carpeta de entrada", self.entrada_var, self.elegir_entrada)
        # self.crear_selector(panel, "Carpeta de salida", self.salida_var, self.elegir_salida)
        # self.crear_selector(panel, "Logo", self.logo_var, self.elegir_logo)
        self.crear_selector(panel, "Carpeta de salida", self.salida_var, self.elegir_salida)
        self.crear_selector(panel, "Logo", self.logo_var, self.elegir_logo)

        ctk.CTkLabel(
            panel,
            text="Procesar PDFs existentes",
            font=("Arial", 17, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.crear_selector(panel, "PDF puntual", self.pdf_unico_var, self.elegir_pdf_unico)
        self.crear_selector(panel, "Carpeta de PDFs", self.entrada_var, self.elegir_entrada)

        ctk.CTkButton(
            panel,
            text="Procesar PDF puntual",
            font=("Arial", 14, "bold"),
            height=42,
            command=self.procesar_pdf_unico
        ).pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkButton(
            panel,
            text="Procesar carpeta de PDFs",
            font=("Arial", 14, "bold"),
            height=42,
            command=self.procesar
        ).pack(fill="x", padx=20, pady=(0, 15))


        ctk.CTkLabel(
            panel,
            text="Convertir exportaciones ZIP de Notion",
            font=("Arial", 17, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.crear_selector(panel, "ZIP puntual", self.zip_var, self.elegir_zip)
        self.crear_selector(panel, "Carpeta de ZIPs", self.zip_folder_var, self.elegir_carpeta_zips)

        ctk.CTkButton(
            panel,
            text="Convertir ZIP puntual",
            font=("Arial", 14, "bold"),
            height=42,
            command=self.convertir_zip
        ).pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkButton(
            panel,
            text="Convertir carpeta de ZIPs",
            font=("Arial", 14, "bold"),
            height=42,
            command=self.convertir_carpeta_zips
        ).pack(fill="x", padx=20, pady=(0, 20))

        #self.crear_selector(panel, "ZIP de Notion", self.zip_var, self.elegir_zip)

        self.crear_entry(panel, "Header", self.header_var)
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

        ctk.CTkLabel(panel, text="Formato de numeración").pack(anchor="w", padx=20, pady=(12, 2))

        self.formato_numeracion_menu = ctk.CTkOptionMenu(
            panel,
            values=[
                "Página 1",
                "Página 1 de 10",
                "1 / 10",
                "Pág. 1",
                "Sin numeración"
            ],
            variable=self.formato_numeracion_var
        )

        self.formato_numeracion_menu.pack(anchor="w", padx=20, pady=(0, 10))

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

        ctk.CTkCheckBox(
            panel,
            text="Mostrar header en portada",
            variable=self.mostrar_header_portada_var
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.crear_entry(panel, "Header de portada", self.header_portada_var)

        ctk.CTkCheckBox(
            panel,
            text="Mostrar footer en portada",
            variable=self.mostrar_footer_portada_var
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.crear_entry(panel, "Footer de portada", self.footer_portada_var)

        self.estado_label = ctk.CTkLabel(
            panel,
            text="Estado: listo para procesar.",
            font=("Arial", 12)
        )
        self.estado_label.pack(anchor="w", padx=20, pady=(20, 5))

        self.progress = ctk.CTkProgressBar(panel, width=420)
        self.progress.pack(anchor="w", padx=20, pady=10)
        self.progress.set(0)

        botones_archivos = ctk.CTkFrame(panel, fg_color="transparent")
        botones_archivos.pack(fill="x", padx=20, pady=(5, 10))

        ctk.CTkButton(
            botones_archivos,
            text="Abrir último PDF",
            command=self.abrir_ultimo_pdf,
            width=190
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            botones_archivos,
            text="Abrir carpeta de salida",
            command=self.abrir_carpeta_salida,
            width=190
        ).pack(side="left")

        # ctk.CTkButton(
        #     panel,
        #     text="Procesar PDFs",
        #     font=("Arial", 16, "bold"),
        #     height=48,
        #     command=self.procesar
        # ).pack(fill="x", padx=20, pady=(10, 25))
        # ctk.CTkButton(
        #     panel,
        #     text="Convertir ZIP de Notion",
        #     font=("Arial", 16, "bold"),
        #     height=48,
        #     command=self.convertir_zip
        # ).pack(fill="x", padx=20, pady=(0, 25))

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
        drop_frame = ctk.CTkFrame(panel, corner_radius=16)
        drop_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            drop_frame,
            text="Arrastrá aquí un PDF, ZIP o carpeta",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            drop_frame,
            text="PDF → procesa archivo\nZIP → convierte exportación Notion\nCarpeta → detecta PDFs o ZIPs",
            font=("Arial", 12)
        ).pack(pady=(0, 20))

        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", self.procesar_drop)

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

        formato_visible = self.formato_numeracion_var.get()

        mapa_numeracion = {
            "Página 1": "Página {pagina}",
            "Página 1 de 10": "Página {pagina} de {total}",
            "1 / 10": "{pagina} / {total}",
            "Pág. 1": "Pág. {pagina}",
            "Sin numeración": "Sin numeración"
        }
        return {
            "entrada": self.entrada_var.get(),
            "salida": self.salida_var.get(),
            "logo": self.logo_var.get(),
            "header": self.header_var.get(),
            "footer": self.footer_var.get(),
            "version": self.version_var.get(),
            "mostrar_logo": self.mostrar_logo_var.get(),
            "mostrar_fecha": self.mostrar_fecha_var.get(),
            "numerar_paginas": self.numerar_paginas_var.get(),
            #"formato_numeracion": self.formato_numeracion_var.get(),
            
            "formato_numeracion": mapa_numeracion.get(
                formato_visible,
                "Página {pagina}"
            ),
            "agregar_portada": self.agregar_portada_var.get(),
            "header_offset": self.header_offset_var.get(),
            "footer_offset": self.footer_offset_var.get(),
            "margen_x": self.margen_x_var.get(),
            "logo_width": self.logo_width_var.get(),
            "logo_height": self.logo_height_var.get(),
            "titulo_portada": self.titulo_portada_var.get(),
            "subtitulo_portada": self.subtitulo_portada_var.get(),
            "area_portada": self.area_portada_var.get(),
            "mostrar_header_portada": self.mostrar_header_portada_var.get(),
            "mostrar_footer_portada": self.mostrar_footer_portada_var.get(),
            "header_portada": self.header_portada_var.get(),
            "footer_portada": self.footer_portada_var.get(),
        }

    def actualizar_preview(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        try:
            from preview import obtener_primer_pdf, generar_preview_pdf
        except Exception:
            self.preview_label.configure(
                text="Vista previa de PDF no disponible.\n\n"
                    "El sistema bloqueó PyMuPDF.\n"
                    "Igual podés procesar PDFs y convertir ZIPs."
            )
            self.preview_info.configure(text="")
            return

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

        # self.preview_image_tk = ImageTk.PhotoImage(imagen)
        # self.preview_label.configure(image=self.preview_image_tk, text="")
        self.preview_image_tk = ctk.CTkImage(
            light_image=imagen,
            dark_image=imagen,
            size=imagen.size
        )

        self.preview_label.configure(image=self.preview_image_tk, text="")

        nombre_pdf = os.path.basename(primer_pdf)
        self.preview_info.configure(text=f"Vista previa PDF: {nombre_pdf}")

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
    
    def elegir_zip(self):
        archivo = filedialog.askopenfilename(
            filetypes=[
                ("ZIP de Notion", "*.zip"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.zip_var.set(archivo)

    def convertir_zip(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        ruta_zip = self.zip_var.get()

        if not ruta_zip or not os.path.exists(ruta_zip):
            messagebox.showerror("Error", "Seleccioná un archivo ZIP válido.")
            return

        os.makedirs(config["salida"], exist_ok=True)

        try:
            self.estado_label.configure(text="Convirtiendo ZIP de Notion...")
            self.progress.set(0.3)
            self.update_idletasks()

            ruta_generada = convertir_zip_notion_a_pdf(
                ruta_zip=ruta_zip,
                carpeta_salida=config["salida"],
                config=config
            )

            self.ultimo_pdf_generado = ruta_generada

            self.progress.set(1)

            os.startfile(config["salida"])

            self.estado_label.configure(text="ZIP convertido correctamente.")

            messagebox.showinfo(
                "Listo",
                f"PDF generado correctamente:\n\n{ruta_generada}"
            )

            os.startfile(ruta_generada)

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo convertir el ZIP:\n\n{error}")

    def abrir_ultimo_pdf(self):
        if not self.ultimo_pdf_generado or not os.path.exists(self.ultimo_pdf_generado):
            messagebox.showwarning("Sin PDF", "Todavía no hay un PDF generado para abrir.")
            return

        os.startfile(self.ultimo_pdf_generado)

    def abrir_carpeta_salida(self):
        config = self.obtener_config_actual()
        carpeta_salida = config.get("salida", "")

        if not carpeta_salida:
            messagebox.showwarning("Sin carpeta", "No hay carpeta de salida configurada.")
            return

        os.makedirs(carpeta_salida, exist_ok=True)
        os.startfile(carpeta_salida)
    
    def elegir_carpeta_zips(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.zip_folder_var.set(carpeta)


    def elegir_pdf_unico(self):
        archivo = filedialog.askopenfilename(
            filetypes=[
                ("PDF", "*.pdf"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.pdf_unico_var.set(archivo)
    
    def procesar_pdf_unico(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        ruta_pdf = self.pdf_unico_var.get()

        if not ruta_pdf or not os.path.exists(ruta_pdf):
            messagebox.showerror("Error", "Seleccioná un PDF válido.")
            return

        os.makedirs(config["salida"], exist_ok=True)

        try:
            archivo = os.path.basename(ruta_pdf)
            titulo = formatear_titulo(archivo)
            nombre_salida = crear_nombre_salida(archivo)
            ruta_salida = os.path.join(config["salida"], nombre_salida)

            self.estado_label.configure(text=f"Procesando PDF: {archivo}")
            self.progress.set(0.5)
            self.update_idletasks()

            procesar_pdf(ruta_pdf, ruta_salida, titulo, config)

            self.ultimo_pdf_generado = ruta_salida
            self.progress.set(1)
            self.estado_label.configure(text="PDF procesado correctamente.")

            messagebox.showinfo("Listo", f"PDF generado:\n\n{ruta_salida}")
            os.startfile(ruta_salida)

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo procesar el PDF:\n\n{error}")
    
    def convertir_carpeta_zips(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        carpeta_zips = self.zip_folder_var.get()

        if not carpeta_zips or not os.path.exists(carpeta_zips):
            messagebox.showerror("Error", "Seleccioná una carpeta de ZIPs válida.")
            return

        os.makedirs(config["salida"], exist_ok=True)

        def estado(texto):
            self.estado_label.configure(text=texto)
            self.update_idletasks()

        def progreso(valor):
            self.progress.set(valor)
            self.update_idletasks()

        try:
            convertidos, total, errores = convertir_carpeta_zips_notion_a_pdf(
                carpeta_zips=carpeta_zips,
                carpeta_salida=config["salida"],
                config=config,
                callback_estado=estado,
                callback_progreso=progreso
            )

            self.estado_label.configure(text=f"ZIPs convertidos: {convertidos}/{total}.")
            self.progress.set(1)

            mensaje = f"Se convirtieron {convertidos} de {total} ZIP(s)."

            if errores:
                mensaje += "\n\nAlgunos archivos fallaron. Se generó la lista en consola."
                print("Errores:")
                for error in errores:
                    print(error)

            messagebox.showinfo("Listo", mensaje)
            os.startfile(config["salida"])

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo convertir la carpeta:\n\n{error}")
    
    def procesar_drop(self, event):
        ruta = event.data.strip()

        # Limpieza de rutas con llaves por espacios
        if ruta.startswith("{") and ruta.endswith("}"):
            ruta = ruta[1:-1]

        if not os.path.exists(ruta):
            messagebox.showerror("Error", f"No se encontró la ruta:\n\n{ruta}")
            return

        if os.path.isfile(ruta):
            extension = os.path.splitext(ruta)[1].lower()

            if extension == ".pdf":
                self.pdf_unico_var.set(ruta)
                self.procesar_pdf_unico()
                return

            if extension == ".zip":
                self.zip_var.set(ruta)
                self.convertir_zip()
                return

            messagebox.showwarning("Archivo no compatible", "Solo se aceptan archivos PDF o ZIP.")
            return

        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)

            tiene_pdfs = any(a.lower().endswith(".pdf") for a in archivos)
            tiene_zips = any(a.lower().endswith(".zip") for a in archivos)

            if tiene_pdfs and not tiene_zips:
                self.entrada_var.set(ruta)
                self.procesar()
                return

            if tiene_zips and not tiene_pdfs:
                self.zip_folder_var.set(ruta)
                self.convertir_carpeta_zips()
                return

            if tiene_pdfs and tiene_zips:
                respuesta = messagebox.askyesno(
                    "Carpeta mixta",
                    "La carpeta contiene PDFs y ZIPs.\n\n"
                    "Sí = procesar PDFs\n"
                    "No = convertir ZIPs"
                )

                if respuesta:
                    self.entrada_var.set(ruta)
                    self.procesar()
                else:
                    self.zip_folder_var.set(ruta)
                    self.convertir_carpeta_zips()

                return

            messagebox.showwarning(
                "Sin archivos compatibles",
                "La carpeta no contiene PDFs ni ZIPs."
            )

def iniciar_app():
    app = PDFNotionApp()
    app.mainloop()