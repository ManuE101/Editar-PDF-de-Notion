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

    return secciones


def estimar_altura_bloque(bloque):
    """
    Estimación simple de altura.
    No dibuja el PDF; solo calcula si conviene dejar algo junto o moverlo.
    """

    if bloque.tipo == "heading":
        if bloque.nivel == 1:
            return 45
        if bloque.nivel == 2:
            return 36
        return 30

    if bloque.tipo == "paragraph":
        caracteres = len(bloque.texto)
        lineas = max(1, caracteres // 85 + 1)
        return lineas * 16 + 6

    if bloque.tipo == "bullet":
        caracteres = len(bloque.texto)
        lineas = max(1, caracteres // 80 + 1)
        return lineas * 15 + 4

    if bloque.tipo == "image":
        return 260

    return 20


def estimar_altura_seccion(seccion):
    return sum(estimar_altura_bloque(bloque) for bloque in seccion.bloques)


def dividir_en_paginas(documento, alto_util=680):
    """
    Convierte el documento en páginas aproximadas.
    Regla principal:
    - Una sección chica se mantiene junta.
    - Una sección grande puede partirse.
    - Nunca deja un heading solo al final de página.
    """

    secciones = agrupar_en_secciones(documento)

    paginas = []
    pagina_actual = PaginaLayout(numero=1)
    espacio_usado = 0

    for seccion in secciones:
        altura_seccion = estimar_altura_seccion(seccion)

        # Caso 1: la sección completa entra
        if espacio_usado + altura_seccion <= alto_util:
            pagina_actual.secciones.append(seccion)
            espacio_usado += altura_seccion
            continue

        # Caso 2: la sección no entra, pero es chica: mandarla entera a nueva página
        if altura_seccion <= alto_util:
            if pagina_actual.secciones:
                paginas.append(pagina_actual)

            pagina_actual = PaginaLayout(numero=len(paginas) + 1)
            pagina_actual.secciones.append(seccion)
            espacio_usado = altura_seccion
            continue

        # Caso 3: sección grande. Hay que partirla cuidadosamente.
        bloques_actuales = []

        for bloque in seccion.bloques:
            altura_bloque = estimar_altura_bloque(bloque)

            # Si el bloque no entra, cerramos la sección parcial y pasamos página
            if espacio_usado + altura_bloque > alto_util:
                if bloques_actuales:
                    pagina_actual.secciones.append(
                        Seccion(
                            titulo=seccion.titulo,
                            nivel=seccion.nivel,
                            bloques=bloques_actuales
                        )
                    )
                    bloques_actuales = []

                if pagina_actual.secciones:
                    paginas.append(pagina_actual)

                pagina_actual = PaginaLayout(numero=len(paginas) + 1)
                espacio_usado = 0

            bloques_actuales.append(bloque)
            espacio_usado += altura_bloque

        if bloques_actuales:
            pagina_actual.secciones.append(
                Seccion(
                    titulo=seccion.titulo,
                    nivel=seccion.nivel,
                    bloques=bloques_actuales
                )
            )

    if pagina_actual.secciones:
        paginas.append(pagina_actual)

    return paginas