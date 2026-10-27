"""PASAJES -- lo que las fuentes ya ingeridas dicen sobre un tema, para que TEMARIO escriba con ellas y no de memoria.

Una fuente de wiki/fuentes/ es un resumen (`## Resumen`, `## Puntos clave`, `## Citas relevantes`...) con su archivo
original en raw/ (la linea `**Origen:** raw/...`). El resumen solo alcanza para un juez; para redactar una sesion con
profundidad hace falta el texto: definiciones, ecuaciones, tablas de datos, ejemplos numericos. Este modulo

    1. junta, de cada fuente, su pagina del wiki y -si el original es un archivo de texto (.md / .txt)- el texto
       completo de raw/, partido en pasajes de ~1400 caracteres que respetan los encabezados;
    2. los indexa en memoria con BM25 (sin embeddings, sin red, sin LLM: pura Python) y
    3. devuelve los pasajes que mejor responden a unos terminos de busqueda.

Los terminos los propone el LLM del plan de la sesion en espanol E ingles (los libros suelen estar en ingles y el curriculo
en espanol); la busqueda no distingue tildes ni mayusculas. Un original que no es texto (un PDF) no se lee: de esa fuente
solo se usa su pagina del wiki.

Solo se leen originales DENTRO de raw/: la ruta sale de una pagina que se edita a mano o la escribe un LLM, y lo que se lee
viaja al proveedor de IA. Cada ruta (y cada archivo de una carpeta) se resuelve -con sus `..` y sus enlaces simbolicos- y si
no queda dentro de raw/ no se lee: se anota en `omitidos` para que TEMARIO lo avise.
"""

from __future__ import annotations

import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import vault

RAIZ_RAW = Path("raw")          # relativa al vault (donde se ejecutan los scripts), como vault.WIKI
FUERA_DE_RAW = "fuera de raw/: no se lee"
EXTENSIONES_TEXTO = (".md", ".markdown", ".txt")
MAX_ARCHIVOS_POR_FUENTE = 200
MAX_AVISOS_FUERA_DE_RAW = 5     # de una carpeta con muchos enlaces que salen de raw/, se nombran los primeros
MAX_BYTES_ARCHIVO = 12_000_000
PASAJE_MAXIMO = 1400            # caracteres por pasaje
PASAJE_MINIMO = 80              # un pasaje mas corto no dice nada (un titulo suelto, un numero de pagina)

_PARADAS = frozenset("""
    the and for with that this from are was were has have had not but its can may also into onto than then them their there these
    those which who whom what when where how why all any each other such only more most some very one two three per via used use using
    los las una uno unos unas del por con para que como mas pero sus son fue ser esta este estos estas esto entre sobre sin desde
    hasta cada cuando donde cual cuales tambien puede pueden segun otro otra otros otras muy solo asi ese esa eso aquel
""".split())


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()


def _tokens(texto: str) -> list[str]:
    """Palabras de un texto para la busqueda: sin tildes ni mayusculas, sin palabras vacias y con el plural recortado."""
    salida = []
    for t in re.findall(r"[a-z0-9]+", _sin_tildes(texto)):
        if t in _PARADAS or (len(t) < 3 and not any(c.isdigit() for c in t)):
            continue
        if len(t) > 4 and t.endswith("s"):
            t = t[:-1]
        salida.append(sys.intern(t))          # un libro repite las mismas palabras miles de veces: una sola copia de cada una
    return salida


@dataclass
class Pasaje:
    fuente: str                 # nombre de la pagina en wiki/fuentes/
    ubicacion: str              # donde esta: "wiki: Resumen" o "raw: archivo.md › Capitulo › Seccion"
    texto: str
    _tokens: list[str] = field(default_factory=list, repr=False)


@dataclass
class FuenteTexto:
    nombre: str
    pasajes: list[Pasaje]
    archivos: list[str]         # los originales de raw/ que se leyeron (vacio: solo se cuenta con la pagina del wiki)
    omitidos: list[str]         # originales citados que no se leen: no son texto (PDF...), no existen o quedan fuera de raw/


