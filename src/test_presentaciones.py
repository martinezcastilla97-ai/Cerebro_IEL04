"""Prueba de PRESENTACIONES (presentaciones.py, diseno_iub.py, schema_presentacion.py, latex_seguro.py) sin LLM real y SIN COMPILAR
(no exige LaTeX): el LLM se sustituye por diapositivas fijas (_fixtures.diapositivas_falsas) y se comprueba todo lo demas.

  A. latex_seguro: el escapado y las formulas de los datos; la lista de permitidos del LaTeX que escribe el modelo (verificar_cuerpo):
     lo que admite (TikZ, pgfplots, circuitikz, tablas, cajas, codigo) y lo que rechaza (\\input, \\write18, \\def, \\csname, ^^,
     variables con nombre de primitivo, \\addplot table/gnuplot, saveto, escapeinside, imagenes...); la verificacion del .tex completo
     y 1500 cuerpos al azar con tokens hostiles: lo que pasa la verificacion nunca lleva un comando fuera de la lista;
  B. el esquema: limites de titulo, cuerpo y cantidad de diapositivas;
  C. el diseno IUB: el preambulo de los ejemplos (paleta, avant, franja, pie, cajas, estilos TikZ, separador de bloque, sin imagenes),
     la portada, la ruta de la sesion, los separadores, las referencias y el cierre, y datos hostiles escapados;
  D. el flujo: una llamada por parte (apertura y bloques), el plan guardado por parte (rehacer sin LLM, pedir solo lo que cambio),
     reintentos, la diapositiva provisional, un plan manipulado, un .tex inseguro que no se escribe ni se compila, lint L14 y el comando.

Uso (desde src/):  python test_presentaciones.py
"""

import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import _fixtures
import diseno_iub
import figuras
import latex_seguro as ls
import lint
import planeador
import presentaciones
import temario
import vault
from schema_planeador import TemasSemana
from schema_presentacion import MAX_DIAPOSITIVAS_PARTE, MAX_TITULO, DiapositivaLatex, DiapositivasParte

SRC = Path(__file__).resolve().parent
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}


def esperar(excepcion, funcion, *args, **kwargs) -> str:
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


def doc_de_prueba(**extra) -> diseno_iub.Documento:
    datos = dict(codigo="ABC01", asignatura="Asignatura de prueba", titulo="Título de la sesión de prueba", semana=3, total_semanas=14,
                 docente="Docente de prueba", programa="Programa de prueba", duracion_min=120, corte=1, tipo_sesion="teórica",
                 subtitulo="Plataforma de prueba", siguiente="Próxima sesión · Semana 4: Tema 4", contacto="docente@ejemplo.edu.co",
                 referencias=["[1] A. Autor, Libro, 2020.", "[2] B. Autor, Otro libro, 2021."])
    datos.update(extra)
    return diseno_iub.Documento(**datos)


def cuerpo(clave: str) -> str:
    normalizado, problemas = ls.verificar_cuerpo(_fixtures.CUERPOS_FALSOS[clave])
    assert not problemas, (clave, problemas)
    return normalizado


# --- A. latex_seguro -------------------------------------------------------------------------------------------------------

HOSTILES = {
    "\\input{/etc/passwd}": "\\input",
    "\\immediate\\write18{rm -rf}": "\\write",
    "\\def\\x{1}": "\\def",
    "\\let\\a\\b": "\\let",
    "\\newcommand{\\a}{b}": "\\newcommand",
    "\\csname input\\endcsname{x}": "\\csname",
    "^^5cinput{x}": "^^",
    "\\catcode`\\|=0 |input{x}": "\\catcode",
    "\\foreach \\input in {1}{} \\input{x}": "(como variable)",
    "\\pgfmathsetmacro{\\write}{1}": "(como variable)",
    "\\foreach \\x [count=\\openin] in {1}{}": "(como variable)",
    "\\includegraphics{figuras/a.png}": "\\includegraphics",
    "\\usepackage{x}": "\\usepackage",
    "\\lstinline{x}": "\\lstinline",
    "\\verb|x|": "\\verb",
    "\\url{http://x}": "\\url",
    "\\href{run:x}{y}": "\\href",
    "\\pause": "\\pause",
    "\\section{x}": "\\section",
    "\\InputIfFileExists{x}{}{}": "\\InputIfFileExists",
    "\\pdffiledump{x}": "\\pdffiledump",
    "\\begin{frame}{x} a \\end{frame}": "\\begin{frame}",
    "\\begin{verbatim} x \\end{verbatim}": "\\begin{verbatim}",
    "\\begin{lstlisting} x \\end{lstlisting}": "\\begin{lstlisting}",
    "\\begin{tikzpicture}\\begin{axis}\\addplot table {/etc/passwd};\\end{axis}\\end{tikzpicture}": "`\\addplot table`",
    "\\begin{tikzpicture}\\begin{axis}\\addplot gnuplot {x};\\end{axis}\\end{tikzpicture}": "`\\addplot gnuplot`",
    "\\begin{tikzpicture}\\begin{axis}\\addplot+[red, mark=*] shell {ls};\\end{axis}\\end{tikzpicture}": "`\\addplot shell`",
    "\\begin{tikzpicture}\\begin{axis}\\addplot graphics {x.png};\\end{axis}\\end{tikzpicture}": "`\\addplot graphics`",
    "\\begin{caja}[saveto=x.tex]{iubblue}{T} a \\end{caja}": "`saveto`",
    "\\begin{caja}[record={x}]{iubblue}{T} a \\end{caja}": "`record`",
    "\\begin{cajaplana}[listing file=x]{iubblue} a \\end{cajaplana}": "`listing file`",
    "\\begin{codebox}[escapeinside=||]{t}\n|\\input{x}|\n\\end{codebox}": "opciones de codebox",
    "\\begin{codebox}[listing options app={escapeinside=||}]{t}\n|\\input{x}|\n\\end{codebox}": "opciones de codebox",
    "\\begin{codebox}[listing options={mathescape}]{t}\nx\n\\end{codebox}": "opciones de codebox",
    "\\begin{codebox}{t} x \\end{codebox}": "cada codebox va así",
    "63.2 % de algo": "un % sin escapar",
    "el # uno": "un # sin escapar",
    "una {llave": "llaves",
    "\\begin{itemize} \\item a": "entornos sin cerrar",
    "una $fórmula sin cerrar": "número impar de signos $",
    "emoji 😀": "U+1F600",
}


