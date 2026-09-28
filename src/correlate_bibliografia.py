"""CORRELATE-BIBLIOGRAFIA -- ¿el temario necesita una fuente que no esta cargada?

Corre en dos vias, por costo:
    1. Escanea el marcador `[FUENTE NO CARGADA EN raw/]` que TEMARIO deja en linea (gratis).
       Si lo encuentra: `vacio_detectado`, y las lineas marcadas quedan en `bibliografia_faltantes`.
    2. Solo si no hay marcador, un juez LLM de respaldo compara la profundidad de lo escrito
       contra las fuentes cargadas del RA (`bibliografia` de la pagina del RA). Si el RA no
       tiene fuentes cargadas, `revisar` sin gastar una llamada.

Escribe en el frontmatter del propio temario: bibliografia_estado (cubierta | revisar |
vacio_detectado), bibliografia_via (marcador | juez | sin_bibliografia),
bibliografia_justificacion, bibliografia_faltantes y bibliografia_fecha. La vista
correlaciones/matriz-temario-bibliografia.md los lee en vivo.

Uso (desde la raiz del vault):
    python src/correlate_bibliografia.py ABC01
    python src/correlate_bibliografia.py --all
"""

from __future__ import annotations

import argparse
import sys
from enum import Enum
from pathlib import Path

import vault
from pydantic import BaseModel
from temario import MARCADOR, fuentes_del_ra


class EstadoBibliografia(str, Enum):
    cubierta = "cubierta"
    revisar = "revisar"
    vacio_detectado = "vacio_detectado"


class JuicioBibliografia(BaseModel):
    """Salida del LLM de respaldo: ¿las fuentes cargadas sostienen lo que dice el temario?"""

    estado: EstadoBibliografia
    justificacion: str


def auditar_temario(ruta: Path) -> tuple[str, str]:
    """Audita un temario y escribe el resultado en su frontmatter. Devuelve (estado, via)."""
    fm, cuerpo = vault.leer_pagina(ruta)
    faltantes = [" ".join(linea.split())[:200] for linea in cuerpo.splitlines() if MARCADOR in linea]

    if faltantes:
        estado, via = EstadoBibliografia.vacio_detectado, "marcador"
        justificacion = f"{len(faltantes)} cita(s) marcada(s) como fuente no cargada"
    else:
        codigo_ra = vault.enlace(fm.get("resultado_aprendizaje"))
        fm_ra, _ = vault.leer_pagina(vault.RESULTADOS / f"{codigo_ra}.md")
        fuentes = fuentes_del_ra(fm_ra)
        if not fuentes:
            estado, via = EstadoBibliografia.revisar, "sin_bibliografia"
            justificacion = "el RA no tiene fuentes cargadas enlazadas en `bibliografia`; no hay con qué contrastar el temario"
        else:
            sistema, plantilla = vault.cargar_prompt("prompt-correlate-bibliografia.md")
            usuario = plantilla.format(
                codigo_ra=codigo_ra,
                enunciado=fm_ra.get("enunciado"),
                fuentes="\n".join(f"- {nombre}: {resumen}" for nombre, resumen in fuentes),
                semana=fm.get("semana"),
                temario=cuerpo.strip(),
            )
            juicio = vault.pedir_estructurado(sistema, usuario, JuicioBibliografia)
            estado, via, justificacion = juicio.estado, "juez", juicio.justificacion

    fm.update({
        "bibliografia_estado": estado.value,
        "bibliografia_via": via,
        "bibliografia_justificacion": justificacion,
        "bibliografia_faltantes": faltantes,
        "bibliografia_fecha": vault.hoy(),
    })
    vault.escribir_pagina(ruta, fm, cuerpo)
    return estado.value, via


def auditar_temarios(codigo: str | None = None) -> list[tuple[str, str, str]]:
    """Audita los temarios de una asignatura (o todos). Devuelve (temario, estado, via)."""
    patron = f"{codigo}-semana*.md" if codigo else "*-semana*.md"
    resultados = []
    for ruta in sorted(vault.TEMARIOS.glob(patron)):
        estado, via = auditar_temario(ruta)
        resultados.append((ruta.stem, estado, via))
    if resultados:
        vault.anotar_log(f"/correlate-bibliografia {codigo or 'todos'}", [f"{n}: {e} ({v})" for n, e, v in resultados])
    return resultados


if __name__ == "__main__":
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Audita si los temarios se sostienen con las fuentes cargadas.")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("codigo", nargs="?", help="código de la asignatura")
    grupo.add_argument("--all", action="store_true", help="todos los temarios de generacion/temarios/")
    args = parser.parse_args()
    resultados = auditar_temarios(None if args.all else args.codigo)
    for nombre, estado, via in resultados:
        print(f"  {nombre:24s} {estado:16s} ({via})")
    if not resultados:
        print("No hay temarios que auditar.")
        sys.exit(1)
