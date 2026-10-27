r"""TEMARIO en LaTeX -- la misma sesion que el .md, escrita como documento LaTeX (article, pdfLaTeX) en paralelo.

TEMARIO escribe dos archivos con el mismo contenido: generacion/temarios/{codigo}-semanaNN.md (para Obsidian) y
generacion/temarios/{codigo}-semanaNN.tex (para imprimir, compartir o subir a Overleaf). El .tex NO se convierte desde el
Markdown: sale de los mismos datos que el .md (el plan, los bloques de cada unidad y el cierre), asi que lleva todo lo que
el .md tiene y en el mismo orden, con la misma numeracion de secciones, tablas, figuras y listados. Sin LLM: es otra forma
de escribir lo que el modelo ya redacto.

    tablas     xltabular + booktabs, encabezado oscuro, se parten entre paginas repitiendo el encabezado
    graficas   pgfplots, con los puntos calculados de la MISMA especificacion que dibuja el PNG (figuras.puntos_de): nunca
               se reescribe la formula en la sintaxis de pgfplots ni se inventa un punto
    diagramas  TikZ, con la MISMA disposicion que el PNG (figuras._mejor_disposicion): cada nodo en su sitio, con su forma
    codigo     listings (con pdfLaTeX no admite Unicode: el codigo se translitera, latex_seguro.ascii_codigo)
    texto      latex_seguro.Conversor: los especiales se escapan, y en las formulas solo se admiten comandos matematicos
               conocidos (lo demas sale como texto, con aviso)

Buenas practicas de tipografia (skill «experto-en-latex»), aplicadas sin cambiar el sentido de lo que el modelo escribio:
    formulas   una ecuacion de varias lineas va en `aligned` (alineada en el `&`) o `gathered`, dentro de `equation` (un solo
               numero, como en el .md); los subindices descriptivos (`P_{out}`, `V_{max}`) van en redonda (`\mathrm`); las
               funciones escritas sin barra (`sin`, `ln`) pasan a `\sin`, `\ln`; una palabra suelta dentro de una formula
               (`Potencia`) va en `\text{}` y no como un producto de variables en cursiva (pulir_formula)
    tablas     sin lineas verticales, el ancho de cada columna segun lo que lleva y las columnas numericas alineadas a la derecha
    codigo     el LaTeX que se escribe va comentado e indentado (cada tabla, grafica, diagrama y listado lleva su comentario)
    errores    antes de escribirlo se revisa el balance de entornos y llaves (revisar_balance); con `temario.py --compilar` se
               compila de verdad con pdfLaTeX (compilar) y cada error o linea que se sale queda como aviso del temario

El documento es autocontenido (sin imagenes ni archivos externos) y usa solo paquetes estandar de TeX Live, MiKTeX y Overleaf.
Antes de escribirlo se comprueba que el cuerpo no tenga primitivas que lean o escriban archivos (latex_seguro.primitivas_peligrosas):
el cuerpo lo arma este modulo y todo lo que viene del modelo pasa por el Conversor, asi que no deberia haber ninguna.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import figuras
import latex_seguro as ls
import paleta_iub
from schema_temario import Bloque, TipoBloque, celdas_de_tabla

VERSION = 2                 # version del formato del .tex (campo `latex_formato` del temario)
INSTITUCION = "Institución Universitaria de Barranquilla"
MARCA = "IUB"
COLORES_SERIE = paleta_iub.SERIES        # los colores (Manual de Identidad IUB y sus tintes) los define paleta_iub
ALTO_GRAFICA = "6.2cm"
CARACTERES_POR_RENGLON_CATEGORIA = 13      # cuantos caben en una linea de la etiqueta de una categoria (text width=2.4cm, \small)

PREAMBULO = r"""% =====================================================================
%  Temario generado por TEMARIO (src/temario.py + src/temario_latex.py), sin LLM,
%  a partir de los mismos datos que el .md. Compilar con pdfLaTeX (dos pasadas).
% =====================================================================
\documentclass[11pt,letterpaper]{article}

% ---------------------------------------------------------------------
%  Codificacion, idioma y tipografia
% ---------------------------------------------------------------------
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot,es-noshorthands,es-tabla]{babel}
\usepackage{lmodern}
\usepackage{textcomp}
\usepackage[margin=2.3cm,headheight=14pt]{geometry}

% ---------------------------------------------------------------------
%  Matematicas y unidades del SI
% ---------------------------------------------------------------------
\usepackage{amsmath,amssymb,mathtools}
\usepackage{siunitx}
\sisetup{output-decimal-marker={.}, per-mode=symbol}

% ---------------------------------------------------------------------
%  Tablas profesionales (sin lineas verticales) y flotantes
% ---------------------------------------------------------------------
\usepackage[table]{xcolor}
\usepackage{booktabs,array,multirow,tabularx,xltabular}
\usepackage{graphicx,float}
\usepackage[font=small,labelfont={bf,color=iubnavy},labelsep=period]{caption}

% ---------------------------------------------------------------------
%  Listas, cajas, graficas, diagramas y codigo
% ---------------------------------------------------------------------
\usepackage{enumitem}
\usepackage{adjustbox}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage[most]{tcolorbox}
\usepackage{listings}

