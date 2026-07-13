import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
PROFILES_FILE = os.path.join(BASE_DIR, "profiles.json")


DEFAULT_CONFIG = {
    "entrada": "Entrada",
    "salida": "Salida",
    "ultima_carpeta_logos": "",
    "ultima_carpeta_pdfs": "",
    "ultima_carpeta_zips": "",
    "ultima_carpeta_word": "",
    "ultima_carpeta_salida": "",
    "perfil_actual": "Predeterminado",
    # "logo": "assets/logo.png",
    "logo_izquierdo": "",
    "logo_central": "",
    "logo_derecho": "",
    "header": "",
    "footer": "Confidencial - Uso interno",
    "version": "v1.0",
    "mostrar_logo": True,
    "mostrar_fecha": True,
    "numerar_paginas": True,
    "formato_numeracion": "Página {pagina}",
    "mostrar_lineas_separadoras": True,
    "fuente_header": "Helvetica-Bold",
    "fuente_footer": "Helvetica",
    "tamano_fuente_header": 10,
    "tamano_fuente_footer": 8,
    "header_text_offset_x": 0,
    "footer_text_offset_x": 0,
    "agregar_portada": True,
    "agregar_indice": False,
    "header_offset": 35,
    "footer_offset": 25,
    "margen_x": 40,
    "logo_width": 80,
    "logo_height": 30,
    "titulo_portada": "Documentación WalkMe",
    "subtitulo_portada": "Documento generado desde Notion",
    "area_portada": "Uso interno",
    "mostrar_header_portada": False,
    "mostrar_footer_portada": False,
    "header_portada": "",
    "footer_portada": ""
}


PROFILE_KEYS = [
    "logo_izquierdo",
    "logo_central",
    "logo_derecho",
    "header",
    "footer",
    "version",
    "mostrar_logo",
    "mostrar_fecha",
    "numerar_paginas",
    "formato_numeracion",
    "mostrar_lineas_separadoras",
    "fuente_header",
    "fuente_footer",
    "tamano_fuente_header",
    "tamano_fuente_footer",
    "header_text_offset_x",
    "footer_text_offset_x",
    "agregar_portada",
    "agregar_indice",
    "header_offset",
    "footer_offset",
    "margen_x",
    "logo_width",
    "logo_height",
    "titulo_portada",
    "subtitulo_portada",
    "area_portada",
    "mostrar_header_portada",
    "mostrar_footer_portada",
    "header_portada",
    "footer_portada",
]


MOJIBAKE_REPLACEMENTS = {
    "P\u00c3\u0192\u00c2\u00a1gina": "Página",
    "\u00c3\u0192\u00c2\u00a1": "á",
    "\u00c3\u0192\u00c2\u00a9": "é",
    "\u00c3\u0192\u00c2\u00ad": "í",
    "\u00c3\u0192\u00c2\u00b3": "ó",
    "\u00c3\u0192\u00c2\u00ba": "ú",
    "\u00c3\u0192\u00c2\u00b1": "ñ",
    "P\u00c3\u00a1gina": "Página",
    "P\u00c3\u00a1g.": "Pág.",
    "Sin numeraci\u00c3\u00b3n": "Sin numeración",
    "Documentaci\u00c3\u00b3n": "Documentación",
    "Versi\u00c3\u00b3n": "Versión",
    "\u00c3\u0081rea": "Área",
    "\u00c3\u00a1": "á",
    "\u00c3\u00a9": "é",
    "\u00c3\u00ad": "í",
    "\u00c3\u00b3": "ó",
    "\u00c3\u00ba": "ú",
    "\u00c3\u00b1": "ñ",
    "\u00c3\u0081": "Á",
    "\u00c3\u0089": "É",
    "\u00c3\u008d": "Í",
    "\u00c3\u0093": "Ó",
    "\u00c3\u009a": "Ú",
    "\u00e2\u2020\u2019": "→",
    "\u00e2\u20ac\u201c\u00b6": "▶",
    "\u00e2\u20ac\u201c\u00bc": "▼",
    "\u00e2\u20ac\u00a2": "•",
}


def normalizar_texto_mojibake(valor):
    if not isinstance(valor, str):
        return valor

    for origen, destino in MOJIBAKE_REPLACEMENTS.items():
        valor = valor.replace(origen, destino)

    return valor


def normalizar_config(config):
    return {
        clave: normalizar_texto_mojibake(valor)
        for clave, valor in config.items()
    }


def cargar_config():
    if not os.path.exists(CONFIG_FILE):
        guardar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, "r", encoding="utf-8-sig") as file:
        config = json.load(file)

    final_config = DEFAULT_CONFIG.copy()
    final_config.update(config)

    return normalizar_config(final_config)


def guardar_config(config):
    config = normalizar_config(config)

    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)


def extraer_config_perfil(config):
    return {
        clave: config.get(clave, DEFAULT_CONFIG.get(clave))
        for clave in PROFILE_KEYS
    }


def cargar_perfiles():
    if not os.path.exists(PROFILES_FILE):
        perfiles = {
            "Predeterminado": extraer_config_perfil(cargar_config())
        }
        guardar_perfiles(perfiles)
        return perfiles

    with open(PROFILES_FILE, "r", encoding="utf-8-sig") as file:
        perfiles = json.load(file)

    if not isinstance(perfiles, dict) or not perfiles:
        perfiles = {
            "Predeterminado": extraer_config_perfil(cargar_config())
        }

    return {
        nombre: normalizar_config(perfil)
        for nombre, perfil in perfiles.items()
        if isinstance(perfil, dict)
    }


def guardar_perfiles(perfiles):
    perfiles_normalizados = {
        nombre: extraer_config_perfil(normalizar_config(perfil))
        for nombre, perfil in perfiles.items()
    }

    with open(PROFILES_FILE, "w", encoding="utf-8") as file:
        json.dump(perfiles_normalizados, file, indent=4, ensure_ascii=False)