# ---------------------------------------------------------------------------
# Lectura de una fuente
# ---------------------------------------------------------------------------


def _partir_parrafo(texto: str, maximo: int) -> list[str]:
    if len(texto) <= maximo:
        return [texto]
    trozos, actual = [], ""
    for frase in re.split(r"(?<=[.!?])\s+", texto):
        while len(frase) > maximo:                      # una frase enorme (o una linea de tabla): se corta donde haya un espacio
            corte = frase.rfind(" ", 0, maximo)
            corte = corte if corte > 0 else maximo
            if actual:
                trozos.append(actual)
                actual = ""
            trozos.append(frase[:corte])
            frase = frase[corte:].lstrip()
        if actual and len(actual) + 1 + len(frase) > maximo:
            trozos.append(actual)
            actual = frase
        else:
            actual = f"{actual} {frase}".strip()
    if actual:
        trozos.append(actual)
    return trozos


def trocear(texto: str, base: str, maximo: int = PASAJE_MAXIMO) -> list[tuple[str, str]]:
    """(ubicacion, texto) de cada pasaje: los parrafos se juntan hasta `maximo` caracteres y un encabezado nuevo siempre abre
    un pasaje nuevo, asi que un pasaje no mezcla dos secciones. La ubicacion es `base › encabezado › subencabezado`."""
    pasajes: list[tuple[str, str]] = []
    encabezados: list[tuple[int, str]] = []
    actual: list[str] = []
    largo = 0

    def ubicacion() -> str:
        return " › ".join([base, *[t for _, t in encabezados[-2:]]])

    def cerrar() -> None:
        nonlocal actual, largo
        cuerpo = "\n\n".join(actual).strip()
        if len(cuerpo) >= PASAJE_MINIMO:
            pasajes.append((ubicacion(), cuerpo))
        actual, largo = [], 0

    for bloque in re.split(r"\n\s*\n", texto.replace("\r\n", "\n")):
        bloque = bloque.strip()
        if not bloque:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", bloque.split("\n", 1)[0])
        if m:
            cerrar()
            nivel = len(m.group(1))
            while encabezados and encabezados[-1][0] >= nivel:
                encabezados.pop()
            encabezados.append((nivel, re.sub(r"[*_`]", "", m.group(2)).strip()))
            bloque = bloque.split("\n", 1)[1].strip() if "\n" in bloque else ""
            if not bloque:
                continue
        for parte in _partir_parrafo(bloque, maximo):
            if actual and largo + len(parte) + 2 > maximo:
                cerrar()
            actual.append(parte)
            largo += len(parte) + 2
    cerrar()
    return pasajes


def _originales(cuerpo: str) -> list[str]:
    """Las rutas que la pagina de la fuente cita en su linea `**Origen:**` (entre comillas invertidas o sueltas)."""
    m = re.search(r"\*\*Origen:\*\*\s*(.+)", cuerpo)
    if not m:
        return []
    linea = m.group(1)
    candidatas = re.findall(r"`([^`]+)`", linea) or [linea.strip()]
    return [c.strip().replace("\\", "/") for c in candidatas if c.strip()]


def _dentro_de_raw(ruta: Path, raiz: Path | None = None) -> bool:
    """True si `ruta` -ya sin sus `..` ni enlaces simbolicos- queda dentro de raw/ (`raiz`, si quien llama ya la resolvio).
    Es la unica puerta por la que un original llega al LLM: una ruta que sale de raw/ (`../x.txt`, `raw/../../x.txt`, una
    absoluta, un enlace) no se lee."""
    try:
        return ruta.resolve().is_relative_to(raiz or RAIZ_RAW.resolve())
    except (OSError, RuntimeError, ValueError):             # un nombre invalido en este sistema, un bucle de enlaces...
        return False


