import os
import shutil
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
        self.geometry("1180x780")
        self.resizable(False, False)

        self.config_data = cargar_config()

        self.entrada_var = ctk.StringVar(value=self.config_data["entrada"])
        self.salida_var = ctk.StringVar(value=self.config_data["salida"])
        # self.logo_var = ctk.StringVar(value=self.config_data["logo"])
        # self.logo_izquierdo_var = ctk.StringVar(value="")
        # self.logo_central_var = ctk.StringVar(value="")
        # self.logo_derecho_var = ctk.StringVar(value="")
        # self.logo_var = ctk.StringVar(value=self.config_data.get("logo", ""))

        self.logo_izquierdo_var = ctk.StringVar(
            value=self.config_data.get("logo_izquierdo", "")
        )
        self.logo_central_var = ctk.StringVar(
            value=self.config_data.get("logo_central", "")
        )
        self.logo_derecho_var = ctk.StringVar(
            value=self.config_data.get("logo_derecho", "")
        )

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
        self.agregar_indice_var = ctk.BooleanVar(value=self.config_data.get("agregar_indice", False))

        self.mostrar_header_portada_var = ctk.BooleanVar(value=self.config_data["mostrar_header_portada"])
        self.mostrar_footer_portada_var = ctk.BooleanVar(value=self.config_data["mostrar_footer_portada"])
        self.header_portada_var = ctk.StringVar(value=self.config_data["header_portada"])
        self.footer_portada_var = ctk.StringVar(value=self.config_data["footer_portada"])


        self.preview_image_tk = None
        self.ultimo_pdf_generado = None
        self.opciones_avanzadas_frame = None
        self.zip_preview_pdf = None
        self.zip_preview_signature = None

        self.crear_interfaz()
        self.actualizar_preview()

    def crear_interfaz(self):
        self.configure(bg="#101318")

        header = ctk.CTkFrame(self, height=78, corner_radius=0, fg_color="#171B22")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="PDF Notion",
            font=("Arial", 28, "bold"),
            text_color="#F4F7FB"
        ).pack(side="left", padx=(30, 14), pady=20)

        ctk.CTkLabel(
            header,
            text="Procesador de PDFs exportados desde Notion",
            font=("Arial", 13),
            text_color="#AEB7C4"
        ).pack(side="left", padx=0, pady=25)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=22)

        panel_config = ctk.CTkScrollableFrame(
            body,
            width=560,
            height=640,
            corner_radius=16,
            fg_color="#171B22",
            scrollbar_button_color="#3A4351",
            scrollbar_button_hover_color="#4C596B"
        )
        panel_config.pack(side="left", fill="y", padx=(0, 22))

        panel_preview = ctk.CTkFrame(
            body,
            width=550,
            height=640,
            corner_radius=16,
            fg_color="#171B22"
        )
        panel_preview.pack(side="right", fill="both", expand=True)

        self.crear_panel_config(panel_config)
        self.crear_panel_preview(panel_preview)

    def crear_card(self, panel, titulo, subtitulo=None):
        card = ctk.CTkFrame(panel, corner_radius=14, fg_color="#202631")
        card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            card,
            text=titulo,
            font=("Arial", 15, "bold"),
            text_color="#F4F7FB"
        ).pack(anchor="w", padx=18, pady=(16, 2 if subtitulo else 10))

        if subtitulo:
            ctk.CTkLabel(
                card,
                text=subtitulo,
                font=("Arial", 11),
                text_color="#9AA6B5"
            ).pack(anchor="w", padx=18, pady=(0, 10))

        return card

    def crear_fila_botones(self, panel):
        fila = ctk.CTkFrame(panel, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(10, 2))
        fila.grid_columnconfigure((0, 1), weight=1, uniform="acciones")
        return fila

    def crear_titulo_seccion(self, panel, texto):
        ctk.CTkLabel(
            panel,
            text=texto,
            font=("Arial", 17, "bold")
        ).pack(anchor="w", padx=20, pady=(24, 8))


    def toggle_opciones_avanzadas(self):
        if self.opciones_avanzadas_frame.winfo_viewable():
            self.opciones_avanzadas_frame.pack_forget()
            self.boton_avanzadas.configure(text="▶ Opciones avanzadas")
        else:
            self.opciones_avanzadas_frame.pack(fill="x", padx=20, pady=(5, 15))
            self.boton_avanzadas.configure(text="▼ Opciones avanzadas")

    def crear_panel_config(self, panel):
        ctk.CTkLabel(
            panel,
            text="Configuración",
            font=("Arial", 20, "bold"),
            text_color="#F4F7FB"
        ).pack(anchor="w", padx=18, pady=(18, 4))

        ctk.CTkLabel(
            panel,
            text="Elegí el origen, ajustá el diseño y procesá el documento.",
            font=("Arial", 12),
            text_color="#9AA6B5"
        ).pack(anchor="w", padx=18, pady=(0, 16))

        card_archivos = self.crear_card(
            panel,
            "Archivos",
            "Arrastrá archivos o elegí manualmente las rutas de trabajo."
        )

        drop_frame = ctk.CTkFrame(
            card_archivos,
            corner_radius=12,
            border_width=1,
            border_color="#3F8CFF",
            fg_color="#151A21"
        )
        drop_frame.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(
            drop_frame,
            text="Arrastrá aquí un PDF, ZIP o carpeta",
            font=("Arial", 14, "bold"),
            text_color="#F4F7FB"
        ).pack(pady=(14, 4))

        ctk.CTkLabel(
            drop_frame,
            text="PDF: procesa archivo | ZIP: convierte Notion | Carpeta: detecta contenido",
            font=("Arial", 11),
            text_color="#9AA6B5"
        ).pack(pady=(0, 14))

        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", self.procesar_drop)

        self.crear_selector(card_archivos, "Carpeta de salida", self.salida_var, self.elegir_salida)

        card_logos = self.crear_card(
            panel,
            "Logos del encabezado",
            "Podés usar uno, dos o tres logos. Se muestran según estén cargados."
        )

        self.logo_izquierdo_entry, self.logo_izquierdo_label = self.crear_selector_logo(
            card_logos, "Logo izquierdo", self.logo_izquierdo_var, self.elegir_logo_izquierdo
        )

        self.logo_central_entry, self.logo_central_label = self.crear_selector_logo(
            card_logos, "Logo central", self.logo_central_var, self.elegir_logo_central
        )

        self.logo_derecho_entry, self.logo_derecho_label = self.crear_selector_logo(
            card_logos, "Logo derecho", self.logo_derecho_var, self.elegir_logo_derecho
        )

        card_pdf = self.crear_card(
            panel,
            "PDFs existentes",
            "Procesá un PDF puntual o una carpeta completa."
        )

        self.pdf_unico_entry, self.pdf_unico_label = self.crear_selector(
            card_pdf,
            "PDF puntual",
            self.pdf_unico_var,
            self.elegir_pdf_unico,
            self.quitar_pdf_unico
        )
        self.crear_selector(card_pdf, "Carpeta de PDFs", self.entrada_var, self.elegir_entrada)

        fila_pdf = self.crear_fila_botones(card_pdf)
        ctk.CTkButton(
            fila_pdf,
            text="Procesar PDF",
            font=("Arial", 13, "bold"),
            height=40,
            command=self.procesar_pdf_unico
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            fila_pdf,
            text="Procesar carpeta",
            font=("Arial", 13, "bold"),
            height=40,
            fg_color="#2D6CDF",
            hover_color="#2458B7",
            command=self.procesar
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        card_zip = self.crear_card(
            panel,
            "ZIP de Notion",
            "Convertí exportaciones de Notion y agregá índice automático si corresponde."
        )

        self.zip_entry, self.zip_label = self.crear_selector(card_zip, "ZIP puntual", self.zip_var, self.elegir_zip)
        self.crear_selector(card_zip, "Carpeta de ZIPs", self.zip_folder_var, self.elegir_carpeta_zips)

        ctk.CTkCheckBox(
            card_zip,
            text="Agregar índice automático",
            variable=self.agregar_indice_var,
            command=self.actualizar_preview
        ).pack(anchor="w", padx=20, pady=(12, 0))

        fila_zip = self.crear_fila_botones(card_zip)
        ctk.CTkButton(
            fila_zip,
            text="Convertir ZIP",
            font=("Arial", 13, "bold"),
            height=40,
            command=self.convertir_zip
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            fila_zip,
            text="Convertir carpeta",
            font=("Arial", 13, "bold"),
            height=40,
            fg_color="#2D6CDF",
            hover_color="#2458B7",
            command=self.convertir_carpeta_zips
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        card_contenido = self.crear_card(
            panel,
            "Header y footer",
            "Ajustá texto, márgenes, numeración y tamaño de logos."
        )

        self.crear_entry(card_contenido, "Header", self.header_var)
        self.crear_entry(card_contenido, "Footer", self.footer_var)
        self.crear_entry(card_contenido, "Versión", self.version_var, width=180)

        self.crear_slider(card_contenido, "Header desde arriba", self.header_offset_var, 10, 150)
        self.crear_slider(card_contenido, "Footer desde abajo", self.footer_offset_var, 10, 150)
        self.crear_slider(card_contenido, "Margen izquierdo/derecho", self.margen_x_var, 10, 120)
        self.crear_slider(card_contenido, "Ancho del logo", self.logo_width_var, 30, 200)
        self.crear_slider(card_contenido, "Alto del logo", self.logo_height_var, 15, 100)

        opciones = ctk.CTkFrame(card_contenido, fg_color="transparent")
        opciones.pack(fill="x", padx=20, pady=(12, 4))
        opciones.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkCheckBox(
            opciones,
            text="Mostrar logos",
            variable=self.mostrar_logo_var,
            command=self.actualizar_preview
        ).grid(row=0, column=0, sticky="w", pady=5)

        ctk.CTkCheckBox(
            opciones,
            text="Mostrar fecha",
            variable=self.mostrar_fecha_var,
            command=self.actualizar_preview
        ).grid(row=0, column=1, sticky="w", pady=5)

        ctk.CTkCheckBox(
            opciones,
            text="Numerar páginas",
            variable=self.numerar_paginas_var,
            command=self.actualizar_preview
        ).grid(row=1, column=0, sticky="w", pady=5)

        ctk.CTkCheckBox(
            opciones,
            text="Agregar portada",
            variable=self.agregar_portada_var,
            command=self.actualizar_preview
        ).grid(row=1, column=1, sticky="w", pady=5)

        ctk.CTkLabel(card_contenido, text="Formato de numeración").pack(anchor="w", padx=20, pady=(12, 2))

        self.formato_numeracion_menu = ctk.CTkOptionMenu(
            card_contenido,
            values=[
                "Página 1",
                "Página 1 de 10",
                "1 / 10",
                "Pág. 1",
                "Sin numeración"
            ],
            variable=self.formato_numeracion_var,
            width=190
        )
        self.formato_numeracion_menu.pack(anchor="w", padx=20, pady=(0, 14))

        card_portada = self.crear_card(
            panel,
            "Portada",
            "Contenido opcional para la primera página."
        )

        self.crear_entry(card_portada, "Título de portada", self.titulo_portada_var)
        self.crear_entry(card_portada, "Subtítulo de portada", self.subtitulo_portada_var)
        self.crear_entry(card_portada, "Área / Empresa", self.area_portada_var)

        ctk.CTkCheckBox(
            card_portada,
            text="Mostrar header en portada",
            variable=self.mostrar_header_portada_var
        ).pack(anchor="w", padx=20, pady=(12, 5))

        self.crear_entry(card_portada, "Header de portada", self.header_portada_var)

        ctk.CTkCheckBox(
            card_portada,
            text="Mostrar footer en portada",
            variable=self.mostrar_footer_portada_var
        ).pack(anchor="w", padx=20, pady=(12, 5))

        self.crear_entry(card_portada, "Footer de portada", self.footer_portada_var)

        card_estado = self.crear_card(panel, "Estado")

        self.estado_label = ctk.CTkLabel(
            card_estado,
            text="Estado: listo para procesar.",
            font=("Arial", 12),
            text_color="#AEB7C4"
        )
        self.estado_label.pack(anchor="w", padx=20, pady=(2, 6))

        self.progress = ctk.CTkProgressBar(card_estado, width=460)
        self.progress.pack(anchor="w", padx=20, pady=(0, 12))
        self.progress.set(0)

        botones_archivos = self.crear_fila_botones(card_estado)

        ctk.CTkButton(
            botones_archivos,
            text="Abrir último PDF",
            command=self.abrir_ultimo_pdf,
            height=38,
            fg_color="#3B4350",
            hover_color="#4B5666"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            botones_archivos,
            text="Abrir salida",
            command=self.abrir_carpeta_salida,
            height=38,
            fg_color="#3B4350",
            hover_color="#4B5666"
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        return

    def crear_panel_preview(self, panel):
        ctk.CTkLabel(
            panel,
            text="Vista previa",
            font=("Arial", 20, "bold"),
            text_color="#F4F7FB"
        ).pack(anchor="w", padx=22, pady=(20, 4))

        ctk.CTkLabel(
            panel,
            text="Visualizá la página completa mientras ajustás header y footer.",
            font=("Arial", 12),
            text_color="#9AA6B5"
        ).pack(anchor="w", padx=22, pady=(0, 14))

        preview_shell = ctk.CTkFrame(panel, corner_radius=14, fg_color="#101318")
        preview_shell.pack(fill="both", expand=True, padx=22, pady=(0, 12))

        self.preview_label = ctk.CTkLabel(
            preview_shell,
            text="",
            fg_color="transparent"
        )
        self.preview_label.pack(expand=True, padx=18, pady=18)

        controles = ctk.CTkFrame(panel, fg_color="transparent")
        controles.pack(fill="x", padx=22, pady=(0, 8))
        controles.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            controles,
            text="Actualizar vista previa",
            command=self.actualizar_preview,
            height=38,
            width=210
        ).grid(row=0, column=0, sticky="w")

        self.preview_info = ctk.CTkLabel(
            controles,
            text="",
            font=("Arial", 12),
            text_color="#AEB7C4"
        )
        self.preview_info.grid(row=0, column=1, sticky="e", padx=(12, 0))

        drop_frame = ctk.CTkFrame(
            panel,
            corner_radius=12,
            border_width=1,
            border_color="#313A47",
            fg_color="#202631"
        )
        drop_frame.pack(fill="x", padx=22, pady=(0, 20))

        ctk.CTkLabel(
            drop_frame,
            text="También podés arrastrar un PDF, ZIP o carpeta acá",
            font=("Arial", 13, "bold"),
            text_color="#F4F7FB"
        ).pack(pady=(14, 4))

        ctk.CTkLabel(
            drop_frame,
            text="El origen se detecta automáticamente y actualiza la vista previa cuando aplica.",
            font=("Arial", 11),
            text_color="#9AA6B5"
        ).pack(pady=(0, 14))

        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", self.procesar_drop)

        return

    def crear_selector(self, panel, texto, variable, comando, comando_quitar=None):
        ctk.CTkLabel(panel, text=texto).pack(anchor="w", padx=20, pady=(12, 2))

        fila = ctk.CTkFrame(panel, fg_color="transparent")
        fila.pack(fill="x", padx=20)

        entry_width = 250 if comando_quitar else 340
        button_width = 74 if comando_quitar else 80

        entry = ctk.CTkEntry(fila, textvariable=variable, width=entry_width)
        entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            fila,
            text="Buscar",
            width=button_width,
            command=comando
        ).pack(side="left")

        nombre_archivo = os.path.basename(variable.get()) if variable.get() else "Sin archivo seleccionado"

        label_archivo = ctk.CTkLabel(
            panel,
            text=nombre_archivo,
            font=("Arial", 11),
            text_color="#AAB0B6"
        )
        label_archivo.pack(anchor="w", padx=22, pady=(3, 0))

        if comando_quitar:
            ctk.CTkButton(
                fila,
                text="Quitar",
                width=74,
                fg_color="#3B3F46",
                hover_color="#4B515A",
                command=lambda: comando_quitar(label_archivo)
            ).pack(side="left", padx=(8, 0))

        return entry, label_archivo

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

    def elegir_logo_izquierdo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo izquierdo",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.logo_izquierdo_var.set(path)
            self.logo_izquierdo_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_central(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo central",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.logo_central_var.set(path)
            self.logo_central_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_derecho(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo derecho",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.logo_derecho_var.set(path)
            self.logo_derecho_label.configure(text=os.path.basename(path))
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
            # "logo": self.logo_var.get(),
            "logo_izquierdo": self.logo_izquierdo_var.get(),
            "logo_central": self.logo_central_var.get(),
            "logo_derecho": self.logo_derecho_var.get(),
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
            "agregar_indice": self.agregar_indice_var.get(),
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

        pdf_unico = self.pdf_unico_var.get()
        ruta_zip = self.zip_var.get()

        if pdf_unico and os.path.exists(pdf_unico):
            primer_pdf = pdf_unico
        elif ruta_zip and os.path.exists(ruta_zip):
            primer_pdf = self.obtener_preview_zip(ruta_zip, config)
        else:
            primer_pdf = obtener_primer_pdf(config["entrada"])

        if not primer_pdf:
            self.preview_label.configure(text="No hay PDFs para previsualizar.")
            self.preview_info.configure(text="")
            return

        imagen = generar_preview_pdf(
            primer_pdf,
            config,
            ancho_preview=430,
            alto_preview=500
        )

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

    def obtener_preview_zip(self, ruta_zip, config):
        try:
            zip_stat = os.stat(ruta_zip)
            signature = (
                ruta_zip,
                zip_stat.st_mtime,
                zip_stat.st_size,
                bool(config.get("agregar_portada", True)),
                bool(config.get("agregar_indice", False)),
            )

            if (
                self.zip_preview_pdf
                and self.zip_preview_signature == signature
                and os.path.exists(self.zip_preview_pdf)
            ):
                return self.zip_preview_pdf

            from notion_parser import parsear_html_notion
            from notion_zip_reader import leer_html_desde_zip
            from smart_pdf_exporter_v2 import exportar_documento_pdf_v2

            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".preview_cache")
            os.makedirs(cache_dir, exist_ok=True)
            ruta_preview = os.path.join(cache_dir, "zip_preview.pdf")

            resultado = leer_html_desde_zip(ruta_zip)
            carpeta_temporal = resultado.get("carpeta_temporal")

            try:
                documento = parsear_html_notion(
                    resultado["contenido_html"],
                    resultado["html_principal"]
                )

                config_preview = config.copy()
                config_preview.update({
                    "mostrar_logo": False,
                    "mostrar_fecha": False,
                    "numerar_paginas": False,
                    "header": "",
                    "footer": "",
                    "version": "",
                    "_omitir_header_footer": True,
                    "_omitir_logos_overlay": True,
                })

                exportar_documento_pdf_v2(
                    documento=documento,
                    ruta_salida=ruta_preview,
                    config=config_preview
                )
            finally:
                if carpeta_temporal and os.path.exists(carpeta_temporal):
                    shutil.rmtree(carpeta_temporal, ignore_errors=True)

            self.zip_preview_pdf = ruta_preview
            self.zip_preview_signature = signature

            return ruta_preview

        except Exception as error:
            self.preview_info.configure(text=f"No se pudo generar vista previa ZIP: {error}")
            return None

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
            self.pdf_unico_var.set("")
            if hasattr(self, "pdf_unico_label"):
                self.pdf_unico_label.configure(text="Sin archivo seleccionado")
            if hasattr(self, "zip_label"):
                self.zip_label.configure(text=os.path.basename(archivo))
            self.actualizar_preview()

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

            self.estado_label.configure(text="ZIP convertido correctamente.")

            abrir_pdf = messagebox.askyesno(
                "Listo",
                f"PDF generado correctamente:\n\n{ruta_generada}\n\n¿Querés abrirlo ahora?"
            )

            if abrir_pdf:
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
            if hasattr(self, "pdf_unico_label"):
                self.pdf_unico_label.configure(text=os.path.basename(archivo))
            self.actualizar_preview()

    def quitar_pdf_unico(self, label=None):
        self.pdf_unico_var.set("")

        if label:
            label.configure(text="Sin archivo seleccionado")

        self.preview_image_tk = None
        self.preview_label.configure(image=None, text="No hay PDF puntual seleccionado.")
        self.preview_info.configure(text="")

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

            abrir_pdf = messagebox.askyesno(
                "Listo",
                f"PDF generado:\n\n{ruta_salida}\n\n¿Querés abrirlo ahora?"
            )

            if abrir_pdf:
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

            abrir_carpeta = messagebox.askyesno(
                "Listo",
                f"{mensaje}\n\n¿Querés abrir la carpeta de salida?"
            )

            if abrir_carpeta:
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
                if hasattr(self, "pdf_unico_label"):
                    self.pdf_unico_label.configure(text=os.path.basename(ruta))
                self.actualizar_preview()
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

    def elegir_logo_izquierdo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo izquierdo",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.logo_izquierdo_var.set(path)
            self.logo_izquierdo_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_central(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo central",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.logo_central_var.set(path)
            self.logo_central_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_derecho(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo derecho",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.logo_derecho_var.set(path)
            self.logo_derecho_label.configure(text=os.path.basename(path))
            self.actualizar_preview()

    def quitar_logo(self, variable, label):
        variable.set("")
        label.configure(text="Sin archivo seleccionado")
        self.actualizar_preview()

    def crear_selector_logo(self, panel, texto, variable, comando):
        ctk.CTkLabel(panel, text=texto).pack(anchor="w", padx=20, pady=(12, 2))

        fila = ctk.CTkFrame(panel, fg_color="transparent")
        fila.pack(fill="x", padx=20)

        entry = ctk.CTkEntry(fila, textvariable=variable, width=260)
        entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            fila,
            text="Buscar",
            width=74,
            command=comando
        ).pack(side="left")

        label = ctk.CTkLabel(
            panel,
            text=os.path.basename(variable.get()) if variable.get() else "Sin archivo seleccionado",
            font=("Arial", 11),
            text_color="#AAB0B6"
        )
        label.pack(anchor="w", padx=22, pady=(3, 0))

        ctk.CTkButton(
            fila,
            text="Quitar",
            width=74,
            fg_color="#3B3F46",
            hover_color="#4B515A",
            command=lambda: self.quitar_logo(variable, label)
        ).pack(side="left", padx=(8, 0))

        return entry, label

def iniciar_app():
    app = PDFNotionApp()
    app.mainloop()
