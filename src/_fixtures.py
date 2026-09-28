"""Vault de muestra con datos INVENTADOS para las pruebas de src/ (no representa ningun
curriculo ni manual real). Lo usan test_generacion.py, test_lint.py, test_flujo_completo.py, test_presentaciones.py y test_analizar_cambios.py.

Contenido: un programa; TEO01 (teorica, HP=0, 1 RA); TPR01 (teorico-practica, HP=26, 3 RA);
un libro (`libro-a`) y un manual de banco (`banco-uno`, con 3 practicas) en wiki/fuentes/.

Tambien trae `responder_temario`, un LLM FALSO para los tres pasos de TEMARIO (plan, cada unidad y cierre): construye respuestas
validas a partir de lo que el prompt realmente pide (los criterios de evaluacion, los elementos de cada unidad, el minimo de
palabras...), igual que un LLM real tendria que hacerlo; `diapositivas_falsas`, las diapositivas en LaTeX de una parte de una
presentacion (cajas, TikZ, pgfplots, tablas, circuitikz, codigo); y `png_falso`, un PNG minimo para las pruebas que no necesitan dibujar.
"""

from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path

import vault
from figuras import Arista, DiagramaSpec, GraficaSpec, Nodo, Parametro, Serie
from schema_presentacion import DiapositivaLatex, DiapositivasParte
from schema_temario import Bloque, CierreSesion, PlanSesion, ResultadoSesion, SeccionRedactada, UnidadPlan

PROGRAMA = "Programa de prueba"
TEO01 = "TEO01 - Asignatura teórica de prueba"
TPR01 = "TPR01 - Asignatura teórico-práctica de prueba"


def ce(codigo: str, texto: str, categoria: str, confianza: float) -> dict:
    return {"codigo": codigo, "texto": texto, "categoria_accion": categoria, "confianza": confianza}


def practica(codigo: str, nombre: str, base: str) -> dict:
    return {
        "codigo": codigo, "nombre_original": nombre, "proposito": ["Proposito de ejemplo."],
        "principio_resumen": f"Resumen de {codigo}.", "equipos": [],
        "terminos_clave": [f"{base} a", f"{base} b", f"{base} c", f"{base} d"],
    }


def _ra(codigo: str, asignatura: str, tipo: str, horas: int, ces: list[dict], bibliografia: list[str]) -> dict:
    return {
        "tipo": "resultado_aprendizaje", "codigo": codigo, "enunciado": f"Enunciado de ejemplo de {codigo}.",
        "pertenece_a": f"[[{asignatura}]]", "tipo_abordaje": tipo, "horas": horas,
        "criterios_evaluacion": ces,
        "contenido_conceptual": [f"Tema A de {codigo}", f"Tema B de {codigo}"],
        "contenido_procedimental": [f"Procedimiento de {codigo}"], "contenido_actitudinal": ["Trabajo en equipo"],
        "bibliografia": [f"[[{b}]]" for b in bibliografia],
        "requiere_practica": None, "practica_experimentos": [],
        "correlacion_estado": None, "correlacion_revisado_por_docente": False,
        "fecha_creacion": "YYYY-MM-DD", "fecha_actualizacion": "YYYY-MM-DD",
    }


def _asignatura(codigo: str, nombre: str, had: int, hp: int, tipo: str, ras: list[str], hti: int = 60) -> dict:
    return {
        "tipo": "asignatura", "codigo": codigo, "nombre": nombre, "programa": [f"[[{PROGRAMA}]]"],
        "tipo_modulo": "TRANSVERSAL", "had_totales": had, "hp_totales": hp, "hti_totales": hti, "creditos": 2,
        "tipo_abordaje": tipo, "estrategia_practica_marcada": hp > 0, "recurso_laboratorio_marcado": hp > 0,
        "resultados_aprendizaje": [f"[[{r}]]" for r in ras], "competencias": [], "recursos_web": [],
        "fecha_creacion": "YYYY-MM-DD", "fecha_actualizacion": "YYYY-MM-DD",
    }


