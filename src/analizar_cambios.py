"""ANALIZAR-CAMBIOS -- que hay que actualizar cuando llega un curriculo nuevo, una version nueva de un documento o bibliografia
nueva, gastando lo minimo (sin LLM y sin escribir nada en wiki/ ni en generacion/).

Un curriculo de un modulo son ~10 000 tokens y una sesion de TEMARIO ~10 llamadas: releer y regenerar todo cuando solo cambio una
seccion es el gasto que este script evita. Trabaja en dos planos:

  1. raw/ contra la LINEA BASE (memory_store/estado-cambios.json, la de la ultima vez que se corrio con --confirmar): documentos
     nuevos, modificados o eliminados.
       - de un CURRICULO modificado dice que SECCIONES cambiaron y a que paginas del wiki corresponde cada una (creditos -> asignatura;
         resultados de aprendizaje -> RA; ...), para que INGEST-CURRICULAR lea solo esas secciones y no el documento entero;
       - de un MANUAL DE BANCO, que EXPERIMENTOS cambiaron (`ingest_manual.py --solo` procesa solo esos);
       - de un LIBRO o una NORMA nueva o modificada, a que RA les serviria: cuantos de los conceptos de sus contenidos aparecen en el
         texto (busqueda por palabras, sin embeddings), y cuales de sus temarios se escribieron sin apoyo en las fuentes.
  2. wiki/ contra generacion/ (sin linea base: se recalcula lo determinista, asi que sirve tambien despues de editar el wiki a mano):
     el cronograma de 14 semanas y la duracion de la sesion contra el planeador, la duracion, las horas de trabajo independiente, el
     RA y su alineacion contra cada temario, y el gate de cada RA contra su correlacion. De ahi sale el plan MINIMO: que RA volver a
     correlacionar, que semanas rehacer, y cuanto cuesta comparado con regenerarlo todo.

Solo LEE. El flujo es: correr el script -> actualizar las paginas del wiki que dice -> volver a correrlo (ya mostrara lo que quedo
desfasado en la generacion) -> ejecutar los comandos del plan -> `--confirmar` para fijar la linea base.

Uso (desde la raiz del vault):
    python src/analizar_cambios.py                       # cambios en raw/ y desfases del wiki con la generacion
    python src/analizar_cambios.py --asignatura ABC01    # los desfases de una sola asignatura
    python src/analizar_cambios.py --detalle             # ademas, el texto de las secciones que cambiaron (lo unico que hay que leer)
    python src/analizar_cambios.py --json                # el mismo informe, para otra herramienta
    python src/analizar_cambios.py --confirmar           # fija la linea base: todo lo de raw/ ya esta incorporado
    python src/analizar_cambios.py --confirmar raw/curriculos/P/X.md   # solo ese documento (o carpeta)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

import correlate
import ingest_manual
import pasajes
import temario
import vault
from schema_extraccion import TipoAbordaje
from schema_planeador import construir_cronograma, horas_hti_semana

RAW = Path("raw")
ESTADO = Path("memory_store") / "estado-cambios.json"       # de la instancia: no viaja en las copias de la plantilla
VERSION_ESTADO = 1
IGNORADAS = ("assets",)                 # raw/assets/: imagenes; no se analizan
NIVEL_DE_LIBROS = 2                     # de un libro solo se siguen los capitulos (h1-h2): mas fino inflaria la linea base sin ayudar
NIVEL_MAXIMO = 7                        # un rotulo suelto o en negrita cuenta como nivel 7: cuelga de cualquier encabezado

LLAMADAS_TEMARIO = 10                   # plan + unidades + cierre (de 8 a 12, mas reintentos)
LLAMADAS_JUEZ = 3                       # CORRELATE: un juicio por cada practica candidata (k=3)
LLAMADAS_PRESENTACION = 9               # PRESENTACIONES: una por parte de un temario nuevo o cambiado (la apertura y cada bloque: de 6 a 12, mas reintentos); sin cambios, 0
FRACCION_CONCEPTO = 0.7                 # un concepto "aparece" si un pasaje trae esa fraccion de sus palabras
MIN_FRACCION_RA = 0.25                  # un RA le sirve a una fuente si esta cubre al menos esa fraccion de sus conceptos...
MIN_CONCEPTOS_RA = 2                    # ...y al menos estos (o todos, si el RA tiene menos)
MAX_LISTA = 12                          # lo que se imprime de una lista larga antes de "... y N mas"
MAX_DETALLE = 12_000                    # caracteres de texto de secciones que imprime --detalle

_TOKENS_POR_CARACTER = 0.25             # ~4 caracteres por token: una estimacion, no una medida


# ---------------------------------------------------------------------------
# A qué corresponde cada sección de un currículo
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Destino:
    clave: str
    patron: re.Pattern
    actualizar: str         # que paginas o campos del wiki toca
    efecto: str             # que arrastra aguas abajo


def _d(clave: str, patron: str, actualizar: str, efecto: str) -> Destino:
    return Destino(clave, re.compile(patron), actualizar, efecto)


# Los rotulos que INGEST-CURRICULAR nombra (CLAUDE.md), sin tildes; el primero que coincide gana, asi que el orden importa.
DESTINOS = (
    _d("marco", r"ensenanza sugerida|didacticas para el aprendizaje|\banexo",
       "wiki/marco-pedagogico.md (si el Anexo difiere del ya transcrito, avisar: no se sobrescribe)", "nada aguas abajo"),
    _d("ra_programa", r"resultados? de aprendizaje del programa",
       "página del programa: `resultados_programa` (RA-PROG-n)", "nada aguas abajo"),
    _d("creditos", r"credito|acompanamiento|trabajo independiente|intensidad horaria",
       "página de la asignatura: `had_totales`, `hp_totales`, `hti_totales`, `creditos` (`tipo_abordaje` se deriva de `hp_totales`)",
       "cambia `horas_sesion` del planeador, las horas de trabajo independiente de los temarios y el gate de CORRELATE (LINT L13 revisa que cuadre)"),
    _d("ra", r"resultados? de aprendizaje|criterios? de evaluacion|contenidos? (conceptual|procedimental|actitudinal)|\bconceptual\b|\bprocedimental\b|\bactitudinal\b",
       "páginas de RA (`{codigo}-RA{n}`): enunciado, criterios (con su categoría), contenidos y horas; `resultados_aprendizaje` de la asignatura",
       "las horas de cada RA reparten las semanas del planeador; su texto entra en el temario (sección 2) y en CORRELATE"),
    _d("competencias", r"competencia",
       "wiki/competencias/: Unidades y Elementos de Competencia; `competencias` de la asignatura",
       "la alineación (sección 2) de los temarios de la asignatura"),
    _d("estrategias", r"estrategias? pedagogicas|practica de laboratorio",
       "página de la asignatura: `estrategia_practica_marcada`", "cambia el score de sus RA: repetir CORRELATE"),
    _d("recursos", r"recursos? (didacticos|locativos)|equipo de laboratorio",
       "página de la asignatura: `recurso_laboratorio_marcado`", "cambia el score de sus RA: repetir CORRELATE"),
    _d("bibliografia", r"bibliografia|normas? tecnicas|referencias",
       "wiki/fuentes/ (INGEST de lo que no tenga página) y `bibliografia` de los RA", "los temarios de esos RA se apoyan en esas fuentes; CORRELATE-BIBLIOGRAFIA"),
    _d("webgrafia", r"webgrafia|bases? de datos|recursos? web",
       "wiki/recursos-web/ y `recursos_web` de la asignatura", "nada aguas abajo"),
    _d("aprobacion", r"aprobacion|docente autor|elaborad",
       "página de la asignatura: `docente_autor`, `fecha_aprobacion`", "el docente que propone PRESENTACIONES (se rehacen desde el plan guardado, sin LLM)"),
    _d("previos", r"aprendizajes? previos|prerrequisito|requisitos",
       "página de la asignatura: `aprendizajes_previos`", "los prerrequisitos de los temarios nuevos; los ya escritos siguen vigentes"),
    _d("identificacion", r"identificacion|datos generales|informacion general|nombre del modulo|codigo del modulo",
       "página de la asignatura: nombre, `codigo`, `tipo_modulo`, programa", "un cambio de código obliga a renombrar la página y sus enlaces (`[[...]]`)"),
)


def destino_de(titulo: str) -> Destino | None:
    plano = pasajes._sin_tildes(titulo)
    return next((d for d in DESTINOS if d.patron.search(plano)), None)


def _destino_de_ruta(titulos: list[str]) -> Destino | None:
    """El destino de una seccion: el de su titulo o, si no lo tiene, el del encabezado que la contiene (bajo «Resultados de
    Aprendizaje» cuelgan RA1, «Criterios de evaluación», etc.)."""
    return next((d for t in reversed(titulos) if (d := destino_de(t))), None)


# ---------------------------------------------------------------------------
# Secciones de un documento
# ---------------------------------------------------------------------------


@dataclass
class SeccionDoc:
    clave: str              # ruta de encabezados: «Resultados de Aprendizaje › RA1»
    titulo: str
    texto: str
    destino: str | None     # clave del Destino


_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_NEGRITA = re.compile(r"^\*\*([^*|]{3,90})\*\*:?$")


def _normalizar(texto: str) -> str:
    """Sin \\r ni espacios finales: un documento que pasa por Windows, Drive o un editor no cambia de huella por eso."""
    return "\n".join(l.rstrip() for l in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def _sha(texto: str) -> str:
    return hashlib.sha256(_normalizar(texto).encode("utf-8")).hexdigest()[:16]


def _es_titulo(linea: str, nivel_maximo: int) -> tuple[int, str] | None:
    """(nivel, titulo) si la linea abre una seccion: un encabezado Markdown, una linea entera en negrita o el rotulo suelto de un
    destino conocido (un PDF convertido pierde los `#`)."""
    t = linea.strip()
    if not t:
        return None
    m = _ENCABEZADO.match(t)
    if m:
        nivel = len(m.group(1))
        return (nivel, re.sub(r"[*_`]", "", m.group(2)).strip()) if nivel <= nivel_maximo else None
    if nivel_maximo < NIVEL_MAXIMO:
        return None
    m = _NEGRITA.match(t)
    if m:
        return NIVEL_MAXIMO, m.group(1).strip()
    es_rotulo = (len(t) <= 100 and len(t.split()) <= 9 and not t.startswith(("|", "-", "*", ">", "+")) and "|" not in t
                 and not t.endswith(".") and not re.search(r":\s*\S", t))          # «Nombre del módulo: X» es un dato, no un rótulo
    if es_rotulo and destino_de(t):
        return NIVEL_MAXIMO, t.rstrip(":").strip()
    return None


def dividir_secciones(texto: str, nivel_maximo: int = NIVEL_MAXIMO) -> list[SeccionDoc]:
    """Las secciones de un documento, de un titulo al siguiente (de cualquier nivel: una seccion no incluye a sus subsecciones,
    asi un cambio en una subseccion no marca como cambiado todo su capitulo). La clave es la ruta de encabezados; si se repite, se
    numera. Lo que hay antes del primer titulo es «(inicio)»."""
    lineas = _normalizar(texto.lstrip("﻿")).split("\n")
    secciones: list[SeccionDoc] = []
    pila: list[tuple[int, str, bool]] = []          # (nivel, titulo, es un rotulo suelto o en negrita)
    vistas: dict[str, int] = {}
    clave, titulo, cuerpo = "(inicio)", "(inicio)", []

    def cerrar() -> None:
        contenido = "\n".join(cuerpo).strip()
        if not contenido and clave == "(inicio)":
            return
        vistas[clave] = vistas.get(clave, 0) + 1
        unica = clave if vistas[clave] == 1 else f"{clave} ({vistas[clave]})"
        destino = _destino_de_ruta([n for _, n, _ in pila]) if pila else None
        secciones.append(SeccionDoc(unica, titulo, contenido, destino.clave if destino else None))

    en_codigo = False
    for linea in lineas:
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
        abre = None if en_codigo else _es_titulo(linea, nivel_maximo)
        if abre:
            cerrar()
            nivel, nombre = abre
            rotulo = nivel == NIVEL_MAXIMO
            if rotulo:              # un rotulo cuelga del ultimo encabezado Markdown; dos rotulos seguidos son hermanos
                nivel = 1 + max((n for n, _, r in pila if not r), default=0)
            while pila and pila[-1][0] >= nivel:
                pila.pop()
            pila.append((nivel, nombre, rotulo))
            clave, titulo, cuerpo = " › ".join(n for _, n, _ in pila), nombre, [linea]
        else:
            cuerpo.append(linea)
    cerrar()
    return secciones


# ---------------------------------------------------------------------------
# La linea base: raw/ tal como estaba la ultima vez que se dio por incorporado
# ---------------------------------------------------------------------------


def _categoria(ruta: str) -> str:
    partes = Path(ruta).parts                # ('raw', 'curriculos', ..., 'x.md')
    carpeta = partes[1] if len(partes) > 2 else ""
    return {"curriculos": "curriculo", "manuales-laboratorio": "manual", "bibliografia": "bibliografia",
            "normas-tecnicas": "norma"}.get(carpeta, "otra")


def _nivel_de(categoria: str) -> int:
    return NIVEL_MAXIMO if categoria in ("curriculo", "manual") else NIVEL_DE_LIBROS


def _archivos_raw() -> list[Path]:
    if not RAW.is_dir():
        return []
    return [p for p in sorted(RAW.rglob("*"))
            if p.is_file() and not p.name.startswith(".") and p.relative_to(RAW).parts[0] not in IGNORADAS]


def huella_de(ruta: Path, categoria: str) -> dict:
    """Huella de un original: la del archivo, la de cada seccion (si es texto) y, en un manual de banco, la de cada experimento."""
    datos = ruta.read_bytes()
    if ruta.suffix.lower() not in pasajes.EXTENSIONES_TEXTO:
        return {"sha": hashlib.sha256(datos).hexdigest()[:16], "bytes": len(datos)}
    texto = datos.decode("utf-8", errors="replace").lstrip("﻿")
    huella: dict = {"sha": _sha(texto), "bytes": len(datos),
                    "secciones": {s.clave: _sha(s.texto) for s in dividir_secciones(texto, _nivel_de(categoria))}}
    if categoria == "manual":
        huella["experimentos"] = {s.numero: _sha(s.texto) for s in ingest_manual.dividir_experimentos(texto)}
    return huella


def instantanea() -> dict[str, dict]:
    return {p.as_posix(): huella_de(p, _categoria(p.as_posix())) for p in _archivos_raw()}


def leer_base() -> dict | None:
    """La linea base, o None si no existe (o esta ilegible: se trata igual, como una primera corrida)."""
    try:
        base = json.loads(ESTADO.read_text(encoding="utf-8"))
        return base if isinstance(base.get("archivos"), dict) else None
    except (OSError, ValueError):
        return None


def escribir_base(archivos: dict[str, dict]) -> Path:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    contenido = {"version": VERSION_ESTADO, "fecha": vault.hoy(), "archivos": archivos}
    ESTADO.write_text(json.dumps(contenido, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    return ESTADO


def confirmar(rutas: list[str] | None = None) -> tuple[int, Path]:
    """Da por incorporado lo de raw/ (todo, o solo `rutas`: archivos o carpetas). Devuelve (archivos fijados, archivo de la base)."""
    actual = instantanea()
    if not rutas:
        return len(actual), escribir_base(actual)
    base = (leer_base() or {"archivos": {}})["archivos"]
    fijados = 0
    for pedida in rutas:
        norma = pedida.replace("\\", "/").strip("/")
        alcanzados = [r for r in {*actual, *base} if r == norma or r.startswith(norma + "/")]
        if not alcanzados:
            raise FileNotFoundError(f"{pedida}: no es un archivo ni una carpeta de raw/ (ni estaba en la línea base)")
        for r in alcanzados:
            if r in actual:
                base[r] = actual[r]
                fijados += 1
            else:
                base.pop(r, None)           # ya no existe en raw/: sale de la base
    return fijados, escribir_base(base)


# ---------------------------------------------------------------------------
# Que cambio en raw/
# ---------------------------------------------------------------------------


@dataclass
class Cambio:
    ruta: str
    categoria: str          # curriculo | manual | bibliografia | norma | otra
    estado: str             # nuevo | modificado | eliminado | sin_base (documento que ya tiene pagina, sin linea base con que compararlo)
    secciones_nuevas: list[str] = field(default_factory=list)
    secciones_modificadas: list[str] = field(default_factory=list)
    secciones_eliminadas: list[str] = field(default_factory=list)
    experimentos_nuevos: list[str] = field(default_factory=list)
    experimentos_modificados: list[str] = field(default_factory=list)
    experimentos_eliminados: list[str] = field(default_factory=list)
    paginas: list[str] = field(default_factory=list)                # paginas del wiki que citan este original
    texto: bool = True                                             # False: un PDF u otro binario, que no se lee
    tokens_totales: int = 0                                        # del documento entero
    tokens_a_leer: int = 0                                         # de lo que cambio (lo unico que hay que leer)
    destinos: list[dict] = field(default_factory=list)             # [{destino, secciones, actualizar, efecto}]
    cobertura: list[dict] = field(default_factory=list)            # RA a los que les sirve (fuentes de texto)
    faltantes_que_cubre: list[str] = field(default_factory=list)   # temarios con una referencia sin cargar que parece esta fuente
    ras_a_correlacionar: dict[str, str] = field(default_factory=dict)      # manuales: RA -> por que
    fuente: str | None = None                                      # nombre de la pagina de wiki/fuentes/ (manuales)


def comparar(base: dict[str, dict], actual: dict[str, dict]) -> list[Cambio]:
    """Que archivos son nuevos, cuales cambiaron (y en que secciones o experimentos) y cuales desaparecieron."""
    cambios: list[Cambio] = []
    for ruta in sorted(set(base) | set(actual)):
        antes, ahora = base.get(ruta), actual.get(ruta)
        categoria = _categoria(ruta)
        if ahora is None:
            cambios.append(Cambio(ruta, categoria, "eliminado"))
            continue
        if antes is not None and antes["sha"] == ahora["sha"]:
            continue
        cambio = Cambio(ruta, categoria, "nuevo" if antes is None else "modificado", texto="secciones" in ahora)
        for clave_huella, nuevas, modificadas, eliminadas in (
                ("secciones", cambio.secciones_nuevas, cambio.secciones_modificadas, cambio.secciones_eliminadas),
                ("experimentos", cambio.experimentos_nuevos, cambio.experimentos_modificados, cambio.experimentos_eliminados)):
            a, b = ahora.get(clave_huella, {}), (antes or {}).get(clave_huella, {})
            nuevas += [k for k in a if k not in b]
            eliminadas += [k for k in b if k not in a]
            modificadas += [k for k in a if k in b and a[k] != b[k]]
        cambios.append(cambio)
    return cambios


def _mapa_de_citas() -> dict[str, list[str]]:
    """{original citado: paginas del wiki que lo citan}, de la linea `**Origen:**` de fuentes, asignaturas y programas."""
    mapa: dict[str, list[str]] = {}
    for carpeta in (vault.FUENTES, vault.ASIGNATURAS, vault.WIKI / "programas"):
        for ruta in sorted(carpeta.glob("*.md")):
            try:
                _, cuerpo = vault.leer_pagina(ruta)
            except Exception:
                continue
            for original in pasajes._originales(cuerpo):
                mapa.setdefault(original.strip("/"), []).append(ruta.as_posix())
    return mapa


def _citantes(ruta: str, mapa: dict[str, list[str]]) -> list[str]:
    paginas: list[str] = []
    for origen, citadas in mapa.items():
        if ruta == origen or ruta.startswith(origen + "/"):
            paginas += [p for p in citadas if p not in paginas]
    return paginas


def _tokens_de(caracteres: int) -> int:
    return int(caracteres * _TOKENS_POR_CARACTER)


# --- currículos -------------------------------------------------------------


def _detallar_curriculo(cambio: Cambio, textos: dict[str, SeccionDoc]) -> None:
    """A que pagina del wiki corresponde cada seccion que cambio, y cuanto hay que leer de verdad."""
    cambio.tokens_totales = _tokens_de(sum(len(s.texto) for s in textos.values()))
    tocadas = [*cambio.secciones_nuevas, *cambio.secciones_modificadas]
    cambio.tokens_a_leer = _tokens_de(sum(len(textos[k].texto) for k in tocadas if k in textos))
    por_destino: dict[str | None, list[str]] = {}
    for clave in [*tocadas, *cambio.secciones_eliminadas]:
        seccion = textos.get(clave)
        if seccion:
            destino = seccion.destino
        else:                                # una seccion que ya no esta: su destino sale de la ruta de su clave
            encontrado = _destino_de_ruta(re.sub(r" \(\d+\)$", "", clave).split(" › "))
            destino = encontrado.clave if encontrado else None
        por_destino.setdefault(destino, []).append(clave)
    tabla = {d.clave: d for d in DESTINOS}
    for clave_destino, claves in por_destino.items():
        d = tabla.get(clave_destino)
        cambio.destinos.append({
            "destino": clave_destino or "sin_reconocer", "secciones": claves,
            "actualizar": d.actualizar if d else "sección que no reconozco: léela y decide qué página toca",
            "efecto": d.efecto if d else "no se sabe",
        })


# --- manuales de banco ------------------------------------------------------


def _ras_del_vault() -> list[tuple[object, dict, str]]:
    """(RA, frontmatter, pagina de su asignatura) de cada RA legible del wiki."""
    ras = []
    for ruta in vault.listar_ras():
        try:
            ras.append(vault.cargar_ra(ruta))
        except Exception:
            continue
    return ras


def _asignaturas() -> dict[str, tuple]:
    """{pagina: (Asignatura, frontmatter)} de las asignaturas legibles."""
    salida = {}
    for ruta in sorted(vault.ASIGNATURAS.glob("*.md")):
        try:
            asignatura, fm = vault.cargar_asignatura(ruta.stem)
        except Exception:
            continue
        salida[ruta.stem] = (asignatura, fm)
    return salida


def _ras_para_manual(cambio: Cambio, ras, asignaturas: dict[str, tuple]) -> dict[str, str]:
    """RA que conviene volver a correlacionar cuando cambia un manual: los de gate abierto que aun no tienen practica aceptada y los
    que apuntan a un experimento que cambio o desaparecio. Con el resto no hay nada que ganar: ya tienen su practica (la palabra
    del docente, `correlacion_revisado_por_docente`, tampoco se toca). No se filtra por palabras: el RA esta en espanol y el
    manual suele estar en ingles, asi que un cruce lexico descartaria justo los que si coinciden."""
    tocados = {*cambio.experimentos_nuevos, *cambio.experimentos_modificados, *cambio.experimentos_eliminados}
    motivos: dict[str, str] = {}
    for ra, fm_ra, pagina_asignatura in ras:
        if fm_ra.get("correlacion_revisado_por_docente") or pagina_asignatura not in asignaturas:
            continue
        asignatura = asignaturas[pagina_asignatura][0]
        apunta = vault.enlace(fm_ra.get("requiere_practica")) == cambio.fuente
        codigos = {str(c).removeprefix("Exp") for c in fm_ra.get("practica_experimentos") or []}
        if apunta and any(c in tocados or f"Exp{c}" in tocados for c in codigos):
            motivos[ra.codigo] = f"su práctica {', '.join(sorted(codigos))} de {cambio.fuente} cambió en el manual"
            continue
        abierto = asignatura.tipo_abordaje != TipoAbordaje.teorica and correlate.calcular_score_ra(ra, asignatura) >= correlate.UMBRAL_GATE
        if abierto and fm_ra.get("correlacion_estado") != "aceptado":
            motivos[ra.codigo] = "su gate está abierto y no tiene práctica aceptada"
    return motivos


# --- libros y normas --------------------------------------------------------


def _indice_invertido(textos: list[str]) -> dict[str, list[int]]:
    """palabra -> pasajes (de todos los textos) donde aparece."""
    postings: dict[str, list[int]] = {}
    n = 0
    for texto in textos:
        for _ubicacion, trozo in pasajes.trocear(texto, "x"):
            for t in set(pasajes._tokens(trozo)):
                postings.setdefault(t, []).append(n)
            n += 1
    return postings


def _concepto_aparece(concepto: str, postings: dict[str, list[int]]) -> bool:
    palabras = set(pasajes._tokens(concepto))
    if not palabras:
        return False
    necesarias = max(1, math.ceil(FRACCION_CONCEPTO * len(palabras)))
    cuenta: Counter = Counter()
    for p in palabras:
        cuenta.update(postings.get(p, ()))
    return any(c >= necesarias for c in cuenta.values())


def cobertura_de_ras(textos: list[str], ras, ya_citan: set[str]) -> list[dict]:
    """A que RA les sirve un texto: cuantos conceptos de su `contenido_conceptual` aparecen (por palabras, en el mismo pasaje).
    Solo los RA con una cobertura que valga la pena: no es una decision de bibliografia, es la lista de a cuales mirar."""
    postings = _indice_invertido(textos)
    if not postings:
        return []
    salida = []
    for ra, fm_ra, _pagina in ras:
        conceptos = [c for c in ra.contenido.conceptual if c.strip()] or [ra.enunciado]
        aparecen = [c for c in conceptos if _concepto_aparece(c, postings)]
        if not aparecen or len(aparecen) / len(conceptos) < MIN_FRACCION_RA or (len(aparecen) < MIN_CONCEPTOS_RA and len(conceptos) > MIN_CONCEPTOS_RA):
            continue
        salida.append({"ra": ra.codigo, "cubiertos": len(aparecen), "total": len(conceptos), "conceptos": aparecen,
                       "ya_la_cita": bool(ya_citan & set(vault.enlaces(fm_ra.get("bibliografia"))))})
    return sorted(salida, key=lambda c: (-c["cubiertos"] / c["total"], c["ra"]))


def _faltantes_que_cubre(cambio: Cambio, texto: str) -> list[str]:
    """Temarios con una referencia `[FUENTE NO CARGADA EN raw/]` que se parece a esta fuente (su titulo o nombre de archivo)."""
    ident = set(pasajes._tokens(f"{Path(cambio.ruta).stem} {' '.join(texto.split()[:60])}"))
    if len(ident) < 2:
        return []
    salida = []
    for ruta in sorted(vault.TEMARIOS.glob("*.md")):
        try:
            fm, _ = vault.leer_pagina(ruta)
        except Exception:
            continue
        for faltante in fm.get("bibliografia_faltantes") or []:
            palabras = set(pasajes._tokens(str(faltante).replace(temario.MARCADOR, "")))
            if palabras and len(palabras & ident) >= max(2, math.ceil(0.5 * min(len(palabras), len(ident)))):
                salida.append(f"{ruta.stem}: {str(faltante)[:90]}")
                break
    return salida


# ---------------------------------------------------------------------------
# El informe de raw/
# ---------------------------------------------------------------------------


def analizar_raw(base: dict | None) -> list[Cambio]:
    actual = instantanea()
    mapa = _mapa_de_citas()
    cambios = comparar(base["archivos"] if base else {}, actual)
    ras = _ras_del_vault() if any(c.estado != "eliminado" and c.categoria != "curriculo" for c in cambios) else []
    asignaturas = _asignaturas() if any(c.categoria == "manual" for c in cambios) else {}

    for cambio in cambios:
        cambio.paginas = _citantes(cambio.ruta, mapa)
        if base is None and cambio.paginas:
            cambio.estado = "sin_base"
        if cambio.estado == "eliminado" or not cambio.texto:
            continue
        ruta = Path(cambio.ruta)
        texto = ruta.read_text(encoding="utf-8", errors="replace").lstrip("﻿")
        secciones = {s.clave: s for s in dividir_secciones(texto, _nivel_de(cambio.categoria))}
        cambio.tokens_totales = _tokens_de(len(texto))
        if cambio.categoria == "curriculo":
            _detallar_curriculo(cambio, secciones)
        elif cambio.categoria == "manual":
            propias = [p for p in cambio.paginas if p.startswith(vault.FUENTES.as_posix() + "/")]
            cambio.fuente = Path(propias[0]).stem if propias else ingest_manual._slug(ruta.stem)
            cambio.ras_a_correlacionar = _ras_para_manual(cambio, ras, asignaturas)
            tocadas = [*cambio.secciones_nuevas, *cambio.secciones_modificadas] if cambio.estado == "modificado" else list(secciones)
            cambio.tokens_a_leer = _tokens_de(sum(len(secciones[k].texto) for k in tocadas if k in secciones))
        elif cambio.estado != "sin_base":
            # un libro o una norma: solo lo que cambio (o todo, si es nuevo) es lo que puede servirle a un RA
            tocadas = [*cambio.secciones_nuevas, *cambio.secciones_modificadas] if cambio.estado == "modificado" else list(secciones)
            relevantes = [secciones[k].texto for k in tocadas if k in secciones] or [texto]
            cambio.tokens_a_leer = _tokens_de(sum(len(t) for t in relevantes))
            citan = {Path(p).stem for p in cambio.paginas}
            cambio.cobertura = cobertura_de_ras(relevantes, ras, citan)
            cambio.faltantes_que_cubre = _faltantes_que_cubre(cambio, texto) if cambio.estado == "nuevo" else []
    return cambios


# ---------------------------------------------------------------------------
# Wiki contra generacion: lo desactualizado
# ---------------------------------------------------------------------------


@dataclass
class PlanAsignatura:
    codigo: str
    pagina: str
    avisos: list[str] = field(default_factory=list)
    sin_planeador: bool = False
    duracion: str | None = None                                        # «planeador 2 h, ahora 4 h»
    semanas_distintas: list[str] = field(default_factory=list)         # «S4: TPR01-RA2 -> TPR01-RA3»
    correlacionar: dict[str, str] = field(default_factory=dict)        # RA -> por que
    temarios: dict[int, list[str]] = field(default_factory=dict)       # semana -> por que hay que rehacerlo (seguro)
    leves: dict[int, list[str]] = field(default_factory=dict)          # semana -> desfase solo de cabecera o alineacion: el resto sigue vigente
    a_considerar: dict[int, list[str]] = field(default_factory=dict)   # semana -> por que podria ganar con una fuente nueva (opcional)
    sin_temario: list[int] = field(default_factory=list)
    clases: int = 0
    ras: list[str] = field(default_factory=list)                       # codigos de sus RA
    ras_gate: list[str] = field(default_factory=list)                  # los de gate abierto (los que gastan llamadas en CORRELATE)


def _iso(valor) -> str | None:
    """'2026-09-26' -> tal cual; una plantilla ('YYYY-MM-DD') o un vacio -> None: no se compara."""
    texto = str(valor or "")
    return texto if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto) else None


def _desfase_de_correlacion(ra, fm_ra: dict, asignatura, practicas: set[str], fuente_reciente: str | None) -> str | None:
    """Por que la correlacion guardada de un RA ya no vale, o None si sigue vigente. Respeta la decision del docente."""
    if fm_ra.get("correlacion_revisado_por_docente"):
        return None
    score = correlate.calcular_score_ra(ra, asignatura)
    abierto = asignatura.tipo_abordaje != TipoAbordaje.teorica and score >= correlate.UMBRAL_GATE
    estado, fecha = fm_ra.get("correlacion_estado"), _iso(fm_ra.get("correlacion_fecha"))
    fuente = vault.enlace(fm_ra.get("requiere_practica"))
    if abierto:
        if not estado and not fecha:
            return "gate abierto y sin correlacionar"
        previo = fm_ra.get("correlacion_score_ra")
        if isinstance(previo, (int, float)) and abs(previo - score) > 0.005:
            return f"el score cambió ({previo:.2f} → {score:.2f}): créditos, horas o criterios distintos"
        if fuente and practicas and correlate.ref_practica(fuente, str((fm_ra.get("practica_experimentos") or [""])[0])) not in practicas:
            return "la práctica que propone ya no existe en su manual"
        if fecha and fuente_reciente and fuente_reciente > fecha and estado != "aceptado":
            return f"un manual se actualizó el {fuente_reciente}, después de su última correlación ({fecha})"
        return None
    if fuente or estado in ("aceptado", "pendiente_revision"):
        return "el gate se cerró pero sigue con una práctica: correlacionar (sin LLM) la limpia"
    return None


def analizar_asignatura(pagina: str, asignatura, fm_asignatura: dict, senales_ra: dict[str, list[str]],
                        practicas: set[str], fuente_reciente: str | None) -> PlanAsignatura:
    """Recalcula lo determinista de una asignatura y lo compara con lo generado. `senales_ra`: RA -> por que sus temarios podrian
    ganar con una fuente nueva o modificada (viene del analisis de raw/)."""
    plan = PlanAsignatura(asignatura.codigo, pagina)
    ras: list[tuple] = []
    for nombre in vault.enlaces(fm_asignatura.get("resultados_aprendizaje")):
        try:
            ras.append(vault.cargar_ra(vault.RESULTADOS / f"{nombre}.md"))
        except FileNotFoundError:
            plan.avisos.append(f"la asignatura lista el RA {nombre}, que no tiene página")
        except Exception as error:
            plan.avisos.append(f"no se puede leer el RA {nombre}: {error}")
    plan.ras = [ra.codigo for ra, _, _ in ras]
    por_codigo = {ra.codigo: (ra, fm_ra) for ra, fm_ra, _ in ras}

    for ra, fm_ra, _ in ras:
        motivo = _desfase_de_correlacion(ra, fm_ra, asignatura, practicas, fuente_reciente)
        if motivo:
            plan.correlacionar[ra.codigo] = motivo
        if asignatura.tipo_abordaje != TipoAbordaje.teorica and correlate.calcular_score_ra(ra, asignatura) >= correlate.UMBRAL_GATE:
            plan.ras_gate.append(ra.codigo)

    ruta_plan = vault.PLANEADOR / f"{asignatura.codigo}-planeador.md"
    if not ruta_plan.exists():
        plan.sin_planeador = True
        return plan
    fm_plan, _ = vault.leer_pagina(ruta_plan)
    filas = {s["semana"]: s for s in fm_plan.get("semanas") or []}
    try:
        cronograma = construir_cronograma(asignatura, [ra for ra, _, _ in ras])
    except ValueError as error:
        plan.avisos.append(f"el cronograma no se puede calcular con lo que hay en el wiki: {error}")
        return plan

    esperada = {s.semana: s for s in cronograma.semanas}
    plan.clases = sum(1 for s in cronograma.semanas if s.tipo.value == "clase")
    if fm_plan.get("horas_sesion") != cronograma.horas_sesion:
        plan.duracion = f"planeador {fm_plan.get('horas_sesion')} h, ahora {cronograma.horas_sesion} h"
    for n, s in esperada.items():
        fila = filas.get(n, {})
        if fila.get("tipo") != s.tipo.value or fila.get("ra") != s.ra:
            plan.semanas_distintas.append(f"S{n}: {fila.get('ra') or fila.get('tipo') or '(no está)'} → {s.ra or 'examen'}")

    hti = horas_hti_semana(asignatura)
    competencias = temario.competencias_de(fm_asignatura)
    for ruta in sorted(vault.TEMARIOS.glob(f"{asignatura.codigo}-semana*.md")):
        try:
            fm, cuerpo = vault.leer_pagina(ruta)
        except Exception:
            continue
        semana = fm.get("semana")
        motivos: list[str] = []          # obligan a rehacer la sesion: cambia de que trata o cuanto dura
        leves: list[str] = []            # solo la cabecera o la alineacion: rehacerla cuesta ~10 llamadas para cambiar dos lineas
        s = esperada.get(semana)
        ra_del_temario = vault.enlace(fm.get("resultado_aprendizaje"))
        if s is None or s.tipo.value != "clase":
            motivos.append("esa semana ya no es de clase")
        else:
            if ra_del_temario != s.ra:
                motivos.append(f"el RA de la semana es ahora {s.ra} (el temario es de {ra_del_temario})")
            if fm.get("horas_sesion") != cronograma.horas_sesion:
                motivos.append(f"duración: el temario es de {fm.get('horas_sesion')} h y la sesión es de {cronograma.horas_sesion} h")
            if fm.get("horas_trabajo_independiente") != hti:
                leves.append(f"trabajo independiente: {fm.get('horas_trabajo_independiente')} h/semana en el temario, {hti} ahora")
            if ra_del_temario == s.ra and s.ra in por_codigo:
                alineacion = " ".join(temario._alineacion(por_codigo[s.ra][0], competencias).split())
                if alineacion not in " ".join(cuerpo.split()):
                    leves.append("la alineación con el RA (sección 2: enunciado, criterios, competencias) no coincide con el wiki")
        if motivos and isinstance(semana, int):
            plan.temarios[semana] = motivos + leves
        elif leves and isinstance(semana, int):
            plan.leves[semana] = leves
        elif isinstance(semana, int) and ra_del_temario in senales_ra:
            estadisticas = fm.get("estadisticas") or {}
            sin_apoyo = estadisticas.get("pasajes") == 0 or fm.get("bibliografia_estado") in ("revisar", "vacio_detectado") or fm.get("bibliografia_faltantes")
            plan.a_considerar[semana] = [*senales_ra[ra_del_temario], *(["se escribió sin apoyo suficiente en las fuentes"] if sin_apoyo else [])]

    tienen = {int(re.search(r"semana(\d+)", r.stem).group(1)) for r in vault.TEMARIOS.glob(f"{asignatura.codigo}-semana*.md") if re.search(r"semana(\d+)", r.stem)}
    if tienen:
        plan.sin_temario = [n for n, s in esperada.items() if s.tipo.value == "clase" and n not in tienen]
    return plan


def analizar_generacion(codigo: str | None, cambios: list[Cambio]) -> list[PlanAsignatura]:
    senales: dict[str, list[str]] = {}
    for c in cambios:
        for cob in c.cobertura:
            senales.setdefault(cob["ra"], []).append(
                f"{Path(c.ruta).name} ({'modificada' if c.estado == 'modificado' else 'nueva'}) cubre {cob['cubiertos']} de {cob['total']} conceptos del RA"
                + (" y ya la cita" if cob["ya_la_cita"] else ""))
    practicas = {correlate.ref_practica(f, p.codigo) for f, p in correlate.listar_practicas()}
    # el manual mas recien actualizado del wiki (no de raw/): asi el aviso sigue en pie despues de `--confirmar` y antes de correlacionar
    fuente_reciente = max((f for f in (_iso(fm.get("fecha_actualizacion")) for _, fm in correlate._fuentes_banco()) if f), default=None)

    planes = []
    for pagina, (asignatura, fm) in _asignaturas().items():
        if codigo and asignatura.codigo != codigo:
            continue
        planes.append(analizar_asignatura(pagina, asignatura, fm, senales, practicas, fuente_reciente))
    if codigo and not planes:
        raise FileNotFoundError(f"No hay ninguna asignatura con codigo {codigo} en {vault.ASIGNATURAS}/")
    return planes


# ---------------------------------------------------------------------------
# El plan minimo
# ---------------------------------------------------------------------------


def _comandos(cambios: list[Cambio], planes: list[PlanAsignatura]) -> tuple[list[dict], int, int]:
    """(pasos, llamadas del plan minimo, llamadas de regenerarlo todo). Los pasos con `llm` 0 no gastan tokens."""
    pasos: list[dict] = []
    llamadas = 0
    manuales = [c for c in cambios if c.categoria == "manual" and c.estado in ("nuevo", "modificado") and c.fuente]
    for c in manuales:
        nombres = sorted({*c.experimentos_nuevos, *c.experimentos_modificados},
                         key=lambda n: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", n)])       # 2 antes que 13
        solo =f" --solo {' '.join('Exp' + n for n in nombres)}" if c.estado == "modificado" and nombres else ""
        n = max(len(nombres), 1)
        pasos.append({"paso": f"extraer {'los experimentos que cambiaron de' if solo else 'los experimentos de'} {Path(c.ruta).name}",
                      "comando": f"python src/ingest_manual.py {c.ruta} --fuente {c.fuente}{solo}", "llm": n})
        llamadas += n
    if manuales:
        pasos.append({"paso": "reindexar las prácticas (embeddings, no chat)", "comando": "python src/correlate.py --indexar", "llm": 0})
    pasos.append({"paso": "revisar la salud del wiki", "comando": "python src/lint.py", "llm": 0})

    todo = 0
    for p in planes:
        if not p.sin_planeador:
            todo += p.clases * (LLAMADAS_TEMARIO + LLAMADAS_PRESENTACION) + len(p.ras) * 2 + len(p.ras_gate) * LLAMADAS_JUEZ
        ras_manual = {ra: m for c in manuales for ra, m in c.ras_a_correlacionar.items() if ra in p.ras}
        correlacionar = {**ras_manual, **p.correlacionar}
        if correlacionar:
            gasta = sum(LLAMADAS_JUEZ for ra in correlacionar if ra in p.ras_gate)
            pasos.append({"paso": f"{p.codigo}: correlacionar solo {len(correlacionar)} de {len(p.ras)} RA",
                          "comando": f"python src/correlate.py --asignatura {p.codigo} --ra {' '.join(sorted(correlacionar))}", "llm": gasta,
                          "nota": "un RA con el gate cerrado no llama al LLM"})
            llamadas += gasta
        if p.semanas_distintas or p.duracion:
            pasos.append({"paso": f"{p.codigo}: rehacer el planeador (el cronograma cambió)",
                          "comando": f"python src/planeador.py {p.codigo} --forzar", "llm": len(p.ras),
                          "nota": "pisa las ediciones a mano del planeador; después: python src/correlate_planeador.py " + p.codigo})
            llamadas += len(p.ras)
        for semana in sorted(p.temarios):
            pasos.append({"paso": f"{p.codigo} semana {semana}: {p.temarios[semana][0]}",
                          "comando": f"python src/temario.py {p.codigo} --semana {semana} --forzar", "llm": LLAMADAS_TEMARIO})
            llamadas += LLAMADAS_TEMARIO
        for semana in sorted(p.leves):
            pasos.append({"paso": f"{p.codigo} semana {semana} (opcional; solo cabecera o alineación): {p.leves[semana][0]}",
                          "comando": f"python src/temario.py {p.codigo} --semana {semana} --forzar", "llm": LLAMADAS_TEMARIO, "opcional": True,
                          "nota": "o corrige esas líneas a mano: el resto del temario sigue vigente"})
        for semana in sorted(p.a_considerar):
            pasos.append({"paso": f"{p.codigo} semana {semana} (opcional): {p.a_considerar[semana][0]}",
                          "comando": f"python src/temario.py {p.codigo} --semana {semana} --forzar", "llm": LLAMADAS_TEMARIO, "opcional": True})
        if p.temarios or p.a_considerar:
            pasos.append({"paso": f"{p.codigo}: auditar la bibliografía de sus temarios", "comando": f"python src/correlate_bibliografia.py {p.codigo}",
                          "llm": 1, "nota": "una llamada por temario sin marcador; con marcadores no gasta"})
    if any(p.temarios or p.a_considerar or p.leves or p.semanas_distintas for p in planes):
        rehechos = sum(len(p.temarios) for p in planes)
        pasos.append({"paso": "rehacer las presentaciones de los temarios que cambiaron (las demás siguen al día)",
                      "comando": "python src/presentaciones.py " + ("--all" if len(planes) != 1 else planes[0].codigo), "llm": rehechos * LLAMADAS_PRESENTACION,
                      "nota": "~9 llamadas por temario rehecho (una por parte: la apertura y cada bloque; solo las partes que cambiaron); "
                              "una presentación cuyo temario no cambió se rehace desde su plan guardado, sin LLM"})
        llamadas += rehechos * LLAMADAS_PRESENTACION
    return pasos, llamadas, todo


# ---------------------------------------------------------------------------
# El informe
# ---------------------------------------------------------------------------


def analizar(codigo: str | None = None) -> dict:
    base = leer_base()
    cambios = analizar_raw(base)
    planes = analizar_generacion(codigo, cambios)
    pasos, minimo, todo = _comandos(cambios, planes)
    return {
        "base": base["fecha"] if base else None,
        "cambios": [asdict(c) for c in cambios],
        "asignaturas": [asdict(p) for p in planes],
        "pasos": pasos,
        "llamadas_minimo": minimo,
        "llamadas_todo": todo,
        "al_dia": not any(_pendiente(c) for c in cambios) and not any(_desfasada(p) for p in planes),
    }


def _pendiente(c: Cambio | dict) -> bool:
    estado = c["estado"] if isinstance(c, dict) else c.estado
    return estado != "sin_base"


def _desfasada(p: PlanAsignatura | dict) -> bool:
    d = p if isinstance(p, dict) else asdict(p)
    return bool(d["avisos"] or d["duracion"] or d["semanas_distintas"] or d["correlacionar"] or d["temarios"])


def _lista(items: list[str], prefijo: str = "      · ", maximo: int = MAX_LISTA) -> list[str]:
    lineas = [f"{prefijo}{i}" for i in items[:maximo]]
    if len(items) > maximo:
        lineas.append(f"{prefijo}… y {len(items) - maximo} más")
    return lineas


def _n(cantidad: int, singular: str, plural: str) -> str:
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def _agrupar(por_semana: dict) -> list[str]:
    """Las semanas con los mismos motivos, juntas: «semanas 3, 4: duración…» en vez de una linea repetida por semana."""
    grupos: dict[tuple, list[int]] = {}
    for semana in sorted(por_semana):
        grupos.setdefault(tuple(por_semana[semana]), []).append(semana)
    return [f"semana{'s' if len(semanas) > 1 else ''} {', '.join(str(s) for s in semanas)}: {'; '.join(motivos)}" for motivos, semanas in grupos.items()]


def imprimir(informe: dict, detalle: bool = False) -> None:
    """El informe en texto. `detalle` agrega el texto de las secciones que cambiaron."""
    print("== 1. Documentos de raw/ " + (f"(contra la línea base del {informe['base']})" if informe["base"] else "(no hay línea base todavía)") + " ==")
    cambios = informe["cambios"]
    if not cambios:
        print("   Sin cambios en raw/.")
    if not informe["base"] and cambios:
        con_pagina = sum(1 for c in cambios if c["estado"] == "sin_base")
        print(f"   Primera corrida: {len(cambios)} documentos; {con_pagina} ya tienen página en el wiki (se suponen incorporados) y "
              f"{len(cambios) - con_pagina} no. Cuando el wiki esté al día: `python src/analizar_cambios.py --confirmar`.")
    presupuesto = MAX_DETALLE
    for c in cambios:
        etiqueta = {"nuevo": "NUEVO", "modificado": "MODIFICADO", "eliminado": "ELIMINADO", "sin_base": "SIN BASE"}[c["estado"]]
        citas = f" → {', '.join(c['paginas'])}" if c["paginas"] else ""
        print(f"   {etiqueta:<11} {c['ruta']}  ({c['categoria']}){citas}")
        if c["estado"] == "eliminado":
            print("      el original ya no está en raw/" + ("; esas páginas lo siguen citando" if c["paginas"] else ""))
            continue
        if not c["texto"]:
            print("      no es texto (PDF u otro): no se lee; conviértelo a Markdown en raw/ para poder ingerirlo y analizarlo por secciones")
            continue
        if c["estado"] == "sin_base":
            continue
        if c["categoria"] == "curriculo":
            if c["estado"] == "nuevo":
                print(f"      currículo nuevo{'' if c['paginas'] else ' sin página en el wiki'}: INGEST-CURRICULAR lo lee completo (≈{c['tokens_totales']} tokens)")
            else:
                cambiadas = len(c["secciones_nuevas"]) + len(c["secciones_modificadas"])
                print(f"      {_n(cambiadas, 'sección nueva o cambiada', 'secciones nuevas o cambiadas')} y {_n(len(c['secciones_eliminadas']), 'quitada', 'quitadas')}: "
                      f"hay que leer ≈{c['tokens_a_leer']} tokens de ≈{c['tokens_totales']}")
                for d in c["destinos"]:
                    print(f"      · {', '.join(d['secciones'][:3])}{' …' if len(d['secciones']) > 3 else ''}")
                    print(f"          actualizar: {d['actualizar']}")
                    print(f"          arrastra:   {d['efecto']}")
        elif c["categoria"] == "manual":
            if c["experimentos_nuevos"] or c["experimentos_modificados"] or c["experimentos_eliminados"]:
                for nombre, lista in (("nuevos", c["experimentos_nuevos"]), ("modificados", c["experimentos_modificados"]), ("eliminados", c["experimentos_eliminados"])):
                    if lista:
                        print(f"      experimentos {nombre}: {', '.join('Exp' + e for e in lista)}" + (" (siguen en `practicas:`: quítalos a mano si ya no aplican)" if nombre == "eliminados" else ""))
            else:
                print("      el texto cambió pero los experimentos son los mismos y con la misma huella (¿encabezados u otra sección?)")
            if c["ras_a_correlacionar"]:
                print(f"      a correlacionar: {len(c['ras_a_correlacionar'])} RA")
        else:
            print(f"      ≈{c['tokens_a_leer']} tokens de lo que cambió; {'sin página en el wiki: INGEST' if not c['paginas'] else 'actualizar su página'}")
            for cob in c["cobertura"]:
                print(f"      · {cob['ra']}: {cob['cubiertos']} de {cob['total']} conceptos aparecen" + (" (ya la cita)" if cob["ya_la_cita"] else " (no la cita)"))
            for f in c["faltantes_que_cubre"]:
                print(f"      · parece cubrir la referencia sin cargar de {f}")
        if detalle and c["categoria"] in ("curriculo", "bibliografia", "norma", "otra") and c["estado"] == "modificado":
            texto = Path(c["ruta"]).read_text(encoding="utf-8", errors="replace")
            secciones = {s.clave: s for s in dividir_secciones(texto, _nivel_de(c["categoria"]))}
            for clave in [*c["secciones_nuevas"], *c["secciones_modificadas"]]:
                if clave in secciones and presupuesto > 0:
                    cuerpo = secciones[clave].texto[:presupuesto]
                    presupuesto -= len(cuerpo)
                    print(f"\n      ---- {c['ruta']} › {clave} ----")
                    print("\n".join("      " + l for l in cuerpo.splitlines()))
            if presupuesto <= 0:
                print("\n      (se alcanzó el límite de --detalle; el resto está en el documento)")

    print("\n== 2. wiki/ contra generacion/ (lo que quedó desactualizado) ==")
    for p in informe["asignaturas"]:
        if not (_desfasada(p) or p["leves"] or p["a_considerar"] or p["sin_temario"]):
            print(f"   {p['codigo']}: al día" + (" (sin planeador todavía)" if p["sin_planeador"] else ""))
            continue
        print(f"   {p['codigo']}")
        for aviso in p["avisos"]:
            print(f"      ! {aviso}")
        if p["duracion"]:
            print(f"      · duración de la sesión: {p['duracion']}")
        if p["semanas_distintas"]:
            print("      · el cronograma cambió:")
            print("\n".join(_lista(p["semanas_distintas"], "          ")))
        if p["correlacionar"]:
            print(f"      · correlación desactualizada en {len(p['correlacionar'])} de {len(p['ras'])} RA:")
            print("\n".join(_lista([f"{ra}: {m}" for ra, m in sorted(p["correlacionar"].items())], "          ")))
        if p["temarios"]:
            print(f"      · temarios a rehacer: {len(p['temarios'])} de {p['clases']}")
            print("\n".join(_lista(_agrupar(p["temarios"]), "          ")))
        if p["leves"]:
            print(f"      · temarios con un desfase solo de cabecera o alineación (el resto sigue vigente): {len(p['leves'])}")
            print("\n".join(_lista(_agrupar(p["leves"]), "          ")))
        if p["a_considerar"]:
            print(f"      · temarios que podrían ganar con una fuente nueva (opcional): {len(p['a_considerar'])}")
            print("\n".join(_lista(_agrupar(p["a_considerar"]), "          ")))
        if p["sin_temario"]:
            print(f"      · sin temario todavía: semanas {', '.join(str(n) for n in p['sin_temario'])} (`temario.py {p['codigo']} --todas`)")

    print("\n== 3. Plan mínimo ==")
    if informe["al_dia"] and not any(p.get("opcional") for p in informe["pasos"]):
        print("   Todo al día: no hay nada que actualizar.")
        return
    if informe["cambios"] and any(c["estado"] != "sin_base" for c in informe["cambios"]) and not any(_desfasada(p) for p in informe["asignaturas"]):
        print("   Primero actualiza las páginas del wiki que indica la sección 1 y vuelve a correr este script: "
              "entonces dirá qué de la generación quedó desfasado.")
    for i, paso in enumerate(informe["pasos"], 1):
        costo = "sin LLM" if not paso["llm"] else f"≈{_n(paso['llm'], 'llamada', 'llamadas')}"
        print(f"   {i:>2}. {'(opcional) ' if paso.get('opcional') else ''}{paso['paso']}  [{costo}]")
        print(f"       {paso['comando']}" + (f"   # {paso['nota']}" if paso.get("nota") else ""))
    if informe["llamadas_todo"]:
        print(f"\n   Llamadas al modelo: ≈{informe['llamadas_minimo']} con este plan (sin las opcionales) contra ≈{informe['llamadas_todo']} "
              "de regenerar todo lo de estas asignaturas.")
    print("   Al terminar: `python src/analizar_cambios.py --confirmar` fija la línea base.")


def main() -> int:
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Dice qué actualizar (y qué no) cuando cambia un currículo o llega bibliografía nueva. No usa LLM ni escribe en wiki/.")
    parser.add_argument("--asignatura", metavar="CODIGO", help="limita la comparación wiki/generación a esa asignatura")
    parser.add_argument("--detalle", action="store_true", help="imprime el texto de las secciones que cambiaron (lo único que hay que leer)")
    parser.add_argument("--json", action="store_true", help="el informe en JSON")
    parser.add_argument("--confirmar", nargs="*", metavar="RUTA", help="fija la línea base: todo raw/ (sin argumentos) o solo esos archivos o carpetas")
    args = parser.parse_args()
    try:
        if args.confirmar is not None:
            n, ruta = confirmar(args.confirmar)
            print(f"Línea base fijada: {n} archivos de raw/ en {ruta}")
            return 0
        informe = analizar(args.asignatura)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=1))
    else:
        imprimir(informe, args.detalle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