def probar_latex_seguro() -> None:
    c = ls.Conversor()
    assert c.escapar("50 % de $x_1$ & #3 {a} ~ \\ ^") == r"50 \% de \$x\_1\$ \& \#3 \{a\} \textasciitilde{} \textbackslash{} \^{}"
    assert c.inline("texto \\input{/etc/passwd}") == r"texto \textbackslash{}input\{/etc/passwd\}", "en los datos, una barra invertida es texto"
    assert c.matematicas(r"\input{x} + a^^5c").count(r"\text{\textbackslash{}") == 1 and "^^" not in c.matematicas("a^^5c")
    simbolos = c.escapar("W = CV² · 2.ª ed. · 5 m³ · ¼ · ‰ · ¬ · nº 1")
    assert not ls.comandos_no_admitidos(simbolos), "lo que escribe el Conversor pasa la lista de permitidos"
    print("A1. los datos del temario y del wiki (títulos, docente, referencias) se escapan, y sus fórmulas solo admiten comandos matemáticos -- OK")

    for clave in _fixtures.CUERPOS_FALSOS:
        cuerpo(clave)
    admitidos = [
        r"\begin{tikzpicture}\foreach \y/\c/\verbo/\nivel [count=\i] in {0/iubblue/Identificar/Comprender}{\node[nodo=\c] at (0,\y) {\verbo}; \node at (2,\y) {\nivel \i};}\end{tikzpicture}",
        r"\begin{tikzpicture}\pgfmathsetmacro{\paso}{0.8}\draw (0,0) -- (\paso,0);\end{tikzpicture}",
        r"\begin{tikzpicture}\begin{axis}\addplot+[mark=*] coordinates {(0,1) (1,2)}; \addplot[domain=0:1] {x^2}; \addplot3 {x*y};\end{axis}\end{tikzpicture}",
        r"\renewcommand{\arraystretch}{1.4}\begin{tabular}{ll}\rowcolor{iubnavy}\hd{a} & \thc{b}\\ 1 & 2\\\end{tabular}",
        r"\begin{columns}[T,onlytextwidth]\column{0.5\textwidth}\begin{cardG}[height=3cm]{T}\alert{x} $\qty{5}{\volt}$ \cod{f()}\end{cardG}\end{columns}",
        r"\begin{align*} a &= b \\ c &= \frac{d}{e} \end{align*} 25\,\% \# \& \_ \$ \{",
    ]
    prompt = (SRC / "prompts" / "prompt-presentacion.md").read_text(encoding="utf-8")
    fragmentos = [re.sub(r"(?m)^    ", "", f) for f in re.findall(r"(?m)((?:^    .*\n)+)", prompt.split("### Fragmentos de referencia")[1])]
    assert len(fragmentos) == 5, len(fragmentos)
    admitidos += fragmentos                              # los fragmentos del prompt salen de las presentaciones de ejemplo del docente
    for texto in admitidos:
        assert ls.verificar_cuerpo(texto)[1] == [], (texto, ls.verificar_cuerpo(texto)[1])
    print(f"A2. la lista de permitidos (comandos, entornos y claves) admite el LaTeX de las presentaciones de ejemplo: cajas, TikZ con \\foreach y "
          f"\\pgfmathsetmacro, pgfplots, circuitikz, tablas, código, y los fragmentos de referencia del prompt ({len(admitidos) + len(_fixtures.CUERPOS_FALSOS)} cuerpos) -- OK")

    claves_hostiles = {
        "\\tikzset{every node/.style={red}}": "\\tikzset",
        "\\tikzset{flecha}": "\\tikzset",
        "\\begin{tikzpicture}\\node[execute at begin node={\\textbf{x}}] {a};\\end{tikzpicture}": "`execute at begin node`",
        "\\begin{tikzpicture}\\node[mistilo/.code={\\textbf{x}}] {a};\\end{tikzpicture}": "`/.code`",
        "\\begin{tikzpicture}\\node[mistilo/.style={red}, mistilo] {a};\\end{tikzpicture}": "`/.style`",
        "\\begin{tikzpicture}[caja/.store in=\\x]\\end{tikzpicture}": "`/.store in`",
        "\\begin{tikzpicture}[a/.initial=1, b/.expanded=x]\\end{tikzpicture}": "`/.initial`",
        "\\begin{tikzpicture}[desconocida]\\draw (0,0) -- (1,1);\\end{tikzpicture}": "`desconocida`",
        "\\begin{tikzpicture}[external/system call={x}]\\end{tikzpicture}": "`external/system call`",
        "\\begin{tikzpicture}\\begin{axis}[every axis plot/.append style={red}]\\addplot {x};\\end{axis}\\end{tikzpicture}": "`/.append style`",
        "\\begin{tikzpicture}\\begin{axis}[x filter/.expression={x}]\\addplot {x};\\end{axis}\\end{tikzpicture}": "`/.expression`",
        "\\begin{tikzpicture}\\begin{axis}[after end axis={\\node {x};}]\\addplot {x};\\end{axis}\\end{tikzpicture}": "`after end axis`",
        "\\begin{tikzpicture}\\begin{axis}[legend style={execute at begin node=x}]\\addplot {x};\\end{axis}\\end{tikzpicture}": "`execute at begin node`",
        "\\begin{tikzpicture}\\begin{axis}\\addplot[/pgf/number format/.cd, fixed] {x};\\end{axis}\\end{tikzpicture}": "`/.cd`",
        "\\begin{caja}[before upper={\\textbf{x}}]{iubblue}{T} a \\end{caja}": "`before upper`",
        "\\begin{cardB}[code={\\textbf{x}}]{T} a \\end{cardB}": "`code`",
        "\\begin{adjustbox}{execute={\\textbf{x}}} a \\end{adjustbox}": "`execute`",
        "\\begin{tikzpicture}\\draw[fill={red, execute at begin node=x}] (0,0) circle (1);\\end{tikzpicture}": "el valor tiene que ser un color",
        "\\begin{tikzpicture}\\node[bloque={red, execute at end node=x}] {a};\\end{tikzpicture}": "el valor tiene que ser un color",
        "\\begin{tikzpicture}\\foreach \\c in {{red, execute at end node=x}}{\\fill[\\c] (0,0) circle (1);}\\end{tikzpicture}": "`\\c`",
        "\\begin{tikzpicture}\\node[label={[execute at begin node=x]above:t}] {a};\\end{tikzpicture}": "`execute at begin node`",
        "\\tikz[append after command={x}] \\draw (0,0);": "`append after command`",
        "\\foreach \\x [/tikz/execute at begin node=y] in {1}{\\x}": "`/tikz/execute at begin node`",
        "\\begin{circuitikz}\\draw (0,0) to[R, execute at begin to={x}] (1,0);\\end{circuitikz}": "`execute at begin to`",
    }
    for texto, esperado in claves_hostiles.items():
        _, problemas = ls.verificar_cuerpo(texto)
        assert any(esperado in p for p in problemas), (texto, esperado, problemas)
    ok = "\\begin{tikzpicture}\\foreach \\c/\\t in {iubblue/a, iuborange!40!white/b}{\\node[bloque=\\c, \\c, draw=\\c] {\\t};}\\draw[-{Stealth[length=2mm]}, shorten >=2pt] (0,0) -- (1,0);\\end{tikzpicture}"
    assert ls.verificar_cuerpo(ok)[1] == [], ls.verificar_cuerpo(ok)[1]
    print(f"A2b. las OPCIONES también van con lista de permitidos: {len(claves_hostiles)} claves desconocidas o manejadores (/.code, /.style, /.append style, "
          "/.store in, /.cd...) en \\tikzset, nodos, ejes, cajas, adjustbox, circuitos y colores de un \\foreach se rechazan -- OK")

    for texto, esperado in HOSTILES.items():
        _, problemas = ls.verificar_cuerpo(texto)
        assert any(esperado in p for p in problemas), (texto, esperado, problemas)
    assert ls.verificar_cuerpo(r"\renewcommand{\x}{1}")[1], "solo se admite redefinir \\arraystretch"
    print(f"A3. la lista rechaza, con el motivo para el modelo, {len(HOSTILES)} construcciones: primitivos que leen o escriben archivos, definiciones, "
          "\\csname, ^^, \\catcode, variables con nombre de primitivo, imágenes, \\addplot table/gnuplot/shell, saveto, escapeinside, % y # sueltos, llaves -- OK")

    normalizado, problemas = ls.verificar_cuerpo(_fixtures.CUERPOS_FALSOS["codigo"])
    assert not problemas and "\\end {frame}" in normalizado and "\n\\end{frame}" not in normalizado and "transicion" in normalizado
    normalizado, problemas = ls.verificar_cuerpo("\\begin{codebox}[ language=C , firstnumber=3 ]{a.c}\nx = 1;\n\\end{codebox}")
    assert not problemas and "\\begin{codebox}[listing options app={language=C,firstnumber=3}]{a.c}\nx = 1;\n\\end{codebox}" in normalizado
    normalizado, problemas = ls.verificar_cuerpo("\\begin{codebox}[listing options app={firstnumber=19}]{a.m}\n% comentario de MATLAB\nx = 1;\n\\end{codebox}")
    assert not problemas and "[listing options app={firstnumber=19}]" in normalizado and "% comentario de MATLAB" in normalizado, "un % del código es código"
    normalizado, problemas = ls.verificar_cuerpo("\\foreach \\y/\\t in {%\n    0/Uno,%\n    1/Dos%\n  }{\\node at (0,\\y) {\\t};}")
    assert not problemas and "{0/Uno,1/Dos}" in normalizado, ("un % al final de línea une las líneas, como en TeX", normalizado)
    _, problemas = ls.verificar_cuerpo("\\begin{codebox}{a.c}\nx = 1; \\end{codebox} \\input{x}\n\\end{codebox}")
    assert problemas, "un \\end{codebox} a media línea cierra el bloque: lo que sigue se revisa como LaTeX (y el \\end suelto se rechaza)"
    normalizado, problemas = ls.verificar_cuerpo("% un comentario\nflecha → y $α$ y ≤\n")
    assert not problemas and "%" not in normalizado and r"\ensuremath{\rightarrow}" in normalizado and r"\ensuremath{\alpha}" in normalizado
    print("A4. se normaliza sin cambiar el sentido: el código a ASCII con \\end{frame} y \\end{codebox} neutralizados, las opciones del codebox canónicas, "
          "sin comentarios y los símbolos Unicode como \\ensuremath -- OK")

    tex, _ = diseno_iub.construir_tex(doc_de_prueba(), [diseno_iub.Diapositiva("A", cuerpo("cajas"))],
                                      [(diseno_iub.BloqueSesion(1, "Uno", 30), [diseno_iub.Diapositiva("B", cuerpo("codigo"))])])
    assert ls.verificar_latex(tex) == [], ls.verificar_latex(tex)
    for inyectado, esperado in (("\\input{secreto.txt}", "primitivas de TeX peligrosas"), ("\\includegraphics{a.png}", "primitivas de TeX peligrosas"),
                                ("\\openin5=x", "primitivas de TeX peligrosas"), ("\\pdffiledump{x}", "comandos o entornos no admitidos"),
                                ("\\begin{tikzpicture}\\node[execute at begin node=x] {a};\\end{tikzpicture}", "opciones no admitidas"),
                                ("\\begin{tikzpicture}[x/.code={a}]\\end{tikzpicture}", "opciones no admitidas"), ("\\begin{tikzpicture}\\begin{axis}\\addplot table {x};\\end{axis}\\end{tikzpicture}", "leen archivos")):
        malo = tex.replace("\\end{document}", inyectado + "\n\\end{document}")
        assert any(esperado in p for p in ls.graves(ls.verificar_latex(malo))), (inyectado, ls.verificar_latex(malo))
    sin_neutralizar = tex.replace("\\end {frame}", "\\end{frame}")
    assert any("un bloque de código contiene" in p for p in ls.graves(ls.verificar_latex(sin_neutralizar)))
    sin_fragil = tex.replace("\\begin{frame}[fragile]", "\\begin{frame}")
    assert any("[fragile]" in p for p in ls.verificar_latex(sin_fragil)) and not ls.graves(ls.verificar_latex(sin_fragil))
    print("A5. la verificación del .tex completo (segunda capa) lo acepta, y marca como GRAVE un \\input, una imagen, un primitivo o un \\addplot table "
          "inyectados y un \\end{frame} en el código; sin [fragile] es un problema, no grave -- OK")

    rng = random.Random(11)
    fichas = ["\\node", "\\draw", "(0,0)", "--", ";", "{", "}", "[", "]", "texto", " ", "\n", "$", "x", "^", "_", "\\\\", "\\textbf", "\\input",
              "\\write", "\\def", "\\csname", "\\endcsname", "\\catcode", "^^", "\\foreach", "\\x", "\\openin", "in", "{1,2}", "\\pgfmathsetmacro",
              "\\immediate", "\\addplot", "table", "coordinates", "gnuplot", "\\begin{codebox}{t}\n", "\n\\end{codebox}", "\\end{frame}",
              "\\begin{axis}", "\\end{axis}", "saveto=", "%", "\\%", "\\includegraphics", "\\let", "\\expandafter", "\\scantokens", "@", "\\makeatletter",
              "\\begin{tikzpicture}", "\\end{tikzpicture}", "[execute at begin node=x]", "[red]", "[fill=red]", "/.code", "[x/.style={red}]",
              "\\tikzset", "\\tikz", "[bloque={red,execute at end node=y}]"]
    prohibidos = ls._PRIMITIVAS_PELIGROSAS | {"csname", "catcode", "expandafter", "scantokens", "makeatletter", "openin", "immediate", "tikzset"}
    admitidas = 0
    for _ in range(2500):
        texto = "".join(rng.choice(fichas) for _ in range(rng.randint(3, 16)))
        normalizado, problemas = ls.verificar_cuerpo(texto)
        if problemas:
            continue
        admitidas += 1
        sin_codigo = re.sub(r"\\begin\{codebox\}.*?\\end\{codebox\}", "", normalizado, flags=re.S)
        assert not ({m for m in re.findall(r"\\([A-Za-z]+)", sin_codigo.replace("\\\\", "")) } & prohibidos) and "^^" not in sin_codigo, texto
        assert "/." not in sin_codigo and not ls.opciones_no_admitidas(sin_codigo), texto     # fuera de TikZ, un [..] es texto
        documento, _ = diseno_iub.construir_tex(doc_de_prueba(), [], [(diseno_iub.BloqueSesion(1, "U", 10), [diseno_iub.Diapositiva("T", normalizado)])])
        assert not ls.graves(ls.verificar_latex(documento)), (texto, ls.verificar_latex(documento))
    assert admitidas >= 20, admitidas
    print(f"A6. 2500 cuerpos al azar con fichas hostiles: los {admitidas} que pasan la verificación no llevan ningún primitivo peligroso, manejador ni clave desconocida fuera del código "
          "y su .tex completo no tiene problemas graves -- OK")


