"""PRESENTACIONES -- una presentacion Beamer (pdfLaTeX, diseno institucional IUB) por temario, al estilo de las presentaciones de
ejemplo del docente, en tres pasos:

    1. las PARTES (sin LLM): el temario se divide en la apertura (metadatos y resultados de aprendizaje) y sus bloques, tal como
       los numera su indice temporizado (`(Bloque k)` en cada encabezado, con sus minutos);
    2. el LaTeX de cada parte (LLM, una llamada por parte): el modelo, con las directrices de un experto en LaTeX y en presentaciones
       academicas (src/prompts/prompt-presentacion.md), escribe las diapositivas de esa parte -- titulo y cuerpo en LaTeX: TikZ,
       pgfplots, circuitikz, tablas y las cajas del diseno, sin imagenes --. Cada diapositiva pasa por latex_seguro.verificar_cuerpo
       (lista de comandos permitidos, claves que leen o escriben archivos, balance); lo que no cumple vuelve al modelo con el motivo,
       hasta 2 veces (temario._redactar). Si aun asi no cumple, esa parte queda con una diapositiva provisional y un aviso;
    3. el DISENO (sin LLM): diseno_iub.py escribe el preambulo, la portada, la ruta de la sesion, un separador por bloque, las
       referencias y el cierre; la verificacion estatica del .tex completo (latex_seguro.verificar_latex) y el registro en el
       frontmatter del temario (`presentacion_*`).

El plan (`{codigo}-semanaNN.plan.json`) guarda las diapositivas de cada parte con la huella de su texto: mientras una parte no
cambie, no se vuelve a pedir. Rehacer la presentacion por otro docente, otro programa o una version nueva del diseno no llama al
modelo; editar un bloque del temario solo vuelve a pedir ese bloque.

Uso (desde la raiz del vault):
    python src/presentaciones.py ABC01 --docente "Nombre" --programa "Programa"     # todas las semanas con temario
    python src/presentaciones.py ABC01 --semana 3
    python src/presentaciones.py --all
    python src/presentaciones.py ABC01 --forzar          # rehace el .tex aunque este al dia (desde el plan guardado, sin LLM)
    python src/presentaciones.py ABC01 --replanificar    # vuelve a pedir todas las partes al modelo aunque el temario no haya cambiado
    python src/presentaciones.py ABC01 --compilar        # ademas, el PDF (requiere pdflatex)
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
from dataclasses import dataclass
from pathlib import Path

import diseno_iub
import latex_seguro as ls
import temario
import vault
from schema_presentacion import DiapositivasParte

DISENO = diseno_iub.VERSION
FORMATO_PLAN = 2                    # el .plan.json del diseno 4 (formato 1) guardaba otra cosa: no se reutiliza
DOCENTE_POR_DEFECTO = "Docente de la asignatura"
PROGRAMA_POR_DEFECTO = "Institución Universitaria de Barranquilla"      # si el wiki no enlaza ningun programa
MINUTOS_POR_DIAPOSITIVA = 8         # orientativo: cuantas diapositivas se piden para un bloque segun su duracion
EXTENSIONES_AUXILIARES = (".aux", ".log", ".nav", ".out", ".snm", ".toc", ".vrb")
APERTURA = "apertura"

_ENCABEZADO_BLOQUE = re.compile(r"^(#{2,4})\s+(?:\d+(?:\.\d+)*\.?\s+)?(.*?)\s*\(Bloque\s+(\d+)\)\s*$")
_ENCABEZADO = re.compile(r"^(#{1,6})\s")
_FILA_INDICE = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*min\s*\|\s*$")
_FIGURA_MD = re.compile(r"!\[([^\]]*)\]\((figuras/[^)\s]+)\)")


def hash_cuerpo(cuerpo: str) -> str:
    """Huella del cuerpo del temario: si cambia (regenerado o editado a mano), su presentacion quedo desactualizada."""
    return hashlib.sha256(cuerpo.strip().encode("utf-8")).hexdigest()[:16]


def ruta_presentacion(codigo: str, semana: int) -> Path:
    return vault.PRESENTACIONES / codigo / f"{codigo}-semana{semana:02d}.tex"


def ruta_plan(tex: Path) -> Path:
    return tex.with_name(tex.stem + ".plan.json")


# ---------------------------------------------------------------------------
# Lo que se lee del temario (sin LLM)
# ---------------------------------------------------------------------------


@dataclass
class Parte:
    """Un trozo del temario que se convierte en diapositivas con una llamada: la apertura o un bloque del indice temporizado."""
    clave: str                       # "apertura" | "bloque-03"
    titulo: str
    texto: str                       # el Markdown de esa parte del temario
    bloque: diseno_iub.BloqueSesion | None = None

    @property
    def huella(self) -> str:
        minutos = self.bloque.minutos if self.bloque else 0
        return hashlib.sha256(f"{self.clave}\n{self.titulo}\n{minutos}\n{self.texto.strip()}".encode("utf-8")).hexdigest()[:16]


def indice_temporizado(cuerpo: str) -> dict[int, tuple[str, int]]:
    """{bloque: (contenido, minutos)} de la tabla de la seccion «Índice Temporizado» del temario."""
    m = re.search(r"(?m)^##\s+\d+\.\s+[ÍI]ndice [Tt]emporizado[^\n]*\n(.*?)(?=^##\s|\Z)", cuerpo, re.S)
    filas = {}
    for linea in (m.group(1).splitlines() if m else []):
        f = _FILA_INDICE.match(linea.strip())
        if f:
            filas[int(f.group(1))] = (re.sub(r"\*\*", "", f.group(2)).strip(), int(f.group(3)))
    return filas


def _sin_imagenes(texto: str) -> str:
    """Las figuras del temario son PNG: la presentacion no usa imagenes. Se le dice al modelo que la figura existe, de que es, y que
    si le sirve la dibuje con TikZ o pgfplots a partir de los datos y las ecuaciones del texto."""
    return _FIGURA_MD.sub(lambda m: f"[FIGURA DEL TEMARIO (imagen PNG, no disponible en la presentación): {m.group(1).strip()}. "
                                    "Si ayuda, redibújala con TikZ o pgfplots con los datos y ecuaciones del texto, sin inventar valores]", texto)


def partes_del_temario(cuerpo: str) -> list[Parte]:
    """La apertura (secciones 1 y 2: metadatos y resultados de aprendizaje) y un bloque por cada encabezado `(Bloque k)`, con el
    titulo y los minutos de su fila del indice temporizado. Un temario sin bloques reconocibles (editado a mano) se trata como uno
    solo, sin la bibliografia."""
    lineas = cuerpo.splitlines()
    indice = indice_temporizado(cuerpo)
    partes: list[Parte] = []

    ini = next((i for i, l in enumerate(lineas) if re.match(r"^##\s+1\.\s", l)), None)
    fin = next((i for i, l in enumerate(lineas) if re.match(r"^##\s+3\.\s", l)), None)
    if ini is not None:
        texto = "\n".join(lineas[ini:fin if fin is not None and fin > ini else ini + 1])
        partes.append(Parte(APERTURA, "Apertura de la sesión", texto))

    actual: dict | None = None
    bloques: list[dict] = []
    for linea in lineas:
        m = _ENCABEZADO_BLOQUE.match(linea)
        e = _ENCABEZADO.match(linea)
        if m:
            actual = {"nivel": len(m.group(1)), "numero": int(m.group(3)), "encabezado": m.group(2).strip(), "lineas": [linea]}
            bloques.append(actual)
        elif e and actual and len(e.group(1)) <= actual["nivel"]:
            actual = None
        elif actual:
            actual["lineas"].append(linea)
    if not bloques:
        sin_bibliografia = re.split(r"(?m)^##\s+\d+\.\s+Bibliograf", cuerpo)[0]
        cuerpo_util = "\n".join(lineas[fin:]) if fin is not None else sin_bibliografia
        bloques = [{"numero": 1, "encabezado": "Desarrollo de la sesión", "lineas": re.split(r"(?m)^##\s+\d+\.\s+Bibliograf", cuerpo_util)[0].splitlines()}]
    for b in bloques:
        titulo, minutos = indice.get(b["numero"], (b["encabezado"], 0))
        bloque = diseno_iub.BloqueSesion(b["numero"], titulo or b["encabezado"], minutos)
        partes.append(Parte(f"bloque-{b['numero']:02d}", bloque.titulo, _sin_imagenes("\n".join(b["lineas"])), bloque))
    return partes


def titulo_del_temario(cuerpo: str, respaldo: str) -> str:
    return next((l[2:].strip() for l in cuerpo.splitlines() if l.startswith("# ")), respaldo)


def plataforma_del_temario(cuerpo: str) -> str:
    m = re.search(r"(?m)^>\s*\*\*Plataforma de referencia:\*\*\s*(.+)$", cuerpo)
    return m.group(1).strip() if m else ""


def referencias_del_temario(cuerpo: str) -> list[str]:
    """Las entradas `[n] ...` de la seccion «Bibliografía» del temario, sin el marcador interno de fuente no cargada."""
    m = re.search(r"(?m)^##\s+\d+\.\s+Bibliograf[ií]a[^\n]*\n(.*?)(?=^##\s|\Z)", cuerpo, re.S)
    if not m:
        return []
    entradas = [" ".join(e.split()) for e in re.split(r"\n\s*\n", m.group(1)) if re.match(r"\s*\[\d+\]", e)]
    return [e.replace(temario.MARCADOR, "(no cargada en el wiki)").strip() for e in entradas]


def _texto_siguiente(filas: list[dict], semana: int, total: int) -> str:
    if semana >= total:
        return "Fin del semestre"
    fila = next((f for f in filas if f["semana"] == semana + 1), None)
    if fila is None:
        return f"Próxima sesión · Semana {semana + 1}"
    if fila["tipo"] == "examen":
        return f"Próxima sesión · Semana {semana + 1}: evaluación"
    return f"Próxima sesión · Semana {semana + 1}" + (f": {fila['tema']}" if fila.get("tema") else "")


# ---------------------------------------------------------------------------
# El LaTeX de cada parte (LLM) y su validacion
# ---------------------------------------------------------------------------


def normalizar_parte(salida: DiapositivasParte) -> tuple[list[diseno_iub.Diapositiva], list[str]]:
    """(diapositivas normalizadas, problemas): cada titulo y cada cuerpo pasan por latex_seguro.verificar_cuerpo."""
    diapositivas, problemas = [], []
    for k, d in enumerate(salida.diapositivas, 1):
        titulo, p_titulo = ls.verificar_cuerpo(d.titulo, titulo=True)
        cuerpo, p_cuerpo = ls.verificar_cuerpo(d.cuerpo)
        problemas += [f"diapositiva {k} («{d.titulo[:40]}»), título: {p}" for p in p_titulo]
        problemas += [f"diapositiva {k} («{d.titulo[:40]}»): {p}" for p in p_cuerpo]
        diapositivas.append(diseno_iub.Diapositiva(titulo, cuerpo))
    return diapositivas, problemas


_VISUAL = re.compile(r"\\begin\{(?:tikzpicture|axis|semilogyaxis|semilogxaxis|loglogaxis|circuitikz|tabularx|tabular|caja|cajaplana|card[BOGN]|codebox)\}")


def validar_parte(salida: DiapositivasParte, parte: Parte, blando: bool = True) -> list[str]:
    """Duro: el LaTeX de cada diapositiva cumple verificar_cuerpo. Blando (solo mientras quedan reintentos): una parte de mas de una
    diapositiva usa algun recurso visual (TikZ, pgfplots, una tabla, cajas, codigo), no solo texto."""
    _, problemas = normalizar_parte(salida)
    if blando and len(salida.diapositivas) > 1 and not any(_VISUAL.search(d.cuerpo) for d in salida.diapositivas):
        problemas.append("ninguna diapositiva usa un recurso visual: integra al menos un diagrama TikZ, una gráfica pgfplots, una tabla o tarjetas (caja/card)")
    return problemas


def _cuantas(parte: Parte) -> tuple[int, int]:
    if not parte.bloque:
        return 2, 2
    m = parte.bloque.minutos
    maximo = max(2, min(5, round(m / MINUTOS_POR_DIAPOSITIVA) + 1)) if m else 4
    return (1 if m and m < 20 else 2), maximo


def _encargo(parte: Parte, partes: list[Parte]) -> str:
    if not parte.bloque:
        return ("Diseña exactamente 2 diapositivas para abrir la sesión, con el texto de abajo (secciones 1 y 2 del temario): "
                "«Punto de partida de la sesión» (continuidad curricular, prerrequisitos y unidades de competencia, en cajas de color, en "
                "columnas) y «Resultados de aprendizaje» (el RA del módulo con sus criterios de evaluación en una caja, y los resultados "
                "de la sesión con su nivel de Bloom en un diagrama TikZ).")
    minimo, maximo = _cuantas(parte)
    bloques = [p for p in partes if p.bloque]
    lista = "; ".join(f"{p.bloque.numero}. {p.titulo}" + (f" ({p.bloque.minutos} min)" if p.bloque.minutos else "") for p in bloques)
    extra = ""
    if parte is bloques[-1]:
        extra = (" Es el cierre de la sesión: una diapositiva de síntesis (las ideas clave en cajas) y otra con el componente "
                 "actitudinal (la reflexión como cita destacada).")
    duracion = f", {parte.bloque.minutos} minutos" if parte.bloque.minutos else ""
    return (f"Diseña de {minimo} a {maximo} diapositivas para el bloque {parte.bloque.numero} «{parte.titulo}»{duracion}. "
            f"Bloques de la sesión: {lista}. El separador del bloque, la portada, la ruta, las referencias y el cierre los pone el "
            f"código: no los repitas.{extra}")


def pedir_parte(codigo: str, nombre_asignatura: str, semana: int, total: int, minutos: int, parte: Parte, partes: list[Parte]) -> list[diseno_iub.Diapositiva]:
    sistema, plantilla = vault.cargar_prompt("prompt-presentacion.md")
    usuario = plantilla.format(codigo_asignatura=codigo, nombre_asignatura=nombre_asignatura, semana=semana, total_semanas=total,
                               minutos_sesion=minutos, encargo=_encargo(parte, partes), texto=parte.texto.strip())
    salida = temario._redactar(sistema, usuario, DiapositivasParte, lambda s, blando: validar_parte(s, parte, blando),
                               f"{codigo} semana {semana}: {parte.titulo}")
    diapositivas, _ = normalizar_parte(salida)
    return diapositivas


# ---------------------------------------------------------------------------
# El plan guardado (las diapositivas de cada parte, con su huella)
# ---------------------------------------------------------------------------


def leer_plan(ruta: Path, huella: str | None = None) -> dict[str, dict]:
    """{clave: {"huella", "diapositivas"}} de las partes del plan guardado que se pueden reutilizar: el archivo es del formato actual
    y cada diapositiva vuelve a pasar la verificacion (un .plan.json es un archivo que cualquiera pudo editar). Con `huella`, solo si
    el plan es del mismo temario. Lo que no se lee o no pasa, no se reutiliza (se vuelve a pedir)."""
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict) or datos.get("formato") != FORMATO_PLAN or not isinstance(datos.get("partes"), dict):
        return {}
    if huella is not None and datos.get("temario_hash") != huella:
        return {}
    partes = {}
    for clave, parte in datos["partes"].items():
        try:
            salida = DiapositivasParte.model_validate({"diapositivas": parte["diapositivas"]})
        except (ValueError, KeyError, TypeError):
            continue
        diapositivas, problemas = normalizar_parte(salida)
        if not problemas and isinstance(parte.get("huella"), str):
            partes[clave] = {"huella": parte["huella"], "diapositivas": diapositivas}
    return partes


def guardar_plan(ruta: Path, huella: str, partes: dict[str, dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {"formato": FORMATO_PLAN, "temario_hash": huella, "modelo": vault.modelo_llm(), "fecha": vault.hoy(),
             "partes": {clave: {"huella": p["huella"], "diapositivas": [{"titulo": d.titulo, "cuerpo": d.cuerpo} for d in p["diapositivas"]]}
                        for clave, p in sorted(partes.items())}}
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def partes_pendientes(ruta_tex: Path, cuerpo: str) -> list[str]:
    """Las partes del temario que habria que pedir al modelo para rehacer su presentacion (las que no estan en el plan guardado, o
    cambiaron). Vacio = se rehace sin LLM. Lo usa lint (L14)."""
    guardadas = leer_plan(ruta_plan(ruta_tex))
    return [p.clave for p in partes_del_temario(cuerpo) if guardadas.get(p.clave, {}).get("huella") != p.huella]


# ---------------------------------------------------------------------------
# Docente y programa
# ---------------------------------------------------------------------------


def datos_por_defecto(codigo: str) -> tuple[str, str]:
    """(docente, programa) si nadie los indica: el docente_autor de la asignatura y los programas que la enlazan en el wiki."""
    _, asignatura, fm_asignatura = vault.localizar_asignatura(codigo)
    programas = [vault.destino_pagina(p) for p in vault.enlaces(fm_asignatura.get("programa"))]
    return asignatura.docente_autor or DOCENTE_POR_DEFECTO, " | ".join(programas) or PROGRAMA_POR_DEFECTO


def _usados_antes(codigo: str) -> tuple[str | None, str | None]:
    for ruta in sorted(vault.TEMARIOS.glob(f"{codigo}-semana*.md")):
        fm, _ = vault.leer_pagina(ruta)
        if fm.get("presentacion_docente") or fm.get("presentacion_programa"):
            return fm.get("presentacion_docente"), fm.get("presentacion_programa")
    return None, None


def completar_datos(codigo: str, docente: str | None, programa: str | None, interactivo: bool = False, preguntar=input) -> tuple[str, str]:
    """El docente y el programa de las presentaciones de `codigo`. Lo que no venga indicado se pregunta (`interactivo`), proponiendo lo
    usado la ultima vez o lo que dice el wiki; Enter acepta. Sin terminal interactiva se usa lo propuesto."""
    docente_wiki, programa_wiki = datos_por_defecto(codigo)
    docente_antes, programa_antes = _usados_antes(codigo)

    def pedir(mensaje: str, propuesto: str) -> str:
        if not interactivo:
            return propuesto
        try:
            return preguntar(f"{mensaje} [{propuesto}]: ").strip() or propuesto
        except EOFError:
            return propuesto

    docente = docente or pedir(f"Nombre del docente que firma las presentaciones de {codigo}", docente_antes or docente_wiki)
    programa = programa or pedir(f"Programa académico de {codigo}", programa_antes or programa_wiki)
    return docente, programa


def terminal_interactiva() -> bool:
    """True solo si hay una persona al otro lado: la entrada Y la salida son una terminal (en Windows, NUL responde isatty() = True)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


