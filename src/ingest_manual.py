"""INGEST de un manual de banco de laboratorio: extrae sus experimentos y los escribe
en `practicas:` de la pagina de wiki/fuentes/ (etiqueta `equipo-laboratorio`), que es
de donde CORRELATE toma sus candidatos.

El manual se divide en experimentos por sus encabezados y se procesa UN experimento
por llamada (src/prompts/prompt-ingest-manual.md, salida `ExtraccionManual`). El codigo
de cada practica sale del numero del encabezado (`Exp{N}`), no del LLM. Si la pagina de la
fuente ya existe, las practicas se fusionan por codigo (se reemplaza la que se repite) y
el resto de la pagina no se toca.

Uso (desde la raiz del vault):
    python src/ingest_manual.py raw/manuales-laboratorio/BANCO/manual.md --fuente mi-banco
    python src/ingest_manual.py raw/.../manual.md --solo-dividir           # lista los experimentos (sin LLM)
    python src/ingest_manual.py raw/.../manual.md --fuente mi-banco --limite 3       # prueba barata
    python src/ingest_manual.py raw/.../manual.md --fuente mi-banco --solo Exp3 Exp5  # solo esos experimentos (lo que cambio; ver analizar_cambios.py)
    python src/ingest_manual.py raw/.../manual.md --fuente mi-banco --patron "^#+\\s*Project\\s+(\\d+)" --prefijo PRJ

Despues de ingerir: python src/correlate.py --indexar
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

import vault
from schema_extraccion import ExtraccionManual, Practica

ETIQUETA_BANCO = "equipo-laboratorio"
# El grupo 1 es el numero del experimento. Reconoce "Experiment 13", "Exp. 13", "Experimento 13",
# "Practice 3", "Project 07"... y numeros compuestos como "Experiment 3-1" / "Experiment 3.2"
# (algunos manuales numeran las sub-practicas asi; sin esto, "3-1" y "3-2" colisionaban en "3").
PATRON_EXPERIMENTO = r"^#{1,6}\s*(?:Experiment|Experimento|Exp\.?|Practice|Pr[aá]ctica|Project|Proyecto)\s*[:\-]?\s*(\d+(?:[-.]\d+)*[A-Za-z]?)\b"


class Seccion(NamedTuple):
    numero: str
    encabezado: str
    capitulo: str
    texto: str


def _nivel(linea: str) -> int:
    """Nivel de un encabezado Markdown (0 si la linea no es un encabezado)."""
    return len(linea) - len(linea.lstrip("#")) if linea.startswith("#") else 0


def dividir_experimentos(texto: str, patron: str = PATRON_EXPERIMENTO) -> list[Seccion]:
    """Un experimento va desde su encabezado hasta el siguiente encabezado del mismo nivel
    o superior. `capitulo` es el encabezado padre mas cercano (nivel menor)."""
    lineas = texto.splitlines()
    regex = re.compile(patron, re.IGNORECASE)
    secciones = []
    for i, linea in enumerate(lineas):
        coincidencia = regex.match(linea)
        if not coincidencia:
            continue
        nivel = _nivel(linea)
        fin = next((j for j in range(i + 1, len(lineas)) if 0 < _nivel(lineas[j]) <= nivel), len(lineas))
        capitulo = next((lineas[j].lstrip("#").strip() for j in range(i - 1, -1, -1) if 0 < _nivel(lineas[j]) < nivel), "")
        secciones.append(Seccion(coincidencia.group(1), linea.strip(), capitulo, "\n".join(lineas[i:fin]).strip()))
    return secciones


def codigos_repetidos(secciones: list[Seccion], prefijo: str) -> dict[str, list[Seccion]]:
    """Codigos que dos o mas secciones producirian dentro de la MISMA corrida (p. ej. dos
    capitulos que cada uno tiene su propio "Experiment 1"). La fusion por codigo de
    escribir_fuente() pisaria silenciosamente una de las dos -- por eso se detiene antes
    de llamar al LLM. Tambien la usa `--solo-dividir` para avisar sin gastar una llamada."""
    por_codigo: dict[str, list[Seccion]] = {}
    for s in secciones:
        por_codigo.setdefault(f"{prefijo}{s.numero}", []).append(s)
    return {codigo: secs for codigo, secs in por_codigo.items() if len(secs) > 1}


def _mensaje_repetidos(repetidos: dict[str, list[Seccion]]) -> str:
    detalle = "; ".join(f"{codigo} en {len(secs)} secciones ({', '.join(s.encabezado for s in secs)})" for codigo, secs in repetidos.items())
    return (f"códigos repetidos dentro de esta corrida: {detalle}. Usa --patron para distinguirlos "
            "(p. ej. incluyendo el capítulo) o procesa cada grupo por separado con un --prefijo distinto.")


def extraer_practica(seccion: Seccion, ruta_raw: str, prefijo: str) -> tuple[ExtraccionManual, Practica]:
    sistema, plantilla = vault.cargar_prompt("prompt-ingest-manual.md")
    usuario = plantilla.format(ruta_raw=ruta_raw, capitulo_actual=seccion.capitulo, seccion_experimento=seccion.texto)
    extraccion = vault.pedir_estructurado(sistema, usuario, ExtraccionManual)
    if len(extraccion.practicas) != 1:
        raise ValueError(f"{seccion.encabezado}: el LLM devolvió {len(extraccion.practicas)} prácticas y se pide exactamente una")
    practica = extraccion.practicas[0]
    # El codigo sale del encabezado, no del LLM: asi es estable y unico dentro del manual.
    practica = practica.model_copy(update={"codigo": f"{prefijo}{seccion.numero}", "capitulo": practica.capitulo or seccion.capitulo or None})
    return extraccion, practica


def _slug(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def escribir_fuente(nombre_fuente: str, practicas: list[Practica], ruta_raw: str, extraccion: ExtraccionManual) -> Path:
    """Crea o actualiza wiki/fuentes/{nombre_fuente}.md. Fusiona por codigo y no toca el resto de la pagina."""
    ruta = vault.FUENTES / f"{nombre_fuente}.md"
    hoy = vault.hoy()
    if ruta.exists():
        fm, cuerpo = vault.leer_pagina(ruta)
    else:
        fm = {"tipo": "fuente", "etiquetas": [ETIQUETA_BANCO], "fecha_creacion": hoy, "origen": "manual"}
        cuerpo = (f"\n\n# {extraccion.banco_nombre}\n\n**Origen:** `{ruta_raw}`\n"
                  "**Tipo:** Manual de equipo didáctico de laboratorio\n"
                  + (f"**Fabricante:** {extraccion.fabricante}\n" if extraccion.fabricante else "")
                  + f"**Idioma original:** {extraccion.idioma_original}\n")
    etiquetas = fm.get("etiquetas") or []
    if isinstance(etiquetas, str):
        etiquetas = [etiquetas]
    if ETIQUETA_BANCO not in etiquetas:
        etiquetas.append(ETIQUETA_BANCO)
    fm["etiquetas"] = etiquetas

    por_codigo = {e["codigo"]: e for e in fm.get("practicas") or []}
    for practica in practicas:
        por_codigo[practica.codigo] = practica.model_dump(mode="json", exclude_none=True)
    fm["practicas"] = list(por_codigo.values())
    fm["fecha_actualizacion"] = hoy
    vault.escribir_pagina(ruta, fm, cuerpo)
    return ruta


def seleccionar(secciones: list[Seccion], solo: list[str], prefijo: str) -> list[Seccion]:
    """Los experimentos de `solo` (por codigo, `Exp3`, o por numero, `3`), en el orden del manual. Uno que el manual no tiene es
    un error, no un descarte silencioso: significaria gastar una corrida sin haber extraido lo que se pidio."""
    pedidos = {s.strip().removeprefix(prefijo) for s in solo if s.strip()}
    tiene = {s.numero for s in secciones}
    if pedidos - tiene:
        raise ValueError(f"el manual no tiene {', '.join(prefijo + n for n in sorted(pedidos - tiene))}; "
                         f"tiene: {', '.join(prefijo + s.numero for s in secciones)}")
    return [s for s in secciones if s.numero in pedidos]


def ingest_manual(ruta_manual: Path, nombre_fuente: str | None = None, patron: str = PATRON_EXPERIMENTO,
                  prefijo: str = "Exp", limite: int | None = None, solo: list[str] | None = None) -> tuple[Path, int]:
    """Devuelve (pagina de la fuente, numero de practicas escritas). Con `solo`, unicamente esos experimentos (los demas
    de la pagina no se tocan: la fusion es por codigo)."""
    secciones = dividir_experimentos(ruta_manual.read_text(encoding="utf-8"), patron)
    if not secciones:
        raise ValueError(f"No se detectó ningún experimento en {ruta_manual}; revisa los encabezados o usa --patron")
    if solo:
        secciones = seleccionar(secciones, solo, prefijo)
    secciones = secciones[:limite] if limite else secciones

    repetidos = codigos_repetidos(secciones, prefijo)
    if repetidos:
        raise ValueError(_mensaje_repetidos(repetidos))

    extracciones = [extraer_practica(s, ruta_manual.as_posix(), prefijo) for s in secciones]
    practicas = [p for _, p in extracciones]
    destino = escribir_fuente(nombre_fuente or _slug(ruta_manual.stem), practicas, ruta_manual.as_posix(), extracciones[0][0])
    vault.anotar_log(f"/ingest {destino.stem}", [
        f"{len(practicas)} prácticas extraídas de {ruta_manual.as_posix()} ({', '.join(p.codigo for p in practicas)})",
        "reindexar: python src/correlate.py --indexar",
    ])
    return destino, len(practicas)


if __name__ == "__main__":
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Extrae los experimentos de un manual de banco a `practicas:` de wiki/fuentes/.")
    parser.add_argument("manual", type=Path, help="manual en Markdown (normalmente en raw/manuales-laboratorio/)")
    parser.add_argument("--fuente", help="nombre de la página de wiki/fuentes/ (por defecto, el nombre del archivo)")
    parser.add_argument("--patron", default=PATRON_EXPERIMENTO, help="regex de los encabezados de experimento; el grupo 1 es el número")
    parser.add_argument("--prefijo", default="Exp", help="prefijo del código de práctica (Exp -> Exp13)")
    parser.add_argument("--limite", type=int, help="procesa solo los N primeros experimentos")
    parser.add_argument("--solo", nargs="+", metavar="EXP",
                        help="procesa solo esos experimentos (por código, Exp3, o por número, 3): los que cambiaron en el manual; el resto de la página no se toca")
    parser.add_argument("--solo-dividir", action="store_true", help="lista los experimentos detectados, sin LLM")
    args = parser.parse_args()
    try:
        if args.solo_dividir:
            secciones = dividir_experimentos(args.manual.read_text(encoding="utf-8"), args.patron)
            for s in secciones:
                print(f"  {args.prefijo}{s.numero:6s} {len(s.texto):6d} car.  [{s.capitulo or '-'}]  {s.encabezado}")
            print(f"{len(secciones)} experimentos detectados")
            repetidos = codigos_repetidos(secciones, args.prefijo)
            if repetidos:
                print(f"AVISO: {_mensaje_repetidos(repetidos)}")
        else:
            destino, n = ingest_manual(args.manual, args.fuente, args.patron, args.prefijo, args.limite, args.solo)
            print(f"{n} prácticas escritas en {destino}. Ahora corre: python src/correlate.py --indexar")
    except (ValueError, FileNotFoundError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)