# --- B. el esquema ---------------------------------------------------------------------------------------------------------


def probar_esquema() -> None:
    bueno = "\\begin{caja}{iubblue}{T} contenido \\end{caja}"
    assert DiapositivaLatex(titulo="  Título  ", cuerpo=f"  {bueno}  ").titulo == "Título"
    assert "máximo es" in esperar(ValueError, DiapositivaLatex, titulo="t" * (MAX_TITULO + 1), cuerpo=bueno)
    assert DiapositivaLatex(titulo="\\textbf{" + "t" * (MAX_TITULO - 2) + "} $x_1$", cuerpo=bueno), "los comandos no cuentan como texto visible"
    assert "no tiene cuerpo" in esperar(ValueError, DiapositivaLatex, titulo="T", cuerpo="x")
    assert "sin \\begin{frame}" in esperar(ValueError, DiapositivaLatex, titulo="T", cuerpo="\\begin{frame}{x}" + bueno + "\\end{frame}")
    d = DiapositivaLatex(titulo="T", cuerpo=bueno)
    assert "de 1 a" in esperar(ValueError, DiapositivasParte, diapositivas=[])
    assert "de 1 a" in esperar(ValueError, DiapositivasParte, diapositivas=[d] * (MAX_DIAPOSITIVAS_PARTE + 1))
    print("B1. el esquema rechaza, con un mensaje para el modelo, un título largo, un cuerpo vacío o con \\begin{frame} y una parte sin diapositivas o con demasiadas -- OK")


