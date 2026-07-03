import os
from bs4 import BeautifulSoup

from document_model import Documento, Bloque


def limpiar_texto(texto):
    return " ".join(texto.split()).strip()


def parsear_html_notion(contenido_html, html_principal):
    soup = BeautifulSoup(contenido_html, "lxml")

    titulo = soup.title.get_text(strip=True) if soup.title else "Documento Notion"
    documento = Documento(titulo=titulo)

    base_dir = os.path.dirname(html_principal)

    cuerpo = soup.body if soup.body else soup

    for elemento in cuerpo.find_all(["h1", "h2", "h3", "p", "li", "img"]):
        if elemento.name in ["h1", "h2", "h3"]:
            texto = limpiar_texto(elemento.get_text())
            if texto:
                nivel = int(elemento.name.replace("h", ""))
                documento.agregar_bloque(Bloque(tipo="heading", texto=texto, nivel=nivel))

        elif elemento.name == "p":
            texto = limpiar_texto(elemento.get_text())
            if texto:
                documento.agregar_bloque(Bloque(tipo="paragraph", texto=texto))

        elif elemento.name == "li":
            texto = limpiar_texto(elemento.get_text())
            if texto:
                documento.agregar_bloque(Bloque(tipo="bullet", texto=texto))

        elif elemento.name == "img":
            src = elemento.get("src")

            if src and not src.startswith("http"):
                ruta_imagen = os.path.join(base_dir, src)

                if os.path.exists(ruta_imagen):
                    documento.agregar_bloque(Bloque(tipo="image", imagen=ruta_imagen))

    return documento