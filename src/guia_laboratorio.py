"""GUIA-LABORATORIO -- la guia de laboratorio de cada semana de clase con practica.

Para las asignaturas teorico-practicas, cada semana de clase cuyo temario ya existe lleva su guia de laboratorio si su RA tiene una
practica, de una de dos fuentes (origen_de_guia):

  - de un MANUAL de laboratorio: el RA tiene una practica asignada (`requiere_practica` y `practica_experimentos`, de CORRELATE); la
    guia sigue ese experimento (proposito, principio y equipos del manual);
  - de la BIBLIOGRAFIA ingerida: el RA no tiene practica de un manual (no hay manuales, o ninguno le corresponde), pero tiene criterios
    de caracter practico y fuentes cargadas; el modelo propone, a partir de esas fuentes y del tema del temario, la practica que se
    puede hacer, y dice en que fuentes se basa (`base_bibliografica`). La guia queda en `revisar`: el docente valida el montaje.

Se redacta con el planeador (el tema de la semana), el temario (su titulo y su caso de estudio), el RA del curriculo (enunciado y
criterios de evaluacion), la practica (si la hay) y los pasajes de las fuentes cargadas mas relevantes para ella (pasajes.py: BM25
sobre el texto completo de raw/ y las paginas de wiki/fuentes/). El procedimiento esta pensado para que el estudiante trabaje sin el
docente al lado: cada etapa lleva su diagrama de flujo (TikZ, con la disposicion de figuras._mejor_disposicion), cada paso lo que
debe comprobar para saber que salio bien y, si ayuda, un recurso: el circuito que se monta (circuitikz), la ecuacion que se aplica
(amsmath) o la grafica que se espera obtener (pgfplots, con los puntos calculados de su especificacion).

Todo es CODIGO LaTeX, nunca una imagen dibujada con Python: las tablas (con el encabezado #121023 y filas alternas), los diagramas
de flujo, los circuitos, las graficas y las ecuaciones, con los colores del Manual de Identidad IUB (paleta_iub). En el .md, las
ecuaciones van en $$...$$ y los diagramas, circuitos y graficas en bloques ```tikz (el plugin TikZJax de Obsidian los dibuja; sin el,
se ve el codigo).

Escribe, en generacion/guias-laboratorio/{codigo}/:

    {codigo}-semanaNN.md         la guia para Obsidian (tipo: guia_laboratorio), con su estado en el frontmatter
    {codigo}-semanaNN.tex        la misma guia con la estructura de la plantilla institucional (pdfLaTeX + biber) y las buenas
                                 practicas de la skill experto-en-latex (ver renderizar_tex)
    {codigo}-semanaNN.bib        sus referencias (biblatex)
    {codigo}-semanaNN.guia.json  lo que escribio el modelo, con la huella de lo que se le dio: rehacer la guia con otro docente o
                                 facultad no vuelve a llamar al modelo
    guialabiub.sty, img/         el estilo y las imagenes de la plantilla (config/framework_iub/guia-laboratorio/), copiados

La plantilla es la de la institucion (guia-laboratorio.tex y guialabiub.sty: carta, margenes de 3 cm, Carlito (el clon de Calibri), banner de
encabezado y pie, marca de agua, tabla Facultad / Modulo / Docente, secciones numeradas y bibliografia IEEE con biblatex): se compila
con pdfLaTeX (pdflatex -> biber -> pdflatex -> pdflatex; en Overleaf, compilador pdfLaTeX). Cuesta UNA llamada al modelo por guia (mas
los reintentos). Todo el texto que viene del modelo pasa por latex_seguro.Conversor (los especiales se escapan; en las formulas solo
se admiten comandos matematicos conocidos), y antes de escribir el .tex se comprueba que no tenga primitivas que lean o escriban
archivos.

Uso (desde la raiz del vault):
    python src/guia_laboratorio.py ABC01 --facultad "Facultad de Ingeniería"
    python src/guia_laboratorio.py ABC01 --semana 3 4
    python src/guia_laboratorio.py --all
    python src/guia_laboratorio.py ABC01 --forzar          # rehace el .md y el .tex desde lo guardado (sin LLM si nada cambio)
    python src/guia_laboratorio.py ABC01 --replanificar    # vuelve a pedir la guia al modelo
    python src/guia_laboratorio.py ABC01 --compilar        # ademas compila el .tex (pdflatex y biber)
    python src/guia_laboratorio.py ABC01 --semana 5 --desde-bibliografia   # aunque el docente no le asigno practica al RA
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Callable

import correlate
import latex_seguro as ls
import paleta_iub
import pasajes
import presentaciones
import temario
import temario_latex
import vault
from schema_extraccion import CategoriaAccionCE, TipoAbordaje
from schema_guia_laboratorio import GuiaLaboratorio, Recurso, Referencia, TipoRecurso

GUIAS = Path("generacion") / "guias-laboratorio"
PLANTILLA = Path("config") / "framework_iub" / "guia-laboratorio"
ARCHIVOS_ESTILO = ("guialabiub.sty", "img/encabezado.png", "img/marca-agua.jpg", "img/pie-pagina.png")
FORMATO = 3                     # version del formato de la guia (.md, .tex y .guia.json). Si cambia, la guia se rehace desde lo guardado
                                # (sin LLM) solo si lo guardado pasa la validacion del formato nuevo; si no, se vuelve a pedir (1 llamada).
                                # 2: diagramas de flujo por etapa, comprobacion de cada paso y guias basadas en la bibliografia (las del
                                # formato 1 no tienen diagramas: no pasan la validacion y cuestan 1 llamada cada una).
                                # 3: todo en LaTeX (sin PNG: el .md lleva bloques ```tikz), tablas con la paleta IUB y el recurso de
                                # cada paso (circuito, ecuacion o grafica, opcional: lo guardado del 2 lo pasa y se rehace sin LLM)
FORMATOS_REUTILIZABLES = (2, 3)  # los formatos cuyo .guia.json pasa la validacion actual (LINT L17 y ACTUALIZAR-ESTRUCTURA cuentan con esto)
MAX_RECURSOS = 12               # recursos (circuitos, ecuaciones y graficas) en toda la guia
PASAJES_GUIA = 8
CARACTERES_DE_PASAJES = 9000
MAX_CASO = 3500                 # caracteres del caso de estudio del temario que se le dan al modelo
PASOS = (4, 40)
CATEGORIAS_PRACTICAS = {CategoriaAccionCE.manipulacion_fisica, CategoriaAccionCE.cognitiva_experimental}
MARCADOR = temario.MARCADOR
EXTENSIONES_AUXILIARES = (".aux", ".log", ".out", ".bbl", ".bcf", ".blg", ".run.xml", ".toc")
TIEMPO_MAXIMO = 600             # segundos por pasada de pdflatex o biber
ORIGENES = ("manual", "bibliografia")
_CITA = re.compile(r"\[(\d+)\]")
_URL = re.compile(r"^https?://[^\s{}\\%#]+$")


def avisar_nada(_: str) -> None:
    pass


# ---------------------------------------------------------------------------
# Rutas y semanas
# ---------------------------------------------------------------------------


def ruta_guia(codigo: str, semana: int) -> Path:
    return GUIAS / codigo / f"{codigo}-semana{semana:02d}.md"


def ruta_contenido(ruta_md: Path) -> Path:
    return ruta_md.with_name(ruta_md.stem + ".guia.json")


def _practica_del_ra(fm_ra: dict) -> tuple[str | None, str | None]:
    fuente = vault.enlace(fm_ra.get("requiere_practica"))
    experimentos = fm_ra.get("practica_experimentos") or []
    return (fuente, str(experimentos[0])) if fuente and experimentos else (None, None)


def origen_de_guia(asignatura, ra, fm_ra: dict, desde_bibliografia: bool = False) -> tuple[str | None, str | None, str | None, str]:
    """(origen, fuente, experimento, por que no lleva guia). `manual`: el RA tiene una practica asignada de un manual de laboratorio.
    `bibliografia`: no la tiene (no hay manuales o ninguno le corresponde), pero tiene criterios de caracter practico y fuentes
    cargadas, de las que se propone la practica. None: no lleva guia (asignatura teorica, o sin practica ni de donde proponerla).
    Si el docente ya reviso la correlacion del RA (`correlacion_revisado_por_docente: true`) y no le asigno practica, esa decision se
    respeta, como en CORRELATE: no se propone una desde la bibliografia, salvo que se pida explicitamente (`desde_bibliografia`,
    la opcion --desde-bibliografia)."""
    if asignatura.tipo_abordaje != TipoAbordaje.teorico_practica:
        return None, None, None, "la asignatura es teórica"
    fuente, experimento = _practica_del_ra(fm_ra)
    if fuente:
        return "manual", fuente, experimento, ""
    if fm_ra.get("correlacion_revisado_por_docente") and not desde_bibliografia:
        return None, None, None, (f"el docente revisó la correlación del RA {ra.codigo} y no asignó práctica: no se propone una desde la bibliografía "
                                  "(`--desde-bibliografia` la pide igual)")
    if not any(ce.categoria_accion in CATEGORIAS_PRACTICAS for ce in ra.criterios_evaluacion):
        return None, None, None, f"el RA {ra.codigo} no tiene una práctica asignada (CORRELATE) ni criterios de carácter práctico"
    if not nombres_fuentes(fm_ra, None):
        return None, None, None, f"el RA {ra.codigo} no tiene una práctica asignada (CORRELATE) ni bibliografía cargada de la que proponer una"
    return "bibliografia", None, None, ""


def pedida_desde_bibliografia(codigo: str, semana: int) -> bool:
    """La guia ya escrita de esa semana se pidio con --desde-bibliografia (el docente la quiso aunque habia decidido no asignar practica)."""
    ruta = ruta_guia(codigo, semana)
    try:
        return ruta.exists() and bool(vault.leer_pagina(ruta)[0].get("desde_bibliografia"))
    except Exception:
        return False


def semanas_con_guia(codigo: str, desde_bibliografia: bool = False) -> tuple[list[int], dict[int, str]]:
    """(semanas que llevan guia, {semana: por que no la lleva}) de las semanas de clase de `codigo`: una semana lleva guia si su temario
    ya existe y el RA de la semana tiene de donde sacar la practica (un manual o la bibliografia: origen_de_guia). `desde_bibliografia`
    (o una guia que ya se pidio asi) propone tambien la de un RA cuya correlacion el docente reviso sin asignar practica."""
    ruta_plan = vault.PLANEADOR / f"{codigo}-planeador.md"
    if not ruta_plan.exists():
        raise FileNotFoundError(f"No hay planeador de {codigo}: corre `python src/planeador.py {codigo}` y luego `python src/temario.py {codigo} --todas`")
    _, asignatura, _ = vault.localizar_asignatura(codigo)
    fm_plan, _ = vault.leer_pagina(ruta_plan)
    con, sin = [], {}
    for fila in fm_plan["semanas"]:
        if fila["tipo"] != "clase":
            continue
        semana = fila["semana"]
        if asignatura.tipo_abordaje != TipoAbordaje.teorico_practica:
            sin[semana] = "la asignatura es teórica"
            continue
        ruta_ra = vault.RESULTADOS / f"{fila['ra']}.md"
        if not ruta_ra.exists():
            sin[semana] = f"el RA {fila['ra']} no tiene página"
            continue
        ra, fm_ra, _ = vault.cargar_ra(ruta_ra)
        origen, _, _, motivo = origen_de_guia(asignatura, ra, fm_ra, desde_bibliografia or pedida_desde_bibliografia(codigo, semana))
        if not origen:
            sin[semana] = motivo
        elif not (vault.TEMARIOS / f"{codigo}-semana{semana:02d}.md").exists():
            sin[semana] = f"no hay temario todavía (`python src/temario.py {codigo} --semana {semana}`)"
        else:
            con.append(semana)
    return con, sin


def caso_del_temario(cuerpo: str) -> str:
    """El caso de estudio del temario (la seccion `## N. Caso de Estudio...`, hasta el siguiente `##`), recortado."""
    m = re.search(r"(?ms)^##\s+\d+\.\s+Caso de Estudio[^\n]*\n(.*?)(?=^##\s|\Z)", cuerpo)
    if not m:
        return "(el temario no tiene caso de estudio)"
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", m.group(1)).strip()
    return texto[:MAX_CASO] + (" […]" if len(texto) > MAX_CASO else "")


# ---------------------------------------------------------------------------
# Validacion de lo que devuelve el modelo
# ---------------------------------------------------------------------------


def _textos(g: GuiaLaboratorio) -> list[str]:
    return [g.titulo, g.introduccion, g.objetivo_general, *(o.enunciado for o in g.objetivos_especificos),
            *(f"{m.nombre} {m.especificacion}" for m in g.materiales), g.procedimiento_introduccion,
            *(e.titulo for e in g.etapas), *(f"{p.texto} {p.seguridad} {p.verificacion}" for p in g.pasos()),
            *(f"{p.recurso.leyenda} {p.recurso.donde}" for p in g.pasos() if p.recurso), *g.cuestiones, *g.analisis,
            *(t.leyenda for t in g.tablas_registro), g.conclusiones, *g.preguntas_conclusion, *g.seguridad]


# Lo unico que va en el cuerpo de un circuito (fuera de las formulas de sus etiquetas, que solo admiten comandos matematicos):
# los trazos de circuitikz y TikZ, unidades y tamanos de letra
_COMANDOS_CIRCUITO = frozenset("""draw node path coordinate fill filldraw foreach SI si qty unit num ang textbf textit textrm
    tiny scriptsize footnotesize small normalsize""".split())


def circuito_tex(r: Recurso) -> tuple[str, list[str]]:
    """(el entorno circuitikz del recurso, normalizado, y lo que no cumple). El cuerpo que escribio el modelo pasa por la misma lista
    de permitidos que las diapositivas (latex_seguro.verificar_cuerpo: comandos, opciones de circuitikz, colores de la paleta IUB,
    llaves) y, ademas, solo puede llevar trazos (\\draw, \\node, \\path, \\coordinate...): ningun otro entorno ni las cajas de
    las presentaciones, que la guia no define. El circuito va en el azul oscuro del manual (#121023)."""
    cuerpo = re.sub(r"^\\begin\{circuitikz\}(\[[^\]]*\])?|\\end\{circuitikz\}$", "", r.circuito.strip()).strip()
    texto, problemas = ls.verificar_cuerpo("\\begin{circuitikz}[color=iubnavy]\n" + cuerpo + "\n\\end{circuitikz}")
    ajenos = sorted({c for c in re.findall(r"\\([A-Za-z]+)", ls._enmascarar_matematicas(cuerpo)) if c not in _COMANDOS_CIRCUITO})
    if ajenos:
        problemas.append("en un circuito solo van trazos de circuitikz (\\draw, \\node, \\path, \\coordinate), sin otros comandos ni entornos: "
                         + ", ".join("\\" + c for c in ajenos[:8]))
    if "\\draw" not in cuerpo:
        problemas.append("el circuito no tiene ningún \\draw (p. ej. `\\draw (0,0) to[battery1, l=$V_s$] (0,2) to[R, l=$R_1$] (3,2);`)")
    return texto, problemas


def problemas_de_recursos(g: GuiaLaboratorio) -> list[str]:
    """Los recursos de los pasos (circuitos, ecuaciones y graficas) que no se pueden escribir en LaTeX sin riesgo: un circuito fuera
    de la lista de permitidos, una ecuacion con comandos que no son matematicos o sin balancear, o demasiados recursos. La grafica
    ya la valida su esquema (figuras.GraficaSpec: los puntos se calculan, no se inventan)."""
    problemas: list[str] = []
    recursos = [(n, p.recurso) for n, p in enumerate(g.pasos(), 1) if p.recurso is not None]
    if len(recursos) > MAX_RECURSOS:
        problemas.append(f"{len(recursos)} pasos llevan recurso: el máximo es {MAX_RECURSOS} (deja solo los que de verdad ayudan a proceder)")
    for n, r in recursos:
        if r.tipo == TipoRecurso.circuito:
            problemas += [f"el circuito del paso {n} («{r.leyenda[:40]}»): {p}" for p in circuito_tex(r)[1]]
        elif r.tipo == TipoRecurso.ecuacion:
            malos = ls.comandos_no_permitidos(r.ecuacion)
            if malos:
                problemas.append(f"la ecuación del paso {n} usa comandos que no son matemáticos: {', '.join(malos[:8])}")
            problemas += [f"la ecuación del paso {n}: {p}" for p in ls._balance(r.ecuacion) if "signos $" not in p]
            if "$" in r.ecuacion:
                problemas.append(f"la ecuación del paso {n} va sin $ (es la fórmula sola)")
    return problemas


def _normal(texto: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", texto.lower()).split())


def validar_guia(g: GuiaLaboratorio, criterios: list, codigo_practica: str | None, equipos: list[str], n_fuentes: int, minutos: int,
                 blando: bool = True) -> list[str]:
    """Lo que el codigo puede comprobar: los criterios de caracter practico cubiertos y ninguno ajeno, los equipos de la practica en
    los materiales, las citas [n] a fuentes que existen, una referencia por fuente cargada, los pasos y su duracion, y los diagramas
    de flujo del procedimiento (al menos en dos etapas). Sin practica de un manual (`codigo_practica` None: la practica se propone de
    la bibliografia), `base_bibliografica` tiene que decir en que fuentes cargadas se basa. Blando (solo mientras quedan reintentos):
    que nombre el codigo del experimento, que cada etapa de 3 o mas pasos lleve su diagrama, que al menos la mitad de los pasos diga
    que comprobar y que el marcador de fuente no cargada lleve su referencia."""
    problemas: list[str] = []
    codigos = {ce.codigo for ce in criterios}
    practicos = {ce.codigo for ce in criterios if ce.categoria_accion in CATEGORIAS_PRACTICAS} or codigos
    citados = {c for o in g.objetivos_especificos for c in o.criterios}
    if citados - codigos:
        problemas.append(f"los objetivos citan criterios que no son del RA: {', '.join(sorted(citados - codigos))} (los del RA: {', '.join(sorted(codigos))})")
    if practicos - citados:
        problemas.append(f"ningún objetivo específico desarrolla {', '.join(sorted(practicos - citados))}: los objetivos deben cubrir todos los criterios de carácter práctico")
    materiales = " | ".join(_normal(f"{m.nombre} {m.especificacion}") for m in g.materiales)
    faltan = [e for e in equipos if _normal(e) not in materiales]
    if faltan:
        problemas.append(f"faltan en los materiales equipos de la práctica: {', '.join(faltan)} (con el mismo nombre)")
    citas = {int(n) for t in _textos(g) for n in _CITA.findall(t)}
    ajenas = sorted(c for c in citas if not 1 <= c <= n_fuentes)
    if ajenas:
        problemas.append(f"citas a fuentes que no existen: {', '.join(f'[{c}]' for c in ajenas)} (hay {n_fuentes} fuente(s) cargada(s))")
    if len(g.referencias_cargadas) != n_fuentes:
        problemas.append(f"`referencias_cargadas` tiene {len(g.referencias_cargadas)} entradas y hay {n_fuentes} fuente(s) cargada(s): una por fuente, en el mismo orden")
    pasos = g.pasos()
    if not PASOS[0] <= len(pasos) <= PASOS[1]:
        problemas.append(f"el procedimiento tiene {len(pasos)} pasos: se esperan de {PASOS[0]} a {PASOS[1]} entre todas las etapas")
    total = sum(p.duracion_min or 0 for p in pasos)
    if total > minutos:
        problemas.append(f"los pasos suman {total} minutos y la sesión dura {minutos}: ajusta las duraciones")
    problemas += problemas_de_recursos(g)
    con_diagrama = sum(1 for e in g.etapas if e.diagrama is not None)
    if con_diagrama < min(2, len(g.etapas)):
        problemas.append(f"solo {con_diagrama} etapa(s) del procedimiento llevan `diagrama`: cada etapa lleva su diagrama de flujo (al menos dos), "
                         "con sus pasos como cajas y cada comprobación como una decisión")
    if codigo_practica is None:
        ajenas_base = sorted(n for n in g.base_bibliografica if not 1 <= n <= n_fuentes)
        if not g.base_bibliografica or ajenas_base:
            problemas.append("sin práctica de un manual, `base_bibliografica` dice en qué fuentes cargadas (sus números [n]) se basa la práctica propuesta"
                             + (f": no existen {', '.join(f'[{n}]' for n in ajenas_base)}" if ajenas_base else ""))
    if blando:
        if codigo_practica and codigo_practica.lower() not in (g.titulo + " " + g.introduccion).lower():
            problemas.append(f"la introducción (o el título) no nombra el experimento de referencia {codigo_practica}")
        sin_diagrama = [e.titulo for e in g.etapas if e.diagrama is None and len(e.pasos) >= 3]
        if sin_diagrama:
            problemas.append(f"etapas de 3 o más pasos sin diagrama de flujo: {', '.join(sin_diagrama)}")
        if sum(1 for p in pasos if p.verificacion) * 2 < len(pasos):
            problemas.append("menos de la mitad de los pasos dice en `verificacion` qué comprobar para saber que salió bien (y qué hacer si no): "
                             "el estudiante debe poder seguir la práctica sin el docente al lado")
        if any(MARCADOR in t for t in _textos(g)) and not g.referencias_externas:
            problemas.append(f"el texto usa {MARCADOR} pero `referencias_externas` está vacía: da la referencia de cada fuente no cargada")
    return problemas


# ---------------------------------------------------------------------------
# Referencias: IEEE para el .md y biblatex para el .tex
# ---------------------------------------------------------------------------


def referencia_ieee(r: Referencia) -> str:
    autores = ", ".join(a.strip() for a in r.autores if a.strip())
    partes = [p for p in (autores, f"*{r.titulo}*", f"{r.edicion} ed." if r.edicion else "", r.editorial, r.anio) if p]
    return ", ".join(partes) + "." + (f" Disponible en: {r.url}" if r.url and _URL.match(r.url) else "")


_CAMPO_EDITORIAL = {"book": "publisher", "manual": "organization", "report": "institution", "online": "organization",
                    "article": "journaltitle", "misc": "organization"}


def balance_bib(texto: str) -> int | None:
    """Como lo cuentan biber y BibTeX: TODA llave cuenta, tenga o no una barra delante. Devuelve el saldo final (0 = balanceado) o
    None si en algun punto se cierra una llave que no estaba abierta."""
    saldo = 0
    for ch in texto:
        saldo += {"{": 1, "}": -1}.get(ch, 0)
        if saldo < 0:
            return None
    return saldo


def campo_bib(texto: str, conv: ls.Conversor) -> str:
    """Un campo del .bib: escapado para LaTeX y con las llaves del texto como \\textbraceleft{} y \\textbraceright{}, porque biber
    cuenta tambien las escapadas (`\\{`) y una suelta desbalancea la entrada. Si aun asi no queda balanceado, sin llaves."""
    valor = conv.escapar(" ".join(str(texto).split()))
    valor = valor.replace("\\{", "\\textbraceleft{}").replace("\\}", "\\textbraceright{}")
    return valor if balance_bib(valor) == 0 else re.sub(r"[{}]", "", valor)


def entrada_bib(clave: str, r: Referencia, conv: ls.Conversor, externa: bool = False) -> str:
    campos: list[tuple[str, str]] = []
    autores = [a.strip() for a in r.autores if a.strip()]
    if autores:
        campos.append(("author", " and ".join(campo_bib(a, conv) for a in autores)))
    campos.append(("title", campo_bib(r.titulo, conv)))
    if r.editorial.strip():
        campos.append((_CAMPO_EDITORIAL[r.tipo], campo_bib(r.editorial.strip(), conv)))
    if re.fullmatch(r"\d{4}", r.anio.strip()):
        campos.append(("year", r.anio.strip()))
    if r.edicion.strip():
        campos.append(("edition", campo_bib(r.edicion.strip(), conv)))
    if r.url and _URL.match(r.url):
        campos.append(("url", r.url))
    if externa:
        campos.append(("note", "Fuente no cargada en el wiki"))
    lineas = ",\n".join(f"  {k:<13}= {{{v}}}" for k, v in campos)
    return f"@{r.tipo}{{{clave},\n{lineas}\n}}\n"


# ---------------------------------------------------------------------------
# Escritura: el .md (Obsidian) y el .tex (la plantilla institucional)
# ---------------------------------------------------------------------------


def renderizar_md(g: GuiaLaboratorio, datos: dict) -> str:
    """El cuerpo Markdown de la guia (las mismas secciones del .tex, numeradas igual)."""
    lineas = [f"# Guía de laboratorio: {g.titulo}", "",
              f"> **Facultad:** {datos['facultad'] or '(sin indicar)'} · **Módulo:** {datos['modulo']} · **Docente:** {datos['docente']}",
              f"> **Semana:** {datos['semana']} de {datos['total']} · **Resultado de aprendizaje:** [[{datos['ra']}]] · "
              f"**Sesión:** [[{datos['temario']}]] · **Práctica:** {_practica_md(g, datos)} · "
              f"**Duración:** {datos['minutos']} minutos", "", g.introduccion, "",
              "## 1. Objetivos", "", f"**Objetivo general:** {g.objetivo_general}", "", "**Objetivos específicos:**", ""]
    lineas += [f"- {o.enunciado}" + (f" *({', '.join(o.criterios)})*" if o.criterios else "") for o in g.objetivos_especificos]
    lineas += ["", "## 2. Materiales y Equipos", "", "**Tabla 1.** Materiales y equipos de la práctica", "",
               "| # | Material o equipo | Especificación | Cantidad |", "|---|---|---|---|"]
    lineas += [f"| {k} | {m.nombre} | {m.especificacion or '—'} | {m.cantidad} |" for k, m in enumerate(g.materiales, 1)]
    lineas += ["", "## 3. Procedimiento", "", g.procedimiento_introduccion]
    if any(e.diagrama is not None for e in g.etapas) or any(p.recurso for p in g.pasos()):
        lineas += ["", "> Los diagramas de flujo, los circuitos y las gráficas son código LaTeX (TikZ, circuitikz y pgfplots), como en el .tex: "
                   "Obsidian los dibuja con el plugin TikZJax; sin él, se ve el código (el PDF de la guía los trae dibujados)."]
    dibujo = _Dibujo()
    paso = 0
    for k, etapa in enumerate(g.etapas, 1):
        minutos = sum(p.duracion_min or 0 for p in etapa.pasos)
        lineas += ["", f"### 3.{k} {etapa.titulo}" + (f" ({minutos} min)" if minutos else ""), ""]
        if etapa.diagrama is not None:
            figura = dibujo.figura()
            lineas += [bloque_tikz(dibujo.diagrama(etapa.diagrama)), "", f"*Figura {figura}. Diagrama de flujo de la etapa {k}: {etapa.titulo}*", ""]
        for p in etapa.pasos:
            paso += 1
            extra = ((f" *(≈ {p.duracion_min} min)*" if p.duracion_min else "") + (f" **Comprobación:** {p.verificacion}" if p.verificacion else "")
                     + (f" **Seguridad:** {p.seguridad}" if p.seguridad else ""))
            lineas.append(f"{paso}. {p.texto}{extra}")
            if p.recurso is not None:
                lineas += ["", *_recurso_md(p.recurso, dibujo), ""]
    lineas += ["", "## 4. Cuestiones a Resolver", ""] + [f"{k}. {c}" for k, c in enumerate(g.cuestiones, 1)]
    lineas += ["", "## 5. Análisis de Resultados", ""]
    for parrafo in g.analisis:
        lineas += [parrafo, ""]
    for k, t in enumerate(g.tablas_registro, 2):              # la Tabla 1 es la de materiales
        lineas += [f"**Tabla {k}.** {t.leyenda}", "", "| " + " | ".join(t.columnas) + " |", "|" + "---|" * len(t.columnas)]
        lineas += ["|" + "   |" * len(t.columnas)] * t.filas + [""]
    lineas += ["## 6. Conclusiones", "", g.conclusiones, ""] + [f"- {p}" for p in g.preguntas_conclusion]
    lineas += ["", "## 7. Recomendaciones de Seguridad", ""] + [f"- {s}" for s in g.seguridad]
    lineas += ["", "## 8. Bibliografía", ""]
    for k, r in enumerate(g.referencias_cargadas, 1):
        lineas += [f"[{k}] {referencia_ieee(r)}", ""]
    for k, r in enumerate(g.referencias_externas, len(g.referencias_cargadas) + 1):
        lineas += [f"[{k}] {referencia_ieee(r)} {MARCADOR}", ""]
    if not g.referencias_cargadas and not g.referencias_externas:
        lineas += ["(sin fuentes cargadas: el RA no tiene `bibliografia` enlazada ni el manual de la práctica tiene página en `wiki/fuentes/`)", ""]
    return "\n".join(lineas).rstrip() + "\n"


def _practica_md(g: GuiaLaboratorio, datos: dict) -> str:
    if datos.get("origen") == "bibliografia":
        return "propuesta a partir de la bibliografía " + " ".join(f"[{n}]" for n in g.base_bibliografica)
    return f"[[{datos['fuente']}]] — {datos['experimento']}"


# Los estilos de los diagramas de flujo (los mismos del .tex del temario) y de las graficas, con la paleta del Manual de Identidad IUB
ESTILOS_TIKZ = "\n".join([
    r"\tikzset{",
    r"  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt, text=iubnavy},",
    r"  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt, text=iubnavy},",
    r"  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt, text=iubnavy},",
    r"  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt, text=iubnavy},",
    r"  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},",
    r"  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},",
    r"}",
])


def estilo_ejes(ancho: str) -> str:
    """El estilo `iubejes` de las graficas (pgfplots), el mismo del temario: rejilla y ejes en tintes de #121023."""
    return (rf"\pgfplotsset{{iubejes/.style={{width={ancho}, height={temario_latex.ALTO_GRAFICA}, grid=major, grid style={{iubgris}}, "
            r"axis lines*=left, axis line style={iubnavy}, tick label style={font=\small}, label style={font=\small}, "
            r"title style={font=\bfseries\small}, legend cell align=left, legend style={draw=none, fill=none, font=\small, "
            r"anchor=north, legend columns=-1, /tikz/every even column/.append style={column sep=8pt}}, unbounded coords=jump}}")


# Lo que necesitan las tablas, los diagramas de flujo, los circuitos y las graficas del procedimiento: va en el preambulo del .tex de
# la guia, despues de la plantilla, que no lo trae. Solo paquetes estandar de TeX Live, MiKTeX y Overleaf.
PREAMBULO_DIAGRAMAS = "\n".join([
    "% ------- Tablas, diagramas de flujo, circuitos y gráficas (todo en LaTeX) -------",
    "% (la plantilla no los trae; los estilos y la paleta son los del .tex del temario)",
    r"\usepackage{colortbl}                    % encabezado #121023 y filas alternas en las tablas",
    r"\usepackage{xltabular}                   % la tabla de materiales se parte entre páginas",
    r"\usepackage{tikz}",
    r"\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}",
    r"\usepackage[siunitx,RPvoltages]{circuitikz}",
    r"\usepackage{pgfplots}",
    r"\pgfplotsset{compat=1.18}",
    r"\usepackage{adjustbox}",
    "",
    "% Paleta del Manual de Identidad Visual IUB 2025 (los colores del manual y sus tintes)",
    paleta_iub.definiciones(),
    paleta_iub.ciclo_pgfplots(),
    "",
    "% Estilos de los diagramas de flujo (TikZ) y de las gráficas (pgfplots)",
    ESTILOS_TIKZ,
    estilo_ejes(r"0.9\linewidth"),
])
# El encabezado de las tablas: texto blanco en negrita sobre el azul oscuro del manual (#121023)
FONDO_ENCABEZADO, FONDO_ALTERNO = "iubnavy", "iubfondogris"


def _ascii_tex(texto: str) -> str:
    """El LaTeX con los caracteres no ASCII escritos como comandos (\\'a, \\~n, ?`): TikZJax (los bloques ```tikz del .md) no lee UTF-8."""
    especiales = {"¿": "?`", "¡": "!`", "°": r"\ensuremath{^\circ}", "º": r"\ensuremath{^\circ}", "–": "--", "—": "---",
                  "·": r"\ensuremath{\cdot}", "±": r"\ensuremath{\pm}", "µ": r"\ensuremath{\mu}", "μ": r"\ensuremath{\mu}",
                  "Ω": r"\ensuremath{\Omega}", "×": r"\ensuremath{\times}", "«": "<<", "»": ">>", "“": "``", "”": "''", "’": "'"}
    acentos = {"́": "'", "̀": "`", "̃": "~", "̈": '"', "̂": "^"}
    salida = []
    for ch in texto:
        if ord(ch) < 128:
            salida.append(ch)
        elif ch in especiales:
            salida.append(especiales[ch])
        else:
            base, *marcas = unicodedata.normalize("NFD", ch)
            if ord(base) < 128 and len(marcas) == 1 and marcas[0] in acentos:
                letra = r"\i" if base == "i" else base
                salida.append("\\" + acentos[marcas[0]] + "{" + letra + "}")
            else:
                salida.append("?")
    return "".join(salida)


def bloque_tikz(dibujo: str) -> str:
    """Un diagrama, un circuito o una grafica para el .md: un bloque ```tikz autocontenido (paquetes, paleta IUB y estilos) que el
    plugin TikZJax de Obsidian dibuja. Es el mismo codigo del .tex, sin el `adjustbox` (TikZJax no lo trae)."""
    dibujo = re.sub(r"(?m)^[ \t]*\\(?:begin|end)\{adjustbox\}.*\n?", "", dibujo).strip()
    paquetes = ([r"\usepackage{pgfplots}"] if "\\begin{axis}" in dibujo else []) + ([r"\usepackage{circuitikz}"] if "circuitikz" in dibujo else [])
    ejes = [r"\pgfplotsset{compat=1.16}", paleta_iub.ciclo_pgfplots(), estilo_ejes("12cm")] if "\\begin{axis}" in dibujo else []
    return "\n".join(["```tikz", *paquetes, r"\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}", r"\begin{document}",
                      paleta_iub.definiciones(), ESTILOS_TIKZ, *ejes, _ascii_tex(dibujo), r"\end{document}", "```"])


class _Dibujo:
    """Los diagramas de flujo y las graficas en LaTeX (temario_latex._Escritor: la misma disposicion, los mismos puntos y la misma
    paleta del temario) y la numeracion de figuras y ecuaciones, la misma en el .md y en el .tex."""

    def __init__(self) -> None:
        self.escritor = temario_latex._Escritor()
        self.figuras = self.ecuaciones = 0

    def figura(self) -> int:
        self.figuras += 1
        return self.figuras

    def ecuacion(self) -> int:
        self.ecuaciones += 1
        return self.ecuaciones

    def diagrama(self, spec) -> str:
        return self.escritor.diagrama(spec)

    def grafica(self, spec) -> str:
        return self.escritor.grafica(spec)


def _recurso_md(r: Recurso, dibujo: _Dibujo) -> list[str]:
    """El recurso de un paso en el .md: el circuito y la grafica en un bloque ```tikz, la ecuacion en $$...$$ con su numero."""
    if r.tipo == TipoRecurso.ecuacion:
        n = dibujo.ecuacion()
        return ([f"**Ecuación ({n}).** {r.leyenda}", "", "$$", temario_latex.pulir_formula(r.ecuacion) + f" \\tag{{{n}}}", "$$"]
                + (["", f"donde {r.donde}"] if r.donde else []))
    n = dibujo.figura()
    codigo = circuito_tex(r)[0] if r.tipo == TipoRecurso.circuito else dibujo.grafica(r.grafica)
    return [bloque_tikz(codigo), "", f"*Figura {n}. {r.leyenda}*"]


class _Escritor:
    """El LaTeX de la guia, con la estructura de config/framework_iub/guia-laboratorio/guia-laboratorio.tex."""

    def __init__(self, n_cargadas: int) -> None:
        self.conv = ls.Conversor()
        self.n_cargadas = n_cargadas

    def texto(self, md: str) -> str:
        md = ls._MATH_INLINE.sub(lambda m: "$" + temario_latex.pulir_formula(m.group(1)) + "$", " ".join(str(md).split()))
        tex = self.conv.inline(md).replace(MARCADOR, r"\textbf{" + MARCADOR + "}")
        return _CITA.sub(lambda m: f"\\cite{{ref{m.group(1)}}}" if 1 <= int(m.group(1)) <= self.n_cargadas else m.group(0), tex)

    def lista(self, entorno: str, items: list[str]) -> str:
        return f"\\begin{{{entorno}}}\n" + "\n".join(f"  \\item {i}" for i in items) + f"\n\\end{{{entorno}}}"

    def encabezado(self, columnas: list[str]) -> str:
        """La fila de encabezado de una tabla con la paleta IUB: texto blanco en negrita sobre #121023."""
        return (f"\\rowcolor{{{FONDO_ENCABEZADO}}} " + " & ".join(f"\\textcolor{{white}}{{\\textbf{{{self.texto(c)}}}}}" for c in columnas) + r" \\")

    def tabla(self, k: int, t) -> str:
        r"""Una tabla de registro (skill experto-en-latex: sin lineas verticales), con la paleta del Manual de Identidad IUB, como las
        del temario: el encabezado en blanco sobre #121023 (sin \toprule: la franja de color es el borde), las filas vacias alternando
        blanco y un tinte de #121023, para escribir a mano sin rejilla, y el \bottomrule en #121023; la leyenda arriba y una etiqueta."""
        n = len(t.columnas)
        columnas = ">{\\raggedright\\arraybackslash}X" * n
        vacia = r"\rule{0pt}{0.8cm}" + " &" * (n - 1) + r" \\"
        alterna = f"\\rowcolor{{{FONDO_ALTERNO}}} "
        filas = [f"    {alterna if j % 2 else ''}{vacia}" for j in range(t.filas)]
        return "\n".join([f"% --- Tabla de registro {k}: {temario_latex._comentario(t.leyenda)} ({t.filas} filas vacías para registrar en el banco) ---",
                          r"\begin{table}[H]", r"  \centering",
                          f"  \\caption{{{self.texto(t.leyenda)}}}", f"  \\label{{tab:registro-{k}}}",
                          r"  \arrayrulecolor{iubnavy}",
                          f"  \\begin{{tabularx}}{{\\linewidth}}{{{columnas}}}", f"    {self.encabezado(t.columnas)}",
                          *filas, r"    \bottomrule", r"  \end{tabularx}", r"\end{table}"])

    def materiales(self, g: GuiaLaboratorio) -> str:
        r"""La tabla de materiales y equipos (xltabular: se parte entre paginas repitiendo el encabezado), con la misma paleta."""
        encabezado = self.encabezado(["\\#", "Material o equipo", "Especificación", "Cantidad"])
        alterna = f"\\rowcolor{{{FONDO_ALTERNO}}} "
        filas = [f"  {alterna if k % 2 == 0 else ''}{k} & {self.texto(m.nombre)} & "
                 f"{self.texto(m.especificacion) if m.especificacion else '---'} & {m.cantidad} \\\\" for k, m in enumerate(g.materiales, 1)]
        return "\n".join([f"% --- Tabla: materiales y equipos ({len(g.materiales)}; xltabular repite el encabezado si se parte) ---",
                          r"\arrayrulecolor{iubnavy}",
                          r"\begin{xltabular}{\linewidth}{>{\raggedleft\arraybackslash}p{0.6cm} >{\raggedright\arraybackslash}X "
                          r">{\raggedright\arraybackslash}X >{\raggedleft\arraybackslash}p{2.2cm}}",
                          r"\caption{Materiales y equipos de la práctica}\label{tab:materiales} \\", encabezado,
                          r"\endfirsthead", encabezado, r"\endhead", r"\bottomrule", r"\endlastfoot",
                          *filas, r"\end{xltabular}"])

    def recurso(self, r: Recurso, numero_paso: int, dibujo: _Dibujo) -> str:
        r"""El recurso de un paso, en LaTeX y justo debajo del paso: el circuito (circuitikz) o la grafica (pgfplots) en un minipage
        con \captionof (dentro de la lista de pasos no va un flotante), o la ecuacion numerada con lo que significa cada simbolo."""
        if r.tipo == TipoRecurso.ecuacion:
            dibujo.ecuacion()
            ecuacion = dibujo.escritor.ecuacion(r.ecuacion).replace("\\end{equation}", f"  \\label{{eq:paso-{numero_paso}}}\n\\end{{equation}}")
            self.conv.avisos.extend(a for a in dibujo.escritor.conv.avisos if a not in self.conv.avisos)
            return "\n".join([f"% ecuación del paso {numero_paso}: {temario_latex._comentario(r.leyenda)}", f"\\par {self.texto(r.leyenda)}",
                              ecuacion] + ([f"donde {self.texto(r.donde)}"] if r.donde else []))
        dibujo.figura()
        if r.tipo == TipoRecurso.circuito:
            codigo, clase = circuito_tex(r)[0], "circuito en circuitikz"
        else:
            codigo, clase = dibujo.grafica(r.grafica), "gráfica en pgfplots con los puntos de su especificación"
        return "\n".join([f"% figura del paso {numero_paso}: {temario_latex._comentario(r.leyenda)} ({clase})",
                          r"\par\medskip\noindent", r"\begin{minipage}{\linewidth}", r"  \centering", r"  \begin{adjustbox}{max width=\linewidth}",
                          *("    " + l for l in codigo.splitlines()), r"  \end{adjustbox}",
                          f"  \\captionof{{figure}}{{{self.texto(r.leyenda)}}}\\label{{fig:paso-{numero_paso}}}", r"\end{minipage}", r"\par\medskip"])


def _practica_tex(g: GuiaLaboratorio, datos: dict, e: _Escritor) -> str:
    if datos.get("origen") == "bibliografia":
        return "propuesta a partir de la bibliografía " + ", ".join(f"\\cite{{ref{n}}}" for n in g.base_bibliografica)
    return f"{e.conv.escapar(datos['experimento'])} ({e.conv.escapar(datos['fuente'])})"


def minutos_si(minutos: int) -> str:
    """Una duracion con siunitx (skill experto-en-latex: las unidades, con su paquete): `\\SI{15}{\\minute}` -> «15 min»."""
    return f"\\SI{{{int(minutos)}}}{{\\minute}}"


def renderizar_tex(g: GuiaLaboratorio, datos: dict) -> tuple[str, str, list[str]]:
    """(.tex, .bib, avisos del Conversor): la guia con la estructura de la plantilla institucional y las buenas practicas de la skill
    experto-en-latex del docente: codigo comentado e indentado, formulas pulidas (subindices descriptivos en redonda, funciones con su
    comando: temario_latex.pulir_formula), unidades con siunitx, tablas con booktabs sin lineas verticales, leyenda arriba y etiquetas
    (\\label) en secciones, etapas, tablas, figuras y ecuaciones, espacios irrompibles (Paso~N) y bibliografia con biblatex. Todo es
    LaTeX (ninguna imagen): las tablas con la paleta IUB, los diagramas de flujo en TikZ, los circuitos en circuitikz, las graficas en
    pgfplots y las ecuaciones en `equation`."""
    e = _Escritor(len(g.referencias_cargadas))
    t = e.texto
    dibujo = _Dibujo()                               # el TikZ y el pgfplots, como en el .tex del temario, y la numeracion del .md
    numero = 0
    etapas = []
    for k, etapa in enumerate(g.etapas, 1):
        flujo = ""
        if etapa.diagrama is not None:
            figura = dibujo.figura()
            flujo = "\n".join([f"% --- Figura {figura}: diagrama de flujo de la etapa {k} (TikZ, con la paleta IUB) ---",
                               r"\begin{figure}[H]", r"  \centering", dibujo.diagrama(etapa.diagrama),
                               f"  \\caption{{Diagrama de flujo de la etapa {k}: {e.conv.titulo(etapa.titulo)}}}", f"  \\label{{fig:flujo-{k}}}",
                               r"\end{figure}", ""])
        items = []
        for p in etapa.pasos:
            numero += 1
            extra = ((f" \\emph{{(aprox.~{minutos_si(p.duracion_min)})}}" if p.duracion_min else "")
                     + (f" \\textbf{{Comprobación:}} {t(p.verificacion)}" if p.verificacion else "")
                     + (f" \\textbf{{Seguridad:}} {t(p.seguridad)}" if p.seguridad else ""))
            recurso = ("\n" + e.recurso(p.recurso, numero, dibujo)) if p.recurso is not None else ""
            items.append(f"\\textbf{{Paso~{numero}:}} {t(p.texto)}{extra}{recurso}")
        minutos = sum(p.duracion_min or 0 for p in etapa.pasos)
        etapas.append(f"% --- Etapa {k}: {temario_latex._comentario(etapa.titulo)} ({len(etapa.pasos)} pasos) ---\n"
                      f"\\subsection{{{e.conv.titulo(etapa.titulo)}" + (f" ({minutos_si(minutos)})" if minutos else "") + f"}}\\label{{sec:etapa-{k}}}\n"
                      + flujo + e.lista("pasos", items))
    e.conv.avisos.extend(a for a in dibujo.escritor.conv.avisos if a not in e.conv.avisos)
    objetivos = [t(o.enunciado) + (f" \\emph{{({', '.join(e.conv.escapar(c) for c in o.criterios)})}}" if o.criterios else "") for o in g.objetivos_especificos]
    # biblatex (style=ieee, sorting=none) numera por orden de primera cita: un \nocite con todas las claves, en el orden del .md
    # ([1], [2]… las cargadas y despues las externas), justo despues de \begin{document}, hace que el PDF numere igual que el .md
    claves = claves_bib(g)
    orden_citas = (["% Orden de la bibliografía: el mismo del .md (biblatex numera por orden de primera cita)",
                    f"\\nocite{{{','.join(claves)}}}", ""] if claves else [])
    ficha = (f"\\textbf{{Semana:}} {datos['semana']} de {datos['total']} \\quad \\textbf{{Resultado de aprendizaje:}} {e.conv.escapar(datos['ra'])} "
             f"\\quad \\textbf{{Práctica:}} {_practica_tex(g, datos, e)} "
             f"\\quad \\textbf{{Duración:}} {minutos_si(datos['minutos'])}")
    partes = [
        "% =====================================================================",
        f"%  Guía de laboratorio — {temario_latex._comentario(datos['modulo'])}, semana {datos['semana']}",
        "%  Escrita por src/guia_laboratorio.py con la plantilla institucional",
        "%  (config/framework_iub/guia-laboratorio/: guialabiub.sty e img/, copiados a esta carpeta).",
        "%",
        "%  Compilar con:  pdflatex -> biber -> pdflatex -> pdflatex",
        "%  (En Overleaf: compilador pdfLaTeX; biber se ejecuta solo.)",
        "% =====================================================================",
        r"\documentclass[12pt]{article}",
        "",
        "% Opciones: [sinmarca] quita la marca de agua; [borrador] muestra márgenes",
        "%           [ieee] referencias IEEE (por defecto); [apa] referencias APA 7",
        r"\usepackage{guialabiub}",
        "",
        PREAMBULO_DIAGRAMAS,
        "",
        "% --------------------------- Bibliografía ----------------------------",
        f"\\addbibresource{{{datos['bib']}}}",
        "",
        "% --------------------------- Datos de la guía -------------------------",
        f"\\facultad{{{e.conv.escapar(datos['facultad'])}}}",
        f"\\modulo{{{e.conv.escapar(datos['modulo'])}}}",
        f"\\docente{{{e.conv.escapar(datos['docente'])}}}",
        "",
        r"\begin{document}",
        "",
        *orden_citas,
        r"\datosguia",
        r"\lineablanco",
        "",
        "% Título de la práctica y ficha de la sesión",
        f"{{\\centering\\bfseries Guía de laboratorio: {e.conv.titulo(g.titulo)}\\par}}",
        r"\lineablanco",
        ficha,
        r"\lineablanco",
        t(g.introduccion),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Objetivos}\label{sec:objetivos}",
        f"\\textbf{{Objetivo general:}} {t(g.objetivo_general)}",
        r"\lineablanco",
        r"\textbf{Objetivos específicos:}",
        e.lista("itemize", objetivos),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Materiales y Equipos}\label{sec:materiales}",
        e.materiales(g),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Procedimiento}\label{sec:procedimiento}",
        t(g.procedimiento_introduccion),
        r"\lineablanco",
        *etapas,
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Cuestiones a Resolver}\label{sec:cuestiones}",
        e.lista("enumerate", [t(c) for c in g.cuestiones]),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Análisis de Resultados}\label{sec:analisis}",
        "\n\\lineablanco\n".join(t(a) for a in g.analisis),
        *(e.tabla(k, tabla) for k, tabla in enumerate(g.tablas_registro, 1)),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Conclusiones}\label{sec:conclusiones}",
        t(g.conclusiones),
        r"\lineablanco",
        e.lista("itemize", [t(p) for p in g.preguntas_conclusion]),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Recomendaciones de Seguridad}\label{sec:seguridad}",
        e.lista("itemize", [t(s) for s in g.seguridad]),
        "",
        "% ---------------------------------------------------------------------",
        r"\section{Bibliografía}\label{sec:bibliografia}",
        "% Las fuentes cargadas se citan en el texto con \\cite{refN}; el \\nocite del principio fija su orden y \\nocite{*} incluye las demás del .bib.",
        r"\nocite{*}",
        r"\bibliografia",
        "",
        r"\end{document}",
        "",
    ]
    bib = ["% Referencias de la guía (escritas por src/guia_laboratorio.py): refN son las fuentes cargadas, citadas como [N];",
           "% extN, las que no están cargadas en el wiki.", ""]
    bib += [entrada_bib(f"ref{k}", r, e.conv) for k, r in enumerate(g.referencias_cargadas, 1)]
    bib += [entrada_bib(f"ext{k}", r, e.conv, externa=True) for k, r in enumerate(g.referencias_externas, 1)]
    return "\n".join(partes), "\n".join(bib), list(e.conv.avisos)