# --- C. el diseno --------------------------------------------------------------------------------------------------------


def probar_diseno() -> None:
    doc = doc_de_prueba()
    apertura = [diseno_iub.Diapositiva("Punto de partida de la sesión", cuerpo("cajas")), diseno_iub.Diapositiva("Resultados de aprendizaje", cuerpo("flujo"))]
    bloques = [(diseno_iub.BloqueSesion(1, "Introducción conceptual", 30), [diseno_iub.Diapositiva("Una gráfica", cuerpo("grafica"))]),
               (diseno_iub.BloqueSesion(2, "Caso de estudio", 45), [diseno_iub.Diapositiva("Una tabla", cuerpo("tabla")),
                                                                     diseno_iub.Diapositiva("Un circuito", cuerpo("circuito"))]),
               (diseno_iub.BloqueSesion(3, "Síntesis", 15), [diseno_iub.Diapositiva("Código", cuerpo("codigo")), diseno_iub.Diapositiva("Cita", cuerpo("cita"))])]
    tex, total = diseno_iub.construir_tex(doc, apertura, bloques)
    assert ls.verificar_latex(tex) == [], ls.verificar_latex(tex)
    for color, hexa in (("iubnavy", "121023"), ("iubyellow", "FFDF2D"), ("iubwhite", "FFFFFF"), ("iubblue", "00ADE7"), ("iuborange", "E39037"), ("iubgreen", "3B9C6D")):
        assert f"\\definecolor{{{color}}}{{HTML}}{{{hexa}}}" in tex
    for requisito in (r"\usepackage{avant}", r"\renewcommand{\familydefault}{\sfdefault}", r"\documentclass[aspectratio=169", r"\usepackage{tikz}",
                      r"\usepackage{pgfplots}", r"\usepackage[most]{tcolorbox}", r"circuitikz}", r"\newtcolorbox{caja}", r"\newtcolorbox{cardN}",
                      r"\newtcblisting{codebox}", r"\newcommand{\bloque}[4]", r"\setbeamertemplate{headline}", r"{IUB}", r"flecha/.style",
                      "Semana 3 \\quad \\insertframenumber", "Docente de prueba", "es-noshorthands"):
        assert requisito in tex, requisito
    assert "includegraphics" not in tex and "logo" not in tex.lower() and ".png" not in tex, "sin imágenes: la marca va como texto y las figuras en TikZ"
    print("C1. el preámbulo es el de las presentaciones de ejemplo: paleta IUB, avant sans serif, franja con el título y «IUB», pie con módulo, docente y semana, "
          "cajas, codebox, estilos TikZ y el separador \\bloque; sin ninguna imagen -- OK")

    documento = tex.partition("\\begin{document}")[2]
    assert documento.count("\\begin{frame}") + documento.count("\\bloque{") == total == 1 + 2 + 1 + 3 + 5 + 1 + 1, total
    assert "\\bloque{01}{Introducción conceptual}{30 min}{iubblue}" in documento and "\\bloque{03}{Síntesis}{15 min}{iubgreen}" in documento
    ruta = re.search(r"\\begin\{frame\}\{Ruta de la sesión.*?\\end\{frame\}", documento, re.S).group(0)
    assert "Ruta de la sesión \\textperiodcentered{} 90 minutos" in ruta and ruta.count("min};") == 3 and "{Caso de estudio}" in ruta
    assert "Plataforma de prueba" in documento and "Corte evaluativo 1" in documento and "Sesión teórica" in documento
    assert "\\begin{frame}[fragile]{Código}" in documento and "\\textexclamdown{}Gracias!" in documento and "Semana 4: Tema 4" in documento
    assert "\\item[{$[1]$}] A. Autor" in documento
    refs = diseno_iub.referencias(doc_de_prueba(referencias=[f"[{k}] " + "Autor, título largo de una referencia de prueba. " * 3 for k in range(1, 13)]))
    assert len(refs) >= 3 and all(r.count("\\item[") <= diseno_iub.MAX_REFERENCIAS for r in refs) and "(1/" in refs[0]
    print(f"C2. el documento: portada, apertura, ruta de la sesión con los minutos, un separador por bloque, las diapositivas del modelo ([fragile] con código), "
          f"referencias paginadas y cierre ({total} diapositivas) -- OK")

    hostil = "\\input{/etc/passwd} \\write18{x} % # _ ^ ~ } { \\def\\x{y} ^^5c"
    doc = doc_de_prueba(titulo=hostil, docente=hostil, programa=hostil, asignatura=hostil, subtitulo=hostil, contacto=hostil, siguiente=hostil,
                        referencias=[f"[1] {hostil}"])
    tex, _ = diseno_iub.construir_tex(doc, [], [(diseno_iub.BloqueSesion(1, hostil, 10), [diseno_iub.provisional(doc, diseno_iub.BloqueSesion(1, hostil, 10), hostil)])])
    assert ls.verificar_latex(tex) == [], ls.verificar_latex(tex)
    print("C3. los datos hostiles del wiki y del temario (docente, programa, títulos, referencias) se escapan en la portada, el pie, los separadores y el cierre -- OK")

    temario_md = """# Título
> **Plataforma de referencia:** Arduino UNO

## 1. Metadatos de la Sesión

### 1.1 Continuidad curricular

Texto de continuidad.

## 2. Resultados de Aprendizaje

RA y criterios.

## 3. Índice Temporizado (120 minutos)

| Bloque | Contenido | Duración |
|---|---|---|
| 1 | Introducción al tema | 20 min |
| 2 | **Concepto uno** | 40 min |
| 3 | Síntesis y cierre | 60 min |
|  | **Total** | **120 min** |

## 4. Desarrollo Teórico

### 4.1 Introducción Conceptual (Bloque 1)

Intro.

![Figura 1. Curva de carga](figuras/x.png)

### 4.2 Conceptos Clave

#### 4.2.1 Concepto uno (Bloque 2)

Texto del concepto.

## 5. Síntesis (Bloque 3)

Síntesis.

### Componente Actitudinal

> *Reflexión.*

## 6. Bibliografía (Formato IEEE)

[1] A. Autor, Libro, 2020.
"""
    partes = presentaciones.partes_del_temario(temario_md)
    assert [p.clave for p in partes] == ["apertura", "bloque-01", "bloque-02", "bloque-03"]
    assert "Continuidad" in partes[0].texto and "Índice" not in partes[0].texto
    assert (partes[1].titulo, partes[1].bloque.minutos) == ("Introducción al tema", 20) and "Conceptos Clave" not in partes[1].texto
    assert "figuras/x.png" not in partes[1].texto and "FIGURA DEL TEMARIO" in partes[1].texto and "Curva de carga" in partes[1].texto
    assert partes[2].titulo == "Concepto uno" and "Componente Actitudinal" in partes[3].texto and "Bibliografía" not in partes[3].texto
    assert presentaciones.plataforma_del_temario(temario_md) == "Arduino UNO" and presentaciones.referencias_del_temario(temario_md) == ["[1] A. Autor, Libro, 2020."]
    sueltas = presentaciones.partes_del_temario("# T\n\nUn temario editado a mano, sin bloques.\n\n## 9. Bibliografía\n\n[1] X.\n")
    assert [p.clave for p in sueltas] == ["bloque-01"] and "sin bloques" in sueltas[0].texto and "[1] X." not in sueltas[0].texto
    print("C4. el temario se divide en la apertura (secciones 1 y 2) y sus bloques, con el título y los minutos del índice temporizado; las figuras PNG se "
          "describen para redibujarlas en TikZ y un temario sin bloques se trata como uno solo -- OK")


