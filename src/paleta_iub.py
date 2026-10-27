"""La paleta del Manual de Identidad Visual IUB 2025 (manualdeidentidadiub2025_IUB.pdf, 1.3 y 1.4), en un solo lugar: los colores de
las tablas, las graficas, los diagramas de flujo y los circuitos de las presentaciones (diseno_iub.py), de las guias de laboratorio
(guia_laboratorio.py) y de la version LaTeX del temario (temario_latex.py), cuyos elementos van tal cual a las presentaciones.

    principal:       #FFDF2D (amarillo), #121023 (azul oscuro) y #FFFFFF (blanco)
    complementarios: #00ADE7 (azul), #E39037 (naranja) y #3B9C6D (verde)

Los demas nombres no son colores nuevos: son tintes de un color del manual (mezclas con blanco, `\\colorlet{iubgris}{iubnavy!18}`),
para fondos suaves, rejillas y rotulos. El LaTeX que escribe el modelo (las diapositivas, los circuitos de las guias) solo puede usar
estos nombres, `white` y sus mezclas (latex_seguro: la lista de colores y colores_fuera_de_paleta).
"""

from __future__ import annotations

MANUAL = {"iubnavy": "121023", "iubyellow": "FFDF2D", "iubwhite": "FFFFFF",
          "iubblue": "00ADE7", "iuborange": "E39037", "iubgreen": "3B9C6D"}
# Tintes de los colores del manual (xcolor: `color!N` = N % del color y el resto blanco)
TINTES = {
    "iubgris": "iubnavy!18",            # rejillas y bordes suaves
    "iubgrisoscuro": "iubnavy!60",      # rotulos secundarios y lineas de referencia
    "iubfondoazul": "iubblue!8",        # fondo de las cajas de un diagrama
    "iubfondonaranja": "iuborange!10",  # fondo de las decisiones y de las notas
    "iubfondoverde": "iubgreen!9",      # fondo de los terminales
    "iubfondogris": "iubnavy!5",        # filas alternas de las tablas
    "iubpurple": "iubnavy!45",          # nombre heredado (era un morado que no es del manual, en los .tex de temarios anteriores): hoy un tinte de #121023
}
NOMBRES = frozenset(MANUAL) | frozenset(TINTES)
# El orden de las series de una grafica: los complementarios, el azul oscuro y el amarillo
SERIES = ["iubblue", "iuborange", "iubgreen", "iubnavy", "iubyellow"]


def definiciones() -> str:
    """Las definiciones de la paleta para un preambulo LaTeX (xcolor): los colores del manual y sus tintes."""
    return "\n".join([*(rf"\definecolor{{{n}}}{{HTML}}{{{h}}}" for n, h in MANUAL.items()),
                      *(rf"\colorlet{{{n}}}{{{v}}}" for n, v in TINTES.items())])


def ciclo_pgfplots() -> str:
    """El ciclo de colores de pgfplots con la paleta: una serie sin color explicito sale en un color del manual, no en los de pgfplots."""
    marcas = ["*", "square*", "triangle*", "diamond*", "pentagon*"]
    return r"\pgfplotsset{cycle list={" + ",".join(f"{{{c}, mark={m}}}" for c, m in zip(SERIES, marcas)) + "}}"