% ---------------------------------------------------------------------
%  Encabezados de pagina y enlaces (hyperref, siempre el ultimo)
% ---------------------------------------------------------------------
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}

% ---------------------------------------------------------------------
%  Paleta institucional IUB (Manual de Identidad Visual 2025)
% ---------------------------------------------------------------------
<<COLORES>>

% ---------------------------------------------------------------------
%  Formato general
% ---------------------------------------------------------------------
\setcounter{secnumdepth}{3}
\setlength{\parskip}{0.45em}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.25}
\setlist{itemsep=0.15em,topsep=0.3em}
\setlist[itemize]{label=\textcolor{iubblue}{\small$\blacktriangleright$}}

% ---------------------------------------------------------------------
%  Encabezado y pie de pagina
% ---------------------------------------------------------------------
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.6pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{iubnavy}\leaders\hrule height \headrulewidth\hfill}}
\fancyhead[L]{\small\textcolor{iubnavy}{\textbf{<<MARCA>>}\quad <<ENCABEZADO>>}}
\fancyhead[R]{\small\textcolor{iubnavy}{Semana <<SEMANA>> de <<TOTAL>>}}
\fancyfoot[C]{\small\textcolor{iubnavy}{\thepage}}

% ---------------------------------------------------------------------
%  Codigo (listings: el codigo va transliterado a ASCII)
% ---------------------------------------------------------------------
\lstset{basicstyle=\ttfamily\small, breaklines=true, columns=fullflexible, keepspaces=true, frame=single,
  rulecolor=\color{iubgris}, backgroundcolor=\color{iubfondogris}, numbers=left, numberstyle=\tiny\color{iubgrisoscuro},
  keywordstyle=\color{iubblue}\bfseries, commentstyle=\color{iubgreen}\itshape, stringstyle=\color{iuborange},
  showstringspaces=false, captionpos=t, aboveskip=0.8em, belowskip=0.8em}
\renewcommand{\lstlistingname}{Listado}

% ---------------------------------------------------------------------
%  Cajas: cabecera, notas, alineacion con el RA y cita actitudinal
% ---------------------------------------------------------------------
\newtcolorbox{cabecera}{enhanced, colback=iubnavy, colframe=iubnavy, coltext=white, arc=2pt, boxrule=0pt,
  left=12pt, right=12pt, top=10pt, bottom=10pt, borderline north={3pt}{0pt}{iubyellow}}
\newtcolorbox{nota}[1]{enhanced, colback=iubfondonaranja, colframe=iuborange, arc=2pt, boxrule=0.6pt, leftrule=3pt,
  fonttitle=\bfseries\small, coltitle=iuborange, colbacktitle=iubfondonaranja, title={#1}, attach title to upper={\ }}
\newtcolorbox{alineacion}{enhanced, colback=iubfondoazul, colframe=iubblue, arc=2pt, boxrule=0.6pt, leftrule=3pt}
\newtcolorbox{cita}{enhanced, colback=iubnavy, colframe=iubnavy, coltext=white, arc=2pt, boxrule=0pt, leftrule=4pt,
  borderline west={4pt}{0pt}{iubyellow}, fontupper=\itshape}

% ---------------------------------------------------------------------
%  Estilos de los diagramas (TikZ) y de las graficas (pgfplots)
% ---------------------------------------------------------------------
\tikzset{
  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt},
  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt},
  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt},
  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt},
  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},
  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},
}
\pgfplotsset{iubejes/.style={width=0.95\linewidth, height=<<ALTO>>, grid=major, grid style={iubgris}, axis lines*=left,
  axis line style={iubnavy}, tick label style={font=\small}, label style={font=\small}, title style={font=\bfseries\small},
  legend cell align=left, legend style={draw=none, fill=none, font=\small, anchor=north, legend columns=-1,
  /tikz/every even column/.append style={column sep=8pt}}, unbounded coords=jump}}