def claves_bib(g: GuiaLaboratorio) -> list[str]:
    """Las claves del .bib en el orden de la bibliografia del .md: ref1…refN (las cargadas) y ext1…extM (las no cargadas)."""
    return [f"ref{k}" for k in range(1, len(g.referencias_cargadas) + 1)] + [f"ext{k}" for k in range(1, len(g.referencias_externas) + 1)]


def problemas_del_tex(tex: str, bib: str) -> list[str]:
    """Verificacion estatica: ninguna primitiva que lea o escriba archivos (fuera del preambulo, que es de la plantilla), sin `^^` y
    con entornos y llaves balanceados."""
    cuerpo = tex.partition(r"\begin{document}")[2]
    problemas = [f"primitivas peligrosas en el documento: {', '.join(p)}" for p in [ls.primitivas_peligrosas(cuerpo + bib)] if p]
    if "^^" in cuerpo or "^^" in bib:
        problemas.append("notación ^^ en el documento")
    problemas += temario_latex.revisar_balance("\\begin{document}" + cuerpo)
    sin_comentarios = re.sub(r"(?<!\\)%.*", "", cuerpo)
    fuera = ls.colores_fuera_de_paleta(sin_comentarios)
    if fuera:
        problemas.append("colores que no son del Manual de Identidad IUB: " + ", ".join(fuera[:8]))
    if "\\includegraphics" in sin_comentarios:
        problemas.append("una imagen (\\includegraphics) en el documento: las tablas, gráficas, diagramas y circuitos van en código LaTeX")
    for entrada in re.split(r"(?m)^(?=@)", bib):
        if entrada.startswith("@") and balance_bib(entrada) != 0:
            clave = re.match(r"@\w+\{([^,\s]*)", entrada)
            problemas.append(f"entrada del .bib con llaves desbalanceadas (biber cuenta todas las llaves): {clave.group(1) if clave else entrada[:40]}")
    claves = set(re.findall(r"^@\w+\{([^,\s]+),", bib, flags=re.M))
    citadas = {c.strip() for grupo in re.findall(r"\\cite\{([^}]*)\}", sin_comentarios) for c in grupo.split(",")}
    if bib and citadas - claves:
        problemas.append(f"citas a claves que no están en el .bib: {', '.join(sorted(citadas - claves))}")
    return problemas


