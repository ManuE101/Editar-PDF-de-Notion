import os
from dataclasses import dataclass, field
from typing import List

from document_model import Bloque


@dataclass
class Seccion:
    titulo: str = ""
    nivel: int = 0
    bloques: List[Bloque] = field(default_factory=list)


@dataclass
class PaginaLayout:
    numero: int
    secciones: List[Seccion] = field(default_factory=list)


def agrupar_en_secciones(documento):
    secciones = []
    seccion_actual = None

    for bloque in documento.bloques:
        if bloque.tipo == "heading":
            if seccion_actual:
                secciones.append(seccion_actual)

            seccion_actual = Seccion(
                titulo=bloque.texto,
                nivel=bloque.nivel,
                bloques=[bloque]
            )
        else:
            if seccion_actual is None:
                seccion_actual = Seccion(
                    titulo="Inicio",
                    nivel=0,
                    bloques=[]
                )

            seccion_actual.bloques.append(bloque)

    if seccion_actual:
        secciones.append(seccion_actual)

    return unir_titulos_sueltos(secciones)


def seccion_solo_titulos(seccion):
    return bool(seccion.bloques) and all(
        bloque.tipo == "heading"
        for bloque in seccion.bloques
    )


def unir_titulos_sueltos(secciones):
    secciones_finales = []
    titulos_pendientes = []

    for seccion in secciones:
        if seccion_solo_titulos(seccion):
            titulos_pendientes.extend(seccion.bloques)
            continue

        if titulos_pendientes:
            seccion = Seccion(
                titulo=titulos_pendientes[0].texto,
                nivel=titulos_pendientes[0].nivel,
                bloques=titulos_pendientes + seccion.bloques
            )
            titulos_pendientes = []

        secciones_finales.append(seccion)

    if titulos_pendientes:
        secciones_finales.append(
            Seccion(
                titulo=titulos_pendientes[0].texto,
                nivel=titulos_pendientes[0].nivel,
                bloques=titulos_pendientes
            )
        )

    return secciones_finales


def estimar_altura_bloque(bloque):
    """
    Estimacion aproximada, alineada con smart_pdf_exporter_v2.draw_bloque.
    Se usa solo para decidir cortes antes de dibujar.
    """

    if bloque.tipo == "heading":
        if bloque.nivel == 1:
            return 45
        if bloque.nivel == 2:
            return 36
        return 30

    if bloque.tipo == "paragraph":
        caracteres = len(bloque.texto)
        lineas = max(1, caracteres // 95 + 1)
        return lineas * 15 + 7

    if bloque.tipo == "bullet":
        caracteres = len(bloque.texto)
        lineas = max(1, caracteres // 90 + 1)
        return lineas * 15 + 5

    if bloque.tipo == "image":
        if not bloque.imagen or not os.path.exists(bloque.imagen):
            return 0
        return 260

    return 20


def estimar_altura_seccion(seccion):
    return sum(estimar_altura_bloque(bloque) for bloque in seccion.bloques)


def dividir_en_paginas(documento, alto_util=720):
    """
    Convierte el documento en paginas aproximadas.

    La regla anterior mantenia cualquier seccion chica junta. Eso evitaba
    cortes internos, pero tambien podia dejar media pagina vacia. Ahora solo
    manda la seccion completa a la pagina siguiente cuando el espacio restante
    es realmente chico; si queda aire util, parte la seccion cuidando no dejar
    un titulo solo al final.
    """

    secciones = agrupar_en_secciones(documento)

    paginas = []
    pagina_actual = PaginaLayout(numero=1)
    espacio_usado = 0
    espacio_minimo_para_partir = 120

    def cerrar_pagina():
        nonlocal pagina_actual, espacio_usado

        if pagina_actual.secciones:
            paginas.append(pagina_actual)

        pagina_actual = PaginaLayout(numero=len(paginas) + 1)
        espacio_usado = 0

    def agregar_seccion_parcial(seccion, bloques):
        if not bloques:
            return

        pagina_actual.secciones.append(
            Seccion(
                titulo=seccion.titulo,
                nivel=seccion.nivel,
                bloques=bloques
            )
        )

    def partir_seccion(seccion):
        nonlocal espacio_usado

        bloques_actuales = []
        bloques = seccion.bloques

        for indice, bloque in enumerate(bloques):
            altura_bloque = estimar_altura_bloque(bloque)
            indice_siguiente_contenido = indice + 1
            while (
                indice_siguiente_contenido < len(bloques)
                and bloques[indice_siguiente_contenido].tipo == "heading"
            ):
                indice_siguiente_contenido += 1

            altura_siguiente = (
                estimar_altura_bloque(bloques[indice_siguiente_contenido])
                if bloque.tipo == "heading" and indice_siguiente_contenido < len(bloques)
                else 0
            )
            altura_titulos_encadenados = sum(
                estimar_altura_bloque(bloques[i])
                for i in range(indice + 1, indice_siguiente_contenido)
            )
            altura_minima_junta = (
                altura_bloque
                + altura_titulos_encadenados
                + min(altura_siguiente, 70)
            )

            if (
                bloque.tipo == "heading"
                and espacio_usado > 0
                and espacio_usado + altura_minima_junta > alto_util
            ):
                agregar_seccion_parcial(seccion, bloques_actuales)
                bloques_actuales = []
                cerrar_pagina()
            elif espacio_usado > 0 and espacio_usado + altura_bloque > alto_util:
                agregar_seccion_parcial(seccion, bloques_actuales)
                bloques_actuales = []
                cerrar_pagina()

            bloques_actuales.append(bloque)
            espacio_usado += altura_bloque

            if espacio_usado >= alto_util:
                agregar_seccion_parcial(seccion, bloques_actuales)
                bloques_actuales = []
                cerrar_pagina()

        agregar_seccion_parcial(seccion, bloques_actuales)

    for seccion in secciones:
        altura_seccion = estimar_altura_seccion(seccion)

        if espacio_usado + altura_seccion <= alto_util:
            pagina_actual.secciones.append(seccion)
            espacio_usado += altura_seccion
            continue

        espacio_restante = alto_util - espacio_usado
        if altura_seccion <= alto_util and espacio_restante < espacio_minimo_para_partir:
            cerrar_pagina()
            pagina_actual.secciones.append(seccion)
            espacio_usado = altura_seccion
            continue

        partir_seccion(seccion)

    if pagina_actual.secciones:
        paginas.append(pagina_actual)

    return paginas