def _archivos_de(ruta: str) -> tuple[list[Path], list[str]]:
    """(archivos de texto, motivos por los que algo se omite) de una ruta de raw/. Una carpeta aporta todos sus archivos de
    texto que esten, ya resueltos, dentro de raw/: un enlace de la carpeta que apunte fuera no cuenta."""
    destino = Path(ruta)
    if not _dentro_de_raw(destino):
        return [], [f"{ruta} ({FUERA_DE_RAW})"]
    if not destino.exists():
        return [], [f"{ruta} (no existe)"]
    if destino.is_dir():
        raiz = RAIZ_RAW.resolve()
        dentro: list[Path] = []
        fuera: list[Path] = []
        for p in sorted(p for p in destino.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONES_TEXTO):
            if len(dentro) >= MAX_ARCHIVOS_POR_FUENTE:      # de los que sobran no se lee ninguno: no hace falta resolverlos
                break
            (dentro if _dentro_de_raw(p, raiz) else fuera).append(p)
        motivos = [f"{p.as_posix()} ({FUERA_DE_RAW})" for p in fuera[:MAX_AVISOS_FUERA_DE_RAW]]
        if len(fuera) > MAX_AVISOS_FUERA_DE_RAW:
            motivos.append(f"{ruta} (y otros {len(fuera) - MAX_AVISOS_FUERA_DE_RAW} archivos: {FUERA_DE_RAW})")
        if not dentro and not fuera:
            motivos.append(f"{ruta} (la carpeta no tiene archivos de texto)")
        return dentro, motivos
    if destino.suffix.lower() not in EXTENSIONES_TEXTO:
        return [], [f"{ruta} (no es un archivo de texto: solo se usa la pagina del wiki)"]
    if destino.stat().st_size > MAX_BYTES_ARCHIVO:
        return [], [f"{ruta} (mas de {MAX_BYTES_ARCHIVO // 1_000_000} MB)"]
    return [destino], []


_CACHE: dict[tuple, "FuenteTexto"] = {}


def cargar_fuente(nombre: str) -> FuenteTexto:
    """Los pasajes de una fuente: su pagina de wiki/fuentes/ (por secciones) y el texto completo de su original en raw/. Se
    guardan en memoria mientras ni la pagina ni los originales cambien: `temario.py --todas` la usa en cada una de las ~11
    sesiones de una asignatura, y leer y partir un libro entero cada vez seria un desperdicio."""
    ruta = vault.FUENTES / f"{nombre}.md"
    _, cuerpo = vault.leer_pagina(ruta)
    huella = [(str(Path.cwd()), nombre, hash(cuerpo))]
    for original in _originales(cuerpo):
        for archivo in _archivos_de(original)[0]:
            estado = archivo.stat()
            huella.append((archivo.as_posix(), estado.st_mtime_ns, estado.st_size))
    clave = tuple(huella)
    if clave not in _CACHE:
        _CACHE[clave] = _leer_fuente(nombre, cuerpo)
    return _CACHE[clave]


def _leer_fuente(nombre: str, cuerpo: str) -> FuenteTexto:
    pasajes: list[Pasaje] = []
    for ubicacion, texto in trocear(cuerpo, "wiki"):
        pasajes.append(Pasaje(nombre, ubicacion, texto))
    archivos: list[str] = []
    omitidos: list[str] = []
    for original in _originales(cuerpo):
        if not original.startswith("raw/") and not Path(original).exists():
            continue                                    # una URL u otro texto que no es una ruta
        encontrados, motivos = _archivos_de(original)
        omitidos.extend(motivos)
        for archivo in encontrados:
            texto = archivo.read_text(encoding="utf-8", errors="replace")
            archivos.append(archivo.as_posix())
            for ubicacion, trozo in trocear(texto, f"raw: {archivo.name}"):
                pasajes.append(Pasaje(nombre, ubicacion, trozo))
    for p in pasajes:
        p._tokens = _tokens(p.texto + " " + p.ubicacion)
    return FuenteTexto(nombre, pasajes, archivos, omitidos)


