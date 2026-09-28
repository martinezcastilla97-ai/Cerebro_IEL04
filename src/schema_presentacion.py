r"""Esquema de PRESENTACIONES (diseno 5): lo que el LLM devuelve por cada PARTE de un temario (la apertura de la sesion y cada
bloque del indice temporizado). Son DIAPOSITIVAS en LaTeX: un titulo y el cuerpo del frame (TikZ, pgfplots, tcolorbox, tablas),
como en las presentaciones de ejemplo del docente. El preambulo, la portada, la ruta de la sesion, los separadores de bloque, las
referencias y el cierre los escribe el codigo (diseno_iub.py); el cuerpo que escribe el modelo pasa por latex_seguro.verificar_cuerpo
(lista de comandos permitidos) antes de llegar al .tex.

    DiapositivasParte   de 1 a MAX_DIAPOSITIVAS_PARTE diapositivas
    DiapositivaLatex    titulo (texto o LaTeX de una linea, sin \begin{frame}) y cuerpo (el interior del frame)

Los limites se validan aqui con un mensaje claro que vuelve al modelo (no con `Field(max_length=...)`: algunas APIs rechazan esas
restricciones en el esquema). Lo que depende del LaTeX (los comandos admitidos) lo valida presentaciones.py con latex_seguro.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, model_validator

MAX_TITULO = 64                   # visible: el titulo va en la franja superior, en una linea
MIN_CUERPO = 20
MAX_DIAPOSITIVAS_PARTE = 6


def _largo(texto: str) -> int:
    """Lo que se ve de un titulo: sin los comandos de LaTeX ni sus llaves, y una formula en linea cuenta la mitad de lo que mide."""
    visible = re.sub(r"\$([^$]*)\$", lambda m: "x" * max(1, len(m.group(1)) // 2), texto)
    visible = re.sub(r"\\[A-Za-z]+\*?|[{}]|\*\*|`", "", visible)
    return len(visible.strip())


class DiapositivaLatex(BaseModel):
    titulo: str
    cuerpo: str

    @model_validator(mode="after")
    def coherente(self):
        self.titulo, self.cuerpo = self.titulo.strip(), self.cuerpo.strip()
        if not self.titulo:
            raise ValueError("una diapositiva no tiene `titulo`")
        if _largo(self.titulo) > MAX_TITULO:
            raise ValueError(f"el título «{self.titulo[:50]}…» mide {_largo(self.titulo)} caracteres visibles: el máximo es {MAX_TITULO}")
        if len(self.cuerpo) < MIN_CUERPO:
            raise ValueError(f"la diapositiva «{self.titulo[:50]}» no tiene cuerpo")
        sin_codigo = re.sub(r"\\begin\{codebox\}.*?\\end\{codebox\}", "", self.cuerpo, flags=re.S)     # el codigo no se ejecuta
        if re.search(r"\\(?:begin|end)\s*\{frame\}|\\frametitle", sin_codigo):
            raise ValueError(f"«{self.titulo[:50]}»: el `cuerpo` es solo el interior de la diapositiva, sin \\begin{{frame}}, \\end{{frame}} ni \\frametitle")
        return self


class DiapositivasParte(BaseModel):
    diapositivas: list[DiapositivaLatex]

    @model_validator(mode="after")
    def cuantas(self):
        if not 1 <= len(self.diapositivas) <= MAX_DIAPOSITIVAS_PARTE:
            raise ValueError(f"se esperan de 1 a {MAX_DIAPOSITIVAS_PARTE} diapositivas por parte y hay {len(self.diapositivas)}")
        return self
