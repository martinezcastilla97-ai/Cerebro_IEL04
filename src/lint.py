"""LINT -- revision de salud del vault (sin LLM, sin OPENAI_API_KEY).

Uso (desde la raiz del vault):
    python src/lint.py

Sale con codigo 1 si hay ERRORES; los AVISOS no hacen fallar. Reglas:

    L01 frontmatter valido y `tipo` acorde con la carpeta
    L02 asignatura valida (tipo_abordaje acorde con hp_totales, hp_totales <= had_totales,
        ninguna hora ni credito negativo)
    L03 RA con `requiere_practica` en una asignatura teorica (prohibido)
    L04 RA valido, con codigo `{asignatura}-RA{n}` y el tipo_abordaje de su asignatura
    L05 RA huerfano: su asignatura no lo lista en `resultados_aprendizaje`  (aviso)
    L06 enlaces [[...]] rotos
    L07 codigos duplicados dentro de un mismo tipo de pagina
    L08 manual de banco (`equipo-laboratorio`): sin `practicas` (aviso) o con practicas invalidas/repetidas
    L09 RA teorico-practico con score_RA < 0.40: sin evidencia semantica de practica  (aviso)
    L10 temario en una semana de examen, o sin planeador
    L11 asignatura que su programa no lista en `asignaturas`  (aviso)
    L12 nombre de archivo de un RA que no coincide con su `codigo`  (aviso; correlate.py,
        temario.py y correlate_planeador.py localizan el RA por `{codigo}.md`)
    L13 horas que no cuadran con los creditos: had_totales + hti_totales != creditos x
        HORAS_POR_CREDITO (aviso; had_totales ya incluye las HP, no se suman aparte)
    L14 presentaciones (aviso): un temario cuya presentacion .tex ya no existe, quedo desactualizada (el temario
        cambio despues de generarla) o se hizo con otra version del diseno (`presentacion_diseno` distinto de
        diseno_iub.VERSION), o un .tex en generacion/presentaciones/ que ningun temario registra. Dice cuanto cuesta
        rehacerla: sin LLM si el plan guardado tiene todas sus partes (con los elementos del .tex del temario que usan);
        si no, una llamada por parte que falta o cambio. Tambien avisa de un PDF mas viejo que su .tex
    L15 figuras del temario (aviso): un temario que incluye una figura (`![...](figuras/x.png)`) que ya no existe
        en generacion/temarios/figuras/, o una figura que ningun temario incluye
    L16 la version LaTeX del temario (aviso): un temario sin su .tex (hecho antes de que TEMARIO lo escribiera), con
        el .tex borrado o con el .md editado despues de escribirlo (`latex_temario_hash`), o un .tex de
        generacion/temarios/ sin su .md, o un PDF mas viejo que su .tex
    L17 guias de laboratorio (aviso): una semana de clase con temario y con practica asignada al RA (o sin ella, pero con criterios
        practicos y bibliografia cargada, de la que se propondria), pero sin guia; una guia cuyo temario ya
        no existe o cambio despues de escribirla, cuyo .tex falta o cuyo PDF es mas viejo que su .tex; o un .tex de
        generacion/guias-laboratorio/ sin su .md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

import vault
from schema_extraccion import Practica, TipoAbordaje

ERROR, AVISO = "ERROR", "AVISO"

# L13: creditos x HORAS_POR_CREDITO = had_totales + hti_totales (had_totales ya incluye
# las horas practicas). Convencion de esta institucion -- ver CLAUDE.md § LINT.
HORAS_POR_CREDITO = 48

CARPETA_TIPO = {
    "wiki/programas": "programa", "wiki/asignaturas": "asignatura", "wiki/resultados-aprendizaje": "resultado_aprendizaje",
    "wiki/competencias": "competencia", "wiki/recursos-web": "recurso_web", "wiki/fuentes": "fuente",
    "wiki/entidades": "entidad", "wiki/conceptos": "concepto", "wiki/consultas": "consulta",
    "generacion/planeador": "planeador", "generacion/temarios": "temario", "generacion/guias-laboratorio": "guia_laboratorio",
    "correlaciones": "vista_dataview",
}
PAGINA_TIPO = {"wiki/index.md": "index", "wiki/marco-pedagogico.md": "marco_pedagogico"}


class Hallazgo(NamedTuple):
    severidad: str
    ruta: str
    regla: str
    mensaje: str


class Pagina(NamedTuple):
    ruta: Path
    fm: dict
    cuerpo: str
    tipo_esperado: str | None


def _tipo_esperado(ruta: Path) -> str | None:
    p = ruta.as_posix()
    if p in PAGINA_TIPO:
        return PAGINA_TIPO[p]
    return next((tipo for carpeta, tipo in CARPETA_TIPO.items() if p.startswith(carpeta + "/")), None)


def _enlaces_profundos(valor) -> list[str]:
    """Destinos de [[...]] en cualquier parte de un frontmatter (texto, listas, diccionarios)."""
    if isinstance(valor, str):
        return vault.enlaces(valor)
    if isinstance(valor, dict):
        return [e for v in valor.values() for e in _enlaces_profundos(v)]
    if isinstance(valor, (list, tuple)):
        destinos: list[str] = []
        for v in valor:
            if isinstance(v, (list, tuple)):            # [[X]] sin comillas: YAML lo lee como lista anidada
                destinos += [str(x).strip() for x in vault._aplanar(v)]
            else:
                destinos += _enlaces_profundos(v)
        return destinos
    return []


_BLOQUE_CODIGO = re.compile(r"```.*?```", re.DOTALL)
_CODIGO_EN_LINEA = re.compile(r"`[^`\n]*`")


def _enlaces_cuerpo(cuerpo: str) -> list[str]:
    return vault.enlaces(_CODIGO_EN_LINEA.sub("", _BLOQUE_CODIGO.sub("", cuerpo)))


def cargar_paginas(hallazgos: list[Hallazgo]) -> list[Pagina]:
    rutas = {*vault.WIKI.rglob("*.md"), *Path("generacion").rglob("*.md"), *Path("correlaciones").rglob("*.md")}
    paginas = []
    for ruta in sorted(rutas):
        if ruta.as_posix() == "wiki/log.md":
            continue
        try:
            fm, cuerpo = vault.leer_pagina(ruta)
        except Exception as error:
            hallazgos.append(Hallazgo(ERROR, ruta.as_posix(), "L01", f"frontmatter YAML inválido: {error}"))
            continue
        paginas.append(Pagina(ruta, fm, cuerpo, _tipo_esperado(ruta)))
    return paginas


def codigo_de(pagina: Pagina) -> str:
    """'TPR01' de generacion/temarios/TPR01-semana03.md"""
    return pagina.ruta.stem.split("-semana")[0]


def revisar() -> list[Hallazgo]:
    import correlate  # calcular_score_ra (no exige openai)

    hallazgos: list[Hallazgo] = []
    paginas = cargar_paginas(hallazgos)
    por_nombre = {p.ruta.stem: p for p in paginas}
    nombres = set(por_nombre) | {"log"}

    def agregar(severidad: str, pagina: Pagina, regla: str, mensaje: str) -> None:
        hallazgos.append(Hallazgo(severidad, pagina.ruta.as_posix(), regla, mensaje))

    # L01 tipo, L06 enlaces, L07 codigos
    codigos: dict[tuple[str, str], list[str]] = {}
    for p in paginas:
        if not p.fm:
            agregar(ERROR, p, "L01", "sin frontmatter")
        elif p.tipo_esperado and p.fm.get("tipo") != p.tipo_esperado:
            agregar(ERROR, p, "L01", f"`tipo: {p.fm.get('tipo')}` no coincide con su carpeta (se esperaba `{p.tipo_esperado}`)")
        for destino in dict.fromkeys(_enlaces_profundos(p.fm) + _enlaces_cuerpo(p.cuerpo)):
            if vault.destino_pagina(destino) not in nombres:
                agregar(ERROR, p, "L06", f"enlace roto: [[{destino}]]")
        if p.fm.get("codigo") is not None:
            codigos.setdefault((str(p.fm.get("tipo")), str(p.fm["codigo"])), []).append(p.ruta.as_posix())
    for (tipo, codigo), rutas in codigos.items():
        if len(rutas) > 1:
            hallazgos.append(Hallazgo(ERROR, rutas[0], "L07", f"código `{codigo}` repetido en {len(rutas)} páginas `{tipo}`: {', '.join(rutas)}"))

    # asignaturas (L02, L11)
    asignaturas = {}
    for p in (p for p in paginas if p.fm.get("tipo") == "asignatura"):
        try:
            asignaturas[p.ruta.stem] = vault.asignatura_desde_frontmatter(p.fm)
        except Exception as error:
            agregar(ERROR, p, "L02", f"asignatura inválida: {' '.join(str(error).split())[:300]}")
            continue
        asignatura_p = asignaturas[p.ruta.stem]
        horas_reales = asignatura_p.had_totales + asignatura_p.hti_totales
        horas_esperadas = asignatura_p.creditos * HORAS_POR_CREDITO
        if horas_reales != horas_esperadas:
            agregar(AVISO, p, "L13", f"`had_totales` + `hti_totales` = {horas_reales} no coincide con "
                                     f"`creditos` × {HORAS_POR_CREDITO} = {horas_esperadas}")
        for nombre_programa in vault.enlaces(p.fm.get("programa")):
            programa = por_nombre.get(vault.destino_pagina(nombre_programa))
            if programa and p.ruta.stem not in [vault.destino_pagina(e) for e in vault.enlaces(programa.fm.get("asignaturas"))]:
                agregar(AVISO, p, "L11", f"el programa [[{nombre_programa}]] no la lista en `asignaturas`")

    # resultados de aprendizaje (L03, L04, L05, L09)
    for p in (p for p in paginas if p.fm.get("tipo") == "resultado_aprendizaje"):
        try:
            ra = vault.ra_desde_frontmatter(p.fm)
        except Exception as error:
            agregar(ERROR, p, "L04", f"RA inválido: {' '.join(str(error).split())[:300]}")
            continue
        nombre_asignatura = vault.enlace(p.fm.get("pertenece_a"))
        asignatura = asignaturas.get(vault.destino_pagina(nombre_asignatura or ""))
        if asignatura is None:
            if nombre_asignatura is None:
                agregar(ERROR, p, "L04", "falta `pertenece_a`")
            continue   # asignatura inexistente o invalida: ya se informo (L06 / L02)
        if not re.fullmatch(rf"{re.escape(asignatura.codigo)}-RA\d+", ra.codigo):
            agregar(ERROR, p, "L04", f"el código `{ra.codigo}` no es `{asignatura.codigo}-RA{{n}}`")
        if p.ruta.stem != ra.codigo:
            agregar(AVISO, p, "L12", f"el nombre de archivo (`{p.ruta.stem}`) no coincide con su `codigo` (`{ra.codigo}`)")
        if ra.tipo_abordaje != asignatura.tipo_abordaje:
            agregar(ERROR, p, "L04", f"`tipo_abordaje` ({ra.tipo_abordaje.value}) difiere del de su asignatura ({asignatura.tipo_abordaje.value})")
        if asignatura.tipo_abordaje == TipoAbordaje.teorica and p.fm.get("requiere_practica"):
            agregar(ERROR, p, "L03", "`requiere_practica` en un RA de una asignatura teórica (solo se permite `aplicacion_potencial`)")
        fm_asignatura = por_nombre[vault.destino_pagina(nombre_asignatura)].fm
        if p.ruta.stem not in [vault.destino_pagina(e) for e in vault.enlaces(fm_asignatura.get("resultados_aprendizaje"))]:
            agregar(AVISO, p, "L05", f"RA huérfano: [[{nombre_asignatura}]] no lo lista en `resultados_aprendizaje`")
        if asignatura.tipo_abordaje == TipoAbordaje.teorico_practica and correlate.calcular_score_ra(ra, asignatura) < correlate.UMBRAL_GATE:
            agregar(AVISO, p, "L09", "RA sin evidencia semántica de práctica pese a HP>0 (score_RA < 0.40)")

    # manuales de banco (L08)
    for p in (p for p in paginas if p.fm.get("tipo") == "fuente"):
        etiquetas = p.fm.get("etiquetas") or []
        if correlate.ETIQUETA_BANCO not in ([etiquetas] if isinstance(etiquetas, str) else etiquetas):
            continue
        if not p.fm.get("practicas"):
            agregar(AVISO, p, "L08", "manual de banco sin `practicas` en el frontmatter: no aporta candidatos a CORRELATE")
            continue
        vistos: set[str] = set()
        for entrada in p.fm["practicas"]:
            try:
                practica = Practica.model_validate(entrada)
            except Exception as error:
                agregar(ERROR, p, "L08", f"práctica inválida ({(entrada or {}).get('codigo', '?')}): {' '.join(str(error).split())[:200]}")
                continue
            if practica.codigo in vistos:
                agregar(ERROR, p, "L08", f"práctica repetida: {practica.codigo}")
            vistos.add(practica.codigo)

    # generacion (L10)
    for p in (p for p in paginas if p.fm.get("tipo") == "temario"):
        codigo = p.ruta.stem.split("-semana")[0]
        plan = por_nombre.get(f"{codigo}-planeador")
        if plan is None:
            agregar(AVISO, p, "L10", f"no existe el planeador de {codigo}")
        elif p.fm.get("semana") in (plan.fm.get("semanas_examen") or []):
            agregar(ERROR, p, "L10", f"temario en la semana {p.fm.get('semana')}, que es de examen")

    # presentaciones (L14)
    import presentaciones  # hash_cuerpo y DISENO (no exige openai)

    registradas: set[str] = set()
    for p in (p for p in paginas if p.fm.get("tipo") == "temario" and p.fm.get("presentacion_archivo")):
        archivo = Path(str(p.fm["presentacion_archivo"]))
        registradas.add(archivo.as_posix())
        semana = p.fm.get("semana")
        # rehacerla es gratis solo si el plan guardado tiene, verificadas, las diapositivas de todas las partes del temario (la apertura
        # y cada bloque) con la misma huella. Las de un diseño anterior al 5 no lo tienen (su plan era de otro formato); uno corrupto o
        # de otra versión del temario tampoco vale: cada parte que falta cuesta una llamada.
        try:
            n_semana = int(semana)
        except (TypeError, ValueError):
            n_semana = 0
        pendientes = presentaciones.partes_pendientes(archivo, p.fm, p.cuerpo, codigo_de(p), n_semana)
        costo = ("desde el plan guardado, sin LLM" if not pendientes
                 else f"pidiendo al modelo {len(pendientes)} parte(s) sin plan guardado válido (.plan.json): cuesta una llamada al modelo por parte")
        if not archivo.exists():
            agregar(AVISO, p, "L14", f"su presentación `{archivo.as_posix()}` ya no existe: `python src/presentaciones.py {codigo_de(p)} --semana {semana} --forzar` "
                                     f"la rehace {costo}")
        elif p.fm.get("presentacion_temario_hash") != presentaciones.hash_cuerpo(p.cuerpo):
            agregar(AVISO, p, "L14", "presentación desactualizada: el temario cambió después de generarla (`python src/presentaciones.py "
                                     f"{codigo_de(p)} --semana {semana}` la rehace {costo})")
        elif p.fm.get("presentacion_diseno") != presentaciones.DISENO:
            agregar(AVISO, p, "L14", "presentación hecha con otra versión del diseño (`python src/presentaciones.py "
                                     f"{codigo_de(p)} --semana {semana}` la rehace {costo})")
        elif pendientes:
            agregar(AVISO, p, "L14", "presentación con partes por rehacer: le faltan al plan, quedaron provisionales o usan figuras, tablas o "
                                     "ecuaciones del .tex del temario que ya no están (`python src/presentaciones.py "
                                     f"{codigo_de(p)} --semana {semana}` la rehace {costo})")
        if archivo.with_suffix(".pdf").exists() and presentaciones.pdf_desactualizado(archivo):
            agregar(AVISO, p, "L14", f"el PDF de `{archivo.as_posix()}` es más viejo que su .tex (es de otra versión): "
                                     f"`python src/presentaciones.py {codigo_de(p)} --semana {semana} --compilar` lo vuelve a compilar, o bórralo")
    for tex in sorted(vault.PRESENTACIONES.rglob("*.tex")):
        if tex.as_posix() not in registradas:
            hallazgos.append(Hallazgo(AVISO, tex.as_posix(), "L14", "presentación que ningún temario registra (¿el temario se regeneró o se borró?)"))

    # figuras de los temarios (L15)
    incluidas: set[str] = set()
    for p in (p for p in paginas if p.fm.get("tipo") == "temario"):
        for figura in re.findall(r"!\[[^\]]*\]\((figuras/[^)\s]+)\)", p.cuerpo):
            incluidas.add(figura)
            if not (vault.TEMARIOS / figura).is_file():
                agregar(AVISO, p, "L15", f"la figura `{figura}` que incluye ya no existe: `python src/temario.py {codigo_de(p)} --semana {p.fm.get('semana')} --forzar` "
                                         "vuelve a generar el temario y sus figuras")
    if (vault.TEMARIOS / "figuras").is_dir():
        for png in sorted((vault.TEMARIOS / "figuras").glob("*.png")):
            if f"figuras/{png.name}" not in incluidas:
                hallazgos.append(Hallazgo(AVISO, png.as_posix(), "L15", "figura que ningún temario incluye (¿el temario se regeneró o se borró?)"))

    # el .tex en paralelo de cada temario (L16)
    import temario_latex  # hash_cuerpo (sin dependencias)

    con_md: set[str] = set()
    for p in (p for p in paginas if p.fm.get("tipo") == "temario"):
        archivo = Path(p.fm.get("latex_archivo") or p.ruta.with_suffix(".tex"))
        con_md.add(archivo.as_posix())
        rehacer = f"`python src/temario.py {codigo_de(p)} --semana {p.fm.get('semana')} --forzar` lo vuelve a redactar con los dos archivos (~10 llamadas al modelo)"
        if not p.fm.get("latex_archivo"):
            agregar(AVISO, p, "L16", f"temario sin su versión LaTeX (se generó antes de que TEMARIO la escribiera): {rehacer}")
        elif not archivo.is_file():
            agregar(AVISO, p, "L16", f"su versión LaTeX `{archivo.as_posix()}` ya no existe: {rehacer}")
        elif p.fm.get("latex_temario_hash") != temario_latex.hash_cuerpo(p.cuerpo):
            agregar(AVISO, p, "L16", f"el .md se editó después de escribir `{archivo.as_posix()}`: el .tex no tiene ese cambio "
                                     f"(cópialo a mano en el .tex, o {rehacer})")
        pdf = archivo.with_suffix(".pdf")
        if archivo.is_file() and pdf.exists() and pdf.stat().st_mtime < archivo.stat().st_mtime:
            agregar(AVISO, p, "L16", f"el PDF `{pdf.as_posix()}` es más viejo que su .tex (es de otra versión): bórralo o vuelve a compilar el .tex "
                                     "(Overleaf, o pdflatex en su carpeta)")
    if vault.TEMARIOS.is_dir():
        for tex in sorted(vault.TEMARIOS.glob("*.tex")):
            if tex.as_posix() not in con_md:
                hallazgos.append(Hallazgo(AVISO, tex.as_posix(), "L16", "versión LaTeX de un temario que ya no existe (¿el .md se borró o se renombró?)"))

    # las guias de laboratorio (L17)
    import json

    import guia_laboratorio  # FORMATO y ruta_contenido (matplotlib solo se importa al dibujar)

    guias = {p.ruta.stem: p for p in paginas if p.fm.get("tipo") == "guia_laboratorio"}
    for p in guias.values():
        semana = p.fm.get("semana")
        rehacer = f"`python src/guia_laboratorio.py {codigo_de(p)} --semana {semana}`"
        ruta_temario = vault.TEMARIOS / f"{p.ruta.stem}.md"
        archivo = Path(str(p.fm.get("archivo_tex") or p.ruta.with_suffix(".tex")))
        if not ruta_temario.exists():
            agregar(AVISO, p, "L17", f"su temario `{ruta_temario.as_posix()}` ya no existe (¿se borró o se renombró?)")
        elif p.fm.get("temario_hash") != temario_latex.hash_cuerpo(vault.leer_pagina(ruta_temario)[1]):
            agregar(AVISO, p, "L17", f"guía desactualizada: el temario cambió después de escribirla ({rehacer} la vuelve a pedir: 1 llamada al modelo)")
        if p.fm.get("formato") != guia_laboratorio.FORMATO:
            try:
                guardado = json.loads(guia_laboratorio.ruta_contenido(p.ruta).read_text(encoding="utf-8")).get("formato")
            except (OSError, ValueError, AttributeError):
                guardado = None
            costo = (f"sin LLM: lo guardado (.guia.json) es del formato {guardado}, que pasa la validación del actual"
                     if guardado in (guia_laboratorio.FORMATO, *guia_laboratorio.FORMATOS_REUTILIZABLES) else
                     "1 llamada al modelo: lo guardado (.guia.json) es de otro formato y no pasa la validación del actual"
                     + (" (el formato 1 no tenía diagramas de flujo)" if guardado in (1, None) else ""))
            agregar(AVISO, p, "L17", f"guía de otro formato ({p.fm.get('formato')}; el actual es {guia_laboratorio.FORMATO}): {rehacer} la rehace — {costo}")
        if not archivo.is_file():
            agregar(AVISO, p, "L17", f"su .tex `{archivo.as_posix()}` no existe ({rehacer} --forzar lo vuelve a escribir, sin LLM si nada cambió)")
        elif archivo.with_suffix(".pdf").exists() and archivo.with_suffix(".pdf").stat().st_mtime < archivo.stat().st_mtime:
            agregar(AVISO, p, "L17", f"el PDF de `{archivo.as_posix()}` es más viejo que su .tex (es de otra versión): {rehacer} --compilar, o bórralo")
    asignaturas = {p.ruta.stem: p for p in paginas if p.fm.get("tipo") == "asignatura"}
    ras = {p.ruta.stem: p for p in paginas if p.fm.get("tipo") == "resultado_aprendizaje"}
    for p in (p for p in paginas if p.fm.get("tipo") == "temario"):
        ra = ras.get(vault.enlace(p.fm.get("resultado_aprendizaje")) or "")
        asignatura = asignaturas.get(vault.enlace(p.fm.get("asignatura")) or "")
        if not (ra and asignatura and (asignatura.fm.get("hp_totales") or 0) > 0) or p.ruta.stem in guias:
            continue
        comando = f"`python src/guia_laboratorio.py {codigo_de(p)} --semana {p.fm.get('semana')}` (1 llamada al modelo)"
        if vault.enlace(ra.fm.get("requiere_practica")) and ra.fm.get("practica_experimentos"):
            agregar(AVISO, p, "L17", f"semana con práctica asignada ({vault.enlace(ra.fm.get('requiere_practica'))} — {ra.fm['practica_experimentos'][0]}) "
                                     f"y sin guía de laboratorio: {comando}")
        elif (not ra.fm.get("correlacion_revisado_por_docente")          # el docente decidio no asignar practica: no se propone desde la bibliografia
              and any((ce or {}).get("categoria_accion") in ("manipulacion_fisica", "cognitiva_experimental") for ce in ra.fm.get("criterios_evaluacion") or [])
              and any((vault.FUENTES / f"{f}.md").exists() for f in vault.enlaces(ra.fm.get("bibliografia")))):
            agregar(AVISO, p, "L17", "semana sin práctica de un manual, pero con criterios de carácter práctico y bibliografía cargada, y sin guía de "
                                     f"laboratorio (se propondría a partir de la bibliografía): {comando}")
    carpeta_guias = Path("generacion") / "guias-laboratorio"
    if carpeta_guias.is_dir():
        for tex in sorted(carpeta_guias.rglob("*.tex")):
            if tex.stem not in guias:
                hallazgos.append(Hallazgo(AVISO, tex.as_posix(), "L17", "guía de laboratorio (.tex) sin su .md (¿se borró o se renombró?)"))

    return sorted(hallazgos, key=lambda h: (h.severidad != ERROR, h.ruta, h.regla))


if __name__ == "__main__":
    vault.consola_utf8()
    hallazgos = revisar()
    for h in hallazgos:
        print(f"{h.severidad:5s} {h.regla} {h.ruta}: {h.mensaje}")
    errores = sum(h.severidad == ERROR for h in hallazgos)
    print(f"\n{errores} errores, {len(hallazgos) - errores} avisos" if hallazgos else "Sin hallazgos: el vault está sano.")
    sys.exit(1 if errores else 0)