# ---------------------------------------------------------------------------
# Generacion
# ---------------------------------------------------------------------------


def semanas_con_temario(codigo: str) -> list[int]:
    ruta = vault.PLANEADOR / f"{codigo}-planeador.md"
    if not ruta.exists():
        raise FileNotFoundError(f"No hay planeador de {codigo}: corre `python src/planeador.py {codigo}` y luego `python src/temario.py {codigo} --todas`")
    fm, _ = vault.leer_pagina(ruta)
    return [s["semana"] for s in fm["semanas"] if s["tipo"] == "clase" and (vault.TEMARIOS / f"{codigo}-semana{s['semana']:02d}.md").exists()]


def generar_presentacion(codigo: str, semana: int, docente: str | None = None, programa: str | None = None, contacto: str | None = None,
                         forzar: bool = False, replanificar: bool = False) -> tuple[Path, str, int]:
    """(ruta del .tex, 'generada' | 'revisar' | 'omitida', cuantas partes se pidieron al modelo). Una presentacion al dia (mismo
    temario, docente, programa, contacto y version del diseno, y su plan completo) se omite; lo que no cambio se toma del plan."""
    nombre_pagina, asignatura, _ = vault.localizar_asignatura(codigo)
    ruta_temario = vault.TEMARIOS / f"{codigo}-semana{semana:02d}.md"
    if not ruta_temario.exists():
        raise FileNotFoundError(f"No existe el temario {ruta_temario.as_posix()}: corre `python src/temario.py {codigo} --semana {semana}`")
    fm, cuerpo = vault.leer_pagina(ruta_temario)
    huella = hash_cuerpo(cuerpo)
    destino = ruta_presentacion(codigo, semana)
    partes = partes_del_temario(cuerpo)

    docente_wiki, programa_wiki = datos_por_defecto(codigo)
    docente = docente or fm.get("presentacion_docente") or docente_wiki
    programa = programa or fm.get("presentacion_programa") or programa_wiki
    contacto = contacto if contacto is not None else (fm.get("presentacion_contacto") or "")
    guardadas = {} if replanificar else leer_plan(ruta_plan(destino))
    vigentes = {p.clave: guardadas[p.clave] for p in partes if guardadas.get(p.clave, {}).get("huella") == p.huella}
    al_dia = (fm.get("presentacion_temario_hash") == huella and fm.get("presentacion_diseno") == DISENO and fm.get("presentacion_estado")
              and (fm.get("presentacion_docente"), fm.get("presentacion_programa"), fm.get("presentacion_contacto") or "") == (docente, programa, contacto))
    if not forzar and len(vigentes) == len(partes) and destino.exists() and al_dia:
        return destino, "omitida", 0

    fm_plan, _ = vault.leer_pagina(vault.PLANEADOR / f"{codigo}-planeador.md")
    total = int(fm.get("total_semanas") or 14)
    minutos = int(fm.get("horas_sesion") or fm_plan.get("horas_sesion") or 2) * 60
    doc = diseno_iub.Documento(
        codigo=codigo, asignatura=asignatura.nombre, titulo=titulo_del_temario(cuerpo, nombre_pagina), semana=semana, total_semanas=total,
        docente=docente, programa=programa, duracion_min=minutos, corte=fm.get("corte_evaluativo"),
        tipo_sesion=asignatura.tipo_abordaje.value if asignatura.tipo_abordaje else "", subtitulo=plataforma_del_temario(cuerpo),
        siguiente=_texto_siguiente(fm_plan["semanas"], semana, total), contacto=contacto, referencias=referencias_del_temario(cuerpo))

    avisos: list[str] = []
    obtenidas = dict(vigentes)
    pedidas = 0
    for parte in partes:
        if parte.clave in obtenidas:
            continue
        pedidas += 1
        try:
            diapositivas = pedir_parte(codigo, asignatura.nombre, semana, total, minutos, parte, partes)
        except ValueError as error:                 # el modelo no cumplio tras los reintentos: esa parte queda provisional
            avisos.append(f"{parte.titulo}: {str(error)[:500]}")
            continue
        obtenidas[parte.clave] = {"huella": parte.huella, "diapositivas": diapositivas}
        guardar_plan(ruta_plan(destino), huella, obtenidas)            # lo ya pedido no se pierde si una parte posterior falla

    def de(parte: Parte) -> list[diseno_iub.Diapositiva]:
        if parte.clave in obtenidas:
            return obtenidas[parte.clave]["diapositivas"]
        return [diseno_iub.provisional(doc, parte.bloque, "")]

    apertura = [d for p in partes if p.clave == APERTURA for d in de(p)]
    bloques = [(p.bloque, de(p)) for p in partes if p.bloque]
    tex, n_diapositivas = diseno_iub.construir_tex(doc, apertura, bloques)
    problemas = ls.verificar_latex(tex)
    avisos += list(doc.conv.avisos) + [f"verificación estática: {p}" for p in problemas]

    destino.parent.mkdir(parents=True, exist_ok=True)
    if ls.graves(problemas):
        # el .tex podria leer o escribir archivos al compilarse: no se escribe (ni queda el de antes, ni el plan que lo produjo)
        destino.unlink(missing_ok=True)
        ruta_plan(destino).unlink(missing_ok=True)
        avisos.append("no se escribió el .tex: la verificación estática encontró algo que podría ejecutarse al compilar (ver arriba); "
                      "corre de nuevo con --replanificar")
    else:
        guardar_plan(ruta_plan(destino), huella, obtenidas)
        destino.write_text(tex, encoding="utf-8", newline="\n")

    estado = "revisar" if avisos else "generada"
    fm.update({
        "presentacion_estado": estado, "presentacion_archivo": destino.as_posix(), "presentacion_avisos": avisos,
        "presentacion_temario_hash": huella, "presentacion_fecha": vault.hoy(), "presentacion_diseno": DISENO,
        "presentacion_diapositivas": n_diapositivas, "presentacion_docente": docente, "presentacion_programa": programa,
        "presentacion_contacto": contacto,
    })
    vault.escribir_pagina(ruta_temario, fm, cuerpo)
    return destino, estado, pedidas