# ---------------------------------------------------------------------------
# Busqueda (BM25)
# ---------------------------------------------------------------------------


class Indice:
    """Indice BM25 en memoria sobre los pasajes de varias fuentes."""

    K1, B = 1.4, 0.75

    def __init__(self, fuentes: list[FuenteTexto]):
        self.pasajes: list[Pasaje] = [p for f in fuentes for p in f.pasajes]
        self.normalizados = [_sin_tildes(p.texto) for p in self.pasajes]
        n = max(len(self.pasajes), 1)
        self.medio = sum(len(p._tokens) for p in self.pasajes) / n or 1.0
        self.frecuencia: dict[str, int] = {}
        for p in self.pasajes:
            for t in set(p._tokens):
                self.frecuencia[t] = self.frecuencia.get(t, 0) + 1
        self.n = len(self.pasajes)

    def _puntaje(self, k: int, consulta: list[str], frases: list[str]) -> float:
        p = self.pasajes[k]
        largo = len(p._tokens) or 1
        conteo: dict[str, int] = {}
        for t in p._tokens:
            conteo[t] = conteo.get(t, 0) + 1
        total = 0.0
        for t in set(consulta):
            f = conteo.get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (self.n - self.frecuencia[t] + 0.5) / (self.frecuencia[t] + 0.5))
            total += idf * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * largo / self.medio))
        for frase in frases:
            if frase in self.normalizados[k]:
                total += 1.5 * len(frase.split())            # una frase exacta ("maquina de estados") pesa mas que sus palabras sueltas
        return total

    def buscar(self, terminos: list[str], k: int = 4, presupuesto: int = 6000, evitar: set[int] | None = None) -> list[tuple[int, Pasaje]]:
        """Los `k` pasajes que mejor responden a los terminos (o menos, si no caben en `presupuesto` caracteres), como
        (indice, pasaje). Los de `evitar` (ya usados en otra seccion) solo entran si no hay otros. Nunca devuelve dos
        pasajes casi iguales."""
        consulta: list[str] = []
        frases: list[str] = []
        for termino in terminos:
            consulta += _tokens(termino)
            palabras = _sin_tildes(termino).strip()
            if len(palabras.split()) > 1:
                frases.append(palabras)
        if not consulta:
            return []
        evitar = evitar or set()
        puntajes = sorted(((self._puntaje(i, consulta, frases), i) for i in range(self.n)), reverse=True)
        elegidos: list[tuple[int, Pasaje]] = []
        usado = 0
        for pasada in (0, 1):
            for puntaje, i in puntajes:
                if puntaje <= 0 or len(elegidos) >= k:
                    break
                if (i in evitar) != (pasada == 1) or any(i == j for j, _ in elegidos):
                    continue
                p = self.pasajes[i]
                if usado + len(p.texto) > presupuesto and elegidos:
                    continue
                conjunto = set(p._tokens)
                if any(len(conjunto & set(q._tokens)) > 0.7 * max(len(conjunto), 1) for _, q in elegidos):
                    continue
                elegidos.append((i, p))
                usado += len(p.texto)
        return elegidos


def formatear(pasajes: list[tuple[int, Pasaje]], numeros: dict[str, int]) -> str:
    """Los pasajes como los ve el LLM: `[n] fuente › ubicacion` y el texto, donde n es el numero de la fuente en la lista de
    referencias de la sesion (el que el modelo debe usar para citarla)."""
    if not pasajes:
        return "(ninguno: no hay fuentes cargadas para este tema; apóyate en conocimiento técnico estándar y no cites ninguna fuente cargada)"
    return "\n\n".join(f"[{numeros.get(p.fuente, '?')}] {p.fuente} — {p.ubicacion}\n{p.texto}" for _, p in pasajes)
