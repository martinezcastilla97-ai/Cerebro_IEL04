"""MIGRACIONES -- lo que una version nueva de la plantilla le hace al CONTENIDO de una copia (paginas de wiki/ y de generacion/), no a
su codigo. Las corre ACTUALIZAR-ESTRUCTURA (src/actualizar_estructura.py) al pasar de una version a otra.

Cuando una version cambia el esquema de las paginas (un campo que se renombra, uno nuevo con valor por defecto, uno que desaparece),
la copia que ya tiene paginas necesita el cambio: se escribe UNA migracion aqui, con la version que lo introduce, y desde entonces toda
copia que pase por esa version la aplica sola, en orden y con respaldo. Una migracion nunca se borra: una copia que salta varias
versiones corre todas las que le faltan.

Reglas para escribir una:
  - idempotente: correrla dos veces no cambia nada mas (si el campo ya esta, no se vuelve a tocar);
  - todo lo que escribe pasa por `Contexto.reescribir`: eso respalda la pagina antes de tocarla y respeta `--simular` (la prueba en seco);
  - solo toca lo que necesita, con las primitivas de abajo (`renombrar_campo`, `agregar_campo`, `quitar_campo`) o con las suyas;
  - las migraciones SI necesitan las dependencias (PyYAML y pydantic, que `vault` importa para leer y escribir paginas), y se importan
    aqui dentro, no arriba, para que el resto del actualizador corra sin ellas. ACTUALIZAR-ESTRUCTURA lo comprueba antes de escribir
    nada: con migraciones pendientes y sin dependencias se detiene y pide `pip install -r requirements.txt`. Nunca captures un
    ImportError: una migracion que «no encuentra paginas» por falta de PyYAML se daria por hecha sin haber cambiado nada;
  - una pagina que no se puede leer (YAML roto, una cabecera `---` sin cerrar) no se migra, pero queda en `Contexto.omitidas` y el
    actualizador la informa: nunca se salta en silencio.

Ejemplo (ilustrativo; las reales estan en MIGRACIONES, al final de las primitivas):

    def _renombrar_semanas(ctx: Contexto) -> None:
        renombrar_campo(ctx, "generacion/temarios", "total_semanas", "semanas_totales")

    MIGRACIONES = [Migracion("1.18", "el temario llama `semanas_totales` a `total_semanas`", _renombrar_semanas)]
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, NamedTuple


def version_tupla(version: str) -> tuple[int, ...]:
    """'1.16' -> (1, 16): se compara por numeros, no por texto ('1.9' < '1.10')."""
    try:
        return tuple(int(p) for p in str(version).strip().split("."))
    except ValueError:
        raise ValueError(f"version no valida: {version!r} (se espera algo como 1.16)") from None


class Contexto:
    """Lo que una migracion puede hacer sobre la copia: recorrer paginas y reescribirlas (con respaldo y sin escribir si se simula)."""

    def __init__(self, raiz: Path, simular: bool, respaldar: Callable[[Path], None] | None = None):
        self.raiz = raiz
        self.simular = simular
        self.cambios: list[str] = []
        self.omitidas: list[str] = []          # paginas que no se pudieron leer (y por eso no se migran): el actualizador las informa
        self._respaldar = respaldar

    def paginas(self, carpeta: str) -> Iterator[Path]:
        base = self.raiz / carpeta
        yield from sorted(base.rglob("*.md")) if base.is_dir() else []

    def leer(self, ruta: Path) -> tuple[dict, str] | None:
        """(frontmatter, cuerpo) de una pagina, o None si no tiene frontmatter (una migracion no tiene nada que cambiarle) o si esa
        pagina no se puede leer (se anota en `omitidas`). Los imports van FUERA del try: si falta PyYAML, o pydantic (que `vault`
        importa), es un ImportError que tiene que propagarse, no «una pagina sin frontmatter»: la migracion terminaria sin cambiar
        nada y la copia se daria por migrada."""
        import yaml

        import vault

        try:
            fm, cuerpo = vault.leer_pagina(ruta)
        except (OSError, ValueError, yaml.YAMLError) as error:        # ValueError: UnicodeDecodeError o una cabecera `---` sin cerrar
            self.omitidas.append(f"{ruta.relative_to(self.raiz).as_posix()}: {type(error).__name__}")
            return None
        if fm and not isinstance(fm, dict):
            self.omitidas.append(f"{ruta.relative_to(self.raiz).as_posix()}: el frontmatter no es un mapa")
            return None
        return (fm, cuerpo) if fm else None

    def reescribir(self, ruta: Path, frontmatter: dict, cuerpo: str, que: str) -> None:
        import vault

        self.cambios.append(f"{ruta.relative_to(self.raiz).as_posix()}: {que}")
        if self.simular:
            return
        if self._respaldar:
            self._respaldar(ruta)
        vault.escribir_pagina(ruta, frontmatter, cuerpo)


class Migracion(NamedTuple):
    version: str                         # la version de la plantilla que introduce el cambio
    descripcion: str
    aplicar: Callable[[Contexto], None]


def pendientes(desde: str | None, hasta: str) -> list[Migracion]:
    """Las migraciones de las versiones posteriores a `desde` y hasta `hasta` inclusive, en orden. Sin version de partida
    (una copia sin manifiesto ni SCHEMA legible) no se sabe cual le toca: ninguna, y el actualizador lo avisa."""
    if desde is None:
        return []
    ini, fin = version_tupla(desde), version_tupla(hasta)
    return sorted((m for m in MIGRACIONES if ini < version_tupla(m.version) <= fin), key=lambda m: version_tupla(m.version))


# --- primitivas ---------------------------------------------------------------------------------------------------------


def _paginas_de(ctx: Contexto, carpeta: str, tipo: str | None):
    for ruta in ctx.paginas(carpeta):
        leido = ctx.leer(ruta)
        if leido and (tipo is None or leido[0].get("tipo") == tipo):
            yield ruta, leido[0], leido[1]


def renombrar_campo(ctx: Contexto, carpeta: str, viejo: str, nuevo: str, tipo: str | None = None) -> int:
    """`viejo` -> `nuevo` en el frontmatter de las paginas de `carpeta` (con ese `tipo`, si se indica). Si la pagina ya tiene `nuevo`
    no se pisa (y `viejo` se quita: era un resto). Conserva el orden de los campos. Devuelve cuantas paginas cambio."""
    cambiadas = 0
    for ruta, fm, cuerpo in _paginas_de(ctx, carpeta, tipo):
        if viejo not in fm:
            continue
        salida = {}
        for clave, valor in fm.items():
            if clave == viejo:
                if nuevo not in fm:
                    salida[nuevo] = valor
            else:
                salida[clave] = valor
        ctx.reescribir(ruta, salida, cuerpo, f"`{viejo}` -> `{nuevo}`")
        cambiadas += 1
    return cambiadas


def agregar_campo(ctx: Contexto, carpeta: str, campo: str, valor, tipo: str | None = None) -> int:
    """Agrega `campo: valor` a las paginas que no lo tienen. Devuelve cuantas paginas cambio."""
    cambiadas = 0
    for ruta, fm, cuerpo in _paginas_de(ctx, carpeta, tipo):
        if campo in fm:
            continue
        ctx.reescribir(ruta, {**fm, campo: valor}, cuerpo, f"agrega `{campo}`")
        cambiadas += 1
    return cambiadas


def quitar_campo(ctx: Contexto, carpeta: str, campo: str, tipo: str | None = None) -> int:
    """Quita `campo` del frontmatter de las paginas que lo tienen. Devuelve cuantas paginas cambio."""
    cambiadas = 0
    for ruta, fm, cuerpo in _paginas_de(ctx, carpeta, tipo):
        if campo not in fm:
            continue
        ctx.reescribir(ruta, {k: v for k, v in fm.items() if k != campo}, cuerpo, f"quita `{campo}`")
        cambiadas += 1
    return cambiadas


# --- las migraciones de la plantilla (nunca se borran) ------------------------------------------------------------------


def _sin_framework(ctx: Contexto) -> None:
    # 1.20 quito el tema Beamer (config/framework_iub/beamerthemeiub.sty): el diseno va en el preambulo de cada .tex
    quitar_campo(ctx, "generacion/temarios", "presentacion_framework", tipo="temario")


MIGRACIONES: list[Migracion] = [
    Migracion("1.20", "el temario ya no lleva `presentacion_framework` (el diseño de las presentaciones va en cada .tex, sin tema .sty)", _sin_framework),
]
