"""Prueba de GUIA-LABORATORIO (guia_laboratorio.py, schema_guia_laboratorio.py) sin LLM real y SIN COMPILAR (no exige LaTeX): el
LLM se sustituye por una guia fija (_fixtures.guia_falsa) y pdflatex y biber por procesos simulados.

  A. el esquema: los limites de cada seccion y de las referencias;
  B. que semanas llevan guia: solo las de clase de una asignatura teorico-practica, con practica asignada al RA y temario;
  C. la guia: el .md y el .tex con la estructura de la plantilla institucional (tabla de datos, las 8 secciones en orden, pasos,
     tablas de registro, bibliografia con biblatex), el .bib, el estilo y las imagenes copiados, el frontmatter y el texto hostil
     escapado;
  D. el flujo: lo que no cumple vuelve al modelo con el motivo; una guia al dia se omite, otro docente o facultad la rehacen sin LLM,
     un temario que cambia la vuelve a pedir; --compilar (simulado) y un PDF de otra version; lint L17; el comando.

Uso (desde src/):  python test_guia_laboratorio.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import _fixtures
import figuras
import guia_laboratorio as gl
import lint
import planeador
import temario
import vault
from schema_guia_laboratorio import GuiaLaboratorio, Material, Referencia, TablaRegistro
from schema_planeador import TemasSemana

SRC = Path(__file__).resolve().parent
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
SECCIONES = ["Objetivos", "Materiales y Equipos", "Procedimiento", "Cuestiones a Resolver", "Análisis de Resultados", "Conclusiones",
             "Recomendaciones de Seguridad", "Bibliografía"]


def esperar(excepcion, funcion, *args, **kwargs) -> str:
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


LLAMADAS: list[str] = []
RESPUESTAS: list = []


def llm_falso(sistema, usuario, formato):
    if formato is GuiaLaboratorio:
        LLAMADAS.append(usuario)
        if RESPUESTAS:
            respuesta = RESPUESTAS.pop(0)
            return respuesta(usuario) if callable(respuesta) else respuesta
        return _fixtures.guia_falsa(usuario)
    if formato is TemasSemana:
        n = int(re.search(r"Semanas de clase de este RA: (\d+)", usuario).group(1))
        return TemasSemana(temas=[f"Tema {i}" for i in range(1, n + 1)])
    return _fixtures.responder_temario(usuario, formato)


def probar_esquema() -> None:
    usuario = ("Criterios de evaluación: CE1: a; CE2: b\nCriterios de carácter práctico (x): CE2\nPráctica de referencia: Exp1 — X\n"
               "Equipos de la práctica (todos): Multímetro\nduración de la sesión: 240 minutos\n"
               "Fuentes cargadas (cita con el número entre corchetes):\n[1] libro-a — datos\n\nPasajes")
    buena = _fixtures.guia_falsa(usuario)
    datos = buena.model_dump()
    malos = {
        "objetivos": {**datos, "objetivos_especificos": datos["objetivos_especificos"][:1]},
        "cuestiones": {**datos, "cuestiones": datos["cuestiones"][:2]},
        "tabla sin columnas": {**datos, "tablas_registro": [{"leyenda": "Registro", "columnas": ["a"], "filas": 3}]},
        "tabla sin filas": {**datos, "tablas_registro": [{"leyenda": "Registro", "columnas": ["a", "b"], "filas": 0}]},
        "referencia": {**datos, "referencias_cargadas": [{"tipo": "libro", "titulo": "X"}]},
        "paso": {**datos, "etapas": [{"titulo": "Etapa", "pasos": [{"texto": "corto"}]}] * 2},
        "duracion": {**datos, "etapas": [{"titulo": "Etapa", "pasos": [{"texto": "Un paso con su texto.", "duracion_min": 999}]}] * 2},
        "introduccion": {**datos, "introduccion": "breve"},
    }
    for nombre, malo in malos.items():
        esperar(ValueError, GuiaLaboratorio.model_validate, malo)
    assert Material(nombre="Fuente  DC ").nombre == "Fuente DC" and TablaRegistro(leyenda="Registro", columnas=["a", "b"], filas=3).filas == 3
    assert gl.referencia_ieee(Referencia(tipo="book", autores=["Ogata, K."], titulo="Ingeniería de control", editorial="Pearson", anio="2010",
                                         edicion="5")) == "Ogata, K., *Ingeniería de control*, 5 ed., Pearson, 2010."
    print(f"A. el esquema acepta una guía válida y rechaza {len(malos)} defectos (secciones cortas, tablas sin columnas o filas, un tipo de "
          "referencia desconocido, pasos y duraciones fuera de rango) -- OK")


def asignar_practica(ra: str, estado: str = "aceptado") -> None:
    ruta = vault.RESULTADOS / f"{ra}.md"
    fm, cuerpo = vault.leer_pagina(ruta)
    fm.update({"requiere_practica": "[[banco-uno]]", "practica_experimentos": ["Exp1"], "correlacion_estado": estado})
    vault.escribir_pagina(ruta, fm, cuerpo)


def semanas_del_ra(ra: str) -> list[int]:
    fm, _ = vault.leer_pagina(vault.PLANEADOR / "TPR01-planeador.md")
    return [f["semana"] for f in fm["semanas"] if f["tipo"] == "clase" and f["ra"] == ra]


def probar_flujo(raiz: Path) -> None:
    vault.pedir_estructurado = llm_falso
    figuras.dibujar_grafica = figuras.dibujar_diagrama = lambda spec, destino: _fixtures.png_falso(destino)
    # el manual del banco con los equipos de la practica Exp1
    fm_banco, cuerpo_banco = vault.leer_pagina(vault.FUENTES / "banco-uno.md")
    fm_banco["practicas"][0]["equipos"] = [{"nombre": "Fuente de tensión DC", "especificacion": "0-30 V", "cantidad": 1},
                                           {"nombre": "Multímetro digital", "cantidad": 2}]
    vault.escribir_pagina(vault.FUENTES / "banco-uno.md", fm_banco, cuerpo_banco)
    asignar_practica("TPR01-RA1")
    planeador.generar_planeador("TPR01")
    planeador.generar_planeador("TEO01")
    s1, s2 = semanas_del_ra("TPR01-RA1")[:2]
    otra = semanas_del_ra("TPR01-RA2")[0]
    for semana in (s1, s2, otra):
        temario.generar_temario("TPR01", semana)

    # B. que semanas llevan guia
    con, sin = gl.semanas_con_guia("TPR01")
    assert con == [s1, s2], (con, sin)
    assert "no tiene una práctica asignada" in sin[otra] and "no hay temario" in sin[semanas_del_ra("TPR01-RA1")[2]], sin
    con_teo, sin_teo = gl.semanas_con_guia("TEO01")
    assert con_teo == [] and all(m == "la asignatura es teórica" for m in sin_teo.values())
    assert "es teórica" in esperar(ValueError, gl.generar_guia, "TEO01", 1)
    assert "no tiene una práctica asignada" in esperar(ValueError, gl.generar_guia, "TPR01", otra)
    print("B. llevan guía solo las semanas de clase de una asignatura teórico-práctica con práctica asignada al RA y temario; las demás "
          "dicen por qué no -- OK")

    # C. la guia: .md, .tex con la estructura de la plantilla, .bib, estilo e imagenes
    LLAMADAS.clear()
    resultados, _ = gl.generar_guias("TPR01", "Docente Uno", "Facultad de Ingeniería")
    assert [(r.name, e, n) for r, e, n in resultados] == [(f"TPR01-semana{s1:02d}.md", "generada", 1), (f"TPR01-semana{s2:02d}.md", "generada", 1)], resultados
    usuario = LLAMADAS[0]
    for dato in ("RA TPR01-RA1", "Criterios de carácter práctico (los objetivos deben cubrirlos todos): CE2", "Exp1 — Practica de ejemplo A",
                 "Fuente de tensión DC (0-30 V); Multímetro digital ×2", "Caso de estudio del temario:", "Estación de prensado de ejemplo",
                 "Pasajes de las fuentes relevantes para la práctica:"):
        assert dato in usuario, dato
    carpeta = gl.GUIAS / "TPR01"
    md = carpeta / f"TPR01-semana{s1:02d}.md"
    archivos = {p.relative_to(carpeta).as_posix() for p in carpeta.rglob("*") if p.is_file()}
    esperados = ({f"TPR01-semana{s:02d}{x}" for s in (s1, s2) for x in (".md", ".tex", ".bib", ".guia.json")}
                 | {f"figuras/TPR01-semana{s:02d}-flujo{k}.png" for s in (s1, s2) for k in (1, 2)})      # un diagrama de flujo por etapa
    assert archivos == esperados | set(gl.ARCHIVOS_ESTILO), archivos
    fm, cuerpo = vault.leer_pagina(md)
    assert fm["tipo"] == "guia_laboratorio" and fm["estado"] == "generada" and fm["avisos"] == [], fm["avisos"]
    assert fm["temario"] == f"[[TPR01-semana{s1:02d}]]" and fm["practica"] == "[[banco-uno]]" and fm["practica_experimento"] == "Exp1"
    assert fm["docente"] == "Docente Uno" and fm["facultad"] == "Facultad de Ingeniería" and fm["formato"] == gl.FORMATO
    assert [l[6:] for l in cuerpo.splitlines() if re.match(r"^## \d\. ", l)] == SECCIONES, cuerpo
    assert "| 1 | Fuente de tensión DC | 0-30 V | 1 |" in cuerpo and "**Tabla 1.** Registro de las mediciones" in cuerpo
    tex = md.with_suffix(".tex").read_text(encoding="utf-8")
    plantilla = (gl.PLANTILLA / "guia-laboratorio.tex").read_text(encoding="utf-8")
    assert re.findall(r"\\section\{([^}]*)\}", tex) == re.findall(r"\\section\{([^}]*)\}", plantilla) == SECCIONES
    for pieza in (r"\documentclass[12pt]{article}", r"\usepackage{guialabiub}", f"\\addbibresource{{TPR01-semana{s1:02d}.bib}}",
                  r"\facultad{Facultad de Ingeniería}", r"\modulo{TPR01 --- Asignatura teórico-práctica de prueba}", r"\docente{Docente Uno}",
                  r"\datosguia", r"\lineablanco", r"\begin{pasos}", r"\textbf{Paso~1:}", r"\textbf{Seguridad:}", r"\cite{ref1}",
                  r"\begin{tabularx}{\linewidth}", r"\caption{Registro de las mediciones}", r"\nocite{*}", r"\bibliografia",
                  # buenas practicas de la skill experto-en-latex: unidades con siunitx, booktabs, etiquetas, comentarios
                  r"\SI{240}{\minute}", r"(aprox.~\SI{", r"\toprule", r"\midrule", r"\cmidrule(lr){1-3}", r"\bottomrule",
                  r"\label{tab:registro-1}", r"\label{sec:objetivos}", r"\label{sec:etapa-1}", "% --- Etapa 1: ", "% --- Tabla 1: "):
        assert pieza in tex, pieza
    assert tex.count(r"\rule{0pt}{0.8cm}") == 5 and r"\subsection{Preparación y montaje" in tex
    assert not re.search(r"\\begin\{tabularx\}\{\\linewidth\}\{[^}]*\|", tex), "las tablas de la guía no llevan líneas verticales"
    bib = md.with_suffix(".bib").read_text(encoding="utf-8")
    assert gl.problemas_del_tex(tex, bib) == []
    assert any("citas a claves que no están en el .bib: ref9" in p for p in gl.problemas_del_tex(tex.replace(r"\cite{ref1}", r"\cite{ref9}"), bib))

    # C1. el .bib: llaves del texto en titulo, autor y editorial no desbalancean la entrada (biber cuenta TODA llave, tambien `\{`)
    conv = gl.ls.Conversor()
    for ref in (Referencia(tipo="book", autores=["Pérez {Juan", "x}y, Ana"], titulo="Circuitos {RLC", editorial="Manual x}y"),
                Referencia(tipo="manual", autores=[r"\textbf{x}"], titulo=r"Guía \textbf{x} de {a}}{b", editorial=r"Ed. \{ y \}")):
        entrada = gl.entrada_bib("ref1", ref, conv)
        assert gl.balance_bib(entrada) == 0, entrada
        assert not any("desbalanceadas" in p for p in gl.problemas_del_tex(tex, entrada)), entrada
    assert r"Circuitos \textbraceleft{}RLC" in gl.entrada_bib("ref1", Referencia(tipo="book", titulo="Circuitos {RLC"), conv)
    rota = "@book{ref1,\n  title = {Circuitos \\{RLC},\n}\n"
    assert any("llaves desbalanceadas" in p and "ref1" in p for p in gl.problemas_del_tex(tex, rota)), "una entrada desbalanceada se avisa"
    assert gl.balance_bib(r"a \{ b") == 1 and gl.balance_bib("}{") is None

    # C3. el PDF numera las referencias como el .md: un \nocite con todas las claves, en orden, justo despues de \begin{document}
    datos_tex = {"facultad": "F", "modulo": "M", "docente": "D", "semana": 1, "total": 14, "ra": "RA", "temario": "T", "fuente": "banco-uno",
                 "experimento": "Exp1", "minutos": 120, "bib": "x.bib"}
    al_reves = _fixtures.guia_falsa(usuario)
    al_reves.introduccion = "Primero se cita la fuente [2] y después la fuente [1]. " + al_reves.introduccion
    al_reves.referencias_externas = [Referencia(tipo="misc", titulo="Una norma no cargada")]
    tex2, bib2, _ = gl.renderizar_tex(al_reves, datos_tex)
    documento = tex2.partition(r"\begin{document}")[2]
    assert documento.lstrip().split("\n", 2)[1] == r"\nocite{ref1,ref2,ext1}", documento[:300]
    assert documento.index(r"\nocite{ref1,ref2,ext1}") < documento.index(r"\cite{ref2}") < documento.index(r"\cite{ref1}")
    assert gl.problemas_del_tex(tex2, bib2) == []
    print("C1. el .bib queda balanceado aunque el título, el autor o la editorial lleven «{», «}» o «\\textbf{x}» (y una entrada desbalanceada "
          "se avisa); C3. un \\nocite con todas las claves en el orden del .md, al principio, hace que el PDF numere igual aunque el texto cite [2] antes que [1] -- OK")
    assert "@book{ref1," in bib and "title        = {Título de la fuente 1}" in bib and bib.count("@book{") == 2      # libro-a y banco-uno
    assert (carpeta / "guialabiub.sty").read_bytes() == (gl.PLANTILLA / "guialabiub.sty").read_bytes()
    assert "/guia-laboratorio TPR01" in Path("wiki/log.md").read_text(encoding="utf-8")
    # el procedimiento, lo mas intuitivo posible: cada etapa con su diagrama de flujo (PNG en el .md, TikZ en el .tex) y cada paso con lo
    # que hay que comprobar
    assert f"![Figura 1. Diagrama de flujo de la etapa 1: Preparación y montaje](figuras/TPR01-semana{s1:02d}-flujo1.png)" in cuerpo
    assert "**Comprobación:** La lectura está entre 4,5 V y 5,5 V" in cuerpo
    assert tex.count(r"\begin{tikzpicture}") == 2 and r"\label{fig:flujo-1}" in tex and r"\node[ddecision" in tex and r"\draw[dflecha]" in tex
    assert r"\caption{Diagrama de flujo de la etapa 1: Preparación y montaje}" in tex and r"\textbf{Comprobación:}" in tex
    preambulo = tex.partition(r"\begin{document}")[0]
    assert r"\usepackage{tikz}" in preambulo and "dcaja/.style" in preambulo and r"\definecolor{iubblue}{HTML}{00ADE7}" in preambulo
    assert preambulo.index(r"\usepackage{guialabiub}") < preambulo.index(r"\usepackage{tikz}"), "los estilos de los diagramas, después de la plantilla"
    print("C. la guía sale en .md y en .tex con la estructura de la plantilla (tabla Facultad/Módulo/Docente, las 8 secciones en el mismo orden, "
          "pasos con duración y seguridad, tablas de registro vacías, \\cite y biblatex), con su .bib, el estilo y las imágenes copiados -- OK")

    # C2. texto hostil del modelo: se escapa (ningun comando suyo llega al .tex)
    hostil = _fixtures.guia_falsa(usuario)
    hostil.introduccion = r"Texto con \input{secreto.txt} y 50 % & #3 y $x \write18{rm}$ y ^^5c " + hostil.introduccion
    hostil.cuestiones[0] = r"¿Qué pasa con \csname x\endcsname?"
    RESPUESTAS.append(hostil)
    gl.generar_guia("TPR01", s1, "Docente Uno", "Facultad de Ingeniería", replanificar=True)
    tex = md.with_suffix(".tex").read_text(encoding="utf-8")
    documento = tex.partition(r"\begin{document}")[2]
    assert r"\input{" not in documento and r"\csname" not in documento and "^^" not in documento and r"\write18" not in documento
    assert r"50 \% \& \#3" in documento and gl.problemas_del_tex(tex, "") == []
    assert vault.leer_pagina(md)[0]["estado"] == "revisar"                       # la formula con un comando no matematico deja aviso
    print("C2. texto hostil del modelo (\\input, \\csname, \\write18 en una fórmula, ^^, % & #): se escapa o se neutraliza y queda un aviso -- OK")

    # D1. lo que no cumple vuelve al modelo con el motivo
    def sin_equipos_ni_criterio(u):
        g = _fixtures.guia_falsa(u)
        g.materiales = [Material(nombre="Cables de conexión"), Material(nombre="Gafas de seguridad")]
        g.objetivos_especificos[0].criterios = ["CE9"]
        g.cuestiones[0] = "¿Qué dice la fuente [7] sobre el error de medición?"
        g.referencias_cargadas = g.referencias_cargadas[:1]
        return g
    LLAMADAS.clear()
    RESPUESTAS.append(sin_equipos_ni_criterio)
    gl.generar_guia("TPR01", s1, "Docente Uno", "Facultad de Ingeniería", replanificar=True)
    assert len(LLAMADAS) == 2, len(LLAMADAS)
    for motivo in ("faltan en los materiales equipos de la práctica: Fuente de tensión DC, Multímetro digital", "criterios que no son del RA: CE9",
                   "ningún objetivo específico desarrolla CE2", "citas a fuentes que no existen: [7]", "`referencias_cargadas` tiene 1 entradas"):
        assert motivo in LLAMADAS[1], motivo
    LLAMADAS.clear()
    RESPUESTAS.extend([sin_equipos_ni_criterio] * 3)
    assert "no cumplió lo pedido tras 3 intentos" in esperar(ValueError, gl.generar_guia, "TPR01", s1, "Docente Uno", "Facultad de Ingeniería", replanificar=True)
    assert md.exists() and gl.ruta_contenido(md).exists(), "una guía que falla no borra la anterior"
    print("D1. lo que no cumple (equipos de la práctica que faltan, un criterio ajeno o uno práctico sin cubrir, una cita a una fuente que no "
          "existe, referencias que no cuadran) vuelve al modelo con el motivo; tras 3 intentos falla con un mensaje claro y deja la guía anterior -- OK")

    # D2. al dia se omite; otro docente o facultad la rehacen sin LLM; un temario que cambia la vuelve a pedir
    gl.generar_guias("TPR01", "Docente Uno", "Facultad de Ingeniería")
    LLAMADAS.clear()
    resultados, _ = gl.generar_guias("TPR01", "Docente Uno", "Facultad de Ingeniería")
    assert {e for _, e, _ in resultados} == {"omitida"} and not LLAMADAS
    resultados, _ = gl.generar_guias("TPR01", "Docente Dos", "Facultad de Ciencias")
    assert {(e, n) for _, e, n in resultados} == {("generada", 0)} and not LLAMADAS and r"\docente{Docente Dos}" in md.with_suffix(".tex").read_text(encoding="utf-8")
    assert {(e, n) for _, e, n in gl.generar_guias("TPR01", forzar=True)[0]} == {("generada", 0)} and not LLAMADAS
    assert vault.leer_pagina(md)[0]["facultad"] == "Facultad de Ciencias", "sin --facultad se usa la última"
    assert not [h for h in lint.revisar() if h.regla == "L17"], [h for h in lint.revisar() if h.regla == "L17"]
    ruta_temario = vault.TEMARIOS / f"TPR01-semana{s1:02d}.md"
    fm_t, cuerpo_t = vault.leer_pagina(ruta_temario)
    vault.escribir_pagina(ruta_temario, fm_t, cuerpo_t + "\nUna línea agregada a mano.\n")
    assert any("desactualizada" in h.mensaje and h.ruta.endswith(md.name) for h in lint.revisar() if h.regla == "L17")
    (_, estado, llamadas), = gl.generar_guias("TPR01", semanas=[s1])[0]
    assert llamadas == 1 and len(LLAMADAS) == 1, "el temario cambió: la guía se vuelve a pedir"
    asignar_practica("TPR01-RA1", "pendiente_revision")
    (_, estado, llamadas), = gl.generar_guias("TPR01", semanas=[s1])[0]
    assert estado == "revisar" and any("pendiente_revision" in a for a in vault.leer_pagina(md)[0]["avisos"])
    asignar_practica("TPR01-RA1")
    print("D2. una guía al día se omite; otro docente o facultad, o --forzar, la rehacen desde lo guardado SIN llamar al modelo; un temario que "
          "cambia la vuelve a pedir (L17 lo avisa); una práctica sin aceptar deja la guía en `revisar` -- OK")

    # D2b. el procedimiento sin diagramas de flujo, o sin que los pasos digan que comprobar, vuelve al modelo
    def sin_diagramas(u):
        g = _fixtures.guia_falsa(u)
        for etapa in g.etapas:
            etapa.diagrama = None
        for p in g.pasos():
            p.verificacion = ""
        return g
    LLAMADAS.clear()
    RESPUESTAS.append(sin_diagramas)
    gl.generar_guia("TPR01", s1, replanificar=True)
    assert len(LLAMADAS) == 2 and "llevan `diagrama`" in LLAMADAS[1] and "qué comprobar" in LLAMADAS[1], LLAMADAS[1][-600:]
    print("D2b. un procedimiento sin diagramas de flujo, o cuyos pasos no dicen qué comprobar, vuelve al modelo con el motivo -- OK")

    # D2c. sin practica de un manual: la guia sale de la bibliografia ingerida (el RA tiene criterios practicos y fuentes cargadas)
    fm_ra, cuerpo_ra = vault.leer_pagina(vault.RESULTADOS / "TPR01-RA1.md")
    sin_manual = {**fm_ra, "requiere_practica": None, "practica_experimentos": [], "correlacion_estado": "sin_candidato"}
    vault.escribir_pagina(vault.RESULTADOS / "TPR01-RA1.md", sin_manual, cuerpo_ra)
    assert gl.semanas_con_guia("TPR01")[0] == [s1, s2], "la bibliografía también da guía"
    def sin_base(u):
        g = _fixtures.guia_falsa(u)
        g.base_bibliografica = []
        return g
    LLAMADAS.clear()
    RESPUESTAS.append(sin_base)
    (_, estado, llamadas), = gl.generar_guias("TPR01", semanas=[s1])[0]
    assert llamadas == 1 and len(LLAMADAS) == 2 and "`base_bibliografica` dice en qué fuentes cargadas" in LLAMADAS[1]
    usuario_bib = LLAMADAS[0]
    for dato in ("Origen de la práctica: bibliografía ingerida", "PROPÓN la práctica", "(ninguna de un manual", "[1] libro-a"):
        assert dato in usuario_bib, dato
    assert "banco-uno" not in usuario_bib.split("Fuentes cargadas")[1].split("Pasajes")[0], "sin manual, las fuentes son la bibliografía del RA"
    fm = vault.leer_pagina(md)[0]
    assert fm["origen_practica"] == "bibliografia" and fm["practica"] is None and fm["practica_experimento"] is None and fm["base_bibliografica"] == ["[[libro-a]]"]
    assert estado == "revisar" and any("propuesta a partir de la bibliografía cargada ([1] libro-a)" in a and "el docente valida" in a for a in fm["avisos"]), fm["avisos"]
    tex_bib = md.with_suffix(".tex").read_text(encoding="utf-8")
    assert r"\textbf{Práctica:} propuesta a partir de la bibliografía \cite{ref1}" in tex_bib and gl.problemas_del_tex(tex_bib, md.with_suffix(".bib").read_text(encoding="utf-8")) == []
    assert "**Práctica:** propuesta a partir de la bibliografía [1]" in vault.leer_pagina(md)[1]
    fm_ra2, cuerpo_ra2 = vault.leer_pagina(vault.RESULTADOS / "TPR01-RA2.md")
    assert "ni bibliografía cargada" in gl.semanas_con_guia("TPR01")[1][otra], "sin manual y sin fuentes no hay de dónde proponerla"

    # el docente revisó la correlación del RA y decidió no asignar práctica: se respeta (no se propone desde la bibliografía), salvo
    # con --desde-bibliografia, que la marca y la deja en `revisar`; una vez pedida así, las corridas siguientes la conservan
    vault.escribir_pagina(vault.RESULTADOS / "TPR01-RA1.md", {**sin_manual, "correlacion_revisado_por_docente": True}, cuerpo_ra)
    con, sin = gl.semanas_con_guia("TPR01")
    assert s1 not in con and "el docente revisó la correlación del RA TPR01-RA1 y no asignó práctica" in sin[s1], sin
    LLAMADAS.clear()
    assert "el docente revisó la correlación" in esperar(ValueError, gl.generar_guias, "TPR01", semanas=[s1]) and not LLAMADAS
    assert s1 in gl.semanas_con_guia("TPR01", desde_bibliografia=True)[0]
    (_, estado, llamadas), = gl.generar_guias("TPR01", semanas=[s1], desde_bibliografia=True)[0]
    fm = vault.leer_pagina(md)[0]
    # (lo que escribió el modelo para esta semana desde la bibliografía sigue guardado con la misma huella: se rehace sin LLM)
    assert llamadas == 0 and estado == "revisar" and fm["desde_bibliografia"] is True and fm["origen_practica"] == "bibliografia", (llamadas, fm)
    assert any("se pidió con --desde-bibliografia" in a for a in fm["avisos"]), fm["avisos"]
    LLAMADAS.clear()
    assert [e for _, e, _ in gl.generar_guias("TPR01", semanas=[s1])[0]] == ["omitida"] and not LLAMADAS, "pedida así, la guía se conserva"
    vault.escribir_pagina(vault.RESULTADOS / "TPR01-RA1.md", fm_ra, cuerpo_ra)
    LLAMADAS.clear()
    gl.generar_guias("TPR01", semanas=[s1])
    assert len(LLAMADAS) == 1 and vault.leer_pagina(md)[0]["origen_practica"] == "manual", "con la práctica asignada otra vez, vuelve al manual"

    # un formato nuevo: lo guardado (.guia.json) se reutiliza sin LLM si pasa la validación actual; uno del formato 1 (sin diagramas) no
    contenido = gl.ruta_contenido(md)
    datos = json.loads(contenido.read_text(encoding="utf-8"))
    fm_md, cuerpo_md = vault.leer_pagina(md)
    vault.escribir_pagina(md, {**fm_md, "formato": 1}, cuerpo_md)
    contenido.write_text(json.dumps({**datos, "formato": 1}, ensure_ascii=False), encoding="utf-8")
    LLAMADAS.clear()
    (_, _, llamadas), = gl.generar_guias("TPR01", semanas=[s1])[0]
    assert llamadas == 0 and not LLAMADAS and vault.leer_pagina(md)[0]["formato"] == gl.FORMATO, "válido con la validación actual: sin LLM"
    for etapa in datos["guia"]["etapas"]:
        etapa["diagrama"] = None
    vault.escribir_pagina(md, {**vault.leer_pagina(md)[0], "formato": 1}, cuerpo_md)
    contenido.write_text(json.dumps({**datos, "formato": 1}, ensure_ascii=False), encoding="utf-8")
    (_, _, llamadas), = gl.generar_guias("TPR01", semanas=[s1])[0]
    assert llamadas == 1 and len(LLAMADAS) == 1, "del formato 1 (sin diagramas de flujo): no pasa la validación, 1 llamada"
    assert json.loads(contenido.read_text(encoding="utf-8"))["formato"] == gl.FORMATO, "el .guia.json guarda su formato"
    print("D2c. sin práctica de un manual, la guía se propone a partir de la bibliografía ingerida (con las fuentes en que se basa, en `revisar` para "
          "que la valide el docente); sin manual ni bibliografía no hay guía; si el docente revisó la correlación sin asignar práctica, solo con "
          "--desde-bibliografia; con la práctica asignada vuelve al manual; un formato nuevo se rehace sin LLM solo si lo guardado pasa la validación -- OK")

    # D3. --compilar (simulado): pdflatex -> biber -> pdflatex -> pdflatex, sin shell-escape, con tiempo maximo y sin entrada
    ordenes: list[list[str]] = []
    falla = [False]

    def proceso_falso(args, **kw):
        assert kw.get("timeout") == gl.TIEMPO_MAXIMO and kw.get("stdin") is subprocess.DEVNULL and kw["env"].get("openin_any") == "p", kw
        ordenes.append([Path(args[0]).name, *args[1:]])
        cwd = Path(kw["cwd"])
        nombre = args[-1] if args[-1].endswith(".tex") else args[-1] + ".tex"
        (cwd / nombre).with_suffix(".aux").write_text("x", encoding="utf-8")
        if falla[0] and "biber" in args[0]:
            (cwd / nombre).with_suffix(".blg").write_text("ERROR - Cannot find 'x.bcf'!\n", encoding="utf-8")
            return subprocess.CompletedProcess(args, 2, "", "")
        (cwd / nombre).with_suffix(".pdf").write_bytes(b"%PDF")
        return subprocess.CompletedProcess(args, 0, "", "")

    which, run = gl.shutil.which, gl.subprocess.run
    gl.shutil.which, gl.subprocess.run = (lambda nombre: nombre), proceso_falso
    try:
        gl.generar_guia("TPR01", s1, forzar=True, compilar_pdf=True)
        assert [o[0] for o in ordenes] == ["pdflatex", "biber", "pdflatex", "pdflatex"] and all("-no-shell-escape" in o for o in ordenes if o[0] == "pdflatex")
        fm = vault.leer_pagina(md)[0]
        assert fm["compilada"] == vault.hoy() and md.with_suffix(".pdf").exists() and not list(carpeta.glob("*.aux")), fm
        falla[0] = True
        gl.generar_guia("TPR01", s1, forzar=True, compilar_pdf=True)
        fm = vault.leer_pagina(md)[0]
        assert fm["compilada"] is None and fm["estado"] == "revisar" and not md.with_suffix(".pdf").exists() and not list(carpeta.glob("*.aux"))
        assert any(a.startswith("compilación: biber: ERROR - Cannot find") for a in fm["avisos"]), fm["avisos"]
    finally:
        gl.shutil.which, gl.subprocess.run = which, run
    md.with_suffix(".pdf").write_bytes(b"%PDF de otra version")
    gl.generar_guia("TPR01", s1, forzar=True)
    assert not md.with_suffix(".pdf").exists(), "reescribir el .tex borra el PDF de antes"
    md.with_suffix(".pdf").write_bytes(b"%PDF")
    momento = md.with_suffix(".tex").stat().st_mtime - 10
    os.utime(md.with_suffix(".pdf"), (momento, momento))
    assert any("más viejo que su .tex" in h.mensaje for h in lint.revisar() if h.regla == "L17")
    md.with_suffix(".pdf").unlink()
    print("D3. --compilar (simulado) corre pdflatex → biber → pdflatex → pdflatex sin shell-escape, con tiempo máximo y sin entrada; un fallo de biber "
          "queda como aviso y borra el PDF y los auxiliares; reescribir el .tex borra el PDF de antes y L17 avisa de uno más viejo -- OK")

    # D4. lint L17: una semana con practica y temario sin guia, un .tex sin su .md, una guia cuyo temario ya no existe
    asignar_practica("TPR01-RA2")
    l17 = [h for h in lint.revisar() if h.regla == "L17"]
    assert any("sin guía de laboratorio" in h.mensaje and h.ruta.endswith(f"TPR01-semana{otra:02d}.md") for h in l17), l17
    (carpeta / "huerfana.tex").write_text("%", encoding="utf-8")
    md2 = carpeta / f"TPR01-semana{s2:02d}.md"
    temario2 = vault.TEMARIOS / f"TPR01-semana{s2:02d}.md"
    respaldo = temario2.read_bytes()
    temario2.unlink()
    l17 = [h for h in lint.revisar() if h.regla == "L17"]
    assert any(h.ruta.endswith("huerfana.tex") for h in l17) and any("su temario" in h.mensaje and h.ruta.endswith(md2.name) for h in l17), l17
    temario2.write_bytes(respaldo)
    (carpeta / "huerfana.tex").unlink()
    print("D4. lint L17 avisa de una semana con práctica y temario sin guía, de un .tex sin su .md y de una guía cuyo temario ya no existe -- OK")

    # D5. el comando
    r = subprocess.run([sys.executable, "-B", str(SRC / "guia_laboratorio.py"), "TPR01", "--semana", str(s1), "--forzar", "--docente", "Docente Tres",
                        "--facultad", "Facultad Tres"], cwd=raiz, capture_output=True, text=True, encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
    assert r.returncode == 0 and "1 guías escritas (0 llamadas al modelo)" in r.stdout, (r.stdout, r.stderr)
    r = subprocess.run([sys.executable, "-B", str(SRC / "guia_laboratorio.py"), "TEO01"], cwd=raiz, capture_output=True, text=True,
                       encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
    assert r.returncode == 1 and "es teórica" in r.stdout and "Traceback" not in r.stderr, (r.stdout, r.stderr)
    assert subprocess.run([sys.executable, "-B", str(SRC / "guia_laboratorio.py"), "--help"], capture_output=True, env=ENTORNO,
                          stdin=subprocess.DEVNULL).returncode == 0
    print("D5. como comando: rehacer con otro docente y facultad no cuesta llamadas; una asignatura teórica da un error claro; --help funciona -- OK")


def main() -> None:
    probar_esquema()
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar_flujo(Path(tmp))
        finally:
            os.chdir(original)
    print("TODO OK -- la guía de laboratorio sale del planeador, el temario, el RA y la práctica del manual, con la estructura de la plantilla "
          "institucional en .md y .tex, se rehace sin LLM mientras nada cambie y se audita (esta suite no compila).")


if __name__ == "__main__":
    main()
