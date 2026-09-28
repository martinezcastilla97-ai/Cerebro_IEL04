"""CORRELATE-PLANEADOR -- ¿el texto del planeador cumple el RA que le tocaba a cada semana?

Audita el TEXTO (los temas), no el cronograma: el cronograma no se reabre. Un juez
LLM compara, RA por RA, los temas de sus semanas contra el enunciado, los criterios
y el contenido conceptual del RA, y escribe `planeador_*` en la pagina del RA:
planeador_estado (cubierto | revisar | desviado), planeador_confianza, planeador_semanas,
planeador_semanas_con_problema, planeador_justificacion y planeador_fecha.
La vista correlaciones/matriz-ra-planeador.md los lee en vivo.

Uso (desde la raiz del vault):
    python src/correlate_planeador.py ABC01
    python src/correlate_planeador.py --all
"""

from __future__ import annotations

import argparse
import sys

import vault
from schema_planeador import JuicioPlaneador


def auditar_planeador(codigo: str) -> list[str]:
    """Audita el planeador de una asignatura. Devuelve los codigos de RA auditados."""
    ruta = vault.PLANEADOR / f"{codigo}-planeador.md"
    if not ruta.exists():
        raise FileNotFoundError(f"No hay planeador de {codigo}: corre `python src/planeador.py {codigo}` primero")
    fm_plan, _ = vault.leer_pagina(ruta)

    semanas_por_ra: dict[str, list[dict]] = {}
    for semana in fm_plan["semanas"]:
        if semana["tipo"] == "clase":
            semanas_por_ra.setdefault(semana["ra"], []).append(semana)
    if not any(s.get("tema") for filas in semanas_por_ra.values() for s in filas):
        raise ValueError(f"El planeador de {codigo} no tiene temas (¿se generó con --sin-llm?): no hay texto que auditar")

    sistema, plantilla = vault.cargar_prompt("prompt-correlate-planeador.md")
    auditados, resultados = [], []
    for codigo_ra, filas in semanas_por_ra.items():
        ruta_ra = vault.RESULTADOS / f"{codigo_ra}.md"
        fm_ra, cuerpo = vault.leer_pagina(ruta_ra)
        ra = vault.ra_desde_frontmatter(fm_ra)
        usuario = plantilla.format(
            codigo_ra=ra.codigo,
            enunciado=ra.enunciado,
            criterios="; ".join(ce.texto for ce in ra.criterios_evaluacion) or "(sin criterios)",
            conceptual="; ".join(ra.contenido.conceptual) or "(sin contenido conceptual)",
            semanas="\n".join(f"- Semana {s['semana']}: {s.get('tema') or '(sin tema)'}" for s in filas),
        )
        juicio = vault.pedir_estructurado(sistema, usuario, JuicioPlaneador)
        semanas_del_ra = [s["semana"] for s in filas]
        fm_ra.update({
            "planeador_estado": juicio.estado.value,
            "planeador_confianza": round(min(max(juicio.confianza, 0.0), 1.0), 4),
            "planeador_semanas": semanas_del_ra,
            "planeador_semanas_con_problema": [n for n in juicio.semanas_con_problema if n in semanas_del_ra],
            "planeador_justificacion": juicio.justificacion,
            "planeador_fecha": vault.hoy(),
        })
        vault.escribir_pagina(ruta_ra, fm_ra, cuerpo)
        auditados.append(codigo_ra)
        resultados.append(f"{codigo_ra}: {juicio.estado.value} — {juicio.justificacion}")
    vault.anotar_log(f"/correlate-planeador {codigo}", resultados)
    return auditados


def codigos_con_planeador() -> list[str]:
    return sorted(p.name.removesuffix("-planeador.md") for p in vault.PLANEADOR.glob("*-planeador.md"))


if __name__ == "__main__":
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Audita el texto del planeador contra los RA.")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("codigo", nargs="?", help="código de la asignatura")
    grupo.add_argument("--all", action="store_true", help="todos los planeadores de generacion/planeador/")
    args = parser.parse_args()
    errores = []
    for codigo in codigos_con_planeador() if args.all else [args.codigo]:
        try:
            print(f"{codigo}: {len(auditar_planeador(codigo))} RA auditados")
        except (FileNotFoundError, ValueError) as error:
            errores.append(f"{codigo}: {error}")
    for error in errores:
        print(f"ERROR: {error}")
    sys.exit(1 if errores else 0)
