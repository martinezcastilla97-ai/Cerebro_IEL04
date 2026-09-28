r"""Diseno institucional IUB de las presentaciones (Beamer, pdfLaTeX), diseno 5: el .tex completo al estilo de las presentaciones de
ejemplo del docente (ELE06 y ELE03). El CODIGO escribe, siempre igual y con los datos del temario, del planeador y del wiki:

    - el preambulo: paleta del Manual de Identidad IUB 2025 (#121023, #FFDF2D, #00ADE7, #E39037, #3B9C6D sobre blanco), tipografia
      `avant` con \familydefault sans serif (el manual usa Nexa y Avenir Next, que pdfLaTeX no tiene), franja superior #121023 con el
      titulo en amarillo y la marca «IUB», pie #121023 con el modulo, el docente, la semana y el numero de diapositiva; las cajas
      tcolorbox (`caja`, `cajaplana`, `cardB/O/G/N`), el `codebox` para codigo, los estilos TikZ (`bloque`, `flecha`, `nodo`, `term`,
      `cable`, `box`, `bB/bO/bG/bN`, `dec`, `tag`) y el separador `\bloque`;
    - la portada, la ruta de la sesion (los bloques del indice temporizado con sus minutos), un separador por bloque, las referencias
      y el cierre.

El cuerpo de las demas diapositivas lo escribe el modelo en LaTeX (TikZ, pgfplots, circuitikz, tablas y las cajas de arriba),
verificado antes con latex_seguro.verificar_cuerpo. Sin imagenes: la marca IUB va como texto y las figuras se dibujan con TikZ.
Todo dato que viene del wiki o del temario pasa por latex_seguro.Conversor (escapado).

Coordenadas en cm; la diapositiva mide 16 x 9 cm (aspectratio=169). La portada, los separadores y el cierre usan
`remember picture, overlay`: hace falta compilar DOS veces. NO se ha compilado en el equipo donde se escribio (no hay LaTeX): la
primera compilacion real (Overleaf o --compilar) es la que confirma que nada desborda.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import latex_seguro as ls
from schema_presentacion import _largo

VERSION = 5                 # version del diseno (campo `presentacion_diseno`): si cambia, las presentaciones se rehacen desde su plan

COLORES = {"iubwhite": "FFFFFF", "iubnavy": "121023", "iubyellow": "FFDF2D",
           "iubblue": "00ADE7", "iuborange": "E39037", "iubgreen": "3B9C6D"}
CICLO = ("iubblue", "iuborange", "iubgreen")            # se alternan para diferenciar bloques y conceptos
MARCA = "IUB"
INSTITUCION = "Institución Universitaria de Barranquilla"
MAX_REFERENCIAS = 5                # entradas de la bibliografia por diapositiva
MAX_LINEAS_REFERENCIAS = 13        # lineas (estimadas) de bibliografia por diapositiva
CARACTERES_POR_LINEA_REFERENCIA = 95


@dataclass
class Documento:
    """Los datos deterministas de la sesion (del temario, el planeador y el wiki)."""
    codigo: str
    asignatura: str
    titulo: str
    semana: int
    total_semanas: int
    docente: str
    programa: str
    duracion_min: int = 0
    corte: int | None = None
    tipo_sesion: str = ""           # «teórica» | «teórico-práctica»
    subtitulo: str = ""             # la plataforma de referencia del temario, si la tiene
    siguiente: str = ""
    contacto: str = ""
    referencias: list[str] = field(default_factory=list)
    conv: ls.Conversor = field(default_factory=ls.Conversor)


@dataclass
class BloqueSesion:
    """Un bloque del indice temporizado del temario."""
    numero: int
    titulo: str
    minutos: int = 0


@dataclass
class Diapositiva:
    """Una diapositiva ya verificada: titulo y cuerpo en LaTeX (el interior del frame)."""
    titulo: str
    cuerpo: str


def _recorte(texto: str, maximo: int) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= maximo else texto[:maximo - 1].rsplit(" ", 1)[0] + "…"


def _comentario(texto: str) -> str:
    """Texto para un comentario del .tex: una linea, sin saltos."""
    return " ".join(str(texto).split())


# ---------------------------------------------------------------------------
# Preambulo (fijo: no depende del modelo)
# ---------------------------------------------------------------------------

_PREAMBULO = r"""% =====================================================================
%  <<CABECERA_1>>
%  <<CABECERA_2>>
%  <<INSTITUCION>> (IUB)
%  Generada por src/presentaciones.py (diseño IUB <<VERSION>>). Compilador: pdfLaTeX (dos pasadas)
% =====================================================================
\documentclass[aspectratio=169,11pt,xcolor={table}]{beamer}