\hypersetup{pdftitle={<<TITULO_PDF>>}, pdfauthor={<<INSTITUCION>>}}
"""


# ---------------------------------------------------------------------------
# Formulas: tipografia correcta sin cambiar su sentido
# ---------------------------------------------------------------------------

# comandos cuyo argumento es texto o un nombre (no se toca lo que va dentro)
_TEXTUALES = frozenset("""text textrm textit textbf textsf texttt textnormal textup mbox mathrm mathbf mathit mathsf mathtt
    mathcal mathbb mathfrak mathscr boldsymbol operatorname unit si SI qty num ang begin end""".split())
# subindices de dos letras que son abreviaturas (los de tres o mas letras siempre lo son: out, max, ref, rms...)
_SUBINDICES_CORTOS = frozenset("in eq th ac dc ef av pk pp ss cc op on dd ce be bc oc sc ca".split())
_FUNCIONES = ("arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp",
              "lim", "max", "min", "det", "arg")
_LETRA = "A-Za-zÁÉÍÓÚáéíóúÑñÜü"
_PROTEGIDO_INI, _PROTEGIDO_FIN = "\ue020", "\ue021"


def _proteger(tex: str) -> tuple[str, list[str]]:
    r"""Aparta los comandos con un nombre de entorno o texto como argumento (`\text{...}`, `\mathrm{...}`, `\begin{aligned}`...),
    con su argumento entero (llaves anidadas incluidas), para no tocar su contenido."""
    guardados: list[str] = []
    salida, i = [], 0
    patron = re.compile(r"\\([A-Za-z]+)\*?\s*(?:\[[^\]]*\]\s*)?\{")
    while i < len(tex):
        m = patron.match(tex, i) if tex[i] == "\\" else None
        if m and m.group(1) in _TEXTUALES:
            nivel, j = 1, m.end()
            while j < len(tex) and nivel:
                if tex[j] == "\\":
                    j += 2
                    continue
                nivel += {"{": 1, "}": -1}.get(tex[j], 0)
                j += 1
            guardados.append(tex[i:j])
            salida.append(f"{_PROTEGIDO_INI}{len(guardados) - 1}{_PROTEGIDO_FIN}")
            i = j
            continue
        if tex[i] == "\\" and i + 1 < len(tex):              # cualquier otro comando: pasa tal cual (no es una palabra)
            fin = re.match(r"\\(?:[A-Za-z]+|.)", tex[i:]).end()
            salida.append(tex[i:i + fin])
            i += fin
            continue
        salida.append(tex[i])
        i += 1
    return "".join(salida), guardados


def _restaurar(tex: str, guardados: list[str]) -> str:
    return re.sub(f"{_PROTEGIDO_INI}(\\d+){_PROTEGIDO_FIN}", lambda m: guardados[int(m.group(1))], tex)


def pulir_formula(tex: str) -> str:
    r"""La formula con la tipografia de un texto cientifico: subindices descriptivos en redonda (`P_{out}` -> `P_{\mathrm{out}}`),
    funciones con su comando (`sin(x)` -> `\sin(x)`) y palabras sueltas en `\text{}` (`Potencia de salida` no es un producto de
    variables). Solo cambia la forma: los comandos, `\text{}` y los entornos se respetan tal cual."""
    tex, guardados = _proteger(tex)

    def subindice(m: re.Match) -> str:
        palabra = m.group(2)
        if len(palabra) >= 3 or palabra.lower() in _SUBINDICES_CORTOS:
            guardados.append(r"\mathrm{" + palabra + "}")
            return f"{m.group(1)}{{{_PROTEGIDO_INI}{len(guardados) - 1}{_PROTEGIDO_FIN}}}"
        return m.group(0)

    tex = re.sub(r"(_)\{([A-Za-z]{2,})\}", subindice, tex)
    # en lo que queda, una barra solo puede ser la de un comando: el lookbehind excluye las letras de su nombre
    tex = re.sub(r"(?<![\\A-Za-z])(" + "|".join(_FUNCIONES) + r")(?![A-Za-z])", r"\\\1", tex)

    def palabra(m: re.Match) -> str:
        guardados.append(r"\text{" + m.group(0) + "}")
        return f"{_PROTEGIDO_INI}{len(guardados) - 1}{_PROTEGIDO_FIN}"

    tex = re.sub(rf"(?<![\\{_LETRA}])[{_LETRA}]{{4,}}(?![{_LETRA}])(?:\s+[{_LETRA}]{{2,}}(?![{_LETRA}]))*", palabra, tex)
    return _restaurar(tex, guardados)


def _columnas_de_nivel_superior(tex: str) -> bool:
    """True si la formula tiene un `&` fuera de todo entorno (lineas que se alinean en ese punto: `aligned`)."""
    profundidad = 0
    for m in ls._ESTRUCTURA_MATE.finditer(tex):
        if m.group(1):
            profundidad += 1
        elif m.group(2):
            profundidad = max(0, profundidad - 1)
        elif m.group(0) == "&" and profundidad == 0:
            return True
    return False


def revisar_balance(tex: str) -> list[str]:
    r"""Comprobacion estatica del cuerpo (fuera del codigo): entornos `\begin`/`\end` que cierran en orden y llaves balanceadas."""
    problemas: list[str] = []
    cuerpo = re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}", "", tex, flags=re.S)
    cuerpo = re.sub(r"(?m)^[ \t]*%.*$", "", cuerpo)                  # los comentarios no abren ni cierran nada
    pila: list[str] = []
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", cuerpo):
        if m.group(1) == "begin":
            pila.append(m.group(2))
        elif not pila or pila.pop() != m.group(2):
            problemas.append(f"un \\end{{{m.group(2)}}} no cierra el entorno que esta abierto")
            break
    if pila and not problemas:
        problemas.append("entornos sin cerrar: " + ", ".join(pila))
    sin_escapar = re.sub(r"\\[\\{}]", "", cuerpo)
    if sin_escapar.count("{") != sin_escapar.count("}"):
        problemas.append("llaves { } sin balancear")
    return problemas


# ---------------------------------------------------------------------------
# Compilacion (opcional: temario.py --compilar)
# ---------------------------------------------------------------------------

EXTENSIONES_AUXILIARES = (".aux", ".log", ".out", ".toc", ".lof", ".lot")
DESBORDE_TOLERADO_PT = 1.0


def compilar(ruta_tex: Path, conservar_log: bool = False) -> list[str]:
    """Compila con pdfLaTeX (dos pasadas: referencias y numeracion) y devuelve los problemas: los errores de TeX y cada linea o
    pagina que se sale mas de DESBORDE_TOLERADO_PT (lista vacia = compila limpio y el PDF queda al lado). Nunca con shell-escape,
    y con openin_any=p y openout_any=p (TeX Live no deja leer ni escribir fuera de la carpeta; MiKTeX puede no respetarlas).
    FileNotFoundError si no hay pdflatex."""
    ejecutable = shutil.which("pdflatex")
    if not ejecutable:
        raise FileNotFoundError("pdflatex no está instalado: instala MiKTeX o TeX Live, o sube el .tex a Overleaf (compilador pdfLaTeX)")
    entorno = dict(os.environ, openin_any="p", openout_any="p")
    problemas: list[str] = []
    r: subprocess.CompletedProcess | None = None      # sin resultado si la primera pasada agota el tiempo
    for _ in range(2):
        try:
            r = subprocess.run([ejecutable, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", ruta_tex.name], cwd=ruta_tex.parent,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno, timeout=600, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            problemas.append("pdflatex tardó más de 10 minutos y se detuvo")
            r = None                                    # el resultado de una pasada anterior ya no dice nada de esta
            break
        if r.returncode != 0:
            break
    log = ruta_tex.with_suffix(".log")
    texto = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    for m in re.finditer(r"^! (.+)$(?:\n.*){0,2}", texto, flags=re.M):
        problemas.append("error de LaTeX: " + " ".join(m.group(0).lstrip("! ").split())[:300])
    for m in re.finditer(r"^Overfull \\([hv])box \(([\d.]+)pt too (?:wide|high)\)(.*)$", texto, flags=re.M):
        if float(m.group(2)) > DESBORDE_TOLERADO_PT:
            que = "una línea se sale del margen" if m.group(1) == "h" else "una página se desborda"
            problemas.append(f"{que} {float(m.group(2)):.1f} pt{m.group(3).strip() and ' (' + m.group(3).strip() + ')'}")
    if not texto:
        problemas.append("pdflatex no dejó registro (.log): no se pudo compilar")
    elif r is not None and r.returncode != 0 and not any(p.startswith("error de LaTeX") for p in problemas):
        problemas.append("pdflatex terminó con error: " + " ".join(texto.splitlines()[-3:])[:300])
    for extension in EXTENSIONES_AUXILIARES:
        if conservar_log and extension == ".log":
            continue
        ruta_tex.with_suffix(extension).unlink(missing_ok=True)
    if r is None or r.returncode != 0:
        ruta_tex.with_suffix(".pdf").unlink(missing_ok=True)   # un PDF de antes, o a medias, no es el de este .tex
    return list(dict.fromkeys(problemas))


@dataclass
class Bloques:
    r"""Bloques de una unidad, con el nivel al que van sus subtitulos (2 = \\subsection, como `### 5.1`)."""
    bloques: list[Bloque]
    nivel_subtitulos: int = 2


@dataclass
class Seccion:
    r"""Un encabezado del temario: nivel 1 = `##` (\\section), 2 = `###` (\\subsection), 3 = `####` (\\subsubsection).
    `numerada=False` es un encabezado sin numero (como «Componente Actitudinal»)."""
    nivel: int
    titulo: str
    numerada: bool = True


@dataclass
class Texto:
    """Un parrafo en Markdown en linea (negrita, cursiva, $formulas$, [[enlaces]])."""
    md: str


@dataclass
class Lista:
    items: list[str]
    numerada: bool = False


@dataclass
class Tabla:
    encabezados: list[str]
    filas: list[list[str]]
    leyenda: str = ""                    # sin leyenda: tabla sin numero (las de la estructura: resultados, indice)
    anchos: list[str] | None = None      # especificacion de columnas; por omision, todas X
    total: bool = False                  # la ultima fila es un total (va resaltada)


@dataclass
class Referencias:
    """La bibliografia: entradas `[n] texto` (Markdown en linea), con el numero a la izquierda y sangria francesa."""
    entradas: list[str]


@dataclass
class Caja:
    """Una caja con contenido: `alineacion` (RA, criterios y competencias) o `cita` (componente actitudinal)."""
    clase: str
    piezas: list = field(default_factory=list)


@dataclass
class Sesion:
    codigo: str
    asignatura: str
    titulo: str
    semana: int
    total_semanas: int
    cabecera: list[tuple[str, str]]       # (rotulo, valor en Markdown en linea), en el orden del .md
    piezas: list                          # Seccion | Texto | Lista | Tabla | Caja | Bloques | Referencias, en el orden del .md


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------


class _Escritor:
    def __init__(self) -> None:
        self.conv = ls.Conversor()
        self.figuras = self.tablas = self.listados = 0

    # --- texto ---

    def inline(self, md: str) -> str:
        md = ls._MATH_INLINE.sub(lambda m: "$" + pulir_formula(m.group(1)) + "$", " ".join(str(md).split()))
        tex = self.conv.inline(md)
        return tex.replace("[FUENTE NO CARGADA EN raw/]", r"\textcolor{iuborange}{\textbf{[FUENTE NO CARGADA EN raw/]}}")

    def titulo(self, md: str) -> str:
        return self.conv.titulo(" ".join(str(md).split()))

    def seccion(self, s: Seccion) -> str:
        comando = {1: "section", 2: "subsection", 3: "subsubsection"}[s.nivel]
        return f"\\{comando}{'' if s.numerada else '*'}{{{self.titulo(s.titulo)}}}"

    def lista(self, items: list[str], numerada: bool = False) -> str:
        entorno = "enumerate" if numerada else "itemize"
        cuerpo = "\n".join(f"  \\item {self.inline(i)}" for i in items if str(i).strip())
        return f"\\begin{{{entorno}}}\n{cuerpo}\n\\end{{{entorno}}}"

    # --- tablas ---

    def tabla(self, t: Tabla) -> str:
        n = len(t.encabezados)
        columnas = "".join(t.anchos) if t.anchos else _columnas(t.encabezados, t.filas)
        encabezado = " & ".join(f"\\textcolor{{white}}{{\\textbf{{{self.inline(c)}}}}}" for c in t.encabezados) + r" \\"
        fila_enc = f"\\rowcolor{{iubnavy}} {encabezado}"
        lineas = []
        if t.leyenda:
            self.tablas += 1
            lineas.append(f"% --- Tabla {self.tablas}: {_comentario(t.leyenda)} (xltabular: se parte entre páginas repitiendo el encabezado) ---")
        lineas.append(r"\begin{xltabular}{\linewidth}{" + columnas + "}")
        if t.leyenda:
            lineas.append(f"\\caption{{{self.inline(t.leyenda)}}} \\\\")
        lineas += [fila_enc, r"\endfirsthead", fila_enc, r"\endhead", r"\bottomrule", r"\endlastfoot"]
        for k, fila in enumerate(t.filas):
            celdas = [self.inline(c) for c in fila] + [""] * (n - len(fila))
            if t.total and k == len(t.filas) - 1:
                lineas.append(r"  \midrule")
                lineas.append(r"  \rowcolor{iubfondogris} " + " & ".join(celdas[:n]) + r" \\")
            else:
                lineas.append("  " + ("\\rowcolor{iubfondogris} " if k % 2 else "") + " & ".join(celdas[:n]) + r" \\")
        lineas.append(r"\end{xltabular}")
        return "\n".join(lineas)

    # --- bloques del modelo ---

    def ecuacion(self, latex: str) -> str:
        r"""Una ecuacion numerada. Si tiene varias lineas sueltas (`\\` fuera de un entorno), van en `aligned` cuando se alinean en un `&`
        (lo moderno en lugar de `eqnarray`, con un solo numero como en el .md) y en `gathered`, centradas, cuando no."""
        latex = pulir_formula(latex.strip())
        if ls.saltos_sueltos(latex):
            entorno = "aligned" if _columnas_de_nivel_superior(latex) else "gathered"
            latex = f"\\begin{{{entorno}}}\n  " + latex.replace("\\\\", "\\\\\n  ") + f"\n\\end{{{entorno}}}"
        return "\\begin{equation}\n  " + self.conv.matematicas(latex).replace("\n", "\n  ") + "\n\\end{equation}"

    def codigo(self, b: Bloque) -> str:
        self.listados += 1
        opciones = []
        lenguaje = ls._LENGUAJES_LISTINGS.get(b.lenguaje.strip().lower())
        if lenguaje:
            opciones.append(f"language={{{lenguaje}}}")
        if b.leyenda.strip():
            opciones.append(f"caption={{{self.inline(b.leyenda)}}}")
        else:
            opciones.append("nolol")
        cuerpo = "\n".join(ls.ascii_codigo(l) for l in b.contenido.strip("\n").splitlines())
        comentario = f"% --- Listado {self.listados}: {_comentario(b.leyenda) or 'código'} (transliterado a ASCII) ---\n"
        return f"{comentario}\\begin{{lstlisting}}[{', '.join(opciones)}]\n{cuerpo}\n\\end{{lstlisting}}"

    def figura(self, dibujo: str, leyenda: str, clase: str) -> str:
        self.figuras += 1
        return (f"% --- Figura {self.figuras}: {_comentario(leyenda)} ({clase}) ---\n\\begin{{figure}}[H]\n  \\centering\n"
                + "\n".join("  " + l if l else l for l in dibujo.splitlines()) + f"\n  \\caption{{{self.inline(leyenda)}}}\n\\end{{figure}}")

    def bloques(self, b: Bloques) -> list[str]:
        partes: list[str] = []
        for bloque in b.bloques:
            t, c = bloque.tipo, bloque.contenido.strip()
            if t == TipoBloque.parrafo:
                partes.append(self.inline(c))
            elif t == TipoBloque.lista:
                partes.append(self.lista([re.sub(r"^\s*([-*•]|\d+[.)])\s+", "", l).strip() for l in c.splitlines() if l.strip()]))
            elif t == TipoBloque.ecuacion:
                partes.append(self.ecuacion(c))
            elif t == TipoBloque.tabla:
                encabezados, filas = celdas_de_tabla(c)
                partes.append(self.tabla(Tabla(encabezados, filas, leyenda=bloque.leyenda)))
            elif t == TipoBloque.nota:
                etiqueta = self.inline(bloque.leyenda.strip().rstrip(":") or "Nota") + ":"
                partes.append(f"\\begin{{nota}}{{{etiqueta}}}\n{self.inline(c)}\n\\end{{nota}}")
            elif t == TipoBloque.codigo:
                partes.append(self.codigo(bloque))
            elif t == TipoBloque.grafica:
                partes.append(self.figura(self.grafica(bloque.grafica), bloque.leyenda, "gráfica en pgfplots con los puntos de su especificación"))
            elif t == TipoBloque.diagrama:
                partes.append(self.figura(self.diagrama(bloque.diagrama), bloque.leyenda, "diagrama en TikZ con la disposición del PNG"))
            elif t == TipoBloque.subtitulo:
                partes.append(self.seccion(Seccion(b.nivel_subtitulos, c)))
        return partes

    # --- graficas (pgfplots) ---

    def grafica(self, spec: figuras.GraficaSpec) -> str:
        opciones = ["iubejes", f"xlabel={{{self.inline(spec.etiqueta_x)}}}", f"ylabel={{{self.inline(spec.etiqueta_y)}}}"]
        if spec.titulo.strip():
            opciones.append(f"title={{{self.inline(spec.titulo)}}}")
        cuerpo: list[str] = []
        leyenda = len(spec.series) > 1 or bool(spec.series[0].nombre.strip())
        renglones = 1
        if spec.tipo == figuras.TipoGrafica.barras:          # las categorias largas ocupan varias lineas bajo el eje
            renglones = max(math.ceil(len(c) / CARACTERES_POR_RENGLON_CATEGORIA) for c in spec.categorias)
        opciones.append(f"legend style={{at={{(0.5,{-0.30 - 0.11 * (renglones - 1):.2f})}}}}")
        if spec.tipo == figuras.TipoGrafica.barras:
            n = len(spec.series)
            valores = [v for s in spec.series for v in (s.y or [])]
            opciones += ["ybar", f"bar width={0.8 / n * 0.92:.3f}", "xtick={" + ",".join(str(i) for i in range(len(spec.categorias))) + "}",
                         "xticklabels={" + ",".join("{" + self.inline(c) + "}" for c in spec.categorias) + "}",
                         "xticklabel style={align=center, text width=2.4cm}", "enlarge x limits=0.15", "major x grid style={draw=none}",
                         "nodes near coords", "nodes near coords style={font=\\scriptsize, text=iubnavy}",
                         "enlarge y limits={upper, value=0.15}"]
            if valores and min(valores) >= 0:
                opciones.append("ymin=0")
            for k, s in enumerate(spec.series):
                color = COLORES_SERIE[k % len(COLORES_SERIE)]
                puntos = " ".join(f"({i},{_num(v)})" for i, v in enumerate(s.y or []))
                cuerpo.append(f"% serie {k + 1}: {_comentario(s.nombre) or 'sin nombre'}")
                cuerpo.append(f"\\addplot[fill={color}, draw=none] coordinates {{{puntos}}};")
                if leyenda:
                    cuerpo.append(f"\\addlegendentry{{{self.inline(s.nombre)}}}")
        else:
            if spec.escala_log_x:
                opciones.append("xmode=log")
            if spec.escala_log_y:
                opciones.append("ymode=log")
            if spec.dominio_min is not None and spec.dominio_max is not None:
                opciones += [f"xmin={_num(spec.dominio_min)}", f"xmax={_num(spec.dominio_max)}"]
            for k, s in enumerate(spec.series):
                color = COLORES_SERIE[k % len(COLORES_SERIE)]
                xs, ys = figuras.puntos_de(spec, s)
                if spec.tipo == figuras.TipoGrafica.dispersion:
                    estilo = f"only marks, mark=*, mark size=1.8pt, color={color}"
                elif s.expresion is None:
                    estilo = f"color={color}, line width=1.4pt, mark=*, mark size=1.6pt"
                else:
                    estilo = f"color={color}, line width=1.4pt, no markers"
                origen = f"«{s.expresion}» en {len(xs)} puntos" if s.expresion is not None else f"{len(xs)} datos"
                cuerpo.append(f"% serie {k + 1}: {_comentario(s.nombre) or 'sin nombre'} ({_comentario(origen)})")
                cuerpo.append(f"\\addplot[{estilo}] coordinates {{{_coordenadas(xs, ys)}}};")
                if leyenda:
                    cuerpo.append(f"\\addlegendentry{{{self.inline(s.nombre)}}}")
        for ref in spec.lineas_referencia:
            cuerpo.append(f"% línea de referencia en {ref.eje.value} = {_num(ref.valor)}")
            etiqueta = self.inline(ref.etiqueta)
            if ref.eje == figuras.EjeReferencia.x:
                y_aux = "1" if spec.escala_log_y else "0"
                punto = f"{{axis cs:{_num(ref.valor)},{y_aux}}}"
                cuerpo.append(f"\\draw[iubgrisoscuro, dashed, line width=0.9pt] ({punto}|-{{rel axis cs:0,0}}) -- ({punto}|-{{rel axis cs:0,1}}) "
                              f"node[drotulo, pos=1, anchor=north west] {{{etiqueta}}};")
            else:
                x_aux = "1" if spec.escala_log_x else "0"
                punto = f"{{axis cs:{x_aux},{_num(ref.valor)}}}"
                cuerpo.append(f"\\draw[iubgrisoscuro, dashed, line width=0.9pt] ({{rel axis cs:0,0}}|-{punto}) -- ({{rel axis cs:1,0}}|-{punto}) "
                              f"node[drotulo, pos=1, anchor=south east] {{{etiqueta}}};")
        return ("\\begin{tikzpicture}\n  \\begin{axis}[\n      " + ",\n      ".join(opciones) + "]\n"
                + "\n".join("    " + l for l in cuerpo) + "\n  \\end{axis}\n\\end{tikzpicture}")

    # --- diagramas (TikZ) ---

    def diagrama(self, spec: figuras.DiagramaSpec) -> str:
        posiciones, tam, retorno, _ = figuras._mejor_disposicion(spec)
        nombre = {n.id: f"n{k}" for k, n in enumerate(spec.nodos)}
        estilo = {figuras.FormaNodo.caja: "dcaja", figuras.FormaNodo.estado: "destado",
                  figuras.FormaNodo.decision: "ddecision", figuras.FormaNodo.terminal: "dterminal"}
        lineas = [r"\begin{adjustbox}{max width=\linewidth}", r"\begin{tikzpicture}[x=1in, y=1in, font=\small]",
                  "  % nodos (centro en pulgadas, con el tamano que calcula figuras.py)"]
        for nodo in spec.nodos:
            x, y = posiciones[nodo.id]
            w, h, renglones = tam[nodo.id]
            texto = r" \\ ".join(self.inline(r) for r in renglones)
            medidas = f"minimum width={w:.3f}in, minimum height={h:.3f}in"
            lineas.append(f"  \\node[{estilo[nodo.forma]}, {medidas}] ({nombre[nodo.id]}) at ({x:.3f},{y:.3f}) {{{texto}}};"
                          f"  % {_comentario(nodo.id)}")
        lineas.append("  % flechas (las de retorno, curvas)")
        pares = [(a.origen, a.destino) for a in spec.aristas]
        rotulos: list[str] = []
        for k, a in enumerate(spec.aristas):
            o, d = nombre[a.origen], nombre[a.destino]
            etiqueta = self.inline(a.etiqueta) if a.etiqueta.strip() else ""
            if a.origen == a.destino:
                lineas.append(f"  \\path ({o}) edge[dflecha, loop above, looseness=6] ({o});")
                if etiqueta:
                    x, y = posiciones[a.origen]
                    rotulos.append(f"  \\node[drotulo, anchor=south] at ({x:.3f},{y + tam[a.origen][1] / 2 + 0.36:.3f}) {{{etiqueta}}};")
                continue
            curva = figuras._curva_de(k, a.origen, a.destino, retorno, pares)
            if curva:
                angulo = round(math.degrees(math.atan(2 * curva)))
                lineas.append(f"  \\draw[dflecha] ({o}) to[bend right={angulo}] ({d});")
            else:
                lineas.append(f"  \\draw[dflecha] ({o}) -- ({d});")
            if etiqueta:
                mx, my = figuras._sitio_de_etiqueta(posiciones[a.origen], posiciones[a.destino], curva, a.etiqueta, posiciones, tam,
                                                    (a.origen, a.destino))
                rotulos.append(f"  \\node[drotulo] at ({mx:.3f},{my:.3f}) {{{etiqueta}}};")
        if rotulos:
            lineas.append("  % rotulos de las flechas (donde no caen sobre un nodo)")
        lineas += rotulos
        lineas += [r"\end{tikzpicture}", r"\end{adjustbox}"]
        return "\n".join(lineas)

    # --- piezas de la estructura ---

    def pieza(self, p) -> list[str]:
        if isinstance(p, Seccion):
            return [self.seccion(p)]
        if isinstance(p, Texto):
            return [self.inline(p.md)]
        if isinstance(p, Lista):
            return [self.lista(p.items, p.numerada)]
        if isinstance(p, Tabla):
            return [self.tabla(p)]
        if isinstance(p, Bloques):
            return self.bloques(p)
        if isinstance(p, Referencias):
            items = []
            for entrada in p.entradas:
                m = re.match(r"^\[(\d+)\]\s*(.*)$", entrada.strip(), flags=re.S)
                numero, texto = (m.group(1), m.group(2)) if m else ("", entrada)
                items.append(f"  \\item[{{[{numero}]}}] {self.inline(texto)}" if numero else f"  \\item[] {self.inline(texto)}")
            return ["{\\sloppy\n\\begin{itemize}[leftmargin=2.6em, labelwidth=2.2em, labelsep=0.4em, align=left]\n"
                    + "\n".join(items) + "\n\\end{itemize}\n}"]
        if isinstance(p, Caja):
            dentro = [x for q in p.piezas for x in self.pieza(q)]
            return [f"\\begin{{{p.clase}}}\n" + "\n\n".join(dentro) + f"\n\\end{{{p.clase}}}"]
        raise TypeError(f"pieza desconocida: {type(p).__name__}")


def hash_cuerpo(cuerpo: str) -> str:
    """Huella del cuerpo del .md al escribir el .tex (la misma cuenta que presentaciones.hash_cuerpo): si el .md se edita a mano
    despues, el .tex ya no le corresponde (LINT L16)."""
    return hashlib.sha256(cuerpo.strip().encode("utf-8")).hexdigest()[:16]


def _num(v: float) -> str:
    """Un numero como lo lee pgfplots (`nan` deja un hueco con `unbounded coords=jump`)."""
    if v is None or not math.isfinite(v):
        return "nan"
    return f"{v:.6g}"


def _comentario(texto: str, maximo: int = 90) -> str:
    """Un texto para un comentario `%` del .tex: en una linea, sin `%`, barras invertidas ni `^` (la notacion `^^` de TeX puede
    escribir cualquier caracter, tambien una barra): nada que parezca un comando. TeX descarta el resto de la linea tras `%`, asi
    que no seria explotable; se limpia igual para que el comentario sea solo texto."""
    plano = " ".join(str(texto).replace("%", "por ciento").replace("\\", "").replace("^", " ").split())
    return plano if len(plano) <= maximo else plano[:maximo - 1] + "…"


def _coordenadas(xs: list[float], ys: list[float], por_linea: int = 6) -> str:
    """Las coordenadas de pgfplots, de a `por_linea` por renglon (un .tex legible, no una linea de miles de caracteres)."""
    pares = [f"({_num(x)},{_num(y)})" for x, y in zip(xs, ys)]
    if len(pares) <= por_linea:
        return " ".join(pares)
    return "\n" + "\n".join("      " + " ".join(pares[i:i + por_linea]) for i in range(0, len(pares), por_linea)) + "\n    "


_NUMERO_CELDA = re.compile(r"^[-+−]?\$?\s*\d[\d.,\s]*(?:[eE][-+]?\d+)?\$?\s*(%|[A-Za-zµμ°Ω/²³·\\{}^_ ]{0,8})?$")


def _plano(celda: str) -> str:
    return re.sub(r"[*`$\\{}]|\[\[|\]\]", "", str(celda)).strip()


def _columnas(encabezados: list[str], filas: list[list[str]]) -> str:
    r"""La especificacion de columnas de una tabla del modelo: todas X (llenan el ancho), cada una tan ancha como lo que lleva
    (`\hsize`, que en tabularx suma el numero de columnas) y las numericas alineadas a la derecha."""
    n = len(encabezados)
    pesos = []
    for k in range(n):
        celdas = [_plano(f[k]) for f in filas if k < len(f)]
        largo = max([len(_plano(encabezados[k])) + 2, *[len(c) + 1 for c in celdas]])     # el encabezado va en negrita: algo mas ancho
        pesos.append(min(max(largo, 7.0), 45.0))
    total = sum(pesos)
    anchos = [round(n * w / total, 3) for w in pesos]
    anchos[-1] = round(n - sum(anchos[:-1]), 3)
    columnas = []
    for k, ancho in enumerate(anchos):
        celdas = [str(f[k]).strip() for f in filas if k < len(f) and str(f[k]).strip()]
        numerica = bool(celdas) and all(_NUMERO_CELDA.match(c) for c in celdas)
        alineacion = r"\raggedleft" if numerica else r"\raggedright"
        columnas.append(rf">{{\hsize={ancho}\hsize\linewidth=\hsize{alineacion}\arraybackslash}}X")
    return "".join(columnas)


def _sin_codigo(tex: str) -> str:
    return re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}", "", tex, flags=re.S)


def documento(sesion: Sesion) -> tuple[str, list[str]]:
    """(el .tex completo, avisos). Los avisos son los del Conversor (un caracter sin equivalente LaTeX, una formula con comandos
    que no son matematicos conocidos o con la sintaxis a medias): el .tex se escribe igual, pero conviene revisarlo.
    ValueError si el cuerpo trae una primitiva que lee o escribe archivos (no deberia pasar: nada del modelo llega sin escapar)."""
    e = _Escritor()
    cabecera = [f"{{\\color{{iubyellow}}\\Large\\bfseries {e.titulo(sesion.titulo)}\\par}}", r"\vspace{0.6em}", r"\small"]
    cabecera += [f"\\textbf{{\\color{{iubyellow}}{e.titulo(r)}:}} {e.inline(v)}\\par" for r, v in sesion.cabecera]
    cuerpo = ["\\begin{cabecera}\n" + "\n".join(cabecera) + "\n\\end{cabecera}"]
    for p in sesion.piezas:
        cuerpo += e.pieza(p)
    texto_cuerpo = "\n\n".join(cuerpo)
    peligrosas = ls.primitivas_peligrosas(_sin_codigo(texto_cuerpo))
    if peligrosas:
        raise ValueError("el LaTeX del temario trae primitivas que leen o escriben archivos: " + ", ".join("\\" + q for q in peligrosas))
    colores = paleta_iub.definiciones() + "\n" + paleta_iub.ciclo_pgfplots()
    preambulo = (PREAMBULO.replace("<<COLORES>>", colores).replace("<<MARCA>>", MARCA).replace("<<INSTITUCION>>", INSTITUCION)
                 .replace("<<ENCABEZADO>>", e.titulo(f"{sesion.codigo} — {sesion.asignatura}"))
                 .replace("<<SEMANA>>", str(sesion.semana)).replace("<<TOTAL>>", str(sesion.total_semanas))
                 .replace("<<ALTO>>", ALTO_GRAFICA).replace("<<TITULO_PDF>>", e.titulo(sesion.titulo)))
    tex = preambulo + "\n\\begin{document}\n\n" + texto_cuerpo + "\n\n\\end{document}\n"
    avisos = list(e.conv.avisos) + [f"revisión estática: {p}" for p in revisar_balance(texto_cuerpo)]
    return tex, avisos