# --- D. el flujo ---------------------------------------------------------------------------------------------------------


LLAMADAS: list[str] = []
RESPUESTAS: list = []           # respuestas que devolvera el LLM falso antes de las de _fixtures


def llm_falso(sistema, usuario, formato):
    if formato is DiapositivasParte:
        LLAMADAS.append(usuario)
        if RESPUESTAS:
            respuesta = RESPUESTAS.pop(0)
            return respuesta(usuario) if callable(respuesta) else respuesta
        return _fixtures.diapositivas_falsas(usuario)
    if formato is TemasSemana:
        n = int(re.search(r"Semanas de clase de este RA: (\d+)", usuario).group(1))
        return TemasSemana(temas=[f"Tema {i}" for i in range(1, n + 1)])
    return _fixtures.responder_temario(usuario, formato)


def comando(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(SRC / "presentaciones.py"), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)


def fm_temario(semana: int) -> dict:
    return vault.leer_pagina(vault.TEMARIOS / f"TPR01-semana{semana:02d}.md")[0]


def partes_de(semana: int) -> list:
    return presentaciones.partes_del_temario(vault.leer_pagina(vault.TEMARIOS / f"TPR01-semana{semana:02d}.md")[1])


def editar_sintesis(semana: int, texto: str) -> None:
    """Agrega una linea al final del bloque de sintesis (justo antes de la bibliografia): cambia UNA parte del temario."""
    ruta = vault.TEMARIOS / f"TPR01-semana{semana:02d}.md"
    fm, cuerpo_md = vault.leer_pagina(ruta)
    nuevo = re.sub(r"(?m)^(##\s+\d+\.\s+Bibliograf)", f"{texto}\n\n\\1", cuerpo_md, count=1)
    assert nuevo != cuerpo_md
    vault.escribir_pagina(ruta, fm, nuevo)


