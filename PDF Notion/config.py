import json
import os


CONFIG_FILE = "config.json"


DEFAULT_CONFIG = {
    "entrada": "Entrada",
    "salida": "Salida",
    "logo": "assets/logo.png",
    "footer": "Confidencial - Uso interno",
    "version": "v1.0",
    "mostrar_logo": True,
    "mostrar_fecha": True,
    "numerar_paginas": True,
    "agregar_portada": True,
    "header_offset": 35,
    "footer_offset": 25,
    "margen_x": 40,
    "logo_width": 80,
    "logo_height": 30,
    "titulo_portada": "Documentación WalkMe",
    "subtitulo_portada": "Documento generado desde Notion",
    "area_portada": "Uso interno"
}


def cargar_config():
    if not os.path.exists(CONFIG_FILE):
        guardar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    final_config = DEFAULT_CONFIG.copy()
    final_config.update(config)

    return final_config


def guardar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)