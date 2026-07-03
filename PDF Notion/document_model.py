from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Bloque:
    tipo: str
    texto: str = ""
    nivel: int = 0
    imagen: Optional[str] = None
    items: List[str] = field(default_factory=list)


@dataclass
class Documento:
    titulo: str
    bloques: List[Bloque] = field(default_factory=list)

    def agregar_bloque(self, bloque: Bloque):
        self.bloques.append(bloque)