def probar_flujo(raiz: Path) -> None:
    vault.pedir_estructurado = llm_falso
    figuras.dibujar_grafica = figuras.dibujar_diagrama = lambda spec, destino: _fixtures.png_falso(destino)
    planeador.generar_planeador("TPR01")
    for semana in (1, 2):
        temario.generar_temario("TPR01", semana)
    LLAMADAS.clear()
    carpeta = Path("generacion/presentaciones/TPR01")
    n1, n2 = len(partes_de(1)), len(partes_de(2))
    assert n1 >= 5 and partes_de(1)[0].clave == "apertura"

    resultados = presentaciones.generar_presentaciones("TPR01", "Docente Uno", "Programa Uno")
    assert [(r.name, e, n) for r, e, n in resultados] == [("TPR01-semana01.tex", "generada", n1), ("TPR01-semana02.tex", "generada", n2)], resultados
    assert len(LLAMADAS) == n1 + n2 and "Diseña exactamente 2 diapositivas para abrir la sesión" in LLAMADAS[0]
    assert "para el bloque 1" in LLAMADAS[1] and "figuras/TPR01" not in "".join(LLAMADAS), "las figuras PNG no se ofrecen como imagen"
    archivos = {p.relative_to(carpeta).as_posix() for p in carpeta.rglob("*") if p.is_file()}
    assert archivos == {"TPR01-semana01.tex", "TPR01-semana01.plan.json", "TPR01-semana02.tex", "TPR01-semana02.plan.json"}, "sin logos ni figuras: todo es TikZ"
    plan = json.loads((carpeta / "TPR01-semana01.plan.json").read_text(encoding="utf-8"))
    assert plan["formato"] == presentaciones.FORMATO_PLAN and len(plan["partes"]) == n1
    fm = fm_temario(1)
    assert fm["presentacion_estado"] == "generada" and fm["presentacion_avisos"] == [] and fm["presentacion_diseno"] == diseno_iub.VERSION
    assert fm["presentacion_docente"] == "Docente Uno" and fm["presentacion_diapositivas"] > 10
    tex = (carpeta / "TPR01-semana01.tex").read_text(encoding="utf-8")
    assert ls.verificar_latex(tex) == [] and "Docente Uno" in tex and "\\bloque{01}" in tex and "\\begin{frame}[fragile]" in tex and "\\end {frame}" in tex
    assert "/presentaciones TPR01" in Path("wiki/log.md").read_text(encoding="utf-8")
    print(f"D1. una llamada por parte ({n1} y {n2}: la apertura y cada bloque), sin ofrecer las figuras como imagen: .tex y plan por partes, sin logos ni PNG, "
          "y los campos presentacion_* en el temario -- OK")

    LLAMADAS.clear()
    assert {e for _, e, _ in presentaciones.generar_presentaciones("TPR01", "Docente Uno", "Programa Uno")} == {"omitida"} and not LLAMADAS
    resultados = presentaciones.generar_presentaciones("TPR01", "Docente Dos", "Programa Uno")
    assert {(e, n) for _, e, n in resultados} == {("generada", 0)} and not LLAMADAS and "Docente Dos" in (carpeta / "TPR01-semana01.tex").read_text(encoding="utf-8")
    assert {(e, n) for _, e, n in presentaciones.generar_presentaciones("TPR01", forzar=True)} == {("generada", 0)} and not LLAMADAS
    version = presentaciones.DISENO
    presentaciones.DISENO = version + 1
    try:
        assert {(e, n) for _, e, n in presentaciones.generar_presentaciones("TPR01")} == {("generada", 0)} and not LLAMADAS
        l14 = [h.mensaje for h in lint.revisar() if h.regla == "L14"]
    finally:
        presentaciones.DISENO = version
    assert not l14, "rehecha con la versión nueva, lint no avisa"
    assert {(e, n) for _, e, n in presentaciones.generar_presentaciones("TPR01")} == {("generada", 0)} and not LLAMADAS
    print("D2. al día se omite; otro docente, --forzar o una versión nueva del diseño rehacen el .tex desde el plan guardado, SIN llamar al modelo -- OK")

    editar_sintesis(1, "Una línea editada a mano en la síntesis.")
    hallazgos = [h for h in lint.revisar() if h.regla == "L14"]
    assert len(hallazgos) == 1 and "desactualizada" in hallazgos[0].mensaje and "pidiendo al modelo 1 parte(s)" in hallazgos[0].mensaje, hallazgos
    (_, estado, pedidas), = presentaciones.generar_presentaciones("TPR01", semanas=[1])
    assert (estado, pedidas) == ("generada", 1) and len(LLAMADAS) == 1 and "Una línea editada a mano" in LLAMADAS[0], "solo el bloque que cambió"
    LLAMADAS.clear()
    fm, cuerpo_md = vault.leer_pagina(vault.TEMARIOS / "TPR01-semana01.md")
    vault.escribir_pagina(vault.TEMARIOS / "TPR01-semana01.md", fm, cuerpo_md.rstrip() + "\n\n[9] Una referencia agregada a mano.\n")
    assert [(e, n) for _, e, n in presentaciones.generar_presentaciones("TPR01", semanas=[1])] == [("generada", 0)], "la bibliografía no es una parte: 0 llamadas"
    assert "Una referencia agregada a mano" in (carpeta / "TPR01-semana01.tex").read_text(encoding="utf-8")
    presentaciones.generar_presentaciones("TPR01", semanas=[2], replanificar=True)
    assert len(LLAMADAS) == n2
    assert not [h for h in lint.revisar() if h.regla == "L14"]
    print("D3. editar un bloque del temario vuelve a pedir SOLO ese bloque (lint L14 lo cuenta); editar la bibliografía no cuesta llamadas; --replanificar pide todas -- OK")

    ruta_plan = carpeta / "TPR01-semana02.plan.json"
    for corrupto in ("{}", "{no es json", json.dumps({"temario_hash": "x", "plan": {"secciones": []}})):
        ruta_plan.write_text(corrupto, encoding="utf-8")
        assert len(presentaciones.partes_pendientes(carpeta / "TPR01-semana02.tex", vault.leer_pagina(vault.TEMARIOS / "TPR01-semana02.md")[1])) == n2
    LLAMADAS.clear()
    presentaciones.generar_presentaciones("TPR01", semanas=[2], forzar=True)
    assert len(LLAMADAS) == n2, "un plan ilegible o del formato del diseño 4 no se reutiliza"
    datos = json.loads(ruta_plan.read_text(encoding="utf-8"))
    clave = sorted(datos["partes"])[1]
    datos["partes"][clave]["diapositivas"][0]["cuerpo"] += "\n\\input{secreto.txt}"
    ruta_plan.write_text(json.dumps(datos), encoding="utf-8")
    LLAMADAS.clear()
    (_, _, pedidas), = presentaciones.generar_presentaciones("TPR01", semanas=[2], forzar=True)
    assert pedidas == 1 and len(LLAMADAS) == 1, "la parte manipulada vuelve a pedirse; las demás siguen del plan"
    assert "secreto" not in (carpeta / "TPR01-semana02.tex").read_text(encoding="utf-8") and "secreto" not in ruta_plan.read_text(encoding="utf-8")
    print("D4. un .plan.json corrupto, del diseño 4 o manipulado (un \\input en un cuerpo) no se reutiliza: se revalida al leerlo y se vuelve a pedir solo lo que no pasa -- OK")

    LLAMADAS.clear()
    malo = DiapositivasParte(diapositivas=[DiapositivaLatex(titulo="Mala", cuerpo="\\begin{caja}{iubblue}{x}\\input{secreto.txt}\\end{caja}")])
    solo_texto = DiapositivasParte(diapositivas=[DiapositivaLatex(titulo=f"Viñetas {k}", cuerpo="\\begin{itemize}\\item a\\item b\\end{itemize}") for k in (1, 2)])
    RESPUESTAS.extend([malo, solo_texto])
    presentaciones.generar_presentaciones("TPR01", semanas=[1], replanificar=True)
    assert len(LLAMADAS) == n1 + 2
    assert "comandos o entornos no admitidos: \\input" in LLAMADAS[1] and "ninguna diapositiva usa un recurso visual" in LLAMADAS[2]
    print("D5. lo que no cumple (un comando fuera de la lista, un bloque sin ningún recurso visual) vuelve al modelo con el motivo -- OK")

    LLAMADAS.clear()
    RESPUESTAS.extend([malo] * 3)
    (destino, estado, _), = presentaciones.generar_presentaciones("TPR01", semanas=[1], replanificar=True)
    tex = destino.read_text(encoding="utf-8")
    assert estado == "revisar" and "secreto" not in tex and "no se generaron: el modelo no cumplió las reglas de LaTeX" in tex
    assert any("tras 3 intentos" in a for a in fm_temario(1)["presentacion_avisos"])
    assert len(presentaciones.partes_pendientes(destino, vault.leer_pagina(vault.TEMARIOS / "TPR01-semana01.md")[1])) == 1
    LLAMADAS.clear()
    (_, estado, pedidas), = presentaciones.generar_presentaciones("TPR01", semanas=[1])
    assert (estado, pedidas) == ("generada", 1) and len(LLAMADAS) == 1, "la próxima corrida pide solo la parte que quedó provisional"
    print("D6. si el modelo nunca cumple en una parte, queda una diapositiva provisional (estado `revisar`) y la presentación se escribe; la próxima corrida "
          "pide solo esa parte -- OK")

    construir = diseno_iub.construir_tex
    diseno_iub.construir_tex = lambda doc, a, b: (lambda t: (t[0].replace(r"\end{document}", "\\input{secreto.txt}\n\\end{document}"), t[1]))(construir(doc, a, b))
    try:
        (destino, estado, _), = presentaciones.generar_presentaciones("TPR01", semanas=[2], forzar=True)
    finally:
        diseno_iub.construir_tex = construir
    fm = fm_temario(2)
    assert estado == "revisar" and not destino.exists() and not ruta_plan.exists(), "ni el .tex inseguro ni el de antes, ni el plan que lo produjo"
    assert any("no se escribió el .tex" in a for a in fm["presentacion_avisos"]) and any("primitivas" in a for a in fm["presentacion_avisos"])
    assert any("ya no existe" in h.mensaje and f"pidiendo al modelo {n2} parte(s)" in h.mensaje for h in lint.revisar() if h.regla == "L14")

    peligroso = carpeta / "peligroso.tex"
    peligroso.write_text("\\documentclass{beamer}\n\\begin{document}\n\\input{secreto.txt}\n\\end{document}\n", encoding="utf-8")
    llamadas_pdflatex: list[list[str]] = []
    entornos: list[dict] = []
    which, run = presentaciones.shutil.which, presentaciones.subprocess.run
    presentaciones.shutil.which = lambda _: "pdflatex"
    presentaciones.subprocess.run = lambda args, **kw: (llamadas_pdflatex.append(args), entornos.append(kw.get("env") or {}))[0] or subprocess.CompletedProcess(args, 0, "", "")
    try:
        assert "no se compila peligroso.tex" in esperar(ValueError, presentaciones.compilar, peligroso) and not llamadas_pdflatex
        presentaciones.generar_presentaciones("TPR01", semanas=[2])
        presentaciones.compilar(carpeta / "TPR01-semana02.tex")
    finally:
        presentaciones.shutil.which, presentaciones.subprocess.run = which, run
        peligroso.unlink()
    assert len(llamadas_pdflatex) == 2 and all("-no-shell-escape" in a for a in llamadas_pdflatex), llamadas_pdflatex
    assert all(e.get("openin_any") == "p" and e.get("openout_any") == "p" and "PATH" in {k.upper() for k in e} for e in entornos), entornos
    print("D7. un .tex con algo que puede ejecutarse no se escribe (se borran el anterior y su plan; L14 dice cuántas partes costaría rehacerlo), compilar() "
          "se niega a compilarlo y pdflatex corre siempre con -no-shell-escape y openin_any=p, openout_any=p (sin leer ni escribir fuera de su carpeta) -- OK")

    (carpeta / "TPR01-semana02.tex").unlink()
    (carpeta / "huerfana.tex").write_text("x", encoding="utf-8")
    l14 = {h.mensaje.split(":")[0] for h in lint.revisar() if h.regla == "L14"}
    assert any("ya no existe" in m for m in l14) and any("ningún temario registra" in m for m in l14), l14
    (carpeta / "huerfana.tex").unlink()
    assert [(e, n) for _, e, n in presentaciones.generar_presentaciones("TPR01", semanas=[2])] == [("generada", 0)], "el plan sigue: se rehace sin LLM"
    assert not [h for h in lint.revisar() if h.regla == "L14"]
    assert "no hay temario de las semanas 3" in esperar(FileNotFoundError, presentaciones.generar_presentaciones, "TPR01", semanas=[3])

    LLAMADAS.clear()
    r = comando("TPR01", "--docente", "Docente Tres", "--programa", "Programa Tres", "--forzar", cwd=raiz)
    assert r.returncode == 0 and "2 presentaciones escritas (0 partes pedidas al modelo)" in r.stdout, (r.stdout, r.stderr)
    assert "Docente Tres" in (carpeta / "TPR01-semana02.tex").read_text(encoding="utf-8")
    editar_sintesis(1, "Otra edición.")
    r = comando("TPR01", "--sin-preguntar", cwd=raiz)                     # sin proveedor de IA configurado: error claro, no un traceback
    assert r.returncode == 1 and "ERROR: TPR01" in r.stdout and "Traceback" not in r.stderr, (r.stdout, r.stderr)
    r = comando("--all", "--semana", "1", cwd=raiz)
    assert r.returncode == 2 and "--semana va con un código" in r.stderr
    assert comando("--help", cwd=raiz).returncode == 0
    print("D8. lint L14 avisa de una presentación borrada o huérfana; como comando, rehacer con otro docente no cuesta llamadas, un temario cambiado sin "
          "proveedor de IA da un error claro y --help y los errores de uso funcionan -- OK")


def main() -> None:
    probar_latex_seguro()
    probar_esquema()
    probar_diseno()
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar_flujo(Path(tmp))
        finally:
            os.chdir(original)
    print("TODO OK -- las presentaciones salen del LaTeX que el modelo escribe por partes, verificado con una lista de permitidos, con el diseño IUB de "
          "los ejemplos; se rehacen sin LLM mientras el temario no cambie y se auditan (esta suite no compila).")


if __name__ == "__main__":
    main()