def generar_presentaciones(codigo: str, docente: str | None = None, programa: str | None = None, contacto: str | None = None,
                           forzar: bool = False, replanificar: bool = False, semanas: list[int] | None = None) -> list[tuple[Path, str, int]]:
    """Las presentaciones de las semanas de clase que ya tienen temario (o solo de `semanas`)."""
    disponibles = semanas_con_temario(codigo)
    if semanas:
        sin_temario = sorted(set(semanas) - set(disponibles))
        if sin_temario:
            raise FileNotFoundError(f"{codigo}: no hay temario de las semanas {', '.join(map(str, sin_temario))} (o no son de clase)")
        disponibles = [s for s in disponibles if s in semanas]
    if not disponibles:
        raise FileNotFoundError(f"{codigo}: no hay ningún temario todavía: `python src/temario.py {codigo} --todas`")
    resultados = [generar_presentacion(codigo, s, docente, programa, contacto, forzar, replanificar) for s in disponibles]
    escritas = [(r, e, n) for r, e, n in resultados if e != "omitida"]
    if escritas:                                            # una corrida que no escribio nada no ensucia el log
        vault.anotar_log(f"/presentaciones {codigo}", [
            f"{len(escritas)} presentaciones escritas en {vault.PRESENTACIONES.as_posix()}/{codigo}/, {len(resultados) - len(escritas)} ya estaban al día",
            f"{sum(n for _, _, n in escritas)} partes (apertura o bloques) pedidas al modelo; el resto se tomó del plan guardado (sin LLM)",
            *[f"{r.name}: revisar los avisos (presentacion_avisos del temario)" for r, e, _ in escritas if e == "revisar"]])
    return resultados


