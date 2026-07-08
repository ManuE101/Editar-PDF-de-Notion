import os
import shutil
import hashlib
import tempfile
import threading
import time
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from config import cargar_config, guardar_config, cargar_perfiles, guardar_perfiles, extraer_config_perfil
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
from title_detector import (
    detectar_titulo_pdf,
    detectar_titulo_zip,
    limpiar_nombre_archivo,
    nombre_pdf_desde_titulo,
)
from notion_zip_reader import ZipNotionInvalido, validar_zip_notion
from word_converter import WordConversionError, convertir_word_a_pdf
from error_messages import describir_error
from process_control import ProcesoCancelado


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
        self.perfiles_data = cargar_perfiles()
        perfil_inicial = self.config_data.get("perfil_actual", "Predeterminado")
        if perfil_inicial not in self.perfiles_data:
            perfil_inicial = next(iter(self.perfiles_data.keys()), "Predeterminado")
        self.perfil_actual_var = ctk.StringVar(
            value=perfil_inicial
        )

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
        self.word_var = ctk.StringVar(value="")
        self.nombre_salida_var = ctk.StringVar(value="")

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
        self.preview_base_key = None
        self.preview_base_image = None
        self.preview_base_scale = None
        self.ultimo_pdf_generado = None
        self.opciones_avanzadas_frame = None
        self.zip_preview_pdf = None
        self.zip_preview_signature = None
        self.preview_after_id = None
        self.word_procesando = False
        self.ventana_progreso = None
        self.progreso_modal = None
        self.estado_modal = None
        self.boton_cancelar_progreso = None
        self.cancelacion_solicitada = False

        self.protocol("WM_DELETE_WINDOW", self.cerrar_app)
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

    def crear_panel_perfiles(self, panel):
        card = self.crear_card(
            panel,
            "Perfil de configuración",
            "Guardá y reutilizá estilos completos de header, footer, logos y portada."
        )

        fila_selector = ctk.CTkFrame(card, fg_color="transparent")
        fila_selector.pack(fill="x", padx=18, pady=(0, 10))
        fila_selector.grid_columnconfigure(0, weight=1)

        self.perfil_menu = ctk.CTkOptionMenu(
            fila_selector,
            values=self.obtener_nombres_perfiles(),
            variable=self.perfil_actual_var,
            command=self.aplicar_perfil
        )
        self.perfil_menu.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(
            fila_selector,
            text="Guardar",
            width=96,
            command=self.guardar_perfil_actual
        ).grid(row=0, column=1, sticky="e")

        fila_acciones = ctk.CTkFrame(card, fg_color="transparent")
        fila_acciones.pack(fill="x", padx=18, pady=(0, 4))
        fila_acciones.grid_columnconfigure((0, 1), weight=1, uniform="perfil")

        ctk.CTkButton(
            fila_acciones,
            text="Nuevo",
            height=34,
            fg_color="#3B4350",
            hover_color="#4B5666",
            command=self.crear_perfil_nuevo
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            fila_acciones,
            text="Eliminar",
            height=34,
            fg_color="#5A2D32",
            hover_color="#713940",
            command=self.eliminar_perfil_actual
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

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

        self.crear_panel_perfiles(panel)

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
        self.crear_entry(card_archivos, "Nombre de salida", self.nombre_salida_var)

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

        # Integración Word reservada para cuando la empresa disponga de un
        # motor de conversión compatible (Microsoft Word o LibreOffice).
        # card_word = self.crear_card(
        #     panel,
        #     "Documentos Word",
        #     "Convertí un archivo DOC o DOCX y aplicá la configuración actual."
        # )
        # self.word_entry, self.word_label = self.crear_selector(
        #     card_word,
        #     "Documento Word",
        #     self.word_var,
        #     self.elegir_word,
        #     self.quitar_word
        # )
        # self.boton_procesar_word = ctk.CTkButton(
        #     card_word,
        #     text="Convertir y procesar Word",
        #     font=("Arial", 13, "bold"),
        #     height=40,
        #     command=self.procesar_word
        # )
        # self.boton_procesar_word.pack(fill="x", padx=20, pady=(14, 18))

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
            command=self.actualizar_preview_indice
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
        preview_header = ctk.CTkFrame(panel, fg_color="transparent")
        preview_header.pack(fill="x", padx=22, pady=(20, 4))
        preview_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_header,
            text="Vista previa",
            font=("Arial", 20, "bold"),
            text_color="#F4F7FB"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            preview_header,
            text="Actualizar",
            command=self.actualizar_preview_forzada,
            height=34,
            width=120
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            panel,
            text="Visualizá la página completa mientras ajustás header y footer.",
            font=("Arial", 12),
            text_color="#9AA6B5"
        ).pack(anchor="w", padx=22, pady=(0, 14))

        preview_shell = ctk.CTkFrame(panel, height=500, corner_radius=14, fg_color="#101318")
        preview_shell.pack(fill="x", padx=22, pady=(0, 10))
        preview_shell.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            preview_shell,
            text="",
            fg_color="transparent"
        )
        self.preview_label.pack(expand=True, fill="both", padx=14, pady=14)

        self.preview_info = ctk.CTkLabel(
            panel,
            text="",
            font=("Arial", 12),
            text_color="#AEB7C4"
        )
        self.preview_info.pack(anchor="w", padx=22, pady=(0, 8))

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
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            drop_frame,
            text="El origen se detecta automáticamente y actualiza la vista previa cuando aplica.",
            font=("Arial", 11),
            text_color="#9AA6B5"
        ).pack(pady=(0, 10))

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

    def obtener_carpeta_dialogo(self, clave, alternativa=""):
        carpeta = self.config_data.get(clave, "") or alternativa
        carpeta = os.path.abspath(carpeta) if carpeta else ""
        return carpeta if os.path.isdir(carpeta) else ""

    def recordar_carpeta_dialogo(self, clave, ruta, es_archivo=False):
        carpeta = os.path.dirname(ruta) if es_archivo else ruta
        if not carpeta or not os.path.isdir(carpeta):
            return

        self.config_data[clave] = os.path.abspath(carpeta)
        config = self.obtener_config_actual()
        config.update({
            nombre: self.config_data.get(nombre, "")
            for nombre in (
                "ultima_carpeta_logos",
                "ultima_carpeta_pdfs",
                "ultima_carpeta_zips",
                "ultima_carpeta_word",
                "ultima_carpeta_salida",
            )
        })
        guardar_config(config)

    def elegir_entrada(self):
        carpeta = filedialog.askdirectory(
            initialdir=self.obtener_carpeta_dialogo(
                "ultima_carpeta_pdfs",
                self.entrada_var.get()
            )
        )
        if carpeta:
            self.entrada_var.set(carpeta)
            self.recordar_carpeta_dialogo("ultima_carpeta_pdfs", carpeta)
            self.actualizar_preview()

    def elegir_salida(self):
        carpeta = filedialog.askdirectory(
            initialdir=self.obtener_carpeta_dialogo(
                "ultima_carpeta_salida",
                self.salida_var.get()
            )
        )
        if carpeta:
            self.salida_var.set(carpeta)
            self.recordar_carpeta_dialogo("ultima_carpeta_salida", carpeta)

    def actualizar_nombre_salida_desde_titulo(self, titulo, fallback):
        nombre = nombre_pdf_desde_titulo(titulo, fallback=fallback)
        self.nombre_salida_var.set(nombre)

    def obtener_nombre_salida_actual(self, fallback):
        nombre = self.nombre_salida_var.get().strip()
        if nombre.lower().endswith(".pdf"):
            nombre = nombre[:-4]

        nombre = limpiar_nombre_archivo(nombre, fallback=fallback)
        return f"{nombre}.pdf"

    def validar_zip_para_notion(self, ruta_zip):
        try:
            validar_zip_notion(ruta_zip)
            return True
        except ZipNotionInvalido as error:
            messagebox.showerror(
                "ZIP de Notion inválido",
                f"No se puede usar este ZIP:\n\n{error}"
            )
            return False
        except Exception as error:
            self.actualizar_estado_progreso("No se pudo validar el ZIP.", 0)
            self.mostrar_error_operacion(
                error,
                "validar el ZIP",
                ruta_zip
            )
            return False

    def mostrar_error_operacion(self, error, accion, ruta=None):
        titulo, mensaje = describir_error(error, accion=accion, ruta=ruta)
        messagebox.showerror(titulo, mensaje)

    def mostrar_resumen_errores(self, errores, tipo_archivo):
        if not errores:
            return

        limite = 8
        lineas = [f"• {error}" for error in errores[:limite]]
        restantes = len(errores) - limite
        if restantes > 0:
            lineas.append(f"• ... y {restantes} error(es) más.")

        messagebox.showwarning(
            f"{tipo_archivo} con errores",
            "Algunos archivos no pudieron procesarse:\n\n"
            + "\n\n".join(lineas)
            + "\n\nLos demás archivos se procesaron normalmente."
        )

    def actualizar_estado_progreso(self, texto=None, valor=None):
        if texto is not None:
            self.estado_label.configure(text=texto)
            if self.estado_modal is not None:
                self.estado_modal.configure(text=texto)
        if valor is not None:
            valor = max(0.0, min(1.0, float(valor)))
            self.progress.set(valor)
            if self.progreso_modal is not None:
                self.progreso_modal.set(valor)
        if self.ventana_progreso is not None:
            self.update()
            if self.cancelacion_solicitada:
                raise ProcesoCancelado()
        else:
            self.update_idletasks()

    def abrir_ventana_progreso(self, titulo):
        if self.ventana_progreso is not None:
            return

        ventana = ctk.CTkToplevel(self)
        ventana.title(titulo)
        ventana.geometry("460x180")
        ventana.resizable(False, False)
        ventana.transient(self)
        ventana.protocol("WM_DELETE_WINDOW", lambda: None)
        ventana.grab_set()

        ctk.CTkLabel(
            ventana,
            text=titulo,
            font=("Arial", 18, "bold")
        ).pack(anchor="w", padx=24, pady=(24, 8))

        self.estado_modal = ctk.CTkLabel(
            ventana,
            text="Preparando...",
            font=("Arial", 12),
            text_color="#B8C1CC",
            wraplength=410,
            justify="left"
        )
        self.estado_modal.pack(anchor="w", padx=24, pady=(0, 18))

        self.progreso_modal = ctk.CTkProgressBar(ventana, width=412)
        self.progreso_modal.pack(padx=24)
        self.progreso_modal.set(0)
        self.boton_cancelar_progreso = ctk.CTkButton(
            ventana,
            text="Cancelar",
            width=110,
            height=32,
            fg_color="#5A2D32",
            hover_color="#713940",
            command=self.solicitar_cancelacion
        )
        self.boton_cancelar_progreso.pack(anchor="e", padx=24, pady=(18, 20))
        ventana.geometry("460x225")
        self.cancelacion_solicitada = False
        self.ventana_progreso = ventana
        ventana.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - ventana.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - ventana.winfo_height()) // 2
        ventana.geometry(f"+{max(0, x)}+{max(0, y)}")
        ventana.lift()

    def solicitar_cancelacion(self):
        if self.cancelacion_solicitada:
            return
        self.cancelacion_solicitada = True
        if self.estado_modal is not None:
            self.estado_modal.configure(
                text="Cancelando en el siguiente punto seguro..."
            )
        if self.boton_cancelar_progreso is not None:
            self.boton_cancelar_progreso.configure(
                state="disabled",
                text="Cancelando..."
            )

    def cerrar_ventana_progreso(self):
        ventana = self.ventana_progreso
        self.ventana_progreso = None
        self.progreso_modal = None
        self.estado_modal = None
        self.boton_cancelar_progreso = None
        self.cancelacion_solicitada = False
        if ventana is None:
            return
        try:
            ventana.grab_release()
            ventana.destroy()
        except Exception:
            pass
        self.update_idletasks()

    def finalizar_cancelacion(self):
        self.cerrar_ventana_progreso()
        self.estado_label.configure(text="Proceso cancelado por el usuario.")
        self.progress.set(0)

    def obtener_nombres_perfiles(self):
        nombres = list(self.perfiles_data.keys())
        return nombres if nombres else ["Predeterminado"]

    def actualizar_menu_perfiles(self):
        if hasattr(self, "perfil_menu"):
            self.perfil_menu.configure(values=self.obtener_nombres_perfiles())

    def formato_config_a_visible(self, formato):
        mapa = {
            "Página {pagina}": "Página 1",
            "Página {pagina} de {total}": "Página 1 de 10",
            "{pagina} / {total}": "1 / 10",
            "Pág. {pagina}": "Pág. 1",
            "Sin numeración": "Sin numeración",
        }
        return mapa.get(formato, formato)

    def aplicar_config_en_ui(self, config):
        self.logo_izquierdo_var.set(config.get("logo_izquierdo", ""))
        self.logo_central_var.set(config.get("logo_central", ""))
        self.logo_derecho_var.set(config.get("logo_derecho", ""))
        self.header_var.set(config.get("header", ""))
        self.footer_var.set(config.get("footer", ""))
        self.version_var.set(config.get("version", ""))
        self.formato_numeracion_var.set(
            self.formato_config_a_visible(config.get("formato_numeracion", "Página {pagina}"))
        )

        self.header_offset_var.set(int(config.get("header_offset", 35)))
        self.footer_offset_var.set(int(config.get("footer_offset", 25)))
        self.margen_x_var.set(int(config.get("margen_x", 40)))
        self.logo_width_var.set(int(config.get("logo_width", 80)))
        self.logo_height_var.set(int(config.get("logo_height", 30)))

        self.titulo_portada_var.set(config.get("titulo_portada", ""))
        self.subtitulo_portada_var.set(config.get("subtitulo_portada", ""))
        self.area_portada_var.set(config.get("area_portada", ""))

        self.mostrar_logo_var.set(bool(config.get("mostrar_logo", True)))
        self.mostrar_fecha_var.set(bool(config.get("mostrar_fecha", True)))
        self.numerar_paginas_var.set(bool(config.get("numerar_paginas", True)))
        self.agregar_portada_var.set(bool(config.get("agregar_portada", True)))
        self.agregar_indice_var.set(bool(config.get("agregar_indice", False)))
        self.mostrar_header_portada_var.set(bool(config.get("mostrar_header_portada", False)))
        self.mostrar_footer_portada_var.set(bool(config.get("mostrar_footer_portada", False)))
        self.header_portada_var.set(config.get("header_portada", ""))
        self.footer_portada_var.set(config.get("footer_portada", ""))

        if hasattr(self, "logo_izquierdo_label"):
            self.logo_izquierdo_label.configure(
                text=os.path.basename(self.logo_izquierdo_var.get()) if self.logo_izquierdo_var.get() else "Sin archivo seleccionado"
            )
        if hasattr(self, "logo_central_label"):
            self.logo_central_label.configure(
                text=os.path.basename(self.logo_central_var.get()) if self.logo_central_var.get() else "Sin archivo seleccionado"
            )
        if hasattr(self, "logo_derecho_label"):
            self.logo_derecho_label.configure(
                text=os.path.basename(self.logo_derecho_var.get()) if self.logo_derecho_var.get() else "Sin archivo seleccionado"
            )

        self.invalidar_base_preview()
        self.actualizar_preview()

    def aplicar_perfil(self, nombre):
        perfil = self.perfiles_data.get(nombre)
        if not perfil:
            return

        self.perfil_actual_var.set(nombre)
        self.aplicar_config_en_ui(perfil)
        self.estado_label.configure(text=f"Perfil aplicado: {nombre}")

    def guardar_perfil_actual(self):
        nombre = self.perfil_actual_var.get().strip() or "Predeterminado"
        self.perfiles_data[nombre] = extraer_config_perfil(self.obtener_config_actual())
        guardar_perfiles(self.perfiles_data)
        self.actualizar_menu_perfiles()
        self.estado_label.configure(text=f"Perfil guardado: {nombre}")

    def crear_perfil_nuevo(self):
        dialogo = ctk.CTkInputDialog(
            text="Nombre del nuevo perfil:",
            title="Nuevo perfil"
        )
        nombre = (dialogo.get_input() or "").strip()

        if not nombre:
            return

        if nombre in self.perfiles_data:
            messagebox.showwarning("Perfil existente", "Ya existe un perfil con ese nombre.")
            return

        self.perfiles_data[nombre] = extraer_config_perfil(self.obtener_config_actual())
        self.perfil_actual_var.set(nombre)
        guardar_perfiles(self.perfiles_data)
        self.actualizar_menu_perfiles()
        self.estado_label.configure(text=f"Perfil creado: {nombre}")

    def eliminar_perfil_actual(self):
        nombre = self.perfil_actual_var.get().strip()

        if not nombre or nombre not in self.perfiles_data:
            return

        if len(self.perfiles_data) <= 1:
            messagebox.showwarning("No se puede eliminar", "Debe quedar al menos un perfil.")
            return

        confirmar = messagebox.askyesno(
            "Eliminar perfil",
            f"¿Querés eliminar el perfil '{nombre}'?"
        )
        if not confirmar:
            return

        del self.perfiles_data[nombre]
        nuevo_nombre = self.obtener_nombres_perfiles()[0]
        self.perfil_actual_var.set(nuevo_nombre)
        guardar_perfiles(self.perfiles_data)
        self.actualizar_menu_perfiles()
        self.aplicar_perfil(nuevo_nombre)

    def preparar_carpeta_salida(self, config):
        carpeta_salida = config.get("salida", "").strip()

        if not carpeta_salida:
            messagebox.showerror("Carpeta de salida faltante", "Elegí una carpeta de salida antes de generar el PDF.")
            return None

        try:
            os.makedirs(carpeta_salida, exist_ok=True)
        except OSError as error:
            messagebox.showerror(
                "No se pudo preparar la salida",
                f"No se pudo crear o acceder a la carpeta de salida:\n\n{carpeta_salida}\n\nDetalle: {error}"
            )
            return None

        config["salida"] = carpeta_salida
        return carpeta_salida

    def confirmar_sobrescritura(self, ruta_salida):
        if not os.path.exists(ruta_salida):
            return True

        return messagebox.askyesno(
            "El PDF ya existe",
            f"Ya existe un PDF con este nombre:\n\n{ruta_salida}\n\n¿Querés sobrescribirlo?"
        )

    def validar_salida_no_pisa_origen(self, ruta_origen, ruta_salida):
        if os.path.abspath(ruta_origen) != os.path.abspath(ruta_salida):
            return True

        messagebox.showerror(
            "Nombre de salida inválido",
            "El PDF de salida no puede tener exactamente la misma ruta que el archivo original."
        )
        return False

    def preguntar_modo_sobrescritura_multiple(self, rutas_existentes):
        if not rutas_existentes:
            return "sobrescribir_todo"

        respuesta = {"valor": None}

        ventana = ctk.CTkToplevel(self)
        ventana.title("PDFs existentes")
        ventana.geometry("520x300")
        ventana.resizable(False, False)
        ventana.transient(self)
        ventana.grab_set()

        ctk.CTkLabel(
            ventana,
            text="Ya existen PDFs con esos nombres",
            font=("Arial", 18, "bold")
        ).pack(anchor="w", padx=22, pady=(22, 6))

        ctk.CTkLabel(
            ventana,
            text=(
                f"Se encontraron {len(rutas_existentes)} archivo(s) de salida ya existente(s).\n"
                "Elegí cómo querés continuar."
            ),
            justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 12))

        nombres = [os.path.basename(ruta) for ruta in rutas_existentes[:5]]
        if len(rutas_existentes) > 5:
            nombres.append(f"... y {len(rutas_existentes) - 5} más")

        ctk.CTkLabel(
            ventana,
            text="\n".join(nombres),
            font=("Arial", 11),
            text_color="#AAB0B6",
            justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 16))

        botones = ctk.CTkFrame(ventana, fg_color="transparent")
        botones.pack(fill="x", padx=22, pady=(4, 18))
        botones.grid_columnconfigure((0, 1, 2), weight=1, uniform="sobrescritura")

        def cerrar(valor):
            respuesta["valor"] = valor
            ventana.destroy()

        ctk.CTkButton(
            botones,
            text="Sobrescribir todo",
            command=lambda: cerrar("sobrescribir_todo")
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            botones,
            text="Uno por uno",
            fg_color="#3B4350",
            hover_color="#4B5666",
            command=lambda: cerrar("preguntar")
        ).grid(row=0, column=1, sticky="ew", padx=6)

        ctk.CTkButton(
            botones,
            text="Cancelar",
            fg_color="#5A2D32",
            hover_color="#713940",
            command=lambda: cerrar(None)
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        ventana.protocol("WM_DELETE_WINDOW", lambda: cerrar(None))
        ventana.wait_window()

        return respuesta["valor"]

    def obtener_conflictos_pdf_carpeta(self, entrada, salida):
        if not os.path.exists(entrada):
            return []

        conflictos = []
        for archivo in os.listdir(entrada):
            if not archivo.lower().endswith(".pdf"):
                continue

            ruta_salida = os.path.join(salida, crear_nombre_salida(archivo))
            if os.path.exists(ruta_salida):
                conflictos.append(ruta_salida)

        return conflictos

    def obtener_conflictos_zip_carpeta(self, carpeta_zips, salida):
        if not os.path.exists(carpeta_zips):
            return []

        conflictos = []
        for archivo in os.listdir(carpeta_zips):
            if not archivo.lower().endswith(".zip"):
                continue

            nombre_salida = f"{os.path.splitext(archivo)[0]}_convertido.pdf"
            ruta_salida = os.path.join(salida, nombre_salida)
            if os.path.exists(ruta_salida):
                conflictos.append(ruta_salida)

        return conflictos

    def elegir_logo(self):
        archivo = filedialog.askopenfilename(
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", archivo, es_archivo=True)
            self.logo_var.set(archivo)
            self.actualizar_preview()

    def elegir_logo_izquierdo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo izquierdo",
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", path, es_archivo=True)
            self.logo_izquierdo_var.set(path)
            self.logo_izquierdo_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_central(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo central",
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", path, es_archivo=True)
            self.logo_central_var.set(path)
            self.logo_central_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_derecho(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo derecho",
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", path, es_archivo=True)
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
            "ultima_carpeta_logos": self.config_data.get("ultima_carpeta_logos", ""),
            "ultima_carpeta_pdfs": self.config_data.get("ultima_carpeta_pdfs", ""),
            "ultima_carpeta_zips": self.config_data.get("ultima_carpeta_zips", ""),
            "ultima_carpeta_word": self.config_data.get("ultima_carpeta_word", ""),
            "ultima_carpeta_salida": self.config_data.get("ultima_carpeta_salida", ""),
            "perfil_actual": self.perfil_actual_var.get(),
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

    def invalidar_preview_zip(self):
        self.zip_preview_pdf = None
        self.zip_preview_signature = None
        self.invalidar_base_preview()

    def invalidar_base_preview(self):
        self.preview_base_key = None
        self.preview_base_image = None
        self.preview_base_scale = None

    def programar_actualizar_preview(self, invalidar_zip=False):
        if invalidar_zip:
            self.invalidar_preview_zip()

        if self.preview_after_id:
            try:
                self.after_cancel(self.preview_after_id)
            except Exception:
                pass

        self.preview_after_id = self.after(80, self.ejecutar_preview_programada)

    def ejecutar_preview_programada(self):
        self.preview_after_id = None
        self.actualizar_preview()

    def actualizar_preview_indice(self):
        self.programar_actualizar_preview(invalidar_zip=True)

    def actualizar_preview_forzada(self):
        ruta_zip = self.zip_var.get().strip().strip("{}")
        self.programar_actualizar_preview(invalidar_zip=bool(ruta_zip))

    def limpiar_preview_visual(self, texto=""):
        try:
            self.preview_label.configure(image=None, text=texto)
        except Exception:
            try:
                self.preview_label._label.configure(image="", text=texto)
                self.preview_label._image = None
                self.preview_label._text = texto
            except Exception:
                pass

        self.preview_image_tk = None

    def actualizar_preview(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        self.limpiar_preview_visual("Generando vista previa...")
        self.preview_info.configure(text="")
        self.update_idletasks()

        try:
            from preview import obtener_primer_pdf, generar_base_preview_pdf, aplicar_overlay_preview
        except Exception:
            self.preview_label.configure(
                text="Vista previa de PDF no disponible.\n\n"
                    "El sistema bloqueó PyMuPDF.\n"
                    "Igual podés procesar PDFs y convertir ZIPs."
            )
            self.preview_info.configure(text="")
            return

        pdf_unico = self.pdf_unico_var.get().strip().strip("{}")
        ruta_zip = self.zip_var.get().strip().strip("{}")
        ruta_word = self.word_var.get().strip().strip("{}")
        preview_es_zip = False

        if ruta_word:
            self.limpiar_preview_visual(
                "Documento Word seleccionado.\n\n"
                "La vista previa estará disponible después de convertirlo."
            )
            self.preview_info.configure(text=os.path.basename(ruta_word))
            return
        if pdf_unico and os.path.exists(pdf_unico):
            primer_pdf = pdf_unico
        elif pdf_unico:
            self.limpiar_preview_visual("El PDF seleccionado no existe o no se puede leer.")
            self.preview_info.configure(text=os.path.basename(pdf_unico))
            return
        elif ruta_zip and os.path.exists(ruta_zip):
            primer_pdf = self.obtener_preview_zip(ruta_zip, config)
            preview_es_zip = bool(primer_pdf)
        else:
            primer_pdf = obtener_primer_pdf(config["entrada"])

        if not primer_pdf:
            self.limpiar_preview_visual("No hay PDFs para previsualizar.")
            self.preview_info.configure(text="")
            return

        ancho_preview = 390
        alto_preview = 455
        try:
            pdf_stat = os.stat(primer_pdf)
            base_key = (
                os.path.abspath(primer_pdf),
                pdf_stat.st_mtime,
                pdf_stat.st_size,
                ancho_preview,
                alto_preview,
            )
        except OSError:
            base_key = None

        if base_key and self.preview_base_key == base_key and self.preview_base_image is not None:
            imagen_base = self.preview_base_image
            escala = self.preview_base_scale
        else:
            resultado_base = generar_base_preview_pdf(
                primer_pdf,
                ancho_preview=ancho_preview,
                alto_preview=alto_preview
            )

            if resultado_base is None:
                imagen_base = None
                escala = None
            else:
                imagen_base, escala = resultado_base
                self.preview_base_key = base_key
                self.preview_base_image = imagen_base
                self.preview_base_scale = escala

        imagen = aplicar_overlay_preview(imagen_base, escala, primer_pdf, config)

        if imagen is None:
            if preview_es_zip:
                self.invalidar_preview_zip()
            self.limpiar_preview_visual("No se pudo generar la vista previa.")
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

    def limpiar_cache_preview(self, max_age_seconds=3600, max_archivos=4, limpiar_todo=False):
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".preview_cache")
        if not os.path.exists(cache_dir):
            return

        ahora = time.time()
        previews = []

        for nombre in os.listdir(cache_dir):
            if not nombre.startswith("zip_preview") or not nombre.lower().endswith(".pdf"):
                continue

            ruta = os.path.join(cache_dir, nombre)
            try:
                edad = ahora - os.path.getmtime(ruta)
                previews.append((os.path.getmtime(ruta), ruta))

                if limpiar_todo or edad > max_age_seconds:
                    os.remove(ruta)
            except OSError:
                pass

        if limpiar_todo:
            return

        existentes = [
            (fecha, ruta)
            for fecha, ruta in previews
            if os.path.exists(ruta)
        ]
        existentes.sort(reverse=True)

        for _, ruta in existentes[max_archivos:]:
            if ruta == self.zip_preview_pdf:
                continue
            try:
                os.remove(ruta)
            except OSError:
                pass

    def cerrar_app(self):
        self.limpiar_cache_preview(limpiar_todo=True)
        self.destroy()

    def obtener_preview_zip(self, ruta_zip, config):
        try:
            self.limpiar_cache_preview(max_age_seconds=3600)

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
                and os.path.getsize(self.zip_preview_pdf) > 0
            ):
                return self.zip_preview_pdf

            from notion_parser import parsear_html_notion
            from notion_zip_reader import leer_html_desde_zip
            from smart_pdf_exporter_v2 import exportar_documento_pdf_v2

            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".preview_cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_key = hashlib.sha1(repr(signature).encode("utf-8")).hexdigest()[:12]
            ruta_preview = os.path.join(cache_dir, f"zip_preview_{cache_key}.pdf")

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

        carpeta_salida = self.preparar_carpeta_salida(config)
        if not carpeta_salida:
            return

        conflictos = self.obtener_conflictos_pdf_carpeta(config["entrada"], carpeta_salida)
        modo_sobrescritura = self.preguntar_modo_sobrescritura_multiple(conflictos)

        if modo_sobrescritura is None:
            self.estado_label.configure(text="Proceso cancelado.")
            return

        callback_sobrescritura = None
        if modo_sobrescritura == "preguntar":
            sobrescrituras_aprobadas = {
                ruta for ruta in conflictos
                if self.confirmar_sobrescritura(ruta)
            }
            callback_sobrescritura = (
                lambda ruta: ruta in sobrescrituras_aprobadas
            )

        def estado(texto):
            self.actualizar_estado_progreso(texto=texto)

        def progreso(valor):
            self.actualizar_estado_progreso(valor=valor)

        self.abrir_ventana_progreso("Procesando carpeta de PDFs")
        try:
            procesados, total, errores = procesar_carpeta(
                config,
                callback_estado=estado,
                callback_progreso=progreso,
                callback_sobrescritura=callback_sobrescritura
            )

            if total == 0:
                self.cerrar_ventana_progreso()
                messagebox.showwarning("Sin PDFs", "No se encontraron PDFs en la carpeta de entrada.")
                return

            self.estado_label.configure(text=f"Proceso finalizado: {procesados}/{total} PDFs procesados.")
            self.progress.set(1)
            self.cerrar_ventana_progreso()

            if errores:
                self.mostrar_resumen_errores(errores, "PDFs")
            else:
                messagebox.showinfo(
                    "Listo",
                    f"Se procesaron {procesados} PDF(s).\n\nRevisá la carpeta de salida."
                )

        except ProcesoCancelado:
            self.finalizar_cancelacion()
        except Exception as error:
            self.cerrar_ventana_progreso()
            self.actualizar_estado_progreso("No se pudo procesar la carpeta de PDFs.", 0)
            self.mostrar_error_operacion(
                error,
                "procesar la carpeta de PDFs",
                config["entrada"]
            )

    def elegir_zip(self):
        archivo = filedialog.askopenfilename(
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_zips"),
            filetypes=[
                ("ZIP de Notion", "*.zip"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.recordar_carpeta_dialogo("ultima_carpeta_zips", archivo, es_archivo=True)
            if not self.validar_zip_para_notion(archivo):
                return

            self.zip_var.set(archivo)
            self.pdf_unico_var.set("")
            self.word_var.set("")
            if hasattr(self, "pdf_unico_label"):
                self.pdf_unico_label.configure(text="Sin archivo seleccionado")
            if hasattr(self, "word_label"):
                self.word_label.configure(text="Sin archivo seleccionado")
            if hasattr(self, "zip_label"):
                self.zip_label.configure(text=os.path.basename(archivo))
            try:
                titulo = detectar_titulo_zip(archivo)
            except Exception:
                titulo = formatear_titulo(os.path.basename(archivo))
            self.actualizar_nombre_salida_desde_titulo(
                titulo,
                fallback=formatear_titulo(os.path.basename(archivo))
            )
            self.actualizar_preview()

    def convertir_zip(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        ruta_zip = self.zip_var.get().strip().strip("{}")

        if not ruta_zip or not os.path.exists(ruta_zip):
            messagebox.showerror("ZIP inválido", "Seleccioná un archivo ZIP válido antes de convertir.")
            return

        if not ruta_zip.lower().endswith(".zip"):
            messagebox.showerror("Archivo no compatible", "El archivo seleccionado no parece ser un ZIP.")
            return

        if not self.validar_zip_para_notion(ruta_zip):
            return

        carpeta_salida = self.preparar_carpeta_salida(config)
        if not carpeta_salida:
            return

        nombre_salida = self.obtener_nombre_salida_actual(
            fallback=formatear_titulo(os.path.basename(ruta_zip))
        )
        ruta_generada = os.path.join(carpeta_salida, nombre_salida)

        if not self.confirmar_sobrescritura(ruta_generada):
            self.estado_label.configure(text="Conversión cancelada: el PDF ya existe.")
            return

        try:
            self.abrir_ventana_progreso("Convirtiendo ZIP de Notion")
            self.actualizar_estado_progreso("Preparando conversión de ZIP...", 0)

            ruta_generada = convertir_zip_notion_a_pdf(
                ruta_zip=ruta_zip,
                carpeta_salida=carpeta_salida,
                config=config,
                nombre_salida=nombre_salida,
                callback_estado=lambda texto: self.actualizar_estado_progreso(texto=texto),
                callback_progreso=lambda valor: self.actualizar_estado_progreso(valor=valor),
            )

            self.ultimo_pdf_generado = ruta_generada

            self.actualizar_estado_progreso("ZIP convertido correctamente.", 1)
            self.cerrar_ventana_progreso()

            abrir_pdf = messagebox.askyesno(
                "Listo",
                f"PDF generado correctamente:\n\n{ruta_generada}\n\n¿Querés abrirlo ahora?"
            )

            if abrir_pdf:
                os.startfile(ruta_generada)

        except ProcesoCancelado:
            self.finalizar_cancelacion()
        except Exception as error:
            self.cerrar_ventana_progreso()
            self.actualizar_estado_progreso("No se pudo convertir el ZIP.", 0)
            self.mostrar_error_operacion(
                error,
                "convertir el ZIP a PDF",
                ruta_zip
            )

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
        carpeta = filedialog.askdirectory(
            initialdir=self.obtener_carpeta_dialogo(
                "ultima_carpeta_zips",
                self.zip_folder_var.get()
            )
        )
        if carpeta:
            self.zip_folder_var.set(carpeta)
            self.recordar_carpeta_dialogo("ultima_carpeta_zips", carpeta)


    def elegir_pdf_unico(self):
        archivo = filedialog.askopenfilename(
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_pdfs"),
            filetypes=[
                ("PDF", "*.pdf"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivo:
            self.recordar_carpeta_dialogo("ultima_carpeta_pdfs", archivo, es_archivo=True)
            self.pdf_unico_var.set(archivo)
            self.zip_var.set("")
            self.word_var.set("")
            if hasattr(self, "pdf_unico_label"):
                self.pdf_unico_label.configure(text=os.path.basename(archivo))
            if hasattr(self, "zip_label"):
                self.zip_label.configure(text="Sin archivo seleccionado")
            if hasattr(self, "word_label"):
                self.word_label.configure(text="Sin archivo seleccionado")
            titulo = detectar_titulo_pdf(archivo)
            self.actualizar_nombre_salida_desde_titulo(
                titulo,
                fallback=formatear_titulo(os.path.basename(archivo))
            )
            self.actualizar_preview()

    def elegir_word(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar documento Word",
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_word"),
            filetypes=[
                ("Documentos Word", "*.doc *.docx"),
                ("Word DOCX", "*.docx"),
                ("Word DOC", "*.doc"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not archivo:
            return

        self.recordar_carpeta_dialogo("ultima_carpeta_word", archivo, es_archivo=True)
        self.word_var.set(archivo)
        self.pdf_unico_var.set("")
        self.zip_var.set("")
        self.word_label.configure(text=os.path.basename(archivo))
        if hasattr(self, "pdf_unico_label"):
            self.pdf_unico_label.configure(text="Sin archivo seleccionado")
        if hasattr(self, "zip_label"):
            self.zip_label.configure(text="Sin archivo seleccionado")

        titulo = formatear_titulo(os.path.basename(archivo))
        self.actualizar_nombre_salida_desde_titulo(titulo, fallback=titulo)
        self.limpiar_preview_visual(
            "Documento Word seleccionado.\n\n"
            "La vista previa estará disponible después de convertirlo."
        )
        self.preview_info.configure(text=os.path.basename(archivo))

    def quitar_word(self, label=None):
        self.word_var.set("")
        if label:
            label.configure(text="Sin archivo seleccionado")
        self.nombre_salida_var.set("")
        self.limpiar_preview_visual("No hay documento seleccionado.")
        self.preview_info.configure(text="")

    def procesar_word(self):
        if self.word_procesando:
            return

        ruta_word = self.word_var.get().strip().strip("{}")
        if not ruta_word or not os.path.isfile(ruta_word):
            messagebox.showerror(
                "Documento inválido",
                "Seleccioná un documento de Word válido antes de convertir."
            )
            return

        if os.path.splitext(ruta_word)[1].lower() not in {".doc", ".docx"}:
            messagebox.showerror(
                "Archivo no compatible",
                "El documento seleccionado debe tener extensión .doc o .docx."
            )
            return

        config = self.obtener_config_actual()
        guardar_config(config)
        carpeta_salida = self.preparar_carpeta_salida(config)
        if not carpeta_salida:
            return

        nombre_salida = self.obtener_nombre_salida_actual(
            fallback=formatear_titulo(os.path.basename(ruta_word))
        )
        ruta_salida = os.path.join(carpeta_salida, nombre_salida)
        if not self.confirmar_sobrescritura(ruta_salida):
            self.estado_label.configure(text="Conversión de Word cancelada.")
            return

        descriptor, ruta_temporal = tempfile.mkstemp(
            prefix="pdf_notion_word_",
            suffix=".pdf",
            dir=carpeta_salida
        )
        os.close(descriptor)
        try:
            os.remove(ruta_temporal)
        except OSError:
            pass

        self.word_procesando = True
        self.boton_procesar_word.configure(state="disabled", text="Convirtiendo Word...")
        self.estado_label.configure(text=f"Convirtiendo Word: {os.path.basename(ruta_word)}")
        self.progress.set(0.2)

        def trabajo():
            try:
                convertir_word_a_pdf(ruta_word, ruta_temporal)
                titulo = os.path.splitext(nombre_salida)[0]
                procesar_pdf(ruta_temporal, ruta_salida, titulo, config)
                self.after(0, lambda: self.finalizar_word(ruta_salida, None))
            except Exception as error:
                self.after(0, lambda error=error: self.finalizar_word(None, error))
            finally:
                try:
                    os.remove(ruta_temporal)
                except OSError:
                    pass

        threading.Thread(target=trabajo, daemon=True).start()

    def finalizar_word(self, ruta_salida, error):
        self.word_procesando = False
        self.boton_procesar_word.configure(
            state="normal",
            text="Convertir y procesar Word"
        )

        if error:
            self.progress.set(0)
            self.estado_label.configure(text="No se pudo convertir el documento Word.")
            titulo = (
                "Microsoft Word no disponible"
                if isinstance(error, WordConversionError)
                else "Error al procesar Word"
            )
            messagebox.showerror(titulo, str(error))
            return

        self.ultimo_pdf_generado = ruta_salida
        self.progress.set(1)
        self.estado_label.configure(text="Documento Word convertido correctamente.")
        abrir_pdf = messagebox.askyesno(
            "Listo",
            f"PDF generado:\n\n{ruta_salida}\n\n¿Querés abrirlo ahora?"
        )
        if abrir_pdf:
            os.startfile(ruta_salida)

    def quitar_pdf_unico(self, label=None):
        self.pdf_unico_var.set("")

        if label:
            label.configure(text="Sin archivo seleccionado")

        self.nombre_salida_var.set("")
        self.limpiar_preview_visual("No hay PDF puntual seleccionado.")
        self.preview_info.configure(text="")

    def procesar_pdf_unico(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        ruta_pdf = self.pdf_unico_var.get().strip().strip("{}")

        if not ruta_pdf or not os.path.exists(ruta_pdf):
            messagebox.showerror("PDF inválido", "Seleccioná un PDF válido antes de procesar.")
            return

        if not ruta_pdf.lower().endswith(".pdf"):
            messagebox.showerror("Archivo no compatible", "El archivo seleccionado no parece ser un PDF.")
            return

        carpeta_salida = self.preparar_carpeta_salida(config)
        if not carpeta_salida:
            return

        try:
            archivo = os.path.basename(ruta_pdf)
            nombre_salida = self.obtener_nombre_salida_actual(
                fallback=formatear_titulo(archivo)
            )
            titulo = os.path.splitext(nombre_salida)[0]
            ruta_salida = os.path.join(carpeta_salida, nombre_salida)

            if not self.validar_salida_no_pisa_origen(ruta_pdf, ruta_salida):
                return

            if not self.confirmar_sobrescritura(ruta_salida):
                self.estado_label.configure(text="Proceso cancelado: el PDF ya existe.")
                return

            self.abrir_ventana_progreso("Procesando PDF")
            self.actualizar_estado_progreso(f"Preparando PDF: {archivo}", 0)

            procesar_pdf(
                ruta_pdf,
                ruta_salida,
                titulo,
                config,
                callback_estado=lambda texto: self.actualizar_estado_progreso(texto=texto),
                callback_progreso=lambda valor: self.actualizar_estado_progreso(valor=valor),
            )

            self.ultimo_pdf_generado = ruta_salida
            self.actualizar_estado_progreso("PDF procesado correctamente.", 1)
            self.cerrar_ventana_progreso()

            abrir_pdf = messagebox.askyesno(
                "Listo",
                f"PDF generado:\n\n{ruta_salida}\n\n¿Querés abrirlo ahora?"
            )

            if abrir_pdf:
                os.startfile(ruta_salida)

        except ProcesoCancelado:
            self.finalizar_cancelacion()
        except Exception as error:
            self.cerrar_ventana_progreso()
            self.actualizar_estado_progreso("No se pudo procesar el PDF.", 0)
            self.mostrar_error_operacion(
                error,
                "procesar el PDF",
                ruta_pdf
            )

    def convertir_carpeta_zips(self):
        config = self.obtener_config_actual()
        guardar_config(config)

        carpeta_zips = self.zip_folder_var.get().strip().strip("{}")

        if not carpeta_zips or not os.path.exists(carpeta_zips):
            messagebox.showerror("Error", "Seleccioná una carpeta de ZIPs válida.")
            return

        carpeta_salida = self.preparar_carpeta_salida(config)
        if not carpeta_salida:
            return

        conflictos = self.obtener_conflictos_zip_carpeta(carpeta_zips, carpeta_salida)
        modo_sobrescritura = self.preguntar_modo_sobrescritura_multiple(conflictos)

        if modo_sobrescritura is None:
            self.estado_label.configure(text="Conversión cancelada.")
            return

        callback_sobrescritura = None
        if modo_sobrescritura == "preguntar":
            sobrescrituras_aprobadas = {
                ruta for ruta in conflictos
                if self.confirmar_sobrescritura(ruta)
            }
            callback_sobrescritura = (
                lambda ruta: ruta in sobrescrituras_aprobadas
            )

        def estado(texto):
            self.actualizar_estado_progreso(texto=texto)

        def progreso(valor):
            self.actualizar_estado_progreso(valor=valor)

        self.abrir_ventana_progreso("Convirtiendo carpeta de ZIPs")
        try:
            convertidos, total, errores = convertir_carpeta_zips_notion_a_pdf(
                carpeta_zips=carpeta_zips,
                carpeta_salida=carpeta_salida,
                config=config,
                callback_estado=estado,
                callback_progreso=progreso,
                callback_sobrescritura=callback_sobrescritura
            )

            self.estado_label.configure(text=f"ZIPs convertidos: {convertidos}/{total}.")
            self.progress.set(1)
            self.cerrar_ventana_progreso()

            mensaje = f"Se convirtieron {convertidos} de {total} ZIP(s)."

            if errores:
                self.mostrar_resumen_errores(errores, "ZIPs")

            abrir_carpeta = messagebox.askyesno(
                "Listo",
                f"{mensaje}\n\n¿Querés abrir la carpeta de salida?"
            )

            if abrir_carpeta:
                os.startfile(config["salida"])

        except ProcesoCancelado:
            self.finalizar_cancelacion()
        except Exception as error:
            self.cerrar_ventana_progreso()
            self.actualizar_estado_progreso("No se pudo convertir la carpeta de ZIPs.", 0)
            self.mostrar_error_operacion(
                error,
                "convertir la carpeta de ZIPs",
                carpeta_zips
            )

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
                self.recordar_carpeta_dialogo("ultima_carpeta_pdfs", ruta, es_archivo=True)
                self.pdf_unico_var.set(ruta)
                self.zip_var.set("")
                self.word_var.set("")
                if hasattr(self, "pdf_unico_label"):
                    self.pdf_unico_label.configure(text=os.path.basename(ruta))
                if hasattr(self, "zip_label"):
                    self.zip_label.configure(text="Sin archivo seleccionado")
                if hasattr(self, "word_label"):
                    self.word_label.configure(text="Sin archivo seleccionado")
                titulo = detectar_titulo_pdf(ruta)
                self.actualizar_nombre_salida_desde_titulo(
                    titulo,
                    fallback=formatear_titulo(os.path.basename(ruta))
                )
                self.actualizar_preview()
                self.estado_label.configure(text="PDF cargado. Revisá el nombre de salida antes de procesar.")
                return

            if extension == ".zip":
                if not self.validar_zip_para_notion(ruta):
                    return

                self.recordar_carpeta_dialogo("ultima_carpeta_zips", ruta, es_archivo=True)
                self.zip_var.set(ruta)
                self.pdf_unico_var.set("")
                self.word_var.set("")
                if hasattr(self, "zip_label"):
                    self.zip_label.configure(text=os.path.basename(ruta))
                if hasattr(self, "pdf_unico_label"):
                    self.pdf_unico_label.configure(text="Sin archivo seleccionado")
                if hasattr(self, "word_label"):
                    self.word_label.configure(text="Sin archivo seleccionado")
                try:
                    titulo = detectar_titulo_zip(ruta)
                except Exception:
                    titulo = formatear_titulo(os.path.basename(ruta))
                self.actualizar_nombre_salida_desde_titulo(
                    titulo,
                    fallback=formatear_titulo(os.path.basename(ruta))
                )
                self.actualizar_preview()
                self.estado_label.configure(text="ZIP cargado. Revisá el nombre de salida antes de convertir.")
                return

            messagebox.showwarning(
                "Archivo no compatible",
                "Solo se aceptan archivos PDF o ZIP."
            )
            return

        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)

            tiene_pdfs = any(a.lower().endswith(".pdf") for a in archivos)
            tiene_zips = any(a.lower().endswith(".zip") for a in archivos)

            if tiene_pdfs and not tiene_zips:
                self.recordar_carpeta_dialogo("ultima_carpeta_pdfs", ruta)
                self.entrada_var.set(ruta)
                self.procesar()
                return

            if tiene_zips and not tiene_pdfs:
                self.recordar_carpeta_dialogo("ultima_carpeta_zips", ruta)
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
                    self.recordar_carpeta_dialogo("ultima_carpeta_pdfs", ruta)
                    self.entrada_var.set(ruta)
                    self.procesar()
                else:
                    self.recordar_carpeta_dialogo("ultima_carpeta_zips", ruta)
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
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", path, es_archivo=True)
            self.logo_izquierdo_var.set(path)
            self.logo_izquierdo_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_central(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo central",
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", path, es_archivo=True)
            self.logo_central_var.set(path)
            self.logo_central_label.configure(text=os.path.basename(path))
            self.actualizar_preview()


    def elegir_logo_derecho(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo derecho",
            initialdir=self.obtener_carpeta_dialogo("ultima_carpeta_logos"),
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*")
            ]
        )

        if path:
            self.recordar_carpeta_dialogo("ultima_carpeta_logos", path, es_archivo=True)
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