def armar_vault_muestra(raiz: Path) -> None:
    def pagina(ruta: str, fm: dict, cuerpo: str = "\n\n# Pagina de prueba\n") -> None:
        vault.escribir_pagina(raiz / ruta, fm, cuerpo)

    for carpeta in ("wiki/fuentes", "wiki/asignaturas", "wiki/resultados-aprendizaje", "wiki/programas",
                    "generacion/planeador", "generacion/temarios", "correlaciones"):
        (raiz / carpeta).mkdir(parents=True, exist_ok=True)

    pagina(f"wiki/programas/{PROGRAMA}.md", {
        "tipo": "programa", "nombre": PROGRAMA, "asignaturas": [f"[[{TEO01}]]", f"[[{TPR01}]]"],
        "resultados_programa": [{"codigo": "RA-PROG-1", "enunciado": "Enunciado de programa de ejemplo."}],
        "fecha_creacion": "YYYY-MM-DD", "fecha_actualizacion": "YYYY-MM-DD"})

    # hti_totales de cada una se elige para que had_totales + hti_totales == creditos x 48
    # (L13 de lint.py): 23+73 y 42+54 dan 96 = 2x48.
    pagina(f"wiki/asignaturas/{TEO01}.md", _asignatura("TEO01", "Asignatura teórica de prueba", 23, 0, "teórica", ["TEO01-RA1"], hti=73))
    pagina(f"wiki/asignaturas/{TPR01}.md",
           # had_totales=42 (no 26): had_totales YA incluye las horas practicas, y 42/14=3
           # es justo el limite para sesion de 4h (ver derivar_horas_sesion). hp_totales=26
           # sigue siendo el que deriva tipo_abordaje y alimenta score_RA, por separado.
           _asignatura("TPR01", "Asignatura teórico-práctica de prueba", 42, 26, "teórico-práctica",
                       ["TPR01-RA1", "TPR01-RA2", "TPR01-RA3"], hti=54))

    conceptual = ce("CE1", "Identificar conceptos.", "cognitiva_conceptual", 0.8)
    manipulacion = ce("CE2", "Realizar mediciones en el circuito.", "manipulacion_fisica", 0.95)
    pagina("wiki/resultados-aprendizaje/TEO01-RA1.md", _ra("TEO01-RA1", TEO01, "teórica", 18, [conceptual], ["libro-a"]))
    pagina("wiki/resultados-aprendizaje/TPR01-RA1.md", _ra("TPR01-RA1", TPR01, "teórico-práctica", 29, [conceptual, manipulacion], ["libro-a"]))
    pagina("wiki/resultados-aprendizaje/TPR01-RA2.md", _ra("TPR01-RA2", TPR01, "teórico-práctica", 29, [manipulacion], []))
    pagina("wiki/resultados-aprendizaje/TPR01-RA3.md", _ra("TPR01-RA3", TPR01, "teórico-práctica", 30, [conceptual], ["libro-a"]))

    pagina("wiki/fuentes/libro-a.md", {"tipo": "fuente", "etiquetas": ["libro"], "origen": "archivo"},
           "\n\n# Libro A\n\n## Resumen\nResumen del libro A: conceptos básicos de ejemplo.\n\n## Ver también\n[[banco-uno]]\n")
    pagina("wiki/fuentes/banco-uno.md", {
        "tipo": "fuente", "etiquetas": ["equipo-laboratorio"], "origen": "manual",
        "practicas": [practica("Exp1", "Practica de ejemplo A", "alfa"), practica("Exp2", "Practica de ejemplo B", "beta"),
                      practica("Exp3", "Practica de ejemplo C", "gamma")]},
           "\n\n# Banco uno\n\n## Resumen\nManual de banco de ejemplo.\n")

    pagina("wiki/index.md", {"tipo": "index", "fecha_actualizacion": "YYYY-MM-DD"}, "\n\n# Índice\n\nVer [[log]].\n")
    (raiz / "wiki" / "log.md").write_text("# Log\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# LLM falso de TEMARIO
# ---------------------------------------------------------------------------

# Lo que las pruebas pueden cambiar: cuantos conceptos, si el plan lleva analisis e implementacion, si usa graficas y ecuaciones.
CONFIG_TEMARIO: dict = {"conceptos": 3, "analisis": True, "implementacion": True, "usa_graficas": True, "usa_ecuaciones": True,
                        "externas": False}


def relleno(palabras: int) -> str:
    """Prosa de relleno con al menos `palabras` palabras."""
    frase = "Este desarrollo explica el contenido con datos, ejemplos y límites de validez propios del tema."      # 14 palabras
    return " ".join([frase] * (palabras // 14 + 1))


def plan_falso(usuario: str) -> PlanSesion:
    ce = re.search(r"Criterios de evaluación: (.+)", usuario).group(1)
    codigos = re.findall(r"\bCE\d+\b", ce)
    n_fuentes = int(re.search(r"Fuentes cargadas \((\d+);", usuario).group(1))
    tema = re.search(r"Tema de la semana: (.+)", usuario).group(1).strip()
    cfg = CONFIG_TEMARIO
    figura = "grafica" if cfg["usa_graficas"] else "diagrama"
    ec = ["ecuacion"] if cfg["usa_ecuaciones"] else []

    def unidad(clase: str, titulo: str, peso: int, elementos: list[str]) -> UnidadPlan:
        return UnidadPlan(clase=clase, titulo=titulo, descripcion=f"Descripción de {titulo}, unidad de la sesión.", peso=peso,
                          terminos_busqueda=["alfa", "beta", "gamma", "delta", "sistema de ejemplo"], elementos=elementos)

    unidades = [unidad("introduccion", "Introducción de la sesión", 8, ["diagrama"])]
    for i in range(1, cfg["conceptos"] + 1):
        elementos = {1: [*ec, figura], 2: ["tabla", "diagrama"]}.get(i, ec if i == 3 else [])
        unidades.append(unidad("concepto", f"Concepto {i} del tema", 15, elementos))
    unidades.append(unidad("caso", "Estación de prensado de ejemplo", 22, ["tabla", *ec]))
    if cfg["analisis"]:
        unidades.append(unidad("analisis", "Selección con justificación cuantitativa", 12, ["tabla"]))
    if cfg["implementacion"]:
        unidades.append(unidad("implementacion", "Implementación de referencia", 10, ["codigo"]))
    unidades.append(unidad("sintesis", "Síntesis", 5, []))
    return PlanSesion(
        titulo=f"Título descriptivo de la sesión sobre {tema}", plataforma_referencia="Plataforma de ejemplo X1",
        continuidad="Esta sesión continúa la secuencia del módulo y prepara la siguiente. " * 6,
        prerrequisitos=["Prerrequisito uno", "Prerrequisito dos", "Prerrequisito tres"],
        resultados_sesion=[ResultadoSesion(enunciado=f"Distinguir los conceptos de {tema}", nivel="Analizar", criterios=codigos),
                           ResultadoSesion(enunciado="Aplicar el modelo a un caso", nivel="Aplicar"),
                           ResultadoSesion(enunciado="Evaluar la solución propuesta", nivel="Evaluar")],
        usa_ecuaciones=cfg["usa_ecuaciones"], usa_graficas=cfg["usa_graficas"], unidades=unidades,
        referencias_cargadas=[f"Autor {i}, Título {i}, Editorial, 2020." for i in range(1, n_fuentes + 1)])


def _bloque(elemento: str) -> Bloque:
    if elemento == "ecuacion":
        return Bloque(tipo="ecuacion", contenido=r"V = I \, R")
    if elemento == "tabla":
        return Bloque(tipo="tabla", contenido="| Parámetro | Valor | Unidad |\n|---|---|---|\n| Tensión | 5 | V |\n| Corriente | 2 | A |",
                      leyenda="Datos del ejemplo")
    if elemento == "grafica":
        return Bloque(tipo="grafica", leyenda="Carga de un capacitor", grafica=GraficaSpec(
            tipo="lineas", titulo="Carga RC", etiqueta_x="Tiempo (s)", etiqueta_y="Tensión (V)", variable="t", dominio_min=0, dominio_max=5,
            parametros=[Parametro(nombre="V0", valor=5), Parametro(nombre="tau", valor=1)],
            series=[Serie(nombre="vC", expresion="V0*(1-exp(-t/tau))")]))
    if elemento == "diagrama":
        return Bloque(tipo="diagrama", leyenda="Flujo del ejemplo", diagrama=DiagramaSpec(
            nodos=[Nodo(id="a", texto="Inicio", forma="terminal"), Nodo(id="b", texto="Medición"), Nodo(id="c", texto="Fin", forma="terminal")],
            aristas=[Arista(origen="a", destino="b"), Arista(origen="b", destino="c", etiqueta="listo")]))
    if elemento == "codigo":
        return Bloque(tipo="codigo", contenido="int x = 0;\nvoid loop() {\n  x++;\n}", lenguaje="cpp", leyenda="Programa de ejemplo")
    raise AssertionError(elemento)


def unidad_falsa(usuario: str) -> SeccionRedactada:
    clase = re.search(r"^Clase: (\w+)", usuario, re.M).group(1)
    titulo = re.search(r"^Título: (.+)$", usuario, re.M).group(1)
    elementos = [e for e in re.search(r"^Elementos que debe llevar: (.+)$", usuario, re.M).group(1).split(", ") if e != "(ninguno en particular)"]
    minimo = int(re.search(r"Mínimo de palabras de prosa: (\d+)", usuario).group(1))
    practica = re.search(r"^Práctica de referencia: (?!\()(\w+)", usuario, re.M)
    fuentes = re.search(r"Fuentes cargadas \(cita con el número entre corchetes\):\n(.*?)\n\nPasajes", usuario, re.S).group(1)
    n_fuentes = len(re.findall(r"^\[\d+\] ", fuentes, re.M))
    cita = " Según la fuente [1]." if n_fuentes else ""
    aparte = f" Se retoma la práctica {practica.group(1)} con sus mismos equipos." if practica and clase == "caso" else ""
    if CONFIG_TEMARIO["externas"] and clase == "concepto":
        aparte += " La norma X 123 " + "[FUENTE NO CARGADA EN raw/]" + " fija el límite."
    bloques: list[Bloque] = []
    if clase == "caso":
        bloques.append(Bloque(tipo="subtitulo", contenido="Descripción del sistema"))
    bloques.append(Bloque(tipo="parrafo", contenido=f"Introducción a {titulo}, con el problema y su contexto.{cita}{aparte}"))
    for e in elementos:
        if clase == "caso" and e == "ecuacion":
            bloques.append(Bloque(tipo="subtitulo", contenido="Cálculos"))
        bloques.append(_bloque(e))
        if e == "ecuacion":
            bloques.append(Bloque(tipo="parrafo", contenido="donde $V$ es la tensión, $I$ la corriente y $R$ la resistencia."))
    if clase == "caso":
        bloques.append(Bloque(tipo="subtitulo", contenido="Resultados"))
    bloques.append(Bloque(tipo="nota", leyenda="Nota pedagógica", contenido="Un matiz importante que conviene recordar."))
    bloques.append(Bloque(tipo="parrafo", contenido=relleno(minimo)))
    return SeccionRedactada(bloques=bloques, referencias_externas=["Comité X, Norma X 123, 2019."] if CONFIG_TEMARIO["externas"] and clase == "concepto" else [])


def cierre_falso(usuario: str) -> CierreSesion:
    minimo = int(re.search(r"Mínimo de palabras de la síntesis: (\d+)", usuario).group(1))
    return CierreSesion(sintesis=relleno(minimo), reflexion_actitudinal="Programar y calcular con responsabilidad protege a las personas y a los equipos que dependen de nuestro trabajo cada día.")


def responder_temario(usuario: str, formato):
    """La respuesta falsa al paso de TEMARIO que corresponda al `formato` pedido."""
    if formato is PlanSesion:
        return plan_falso(usuario)
    if formato is SeccionRedactada:
        return unidad_falsa(usuario)
    if formato is CierreSesion:
        return cierre_falso(usuario)
    raise AssertionError(f"no es un paso de TEMARIO: {formato}")


# ---------------------------------------------------------------------------
# LLM falso de PRESENTACIONES
# ---------------------------------------------------------------------------


# Cuerpos de diapositiva validos, al estilo de las presentaciones de ejemplo: cajas en columnas, un flujo TikZ con \foreach, una
# grafica pgfplots, una tabla, circuitikz y codigo (con tildes y una linea `\end{frame}`, que verificar_cuerpo neutraliza).
CUERPOS_FALSOS = {
    "cajas": r"""\begin{columns}[T,onlytextwidth]
  \column{0.48\textwidth}
  \begin{caja}{iubblue}{Continuidad curricular}
    \footnotesize \textbf{Semana anterior:} fundamentos.\\[3pt]
    \textbf{Hoy:} máquinas de estados ($x \geq 0$).
  \end{caja}
  \column{0.48\textwidth}
  \begin{cardO}{Prerrequisitos}
    \begin{itemize}\setlength{\itemsep}{0pt}
      \item Lógica combinacional
      \item Programación estructurada
    \end{itemize}
  \end{cardO}
\end{columns}
\vspace{2mm}
\begin{cajaplana}{iubgreen}
  \centering\small El 95\,\% de los sistemas secuenciales se modela así $[1]$.
\end{cajaplana}""",
    "flujo": r"""\centering
\begin{tikzpicture}[node distance=0.3cm]
  \pgfmathsetmacro{\ancho}{1.8}
  \foreach \x/\c/\t [count=\i] in {0/iubblue/Estados, 2.4/iuborange/Eventos, 4.8/iubgreen/Transiciones}
    \node[bloque=\c] (n\i) at (\x,0) {\t};
  \foreach \a/\b in {n1/n2, n2/n3}
    \draw[flecha] (\a) -- (\b);
  \node[dec, below=0.6cm of n3] (d) {¿Fin?};
  \draw[flecha] (n3) -- (d);
  \draw[decorate, decoration={brace, amplitude=5pt, mirror}, line width=0.9pt, iubnavy]
    ([yshift=-0.2cm]n1.south west) -- ([yshift=-0.2cm]n2.south east)
    node[midway, below=7pt, font=\scriptsize\bfseries] {Modelo};
\end{tikzpicture}""",
    "grafica": r"""\begin{columns}[c,onlytextwidth]
  \column{0.60\textwidth}
  \centering
  \begin{tikzpicture}
    \begin{axis}[width=8cm, height=5cm, xmin=0, xmax=10, xlabel={$t$ (s)}, ylabel={$v$ (\unit{\volt})},
        label style={font=\scriptsize}, grid=major, grid style={iubnavy!12}]
      \addplot[domain=0:10, samples=60, line width=1.4pt, iubblue] {5*(1-exp(-x/2))};
      \addplot[only marks, mark=*, iuborange] coordinates {(2,3.16) (4,4.32)};
    \end{axis}
  \end{tikzpicture}
  \column{0.37\textwidth}
  \begin{caja}{iubblue}{Lectura}
    \footnotesize Con $\tau = \qty{2}{\second}$ se llega al 63.2\,\% en $t=\tau$.
  \end{caja}
\end{columns}""",
    "tabla": r"""\centering\scriptsize
\renewcommand{\arraystretch}{1.4}
\rowcolors{2}{iubnavy!6}{white}
\begin{tabularx}{\textwidth}{>{\bfseries}l l >{\raggedright\arraybackslash}X}
  \rowcolor{iubnavy}
  \hd{Magnitud} & \hd{Valor} & \hd{Unidad}\\
  Tensión   & 24  & \unit{\volt}\\
  Corriente & 0.5 & \unit{\ampere}\\
\end{tabularx}
\vspace{2mm}
{\scriptsize Tabla 1. Datos del caso.\par}""",
    "circuito": r"""\centering
\begin{circuitikz}[scale=0.9, transform shape, color=iubnavy]
  \draw (0,3) node[vcc]{$V_{CC}$} to[R, l_=$R_1$] (0,1.5) to[R, l_=$R_2$] (0,0) node[ground]{};
  \draw (0,1.5) to[short, *-o] (2,1.5) node[right]{A0};
\end{circuitikz}""",
    "codigo": """\\begin{columns}[T,onlytextwidth]
  \\column{0.62\\textwidth}
\\begin{codebox}[language=Python]{maquina.py}
estado = "reposo"   # comentario con tildes: transición
if evento == "marcha":
    estado = "activo"
\\end{frame}
\\end{codebox}
  \\column{0.35\\textwidth}
  \\begin{cardN}{Idea}
    \\cod{estado} guarda la memoria del sistema.
  \\end{cardN}
\\end{columns}""",
    "cita": r"""\centering
\begin{tikzpicture}
  \node[fill=iubnavy, text=white, rounded corners=2mm, text width=12cm, inner sep=10pt,
        font=\normalsize\itshape, align=center] (q) {«Programar con responsabilidad protege a las personas.»};
  \fill[iubyellow] ([yshift=-1pt]q.south west) rectangle ([yshift=-4pt]q.south east);
\end{tikzpicture}""",
}


def diapositivas_falsas(usuario: str) -> DiapositivasParte:
    """Las diapositivas que devolveria un LLM para la parte que pide el prompt: la apertura (2) o un bloque (de 2 a 3, con un
    recurso visual cada una). Usan TODOS los recursos de CUERPOS_FALSOS a lo largo de la sesion."""
    if "Diseña exactamente 2 diapositivas para abrir la sesión" in usuario:
        return DiapositivasParte(diapositivas=[DiapositivaLatex(titulo="Punto de partida de la sesión", cuerpo=CUERPOS_FALSOS["cajas"]),
                                               DiapositivaLatex(titulo="Resultados de aprendizaje", cuerpo=CUERPOS_FALSOS["flujo"])])
    m = re.search(r"para el bloque (\d+) «([^»]*)»", usuario)
    k = int(m.group(1)) if m else 1
    claves = list(CUERPOS_FALSOS)
    elegidas = [claves[(k + j) % len(claves)] for j in range(2 + k % 2)]
    return DiapositivasParte(diapositivas=[DiapositivaLatex(titulo=f"Bloque {k}: {c} ({j + 1})", cuerpo=CUERPOS_FALSOS[c])
                                           for j, c in enumerate(elegidas)])


def png_falso(destino: Path, ancho: int = 640, alto: int = 360) -> None:
    """Un PNG valido y diminuto (escala de grises de 1 bit, todo blanco): sirve de figura cuando la prueba no necesita dibujar."""
    def trozo(tipo: bytes, datos: bytes) -> bytes:
        cuerpo = tipo + datos
        return struct.pack(">I", len(datos)) + cuerpo + struct.pack(">I", zlib.crc32(cuerpo))

    fila = b"\x00" + b"\xff" * ((ancho + 7) // 8)
    datos = (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 1, 0, 0, 0, 0))
             + trozo(b"IDAT", zlib.compress(fila * alto)) + trozo(b"IEND", b""))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(datos)