def compilar(ruta_tex: Path) -> Path:
    """Compila con pdflatex (dos pasadas: las posiciones de la portada y el total de diapositivas) y devuelve el PDF. Antes vuelve a
    verificar el .tex: si podria leer o escribir archivos (ls.graves), no lo compila (ValueError). Nunca con shell-escape, y con
    openin_any=p y openout_any=p (modo «paranoico» de TeX Live): no puede leer ni escribir fuera del directorio de la presentacion
    (ni archivos ocultos). Lo recomendado sigue siendo compilar en Overleaf, que ya compila aislado."""
    problemas = ls.graves(ls.verificar_latex(ruta_tex.read_text(encoding="utf-8")))
    if problemas:
        raise ValueError(f"no se compila {ruta_tex.name}: " + "; ".join(problemas))
    ejecutable = shutil.which("pdflatex")
    if not ejecutable:
        raise FileNotFoundError("pdflatex no está instalado: instala MiKTeX o TeX Live, o sube la carpeta a Overleaf (compilador pdfLaTeX)")
    entorno = dict(os.environ, openin_any="p", openout_any="p")
    for _ in range(2):
        r = subprocess.run([ejecutable, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", ruta_tex.name], cwd=ruta_tex.parent,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno)
        if r.returncode != 0:
            raise RuntimeError(f"pdflatex falló con {ruta_tex.name}:\n" + "\n".join((r.stdout or "").splitlines()[-25:]))
    for extension in EXTENSIONES_AUXILIARES:
        ruta_tex.with_suffix(extension).unlink(missing_ok=True)
    return ruta_tex.with_suffix(".pdf")


def codigos_con_planeador() -> list[str]:
    return sorted(p.name.removesuffix("-planeador.md") for p in vault.PLANEADOR.glob("*-planeador.md"))


def main() -> int:
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Genera la presentación Beamer (diseño institucional IUB) de cada temario.")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("codigo", nargs="?", help="código de la asignatura")
    grupo.add_argument("--all", action="store_true", help="todas las asignaturas que tienen planeador")
    parser.add_argument("--semana", type=int, nargs="+", help="solo esas semanas")
    parser.add_argument("--forzar", action="store_true", help="rehace el .tex aunque esté al día (desde el plan guardado: sin LLM si el temario no cambió)")
    parser.add_argument("--replanificar", action="store_true", help="vuelve a pedir al modelo todas las partes (una llamada por parte: la apertura y cada bloque)")
    parser.add_argument("--docente", help="nombre del docente en la portada y el pie; si no se indica, el script lo pregunta")
    parser.add_argument("--programa", help="programa académico en la portada; si no se indica, el script lo pregunta")
    parser.add_argument("--contacto", help="contacto de la portada y del cierre (opcional)")
    parser.add_argument("--sin-preguntar", action="store_true", help="no pregunta nada: usa lo indicado, lo último usado o lo del wiki")
    parser.add_argument("--compilar", action="store_true", help="además del .tex, compila el PDF (requiere pdflatex)")
    args = parser.parse_args()
    if args.all and args.semana:
        parser.error("--semana va con un código de asignatura, no con --all")

    interactivo = terminal_interactiva() and not args.sin_preguntar
    errores: list[str] = []
    for codigo in codigos_con_planeador() if args.all else [args.codigo]:
        try:
            semanas_con_temario(codigo)                          # antes de preguntar: si no se puede generar, no se pregunta nada
            docente, programa = completar_datos(codigo, args.docente, args.programa, interactivo)
            print(f"{codigo}: docente «{docente}», programa «{programa}»" + (
                "" if interactivo or (args.docente and args.programa) else
                "  (los usados la última vez o los del wiki: indícalos con --docente y --programa, o corre el script en una terminal para que los pregunte)"))
            resultados = generar_presentaciones(codigo, docente, programa, args.contacto, args.forzar, args.replanificar, args.semana)
            escritas = [(r, e, n) for r, e, n in resultados if e != "omitida"]
            print(f"{codigo}: {len(escritas)} presentaciones escritas ({sum(n for *_, n in escritas)} partes pedidas al modelo), "
                  f"{len(resultados) - len(escritas)} ya al día")
            for ruta, estado, _ in escritas:
                print(f"  {ruta.as_posix()}" + ("   (revisar: avisos en el temario)" if estado == "revisar" else ""))
            if args.compilar:
                for ruta, _, _ in escritas:
                    if not ruta.exists():                # no se escribio: la verificacion encontro algo que podria ejecutarse
                        print(f"  sin PDF: {ruta.name} no se escribió (ver presentacion_avisos del temario)")
                        continue
                    try:
                        print(f"  PDF: {compilar(ruta).as_posix()}")
                    except ValueError as error:
                        print(f"  sin PDF: {error}")
        except (FileNotFoundError, ValueError, RuntimeError, KeyError) as error:
            errores.append(f"{codigo}: {error}")
    for error in errores:
        print(f"ERROR: {error}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