def copiar_estilo(carpeta: Path) -> list[str]:
    """Copia a la carpeta de la asignatura el estilo y las imagenes de la plantilla; devuelve los que faltan en la plantilla."""
    faltan = []
    for relativo in ARCHIVOS_ESTILO:
        origen, destino = PLANTILLA / relativo, carpeta / relativo
        if not origen.is_file():
            faltan.append(relativo)
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.is_file() or destino.read_bytes() != origen.read_bytes():
            shutil.copyfile(origen, destino)
    return faltan


# ---------------------------------------------------------------------------
# Compilacion (opcional: --compilar)
# ---------------------------------------------------------------------------


def compilar(ruta_tex: Path) -> list[str]:
    """pdflatex -> biber -> pdflatex -> pdflatex en la carpeta de la guia. Devuelve los problemas (vacio = compila limpio y el PDF queda
    al lado). Nunca con shell-escape, con openin_any=p y openout_any=p (TeX Live; MiKTeX puede no respetarlas), sin entrada y con
    TIEMPO_MAXIMO por pasada. Si falla, se borra el PDF (seria de otra version). FileNotFoundError si falta pdflatex o biber."""
    pdflatex, biber = shutil.which("pdflatex"), shutil.which("biber")
    if not pdflatex or not biber:
        raise FileNotFoundError("--compilar necesita pdflatex y biber (MiKTeX o TeX Live); o sube la carpeta a Overleaf (compilador pdfLaTeX)")
    if ls.primitivas_peligrosas(ruta_tex.read_text(encoding="utf-8").partition(r"\begin{document}")[2]):
        raise ValueError(f"no se compila {ruta_tex.name}: tiene primitivas que leen o escriben archivos")
    entorno = dict(os.environ, openin_any="p", openout_any="p")
    tex = [pdflatex, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", ruta_tex.name]
    problemas: list[str] = []
    try:
        for orden, nombre in ((tex, "pdflatex"), ([biber, ruta_tex.stem], "biber"), (tex, "pdflatex"), (tex, "pdflatex")):
            try:
                r = subprocess.run(orden, cwd=ruta_tex.parent, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   env=entorno, timeout=TIEMPO_MAXIMO, stdin=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                problemas.append(f"{nombre} tardó más de {TIEMPO_MAXIMO // 60} minutos y se detuvo")
                break
            if r.returncode != 0:
                log = ruta_tex.with_suffix(".blg" if nombre == "biber" else ".log")
                texto = log.read_text(encoding="utf-8", errors="replace") if log.exists() else (r.stdout or "")
                errores = [" ".join(m.group(0).lstrip("! ").split())[:300] for m in re.finditer(r"^! (.+)$(?:\n.*){0,2}", texto, flags=re.M)]
                errores += [l.strip()[:300] for l in texto.splitlines() if l.startswith("ERROR")]
                problemas += [f"{nombre}: {x}" for x in errores] or [f"{nombre} terminó con error: " + " ".join(texto.splitlines()[-3:])[:300]]
                break
    finally:
        for extension in EXTENSIONES_AUXILIARES:
            ruta_tex.with_name(ruta_tex.stem + extension).unlink(missing_ok=True)
    if problemas:
        ruta_tex.with_suffix(".pdf").unlink(missing_ok=True)
    return list(dict.fromkeys(problemas))


# ---------------------------------------------------------------------------
# Docente y facultad
# ---------------------------------------------------------------------------


def _usados_antes(codigo: str) -> tuple[str | None, str | None]:
    """(docente, facultad) de la ultima guia escrita: primero las de la asignatura, despues cualquiera."""
    for patron in (f"{codigo}/*.md", "*/*.md"):
        for ruta in sorted(GUIAS.glob(patron), reverse=True):
            fm, _ = vault.leer_pagina(ruta)
            if fm.get("tipo") == "guia_laboratorio" and (fm.get("docente") or fm.get("facultad")):
                return fm.get("docente"), fm.get("facultad")
    return None, None


def completar_datos(codigo: str, docente: str | None, facultad: str | None, interactivo: bool = False, preguntar=input) -> tuple[str, str]:
    """El docente y la facultad de las guias de `codigo`. El docente: el indicado, el de la ultima guia o presentacion, o el del wiki.
    La facultad (el wiki no la guarda): la indicada, la de la ultima guia o, con una persona en la terminal, se pregunta."""
    docente_antes, facultad_antes = _usados_antes(codigo)
    docente_presentacion, _ = presentaciones._usados_antes(codigo)
    docente_wiki, _ = presentaciones.datos_por_defecto(codigo)
    propuesto_docente = docente_antes or docente_presentacion or docente_wiki

    def pedir(mensaje: str, propuesto: str) -> str:
        if not interactivo:
            return propuesto
        try:
            return preguntar(f"{mensaje} [{propuesto}]: ").strip() or propuesto
        except EOFError:
            return propuesto

    docente = docente or pedir(f"Nombre del docente de las guías de laboratorio de {codigo}", propuesto_docente)
    facultad = facultad if facultad is not None else pedir(f"Facultad de {codigo}", facultad_antes or "")
    return docente, facultad


# ---------------------------------------------------------------------------
# Generacion
# ---------------------------------------------------------------------------


def _leer_contenido(ruta: Path, huella: str) -> GuiaLaboratorio | None:
    """Lo que escribio el modelo, si es de las mismas entradas (`huella`) y vuelve a pasar el esquema actual. Lo guardado con otro
    formato no se descarta de entrada: se reutiliza (sin LLM) si tambien pasa validar_guia, que generar_guia aplica despues; uno del
    formato 1 (sin diagramas de flujo) no la pasa y se vuelve a pedir."""
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if datos.get("huella") != huella:
            return None
        return GuiaLaboratorio.model_validate(datos["guia"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def _guardar_contenido(ruta: Path, huella: str, guia: GuiaLaboratorio) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {"formato": FORMATO, "huella": huella, "modelo": vault.modelo_llm(), "fecha": vault.hoy(), "guia": guia.model_dump()}
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def borrar_figuras_png(destino: Path) -> None:
    """Borra los PNG de los diagramas de flujo que escribia el formato 2 (figuras/{guia}-flujoK.png, dibujados con matplotlib): desde
    el formato 3 todo va en codigo LaTeX y no queda al lado una imagen de otra version. La carpeta figuras/ se quita si queda vacia."""
    carpeta = destino.parent / "figuras"
    for viejo in carpeta.glob(f"{destino.stem}-flujo*.png"):
        viejo.unlink()
    if carpeta.is_dir() and not any(carpeta.iterdir()):
        carpeta.rmdir()


def huella_entradas(cuerpo_temario: str, ra, practica, fuentes: list[str], minutos: int, tema: str) -> str:
    """La huella de todo lo que se le da al modelo para una guia: el temario, el RA, la practica del manual, las fuentes de la sesion,
    la duracion y el tema de la semana. Si cambia, la guia se vuelve a pedir (generar_guia) y ANALIZAR-CAMBIOS la marca."""
    entradas = {"temario": temario_latex.hash_cuerpo(cuerpo_temario), "ra": ra.model_dump(mode="json"),
                "practica": practica.model_dump(mode="json") if practica is not None else "bibliografia",
                "fuentes": list(fuentes), "minutos": minutos, "tema": tema}
    return hashlib.sha256(json.dumps(entradas, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def nombres_fuentes(fm_ra: dict, fuente_practica: str | None) -> list[str]:
    """Los nombres de las fuentes de la sesion, en el orden de temario.fuentes_de_la_sesion, sin leer sus textos."""
    nombres: list[str] = []
    for nombre in [*vault.enlaces(fm_ra.get("bibliografia")), *([fuente_practica] if fuente_practica else [])]:
        if nombre not in nombres and (vault.FUENTES / f"{nombre}.md").exists():
            nombres.append(nombre)
    return nombres


def huella_actual(codigo: str, semana: int) -> str | None:
    """La huella de entradas que tendria hoy la guia de esa semana (sin LLM y sin leer las fuentes); None si la semana no lleva guia
    (sin planeador, de examen, sin temario o sin de donde sacar la practica) o algo no se puede leer. La usa ANALIZAR-CAMBIOS."""
    try:
        fm_plan, _ = vault.leer_pagina(vault.PLANEADOR / f"{codigo}-planeador.md")
        fila = next((f for f in fm_plan["semanas"] if f["semana"] == semana and f["tipo"] == "clase"), None)
        ruta_temario = vault.TEMARIOS / f"{codigo}-semana{semana:02d}.md"
        if fila is None or not ruta_temario.exists():
            return None
        ra, fm_ra, _ = vault.cargar_ra(vault.RESULTADOS / f"{fila['ra']}.md")
        _, asignatura, _ = vault.localizar_asignatura(codigo)
        origen, fuente, experimento, _ = origen_de_guia(asignatura, ra, fm_ra, pedida_desde_bibliografia(codigo, semana))
        if not origen:
            return None
        practica = correlate.cargar_practica(fuente, experimento) if origen == "manual" else None
        fm_temario, cuerpo_temario = vault.leer_pagina(ruta_temario)
        minutos = int(fm_temario.get("horas_sesion") or fm_plan.get("horas_sesion") or 2) * 60
        return huella_entradas(cuerpo_temario, ra, practica, nombres_fuentes(fm_ra, fuente), minutos, fila.get("tema") or "")
    except (OSError, ValueError, KeyError, TypeError):
        return None


def generar_guia(codigo: str, semana: int, docente: str | None = None, facultad: str | None = None, forzar: bool = False,
                 replanificar: bool = False, compilar_pdf: bool = False, progreso: Callable[[str], None] | None = None,
                 desde_bibliografia: bool = False) -> tuple[Path, str, int]:
    """(ruta del .md, 'generada' | 'revisar' | 'omitida', cuantas llamadas al modelo). Una guia al dia (las mismas entradas, el mismo
    docente y facultad y el formato actual) se omite; si solo cambio el docente, la facultad o el formato, se rehace desde lo guardado
    (sin LLM) si lo guardado pasa la validacion actual. `desde_bibliografia`: ver origen_de_guia."""
    avisar = progreso or avisar_nada
    if compilar_pdf and not (shutil.which("pdflatex") and shutil.which("biber")):
        raise RuntimeError("--compilar necesita pdflatex y biber (MiKTeX o TeX Live): instálalos, o genera sin --compilar y sube la carpeta a Overleaf (pdfLaTeX)")
    nombre_pagina, asignatura, fm_asignatura = vault.localizar_asignatura(codigo)
    if asignatura.tipo_abordaje != TipoAbordaje.teorico_practica:
        raise ValueError(f"{codigo} es teórica: sus semanas no llevan guía de laboratorio")
    ruta_planeador = vault.PLANEADOR / f"{codigo}-planeador.md"
    if not ruta_planeador.exists():
        raise FileNotFoundError(f"No hay planeador de {codigo}: corre `python src/planeador.py {codigo}` primero")
    fm_plan, _ = vault.leer_pagina(ruta_planeador)
    fila = next((f for f in fm_plan["semanas"] if f["semana"] == semana), None)
    if fila is None or fila["tipo"] != "clase":
        raise ValueError(f"La semana {semana} de {codigo} no es de clase: no lleva guía de laboratorio")
    ruta_temario = vault.TEMARIOS / f"{codigo}-semana{semana:02d}.md"
    if not ruta_temario.exists():
        raise FileNotFoundError(f"No existe el temario {ruta_temario.as_posix()}: corre `python src/temario.py {codigo} --semana {semana}`")
    ra, fm_ra, _ = vault.cargar_ra(vault.RESULTADOS / f"{fila['ra']}.md")
    forzada = desde_bibliografia or pedida_desde_bibliografia(codigo, semana)
    origen, fuente_practica, experimento, motivo = origen_de_guia(asignatura, ra, fm_ra, forzada)
    if not origen:
        raise ValueError(f"semana {semana}: {motivo}: no hay de dónde sacar la práctica (corre CORRELATE, `python src/correlate.py --ra {ra.codigo}`, "
                         "o enlaza en el RA la bibliografía cargada)")
    practica = correlate.cargar_practica(fuente_practica, experimento) if origen == "manual" else None
    fm_temario, cuerpo_temario = vault.leer_pagina(ruta_temario)
    fuentes = temario.fuentes_de_la_sesion(fm_ra, fuente_practica)
    horas_sesion = int(fm_temario.get("horas_sesion") or fm_plan.get("horas_sesion") or 2)
    minutos = horas_sesion * 60
    total = int(fm_temario.get("total_semanas") or 14)
    docente, facultad = completar_datos(codigo, docente, facultad)

    huella = huella_entradas(cuerpo_temario, ra, practica, [f.nombre for f in fuentes], minutos, fila.get("tema") or "")
    destino = ruta_guia(codigo, semana)
    destino_tex, destino_bib = destino.with_suffix(".tex"), destino.with_suffix(".bib")
    fm_antes = vault.leer_pagina(destino)[0] if destino.exists() else {}
    guardada = None if replanificar else _leer_contenido(ruta_contenido(destino), huella)
    equipos = [e.nombre for e in practica.equipos] if practica else []
    codigo_practica = practica.codigo if practica else None
    if guardada is not None and validar_guia(guardada, ra.criterios_evaluacion, codigo_practica, equipos, len(fuentes), minutos, blando=False):
        guardada = None                                  # alguien edito el .guia.json: no pasa la validacion, se pide otra vez
    al_dia = (guardada is not None and destino_tex.exists() and fm_antes.get("formato") == FORMATO and fm_antes.get("huella") == huella
              and (fm_antes.get("docente"), fm_antes.get("facultad") or "") == (docente, facultad)
              and (fm_antes.get("practica_correlacion_estado"), bool(fm_antes.get("practica_revisada_por_docente")))
              == (fm_ra.get("correlacion_estado"), bool(fm_ra.get("correlacion_revisado_por_docente"))))
    if al_dia and not forzar:
        return destino, "omitida", 0

    llamadas = 0
    if guardada is None:
        avisar(f"{codigo} semana {semana}: redactando la guía de laboratorio ({practica.codigo if practica else 'práctica propuesta a partir de la bibliografía'})")
        indice = pasajes.Indice(fuentes)
        practicos_texto = [ce.texto for ce in ra.criterios_evaluacion if ce.categoria_accion in CATEGORIAS_PRACTICAS]
        if practica:
            terminos = [practica.nombre_original, *practica.terminos_clave, *practica.proposito, *(e.nombre for e in practica.equipos), *practicos_texto]
        else:                                        # sin manual: los pasajes de las fuentes sobre el tema de la sesion y lo que se debe hacer
            terminos = [presentaciones.titulo_del_temario(cuerpo_temario, ruta_temario.stem), fila.get("tema") or "", *practicos_texto,
                        *ra.contenido.procedimental, *ra.contenido.conceptual, "experimento", "laboratorio", "medición", "experiment", "laboratory", "measurement"]
        encontrados = indice.buscar(terminos, PASAJES_GUIA, CARACTERES_DE_PASAJES)
        numeros = {f.nombre: i for i, f in enumerate(fuentes, 1)}
        practicos = [ce for ce in ra.criterios_evaluacion if ce.categoria_accion in CATEGORIAS_PRACTICAS]
        sistema, plantilla = vault.cargar_prompt("prompt-guia-laboratorio.md")
        usuario = plantilla.format(
            codigo_asignatura=asignatura.codigo, nombre_asignatura=asignatura.nombre, tipo_abordaje=asignatura.tipo_abordaje.value,
            semana=semana, total_semanas=total, minutos_sesion=minutos, horas_sesion=horas_sesion, codigo_ra=ra.codigo,
            enunciado=ra.enunciado,
            criterios="; ".join(f"{ce.codigo} ({ce.categoria_accion.value}): {ce.texto}" for ce in ra.criterios_evaluacion) or "(sin criterios)",
            criterios_practicos=", ".join(ce.codigo for ce in practicos) or "(ninguno marcado: cubre todos los del RA)",
            procedimental="; ".join(ra.contenido.procedimental) or "(sin contenido procedimental)",
            actitudinal="; ".join(ra.contenido.actitudinal) or "(sin contenido actitudinal)",
            titulo_sesion=presentaciones.titulo_del_temario(cuerpo_temario, ruta_temario.stem), tema=fila.get("tema") or ra.enunciado,
            caso=caso_del_temario(cuerpo_temario),
            origen=("manual de laboratorio: la guía sigue el experimento de referencia" if practica else
                    "bibliografía ingerida: no hay una práctica de un manual de laboratorio para este RA; PROPÓN la práctica a partir de las fuentes "
                    "cargadas y del tema de la sesión (ver la regla 1 bis)"),
            practica=((f"{practica.codigo} — {practica.nombre_original} (manual: {fuente_practica}"
                       + (f", {practica.capitulo}" if practica.capitulo else "") + (f", p. {practica.pagina_inicio}" if practica.pagina_inicio else "")
                       + f"). Propósito: {'; '.join(practica.proposito)}. Principio: {practica.principio_resumen}") if practica else
                      "(ninguna de un manual: propónla a partir de la bibliografía cargada)"),
            equipos=("; ".join(f"{e.nombre}" + (f" ({e.especificacion})" if e.especificacion else "") + (f" ×{e.cantidad}" if e.cantidad > 1 else "")
                               for e in practica.equipos) or "(el manual no lista equipos: deduce del procedimiento solo lo imprescindible)") if practica else
                    "(sin manual: los que pidan las fuentes cargadas para la práctica que propongas, de uso común en un laboratorio universitario)",
            fuentes=temario._describir_fuentes(fuentes, detallado=True), pasajes=pasajes.formatear(encontrados, numeros))
        validar = lambda g, blando: validar_guia(g, ra.criterios_evaluacion, codigo_practica, equipos, len(fuentes), minutos, blando)  # noqa: E731
        guardada = temario._redactar(sistema, usuario, GuiaLaboratorio, validar, f"{codigo} semana {semana}: la guía de laboratorio")
        llamadas = 1
        _guardar_contenido(ruta_contenido(destino), huella, guardada)

    datos = {"facultad": facultad, "modulo": f"{asignatura.codigo} — {asignatura.nombre}", "docente": docente, "semana": semana,
             "total": total, "ra": ra.codigo, "temario": ruta_temario.stem, "fuente": fuente_practica, "experimento": codigo_practica,
             "minutos": minutos, "bib": destino_bib.name, "origen": origen}
    borrar_figuras_png(destino)                       # los PNG del formato 2: la guia ya no usa imagenes
    cuerpo_md = renderizar_md(guardada, datos)
    tex, bib, avisos_tex = renderizar_tex(guardada, datos)
    avisos = list(avisos_tex)
    if not facultad:
        avisos.append("sin facultad: la casilla «Facultad» de la guía va vacía (indícala con --facultad)")
    estado_correlacion = fm_ra.get("correlacion_estado")
    if origen == "bibliografia":
        base = ", ".join(f"[{n}] {fuentes[n - 1].nombre}" for n in guardada.base_bibliografica if 1 <= n <= len(fuentes))
        avisos.append(f"práctica propuesta a partir de la bibliografía cargada ({base}), no de un manual de laboratorio: el docente valida que el "
                      "montaje, los equipos y las medidas de seguridad sean los del laboratorio antes de usar la guía")
        if fm_ra.get("correlacion_revisado_por_docente"):
            avisos.append(f"el docente había revisado la correlación del RA {ra.codigo} sin asignar práctica: esta guía se propuso desde la "
                          "bibliografía porque se pidió con --desde-bibliografia")
    elif estado_correlacion != "aceptado" and not fm_ra.get("correlacion_revisado_por_docente"):
        avisos.append(f"la práctica del RA {ra.codigo} está en «{estado_correlacion or 'sin estado'}» (no aceptada ni revisada por el docente): "
                      "confírmala en el RA antes de usar la guía")
    faltan = copiar_estilo(destino.parent)
    if faltan:
        avisos.append(f"faltan archivos de la plantilla en {PLANTILLA.as_posix()}/: {', '.join(faltan)} (la guía no compila sin ellos)")
    problemas = problemas_del_tex(tex, bib)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino_tex.with_suffix(".pdf").unlink(missing_ok=True)             # el PDF de antes ya no es el de esta guia
    if any(p.startswith("primitivas peligrosas") or p.startswith("notación ^^") for p in problemas):
        destino_tex.unlink(missing_ok=True)
        destino_bib.unlink(missing_ok=True)
        avisos.append("no se escribió el .tex: la verificación estática encontró algo que podría ejecutarse al compilar: " + "; ".join(problemas))
    else:
        avisos += [f"verificación estática: {p}" for p in problemas]
        destino_tex.write_text(tex, encoding="utf-8", newline="\n")
        destino_bib.write_text(bib, encoding="utf-8", newline="\n")

    fm = {
        "tipo": "guia_laboratorio", "asignatura": f"[[{nombre_pagina}]]", "resultado_aprendizaje": f"[[{ra.codigo}]]",
        "temario": f"[[{ruta_temario.stem}]]", "semana": semana, "total_semanas": total,
        "origen_practica": origen, "practica": f"[[{fuente_practica}]]" if fuente_practica else None, "practica_experimento": codigo_practica,
        "base_bibliografica": [f"[[{fuentes[n - 1].nombre}]]" for n in guardada.base_bibliografica if 1 <= n <= len(fuentes)],
        "practica_correlacion_estado": estado_correlacion,
        "practica_revisada_por_docente": bool(fm_ra.get("correlacion_revisado_por_docente")),
        "desde_bibliografia": bool(origen == "bibliografia" and fm_ra.get("correlacion_revisado_por_docente")),
        "estado": "revisar" if avisos else "generada", "avisos": avisos, "archivo_tex": destino_tex.as_posix() if destino_tex.exists() else None,
        "temario_hash": temario_latex.hash_cuerpo(cuerpo_temario), "huella": huella, "formato": FORMATO,
        "docente": docente, "facultad": facultad, "compilada": None,
        "fecha_creacion": fm_antes.get("fecha_creacion") or vault.hoy(), "fecha_actualizacion": vault.hoy(),
    }
    vault.escribir_pagina(destino, fm, "\n" + cuerpo_md)
    if compilar_pdf and destino_tex.exists():
        avisar(f"{codigo} semana {semana}: compilando la guía (pdflatex y biber)")
        try:
            errores = compilar(destino_tex)
        except Exception as error:                   # noqa: BLE001 -- un fallo al compilar es un aviso: la guia ya esta escrita
            destino_tex.with_suffix(".pdf").unlink(missing_ok=True)
            errores = [f"no se pudo compilar: {type(error).__name__}: {str(error)[:300]}"]
        fm["avisos"] = [*avisos, *(f"compilación: {x}" for x in errores)]
        fm["estado"] = "revisar" if fm["avisos"] else "generada"
        fm["compilada"] = vault.hoy() if not errores else None
        vault.escribir_pagina(destino, fm, "\n" + cuerpo_md)
    return destino, fm["estado"], llamadas


def generar_guias(codigo: str, docente: str | None = None, facultad: str | None = None, forzar: bool = False, replanificar: bool = False,
                  semanas: list[int] | None = None, compilar_pdf: bool = False, progreso: Callable[[str], None] | None = None,
                  desde_bibliografia: bool = False) -> tuple[list[tuple[Path, str, int]], dict[int, str]]:
    """Las guias de las semanas de `codigo` que llevan guia (o solo de `semanas`). Devuelve (resultados, {semana: por que no lleva})."""
    con, sin = semanas_con_guia(codigo, desde_bibliografia)
    if semanas:
        no = {s: sin.get(s, "no es una semana de clase") for s in semanas if s not in con}
        if no:
            raise ValueError(f"{codigo}: sin guía posible en " + "; ".join(f"semana {s} ({m})" for s, m in sorted(no.items())))
        con = [s for s in con if s in semanas]
    resultados = [generar_guia(codigo, s, docente, facultad, forzar, replanificar, compilar_pdf, progreso, desde_bibliografia) for s in con]
    escritas = [(r, e, n) for r, e, n in resultados if e != "omitida"]
    if escritas:
        vault.anotar_log(f"/guia-laboratorio {codigo}", [
            f"{len(escritas)} guías escritas en {GUIAS.as_posix()}/{codigo}/, {len(resultados) - len(escritas)} ya estaban al día",
            f"{sum(n for _, _, n in escritas)} llamadas al modelo; el resto se rehízo desde lo guardado (sin LLM)",
            *[f"{r.name}: revisar los avisos (frontmatter de la guía)" for r, e, _ in escritas if e == "revisar"]])
    return resultados, sin


def main() -> int:
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Genera la guía de laboratorio (plantilla institucional, pdfLaTeX) de cada semana con práctica asignada.")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("codigo", nargs="?", help="código de la asignatura")
    grupo.add_argument("--all", action="store_true", help="todas las asignaturas teórico-prácticas que tienen planeador")
    parser.add_argument("--semana", type=int, nargs="+", help="solo esas semanas")
    parser.add_argument("--facultad", help="la facultad de la tabla de datos de la guía; si no se indica, se pregunta (o se usa la última)")
    parser.add_argument("--docente", help="el docente de la tabla de datos; si no se indica, el de la última guía o presentación, o el del wiki")
    parser.add_argument("--forzar", action="store_true", help="rehace el .md y el .tex aunque estén al día (desde lo guardado: sin LLM si nada cambió)")
    parser.add_argument("--replanificar", action="store_true", help="vuelve a pedir la guía al modelo (una llamada por guía)")
    parser.add_argument("--desde-bibliografia", action="store_true",
                        help="propone la práctica desde la bibliografía también si el docente revisó la correlación del RA sin asignar una (queda en `revisar`)")
    parser.add_argument("--sin-preguntar", action="store_true", help="no pregunta nada: usa lo indicado o lo último usado")
    parser.add_argument("--compilar", action="store_true", help="además compila el .tex (pdflatex -> biber -> pdflatex -> pdflatex)")
    args = parser.parse_args()
    if args.all and args.semana:
        parser.error("--semana va con un código de asignatura, no con --all")

    interactivo = presentaciones.terminal_interactiva() and not args.sin_preguntar
    codigos = presentaciones.codigos_con_planeador() if args.all else [args.codigo]
    errores: list[str] = []
    for codigo in codigos:
        try:
            _, asignatura, _ = vault.localizar_asignatura(codigo)
            if asignatura.tipo_abordaje != TipoAbordaje.teorico_practica:
                if not args.all:
                    errores.append(f"{codigo}: la asignatura es teórica, sus semanas no llevan guía de laboratorio")
                continue
            con, _ = semanas_con_guia(codigo, args.desde_bibliografia)
            if not con:
                print(f"{codigo}: ninguna semana lleva guía todavía (necesita una práctica asignada al RA y el temario de la semana)")
                continue
            docente, facultad = completar_datos(codigo, args.docente, args.facultad, interactivo)
            print(f"{codigo}: docente «{docente}», facultad «{facultad or '(sin indicar)'}»")
            resultados, sin = generar_guias(codigo, docente, facultad, args.forzar, args.replanificar, args.semana, args.compilar, print,
                                            args.desde_bibliografia)
            escritas = [(r, e, n) for r, e, n in resultados if e != "omitida"]
            print(f"{codigo}: {len(escritas)} guías escritas ({sum(n for *_, n in escritas)} llamadas al modelo), {len(resultados) - len(escritas)} ya al día")
            for ruta, estado, _ in escritas:
                print(f"  {ruta.as_posix()}" + ("   (revisar: avisos en su frontmatter)" if estado == "revisar" else ""))
            for semana, motivo in sorted(sin.items()):
                if not args.semana:
                    print(f"  semana {semana}: sin guía ({motivo})")
        except (FileNotFoundError, ValueError, RuntimeError, KeyError) as error:
            errores.append(f"{codigo}: {error}")
    for error in errores:
        print(f"ERROR: {error}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