% ---------------------------------------------------------------------
%  Codificación, idioma y tipografía
% ---------------------------------------------------------------------
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot,es-noshorthands]{babel}
\usepackage{avant}                       % Sans geométrica (emula Avenir Next)
\renewcommand{\familydefault}{\sfdefault}
\renewcommand{\ttdefault}{pcr}           % Monoespaciada para código
\usepackage{textcomp}

% ---------------------------------------------------------------------
%  Paquetes
% ---------------------------------------------------------------------
\usepackage{amsmath,amssymb,mathtools}
\usepackage{siunitx}
\sisetup{output-decimal-marker={.}, per-mode=symbol}
\usepackage{booktabs,tabularx,multirow,array}
\usepackage{adjustbox}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,shapes.geometric,shapes.misc,
  decorations.pathreplacing,fit,backgrounds,babel}
\usepackage[siunitx,RPvoltages]{circuitikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage[most]{tcolorbox}
\usepackage{listings}

% ---------------------------------------------------------------------
%  Paleta institucional IUB (Manual de Identidad Visual 2025)
% ---------------------------------------------------------------------
<<COLORES>>

% ---------------------------------------------------------------------
%  Configuración de Beamer
% ---------------------------------------------------------------------
\setbeamertemplate{navigation symbols}{}
\setbeamersize{text margin left=0.6cm, text margin right=0.6cm}
\setbeamercolor{normal text}{fg=iubnavy, bg=iubwhite}
\setbeamercolor{background canvas}{bg=iubwhite}
\setbeamercolor{structure}{fg=iubnavy}
\setbeamercolor{alerted text}{fg=iuborange}
\setbeamertemplate{itemize item}{\textcolor{iubblue}{\small$\blacktriangleright$}}
\setbeamertemplate{itemize subitem}{\textcolor{iuborange}{\scriptsize$\bullet$}}
\setbeamertemplate{enumerate item}{\textcolor{iubblue}{\bfseries\insertenumlabel.}}
\setbeamertemplate{frametitle}{}         % el título vive en el headline

% Parches: el headline se pre-mide antes del primer frame
\makeatletter
\providecommand{\insertframetitle}{}
\providecommand{\insertframesubtitle}{}
\makeatother

% ---------- Encabezado ----------
\setbeamertemplate{headline}{%
  \begin{tikzpicture}
    \useasboundingbox (0,0) rectangle (\paperwidth,1.05cm);
    \fill[iubnavy] (0,0) rectangle (\paperwidth,1.05cm);
    \fill[iubyellow] (0,0) rectangle (\paperwidth,0.05cm);
    \node[anchor=west, text=iubyellow, font=\large\bfseries]
      at (0.6cm,0.55cm) {\strut\insertframetitle};
    \node[anchor=east, text=iubyellow, font=\footnotesize\bfseries]
      at ([xshift=-0.6cm]\paperwidth,0.55cm) {<<MARCA>>};
  \end{tikzpicture}}

% ---------- Pie de página ----------
\setbeamertemplate{footline}{%
  \begin{tikzpicture}
    \useasboundingbox (0,0) rectangle (\paperwidth,0.55cm);
    \fill[iubnavy] (0,0) rectangle (\paperwidth,0.55cm);
    \node[anchor=west, text=iubyellow, font=\tiny]
      at (0.6cm,0.275cm) {<<PIE_MODULO>>};
    \node[anchor=center, text=iubyellow, font=\tiny]
      at (0.66\paperwidth,0.275cm) {<<PIE_DOCENTE>>};
    \node[anchor=east, text=iubyellow, font=\tiny\bfseries]
      at ([xshift=-0.6cm]\paperwidth,0.275cm)
      {Semana <<SEMANA>> \quad \insertframenumber\,/\,\inserttotalframenumber};
  \end{tikzpicture}}

% ---------------------------------------------------------------------
%  Cajas tcolorbox (texto blanco sobre la paleta complementaria)
%  \begin{caja}[opciones]{color}{título} ... \end{caja}
%  \begin{cajaplana}[opciones]{color} ... \end{cajaplana}
%  \begin{cardB|cardO|cardG|cardN}[opciones]{título} ... \end{cardX}
% ---------------------------------------------------------------------
\tcbset{
  iubbase/.style={enhanced, arc=1.5mm, boxrule=0pt, coltext=white, coltitle=white,
    fonttitle=\bfseries\footnotesize, fontupper=\footnotesize,
    left=1.8mm, right=1.8mm, top=1mm, bottom=1.2mm,
    toptitle=0.6mm, bottomtitle=0.6mm, halign=left,
    before upper={\hyphenpenalty=5000\setbeamercolor{itemize item}{fg=white}%
                  \setbeamercolor{itemize/enumerate body}{fg=white}%
                  \setbeamercolor{itemize/enumerate subbody}{fg=white}%
                  \setbeamercolor{itemize subitem}{fg=white}%
                  \setbeamercolor{enumerate item}{fg=white}%
                  \setbeamertemplate{itemize item}{\textcolor{white}{\small$\blacktriangleright$}}}}
}
\newtcolorbox{caja}[3][]{iubbase, colback=#2, colframe=#2,
  colbacktitle=#2!78!iubnavy, title={#3}, #1}
\newtcolorbox{cajaplana}[2][]{iubbase, colback=#2, colframe=#2, #1}
\newtcolorbox{cardB}[2][]{iubbase, colback=iubblue,   colframe=iubblue,
  colbacktitle=iubblue!78!iubnavy,   title={#2}, #1}
\newtcolorbox{cardO}[2][]{iubbase, colback=iuborange, colframe=iuborange,
  colbacktitle=iuborange!78!iubnavy, title={#2}, #1}
\newtcolorbox{cardG}[2][]{iubbase, colback=iubgreen,  colframe=iubgreen,
  colbacktitle=iubgreen!78!iubnavy,  title={#2}, #1}
\newtcolorbox{cardN}[2][]{iubbase, colback=iubnavy,   colframe=iubnavy,
  colbacktitle=iubnavy, coltitle=iubyellow, title={#2}, #1}

% Celda de encabezado de tabla (texto amarillo sobre \rowcolor{iubnavy}) y código en línea
\newcommand{\hd}[1]{\textcolor{iubyellow}{\bfseries #1}}
\newcommand{\thc}[1]{\textcolor{iubyellow}{\textbf{#1}}}
\newcommand{\cod}[1]{\texttt{\textbf{#1}}}

% ---------------------------------------------------------------------
%  Código sobre fondo oscuro:
%  \begin{codebox}[listing options app={language=Python,firstnumber=1}]{título}
% ---------------------------------------------------------------------
\lstdefinestyle{iubcode}{
  basicstyle=\ttfamily\fontsize{7}{8.4}\selectfont\color{white},
  keywordstyle=\color{iubblue}\bfseries,
  commentstyle=\color{iubgreen!55!white}\itshape,
  stringstyle=\color{iuborange!80!white},
  numbers=left, numberstyle=\tiny\color{iubyellow}, numbersep=6pt,
  showstringspaces=false, breaklines=true, tabsize=4,
  columns=fullflexible, keepspaces=true, upquote=true}
\newtcblisting{codebox}[2][]{enhanced, listing only, colback=iubnavy,
  colframe=iubnavy, colbacktitle=iubnavy!85!white, coltitle=iubyellow,
  fonttitle=\bfseries\scriptsize, title={#2}, arc=1.5mm, boxrule=0pt,
  left=6mm, right=1mm, top=0.5mm, bottom=0.5mm, toptitle=0.5mm, bottomtitle=0.5mm,
  listing options={style=iubcode}, #1}

% ---------------------------------------------------------------------
%  Estilos TikZ
% ---------------------------------------------------------------------
\tikzset{
  bloque/.style={rectangle, rounded corners=2mm, fill=#1, text=white,
    font=\scriptsize\bfseries, align=center, minimum height=1.1cm,
    text width=1.8cm, inner sep=1.2mm},
  flecha/.style={-{Stealth[length=2.2mm]}, line width=1pt, draw=iubnavy},
  arr/.style={flecha},
  term/.style={rectangle, draw=#1, line width=1.2pt, fill=white,
    text=iubnavy, font=\tiny\bfseries, minimum width=1.05cm,
    minimum height=0.5cm, inner sep=1pt},
  nodo/.style={rectangle, rounded corners=1mm, fill=#1, text=white,
    font=\scriptsize\bfseries, minimum size=0.75cm, align=center},
  cable/.style={line width=1.4pt, draw=#1},
  box/.style={rectangle, rounded corners=1.5mm, draw=none, text=white,
    font=\scriptsize\bfseries, align=center, minimum height=0.8cm, inner sep=3pt},
  bB/.style={box, fill=iubblue}, bO/.style={box, fill=iuborange},
  bG/.style={box, fill=iubgreen}, bN/.style={box, fill=iubnavy},
  dec/.style={diamond, aspect=1.9, fill=iuborange, text=white,
    font=\scriptsize\bfseries, align=center, inner sep=1pt},
  tag/.style={fill=#1, text=white, font=\scriptsize\bfseries, rounded corners=1mm,
    minimum width=0.7cm, anchor=north west},
}

% ---------------------------------------------------------------------
%  Diapositiva separadora de bloque
%  #1 número  #2 título  #3 duración  #4 color
% ---------------------------------------------------------------------
\newcommand{\bloque}[4]{%
\section{#2}
\begin{frame}[plain]
\begin{tikzpicture}[remember picture, overlay]
  \fill[#4] (current page.north west) rectangle
        ([xshift=5.2cm]current page.south west);
  \node[anchor=north west, text=white, font=\bfseries\large]
    at ([xshift=0.8cm,yshift=-2.2cm]current page.north west) {BLOQUE};
  \node[anchor=north west, text=white, font=\bfseries\fontsize{72}{72}\selectfont]
    at ([xshift=0.65cm,yshift=-2.9cm]current page.north west) {#1};
  \node[anchor=north west, text=iubnavy, font=\bfseries\LARGE,
        text width=9.4cm, align=left]
    at ([xshift=6.2cm,yshift=-2.8cm]current page.north west)
    {\hyphenpenalty=10000\exhyphenpenalty=10000 #2};
  \node[anchor=north west, fill=iubnavy, text=iubyellow, rounded corners=1.5mm,
        font=\small\bfseries, inner sep=2mm]
    at ([xshift=6.2cm,yshift=-6.0cm]current page.north west) {Duración: #3};
  \fill[iubnavy] ([xshift=5.2cm]current page.south west) rectangle
        ([yshift=0.35cm]current page.south east);
  \fill[iubyellow] ([xshift=5.2cm,yshift=0.35cm]current page.south west)
        rectangle ([yshift=0.42cm]current page.south east);
  \node[anchor=north east, text=iubnavy, font=\small\bfseries]
    at ([xshift=-0.6cm,yshift=-0.5cm]current page.north east) {<<MARCA>> · <<CODIGO>>};
\end{tikzpicture}
\end{frame}}
"""


def preambulo(doc: Documento) -> str:
    c = doc.conv
    colores = "\n".join(rf"\definecolor{{{n}}}{{HTML}}{{{h}}}" for n, h in COLORES.items())
    reemplazos = {
        "<<CABECERA_1>>": _comentario(f"{doc.codigo} - {doc.asignatura}"),
        "<<CABECERA_2>>": _comentario(f"Semana {doc.semana}: {doc.titulo}"),
        "<<INSTITUCION>>": INSTITUCION, "<<VERSION>>": str(VERSION), "<<COLORES>>": colores, "<<MARCA>>": MARCA,
        "<<CODIGO>>": c.escapar(doc.codigo),
        "<<PIE_MODULO>>": c.escapar(_recorte(f"{doc.codigo} · {doc.asignatura}", 58)),
        "<<PIE_DOCENTE>>": c.escapar(_recorte(doc.docente, 34)),
        "<<SEMANA>>": str(doc.semana),
    }
    texto = _PREAMBULO
    for marca, valor in reemplazos.items():
        texto = texto.replace(marca, valor)
    return texto


# ---------------------------------------------------------------------------
# Diapositivas fijas: portada, ruta de la sesion, separadores, referencias y cierre
# ---------------------------------------------------------------------------

def _tam_titulo_portada(titulo: str) -> str:
    n = _largo(titulo)
    if n <= 40:
        return r"\fontsize{21}{25}\selectfont"
    if n <= 70:
        return r"\fontsize{18}{22}\selectfont"
    return r"\fontsize{15}{18}\selectfont" if n <= 110 else r"\fontsize{13}{16}\selectfont"


def portada(doc: Documento) -> str:
    c = doc.conv
    etiqueta = [doc.codigo, f"Semana {doc.semana} de {doc.total_semanas}"] + ([f"Corte evaluativo {doc.corte}"] if doc.corte else [])
    sesion = ([f"Sesión {doc.tipo_sesion}"] if doc.tipo_sesion else []) + ([f"{doc.duracion_min} min"] if doc.duracion_min else [])
    pie_docente = c.escapar(_recorte(doc.docente, 60)) + (rf"\\[1pt]\textcolor{{iubyellow}}{{{c.escapar(_recorte(doc.contacto, 60))}}}" if doc.contacto else "")
    subtitulo = (rf"""  \node[anchor=north west, text=iubnavy, font=\normalsize, text width=9.0cm, align=left]
    at ([yshift=-0.3cm]t.south west)
    {{\hyphenpenalty=10000 {c.inline(_recorte(doc.subtitulo, 140))}}};
""" if doc.subtitulo.strip() else "")
    return rf"""% ---------------------------------------------------------------------
%  PORTADA
% ---------------------------------------------------------------------
\begin{{frame}}[plain]
\begin{{tikzpicture}}[remember picture, overlay]
  % Panel institucional
  \fill[iubnavy] (current page.north west) rectangle
        ([xshift=5.6cm]current page.south west);
  \node[anchor=north west, text=iubyellow, font=\bfseries\fontsize{{54}}{{54}}\selectfont]
    at ([xshift=0.7cm,yshift=-1.0cm]current page.north west) {{{MARCA}}};
  \node[anchor=north west, text=white, font=\footnotesize, text width=4.3cm, align=left]
    at ([xshift=0.75cm,yshift=-3.0cm]current page.north west)
    {{{c.escapar(INSTITUCION)}}};
  \draw[iubyellow, line width=1.2pt]
    ([xshift=0.75cm,yshift=-4.25cm]current page.north west) --
    ([xshift=2.6cm,yshift=-4.25cm]current page.north west);
  \node[anchor=north west, text=iubyellow, font=\scriptsize\bfseries,
        text width=4.3cm, align=left]
    at ([xshift=0.75cm,yshift=-4.5cm]current page.north west)
    {{{c.escapar(_recorte(doc.programa, 90))}}};
  \node[anchor=south west, text=white, font=\scriptsize, text width=4.3cm, align=left]
    at ([xshift=0.75cm,yshift=0.9cm]current page.south west)
    {{{pie_docente}}};
  % Bloque de título
  \node[anchor=north west, fill=iubblue, text=white, rounded corners=1.5mm,
        font=\scriptsize\bfseries, inner sep=2mm]
    at ([xshift=6.4cm,yshift=-1.0cm]current page.north west)
    {{{c.escapar(' · '.join(etiqueta))}}};
  \node[anchor=north west, text=iubnavy, font=\small, text width=9.0cm, align=left] (a)
    at ([xshift=6.4cm,yshift=-1.9cm]current page.north west)
    {{{c.escapar(_recorte(doc.asignatura, 110))}}};
  \node[anchor=north west, text=iubnavy, font=\bfseries{_tam_titulo_portada(doc.titulo)},
        text width=9.0cm, align=left] (t)
    at ([yshift=-0.35cm]a.south west)
    {{\hyphenpenalty=10000 {c.inline(_recorte(doc.titulo, 160))}}};
{subtitulo}  % Franjas de la paleta complementaria
  \fill[iubblue]   ([xshift=6.4cm,yshift=1.1cm]current page.south west)
    rectangle ++(1.6cm,0.18cm);
  \fill[iuborange] ([xshift=8.1cm,yshift=1.1cm]current page.south west)
    rectangle ++(1.6cm,0.18cm);
  \fill[iubgreen]  ([xshift=9.8cm,yshift=1.1cm]current page.south west)
    rectangle ++(1.6cm,0.18cm);
  \node[anchor=north west, text=iubnavy, font=\scriptsize]
    at ([xshift=6.4cm,yshift=0.95cm]current page.south west)
    {{{c.escapar(' · '.join(sesion))}}};
\end{{tikzpicture}}
\end{{frame}}
"""


def ruta(doc: Documento, bloques: list[BloqueSesion]) -> str:
    """La ruta de la sesion: un renglon por bloque (numero, contenido y una barra proporcional a sus minutos)."""
    c = doc.conv
    if not bloques:
        return ""
    total = sum(b.minutos for b in bloques) or doc.duracion_min
    paso = min(0.82, 5.3 / max(1, len(bloques) - 1)) if len(bloques) > 1 else 0.82
    mayor = max((b.minutos for b in bloques), default=0) or 1
    escala = min(0.11, 4.6 / mayor)
    filas = []
    for k, b in enumerate(bloques):
        y = -k * paso
        color = CICLO[k % len(CICLO)]
        barra = b.minutos * escala
        filas.append(
            rf"  \node[circle, fill={color}, text=white, font=\scriptsize\bfseries, minimum size=0.6cm, inner sep=0] at (0,{y:.2f}) {{{b.numero}}};" "\n"
            rf"  \node[anchor=west, font=\scriptsize, text width=7.6cm] at (0.45,{y:.2f}) {{{c.inline(_recorte(b.titulo, 110))}}};" "\n"
            + (rf"  \fill[{color}] (8.3,{y - 0.2:.2f}) rectangle ++({barra:.2f},0.4);" "\n"
               rf"  \node[anchor=west, font=\scriptsize\bfseries] at ({8.4 + barra:.2f},{y:.2f}) {{{b.minutos} min}};" "\n" if b.minutos else ""))
    titulo = f"Ruta de la sesión · {total} minutos" if total else "Ruta de la sesión"
    return (f"% ---------------------------------------------------------------------\n\\begin{{frame}}{{{c.escapar(titulo)}}}\n\\centering\n"
            "\\begin{tikzpicture}[x=1cm,y=1cm]\n" + "".join(filas)
            + rf"  \draw[iubnavy, line width=0.6pt] (8.3,0.45) -- (8.3,{-(len(bloques) - 1) * paso - 0.4:.2f});" "\n"
            "\\end{tikzpicture}\n\\end{frame}\n")


def separador(doc: Documento, bloque: BloqueSesion, indice: int) -> str:
    c = doc.conv
    duracion = f"{bloque.minutos} min" if bloque.minutos else "—"
    return ("% =====================================================================\n"
            f"\\bloque{{{bloque.numero:02d}}}{{{c.inline(_recorte(bloque.titulo, 110))}}}{{{c.escapar(duracion)}}}{{{CICLO[indice % len(CICLO)]}}}\n"
            "% =====================================================================\n")


def diapositiva(d: Diapositiva) -> str:
    """Un frame con el cuerpo que escribio el modelo (ya verificado). Con codigo, [fragile]; un titulo largo, un punto mas chico."""
    fragil = "[fragile]" if "\\begin{codebox}" in d.cuerpo else ""
    titulo = d.titulo if _largo(d.titulo) <= 50 else f"{{\\normalsize {d.titulo}}}"
    return f"% ---------------------------------------------------------------------\n\\begin{{frame}}{fragil}{{{titulo}}}\n{d.cuerpo.strip()}\n\\end{{frame}}\n"


def _item_referencia(c: ls.Conversor, entrada: str) -> str:
    """`[3] Autor, Titulo...` -> `\\item[{$[3]$}] Autor, Titulo...` (la etiqueta entre corchetes, como en los ejemplos)."""
    m = re.match(r"\s*\[(\d+)\]\s*(.*)$", entrada, re.S)
    if not m:
        return rf"  \item {c.inline(entrada)}"
    return rf"  \item[{{$[{m.group(1)}]$}}] {c.inline(m.group(2))}"


def referencias(doc: Documento) -> list[str]:
    c = doc.conv
    grupos: list[list[str]] = []
    grupo: list[str] = []
    lineas = 0
    for entrada in doc.referencias:
        n = 1 + len(entrada) // CARACTERES_POR_LINEA_REFERENCIA
        if grupo and (lineas + n > MAX_LINEAS_REFERENCIAS or len(grupo) >= MAX_REFERENCIAS):
            grupos.append(grupo)
            grupo, lineas = [], 0
        grupo.append(entrada)
        lineas += n
    if grupo:
        grupos.append(grupo)
    diapositivas = []
    for k, g in enumerate(grupos, 1):
        titulo = "Referencias bibliográficas" + (f" ({k}/{len(grupos)})" if len(grupos) > 1 else "")
        items = "\n".join(_item_referencia(c, e) for e in g)
        diapositivas.append(f"% ---------------------------------------------------------------------\n\\begin{{frame}}{{{c.escapar(titulo)}}}\n"
                            f"\\small\n\\begin{{itemize}}\\setlength{{\\itemsep}}{{8pt}}\n{items}\n\\end{{itemize}}\n\\end{{frame}}\n")
    return diapositivas


def cierre(doc: Documento) -> str:
    c = doc.conv
    firma = " \\quad · \\quad ".join([c.escapar(_recorte(doc.docente, 60))] + ([c.escapar(_recorte(doc.contacto, 60))] if doc.contacto else []))
    siguiente = (rf"""  \node[anchor=north west, fill=iubblue, text=white, rounded corners=1.5mm,
        font=\small\bfseries, inner sep=2.2mm, text width=11.5cm]
    at ([xshift=1.2cm,yshift=-4.4cm]current page.north west)
    {{{c.inline(_recorte(doc.siguiente, 200))}}};
""" if doc.siguiente.strip() else "")
    return rf"""% ---------------------------------------------------------------------
%  CIERRE
% ---------------------------------------------------------------------
\begin{{frame}}[plain]
\begin{{tikzpicture}}[remember picture, overlay]
  \fill[iubnavy] (current page.north west) rectangle (current page.south east);
  \node[anchor=north west, text=iubyellow, font=\bfseries\fontsize{{40}}{{44}}\selectfont]
    at ([xshift=1.2cm,yshift=-1.6cm]current page.north west) {{{c.escapar('¡Gracias!')}}};
  \node[anchor=north west, text=white, font=\normalsize, text width=14cm, align=left]
    at ([xshift=1.2cm,yshift=-3.4cm]current page.north west)
    {{{c.escapar(_recorte(f'{doc.codigo} · {doc.asignatura}', 120))}}};
{siguiente}  \node[anchor=south west, text=iubyellow, font=\small, align=left]
    at ([xshift=1.2cm,yshift=0.9cm]current page.south west)
    {{{firma}}};
  \fill[iubblue]   ([xshift=1.2cm,yshift=0.55cm]current page.south west) rectangle ++(1.6cm,0.15cm);
  \fill[iuborange] ([xshift=2.9cm,yshift=0.55cm]current page.south west) rectangle ++(1.6cm,0.15cm);
  \fill[iubgreen]  ([xshift=4.6cm,yshift=0.55cm]current page.south west) rectangle ++(1.6cm,0.15cm);
\end{{tikzpicture}}
\end{{frame}}
"""


def provisional(doc: Documento, bloque: BloqueSesion | None, motivo: str) -> Diapositiva:
    """La diapositiva que ocupa el lugar de una parte que el modelo no logro escribir con LaTeX admitido: la presentacion se puede
    compilar igual, y la proxima corrida vuelve a pedir esa parte."""
    c = doc.conv
    que = f"el bloque {bloque.numero} («{_recorte(bloque.titulo, 80)}»)" if bloque else "la apertura de la sesión"
    aviso = (f"Las diapositivas de {que} no se generaron: el modelo no cumplió las reglas de LaTeX de la presentación. "
             "Vuelve a correr presentaciones.py para pedirlas otra vez (ver presentacion_avisos del temario).")
    detalle = f"{{\\scriptsize {c.escapar(_recorte(motivo, 300))}\\par}}\n" if motivo else ""
    return Diapositiva(
        titulo=c.escapar(_recorte(bloque.titulo, 60)) if bloque else "Punto de partida de la sesión",
        cuerpo=f"\\begin{{cajaplana}}{{iuborange}}\n\\small\\centering\n{c.escapar(aviso)}\n\\end{{cajaplana}}\n{detalle}")


# ---------------------------------------------------------------------------
# El documento
# ---------------------------------------------------------------------------

def construir_tex(doc: Documento, apertura: list[Diapositiva], bloques: list[tuple[BloqueSesion, list[Diapositiva]]]) -> tuple[str, int]:
    """(el .tex completo, cuantas diapositivas tiene): portada, apertura, ruta, cada bloque con su separador y sus diapositivas,
    referencias y cierre. Los avisos del escapado quedan en `doc.conv.avisos`."""
    partes = [portada(doc)] + [diapositiva(d) for d in apertura]
    total = 1 + len(apertura)
    texto_ruta = ruta(doc, [b for b, _ in bloques])
    if texto_ruta:
        partes.append(texto_ruta)
        total += 1
    for k, (bloque, diapositivas) in enumerate(bloques):
        partes.append(separador(doc, bloque, k))
        partes += [diapositiva(d) for d in diapositivas]
        total += 1 + len(diapositivas)
    refs = referencias(doc)
    partes += refs
    partes.append(cierre(doc))
    total += len(refs) + 1
    cuerpo = "\n".join(partes)
    tex = (f"{preambulo(doc)}\n% =====================================================================\n\\begin{{document}}\n"
           f"% =====================================================================\n\n{cuerpo}\n\\end{{document}}\n")
    return tex, total
