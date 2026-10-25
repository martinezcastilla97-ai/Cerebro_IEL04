r"""ELEMENTOS DEL TEMARIO EN LATEX -- las ecuaciones, tablas, graficas y diagramas del .tex del temario, listos para una diapositiva.

TEMARIO escribe en paralelo al .md un .tex (temario_latex.py) donde cada tabla, grafica y diagrama ya es codigo LaTeX: las graficas
en pgfplots con los puntos de su especificacion, los diagramas en TikZ con su disposicion, las tablas con su encabezado oscuro y las
ecuaciones con la tipografia corregida. PRESENTACIONES no los vuelve a pedir al modelo ni los redibuja: los toma de ahi.

    leer(ruta_tex)          los elementos del .tex del temario, cada uno con su numero (el mismo del .md: «Figura 3», «Tabla 2»;
                            las ecuaciones, en el orden en que aparecen) y el bloque del indice temporizado al que pertenece
    Elemento.diapositivas() el LaTeX para Beamer: la figura dentro de un adjustbox que la acota al area util, la tabla partida en
                            trozos que caben (repitiendo el encabezado) y la ecuacion sin numero
    marcar_elementos(md)    el texto del temario para el modelo, con cada figura, tabla y ecuacion marcada con la orden que la incluye
                            (\elementoTemario{figura}{3}): el modelo decide donde va, el codigo pone el LaTeX
    sustituir(cuerpo, ...)  pone en el cuerpo de una diapositiva el LaTeX de cada \elementoTemario

Solo se leen las construcciones que escribe temario_latex.py (los comentarios `% --- Figura N` / `% --- Tabla N` y los entornos
figure, xltabular y equation). Lo que no se reconoce se omite, y el .tex final de la presentacion pasa igual por la verificacion
estatica (latex_seguro.verificar_latex): un .tex del temario editado a mano no puede colar nada que lea o escriba archivos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

MAX_FILAS_TABLA = 8               # filas de datos por diapositiva (con su encabezado)
ALTO_FIGURA = "5.6cm"             # alto maximo de una figura en el area util (6,6 cm, menos el pie de la figura)
ALTO_FIGURA_CON_TEXTO = "4.4cm"   # si la diapositiva lleva tambien texto
ORDEN = re.compile(r"\\elementoTemario\{(figura|tabla|ecuacion)\}\{(\d+)\}")
CLASES = ("figura", "tabla", "ecuacion")


@dataclass
class Elemento:
    clase: str                    # figura | tabla | ecuacion
    numero: int
    bloque: int | None            # None: fuera de todo bloque (apertura)
    leyenda: str = ""             # LaTeX (ya escapado por temario_latex)
    dibujo: str = ""              # figura: el tikzpicture (o el adjustbox que lo envuelve)
    tipo: str = ""                # figura: «gráfica» | «diagrama»
    columnas: str = ""            # tabla: especificacion de columnas para Beamer
    encabezado: str = ""          # tabla: la fila del encabezado
    filas: list[str] = field(default_factory=list)   # tabla: las filas de datos (cada una termina en \\)
    formula: str = ""             # ecuacion: el contenido de equation

    @property
    def clave(self) -> str:
        return f"{self.clase}-{self.numero}"

    def describir(self) -> str:
        """Una linea para el modelo: que es y con que orden se incluye."""
        if self.clase == "figura":
            que = f"FIGURA {self.numero} ({self.tipo}): {_plano(self.leyenda)}"
        elif self.clase == "tabla":
            que = f"TABLA {self.numero} ({len(self.filas)} filas): {_plano(self.leyenda)}"
        else:
            que = f"ECUACIÓN {self.numero}: ${_recorte(self.formula, 160)}$"
        return f"{que} — inclúyela con \\elementoTemario{{{self.clase}}}{{{self.numero}}}"

    def latex(self, con_texto: bool = False, trozo: int = 0) -> str:
        """El LaTeX del elemento para el cuerpo de una diapositiva (una tabla, el trozo `trozo`)."""
        if self.clase == "ecuacion":
            return "{\\large\n\\begin{equation*}\n  " + self.formula.replace("\n", "\n  ") + "\n\\end{equation*}\n}"
        alto = ALTO_FIGURA_CON_TEXTO if con_texto else ALTO_FIGURA
        if self.clase == "figura":
            dibujo = re.sub(r"\\begin\{adjustbox\}\{max width=\\linewidth\}", "", self.dibujo, count=1)
            dibujo = re.sub(r"\\end\{adjustbox\}\s*$", "", dibujo.rstrip())
            return ("\\begin{center}\n\\begin{adjustbox}{max width=\\linewidth, max totalheight=" + alto + "}\n" + dibujo.strip()
                    + "\n\\end{adjustbox}\n\n{\\scriptsize\\textbf{Figura " + str(self.numero) + ".} " + self.leyenda + "\\par}\n\\end{center}")
        trozos = self.trozos()
        filas = trozos[min(trozo, len(trozos) - 1)]
        sigue = len(trozos) > 1
        pie = f" ({trozo + 1}/{len(trozos)})" if sigue else ""
        columnas = len(re.findall(r"(?<!\\)&", self.encabezado)) + 1
        letra = "\\small" if len(filas) <= 6 and columnas <= 4 and not con_texto else "\\scriptsize"   # una tabla corta se lee mejor mas grande
        return ("\\begin{center}\n{\\scriptsize\\textbf{Tabla " + str(self.numero) + ".} " + self.leyenda + pie + "\\par}\n"
                "\\vspace{1mm}\n" + letra + "\n\\renewcommand{\\arraystretch}{1.35}\n"
                "\\begin{adjustbox}{max width=\\linewidth, max totalheight=" + alto + "}\n"
                "\\begin{tabular}{" + self.columnas + "}\n" + self.encabezado + "\n" + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}\n"
                "\\end{adjustbox}\n\\end{center}")

    def trozos(self) -> list[list[str]]:
        """Las filas de la tabla en grupos de MAX_FILAS_TABLA (un \\midrule suelto no cuenta como fila)."""
        grupos: list[list[str]] = [[]]
        for fila in self.filas:
            if fila.strip() != r"\midrule" and sum(1 for f in grupos[-1] if f.strip() != r"\midrule") >= MAX_FILAS_TABLA:
                grupos.append([])
            grupos[-1].append(fila)
        return [g for g in grupos if g] or [[]]


def _plano(latex: str) -> str:
    """El texto de una leyenda sin comandos (para describirla al modelo)."""
    texto = re.sub(r"\\[A-Za-z]+\*?", " ", latex)
    return " ".join(re.sub(r"[{}]", "", texto).split())


def _recorte(texto: str, maximo: int) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= maximo else texto[:maximo - 1] + "…"


def _argumento(texto: str, inicio: int) -> tuple[str, int]:
    """(contenido, fin) del grupo {...} que empieza en `inicio` (llaves anidadas; `\\{` no cuenta)."""
    if inicio >= len(texto) or texto[inicio] != "{":
        return "", inicio
    nivel, i = 0, inicio
    while i < len(texto):
        ch = texto[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            nivel += 1
        elif ch == "}":
            nivel -= 1
            if nivel == 0:
                return texto[inicio + 1:i], i + 1
        i += 1
    return texto[inicio + 1:], len(texto)


_SECCION = re.compile(r"^\\(section|subsection|subsubsection)\*?\{")
_NIVEL = {"section": 1, "subsection": 2, "subsubsection": 3}
_BLOQUE = re.compile(r"\(Bloque (\d+)\)\s*$")
_COLUMNA_X = re.compile(r">\{\\hsize=([\d.]+)\\hsize\\linewidth=\\hsize\\(raggedright|raggedleft)\\arraybackslash\}X")


def _columnas_beamer(especificacion: str, n_celdas: int) -> str:
    r"""Las columnas X con `\hsize` de temario_latex como columnas p{} de ancho fijo (sin asignaciones de TeX en el cuerpo): la
    misma proporcion, y el adjustbox acota el conjunto al ancho de la diapositiva. Una especificacion que no es la de temario_latex
    (el .tex se edito a mano) pasa a columnas `l`, tantas como celdas tiene el encabezado."""
    columnas = _COLUMNA_X.findall(especificacion)
    if len(columnas) != n_celdas:
        return "l" * max(1, n_celdas)
    n = len(columnas)
    util = max(0.5, 1 - 0.03 * n)
    return "".join(f">{{\\{alineacion}\\arraybackslash}}p{{{float(h) / n * util:.3f}\\linewidth}}" for h, alineacion in columnas)


def leer(ruta_tex: Path) -> list[Elemento]:
    """Los elementos del .tex del temario (lista vacia si no existe o no se reconoce nada)."""
    try:
        tex = ruta_tex.read_text(encoding="utf-8")
    except OSError:
        return []
    _, _, cuerpo = tex.partition("\\begin{document}")
    lineas = cuerpo.splitlines()
    elementos: list[Elemento] = []
    bloque, nivel_bloque = None, 0
    ecuaciones = 0
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        s = _SECCION.match(linea)
        if s:
            titulo, _ = _argumento(linea, s.end() - 1)
            nivel = _NIVEL[s.group(1)]
            b = _BLOQUE.search(titulo)
            if b:
                bloque, nivel_bloque = int(b.group(1)), nivel
            elif bloque is not None and nivel <= nivel_bloque:
                bloque = None
            i += 1
            continue
        m = re.match(r"^% --- (Figura|Tabla) (\d+):", linea)
        if m and i + 1 < len(lineas):
            fin = next((j for j in range(i + 1, len(lineas)) if lineas[j].startswith("\\end{figure}" if m.group(1) == "Figura" else "\\end{xltabular}")), None)
            if fin is None:
                i += 1
                continue
            bloque_texto = "\n".join(lineas[i + 1:fin + 1])
            if m.group(1) == "Figura":
                e = _figura(int(m.group(2)), bloque, bloque_texto)
            else:
                e = _tabla(int(m.group(2)), bloque, bloque_texto)
            if e:
                elementos.append(e)
            i = fin + 1
            continue
        if linea.startswith("\\begin{equation}"):
            fin = next((j for j in range(i + 1, len(lineas)) if lineas[j].startswith("\\end{equation}")), None)
            if fin is None:
                i += 1
                continue
            ecuaciones += 1
            formula = "\n".join(l[2:] if l.startswith("  ") else l for l in lineas[i + 1:fin]).strip()
            elementos.append(Elemento("ecuacion", ecuaciones, bloque, formula=formula))
            i = fin + 1
            continue
        i += 1
    return elementos


def _figura(numero: int, bloque: int | None, texto: str) -> Elemento | None:
    lineas = [l[2:] if l.startswith("  ") else l for l in texto.splitlines()]
    cuerpo = "\n".join(lineas)
    c = cuerpo.rfind("\\caption{")
    if c < 0:
        return None
    leyenda, _ = _argumento(cuerpo, c + len("\\caption"))
    dibujo = cuerpo[:c]
    dibujo = re.sub(r"^\\begin\{figure\}\[H\]\s*", "", dibujo.strip())
    dibujo = re.sub(r"^\\centering\s*", "", dibujo.strip())
    dibujo = re.sub(r"(?m)^[ \t]*%.*\n?", "", dibujo)            # los comentarios de temario_latex no van a la presentacion
    dibujo = re.sub(r"\s+% [^\n]*$", "", dibujo, flags=re.M)
    if "\\begin{tikzpicture}" not in dibujo:
        return None
    tipo = "gráfica" if "\\begin{axis}" in dibujo else "diagrama"
    return Elemento("figura", numero, bloque, leyenda=leyenda.strip(), dibujo=dibujo.strip(), tipo=tipo)


def _tabla(numero: int, bloque: int | None, texto: str) -> Elemento | None:
    lineas = texto.splitlines()
    m = re.match(r"^\\begin\{xltabular\}\{\\linewidth\}\{(.*)\}\s*$", lineas[0]) if lineas else None
    if not m:
        return None
    leyenda = ""
    encabezado = ""
    filas: list[str] = []
    despues_del_pie = False
    for linea in lineas[1:]:
        l = linea.strip()
        if l.startswith("\\caption{"):
            leyenda, _ = _argumento(l, len("\\caption"))
        elif l.startswith("\\rowcolor{iubnavy}") and not encabezado:
            encabezado = l
        elif l == "\\endlastfoot":
            despues_del_pie = True
        elif despues_del_pie and l and not l.startswith("\\end{xltabular}"):
            filas.append(l)
    if not encabezado or not filas:
        return None
    celdas = len(re.findall(r"(?<!\\)&", encabezado)) + 1
    return Elemento("tabla", numero, bloque, leyenda=leyenda.strip(), columnas=_columnas_beamer(m.group(1), celdas), encabezado=encabezado, filas=filas)


# ---------------------------------------------------------------------------
# El texto que ve el modelo y la sustitucion en las diapositivas
# ---------------------------------------------------------------------------

_FIGURA_MD = re.compile(r"!\[Figura (\d+)\.[^\]]*\]\(figuras/[^)\s]+\)(?:\s*\n\s*\*Figura \d+\.[^\n]*\*)?")
_TABLA_MD = re.compile(r"^\*\*Tabla (\d+)\.\*\*[^\n]*$", re.M)
_ECUACION_MD = re.compile(r"^\$\$\s*\n(.*?)\n\$\$\s*$", re.M | re.S)


def marcar_elementos(md: str, elementos: list[Elemento], primera_ecuacion: int) -> tuple[str, int]:
    """(el texto para el modelo, cuantas ecuaciones tenia): cada figura, tabla y ecuacion del Markdown, con la linea que dice que es
    y con que orden se incluye. Las ecuaciones se numeran en orden desde `primera_ecuacion` (las del .tex van en el mismo orden).
    Las tablas y ecuaciones conservan su contenido (el modelo necesita sus datos para comentarlos)."""
    por_clave = {e.clave: e for e in elementos}

    def figura(m: re.Match) -> str:
        e = por_clave.get(f"figura-{m.group(1)}")
        return f"[{e.describir()}]" if e else m.group(0)

    def tabla(m: re.Match) -> str:
        e = por_clave.get(f"tabla-{m.group(1)}")
        return f"{m.group(0)}\n[{e.describir()}; no la copies a mano]" if e else m.group(0)

    contador = [primera_ecuacion - 1]

    def ecuacion(m: re.Match) -> str:
        contador[0] += 1
        e = por_clave.get(f"ecuacion-{contador[0]}")
        return f"{m.group(0)}\n[{e.describir()}]" if e else m.group(0)

    texto = _FIGURA_MD.sub(figura, md)
    texto = _TABLA_MD.sub(tabla, texto)
    texto = _ECUACION_MD.sub(ecuacion, texto)
    return texto, contador[0] - (primera_ecuacion - 1)


def referencias(cuerpo: str) -> list[str]:
    """Las claves (`figura-3`) que un cuerpo de diapositiva incluye con \\elementoTemario."""
    return [f"{c}-{n}" for c, n in ORDEN.findall(cuerpo)]


def sustituir(cuerpo: str, elementos: dict[str, Elemento]) -> str:
    """El cuerpo con el LaTeX de cada \\elementoTemario. Si la diapositiva lleva mas texto, la figura o la tabla se acotan a un alto
    menor para que quepan juntos. Una orden a un elemento que no existe se deja: el preambulo la define como un aviso visible."""
    otro_texto = bool(ORDEN.sub("", cuerpo).strip())        # una sola linea de texto mas ya no cabe con la figura a todo lo alto

    def poner(m: re.Match) -> str:
        e = elementos.get(f"{m.group(1)}-{m.group(2)}")
        return e.latex(con_texto=otro_texto) if e else m.group(0)

    return ORDEN.sub(poner, cuerpo)
