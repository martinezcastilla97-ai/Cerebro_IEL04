"""PLANEADOR -- programa de estudios de una asignatura (14 semanas).

El cronograma lo calcula codigo (schema_planeador.py); el LLM solo redacta el tema
de cada semana de clase, RA por RA. Lee wiki/ y escribe generacion/planeador/{codigo}-planeador.md.

Uso (desde la raiz del vault):
    python src/planeador.py ABC01               # cronograma + temas redactados por el LLM
    python src/planeador.py ABC01 --sin-llm     # solo el cronograma determinista (sin OPENAI_API_KEY)
    python src/planeador.py ABC01 --forzar      # sobrescribe un planeador ya existente
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import vault
from schema_extraccion import Asignatura, ResultadoAprendizajeModulo
from schema_planeador import Cronograma, TemasSemana, TipoSemana, construir_cronograma


def _lista(elementos: list[str], vacio: str) -> str:
    return "; ".join(elementos) if elementos else vacio


def redactar_temas(asignatura: Asignatura, ra: ResultadoAprendizajeModulo, n_semanas: int) -> list[str]:
    """Un tema por cada semana de clase del RA (el LLM reparte el contenido del RA entre ellas)."""
    sistema, plantilla = vault.cargar_prompt("prompt-planeador.md")
    usuario = plantilla.format(
        codigo_asignatura=asignatura.codigo,
        nombre_asignatura=asignatura.nombre,
        tipo_abordaje=asignatura.tipo_abordaje.value,
        codigo_ra=ra.codigo,
        enunciado=ra.enunciado,
        criterios=_lista([ce.texto for ce in ra.criterios_evaluacion], "(sin criterios)"),
        conceptual=_lista(ra.contenido.conceptual, "(sin contenido conceptual)"),
        procedimental=_lista(ra.contenido.procedimental, "(sin contenido procedimental)"),
        actitudinal=_lista(ra.contenido.actitudinal, "(sin contenido actitudinal)"),
        n_semanas=n_semanas,
    )
    temas = vault.pedir_estructurado(sistema, usuario, TemasSemana).temas
    if len(temas) != n_semanas:
        raise ValueError(f"{ra.codigo}: el LLM devolvió {len(temas)} temas y se pedían {n_semanas}")
    return [t.strip() for t in temas]


def renderizar_planeador(nombre_pagina: str, asignatura: Asignatura, cronograma: Cronograma) -> tuple[dict, str]:
    """(frontmatter, cuerpo) del planeador. Los temas viven en el frontmatter (`semanas`)
    para que CORRELATE-PLANEADOR y TEMARIO los lean sin interpretar una tabla."""
    hoy = vault.hoy()
    frontmatter = {
        "tipo": "planeador",
        "asignatura": f"[[{nombre_pagina}]]",
        "horas_sesion": cronograma.horas_sesion,
        "semanas_examen": cronograma.semanas_examen,
        "semanas": [
            {"semana": s.semana, "tipo": s.tipo.value, "ra": s.ra, "tema": s.tema} for s in cronograma.semanas
        ],
        "fecha_creacion": hoy,
        "fecha_actualizacion": hoy,
    }
    filas = []
    for s in cronograma.semanas:
        if s.tipo == TipoSemana.examen:
            filas.append(f"| {s.semana} | examen | — | Evaluación de aplicación práctica |")
        else:
            filas.append(f"| {s.semana} | clase | [[{s.ra}]] | {s.tema or ''} |")
    cuerpo = (
        f"\n\n# Planeador — {asignatura.codigo} {asignatura.nombre}\n\n"
        f"**Sesión semanal:** {cronograma.horas_sesion} h · "
        f"**Semanas de examen:** {', '.join(str(n) for n in cronograma.semanas_examen)}\n\n"
        "## Cronograma\n\n| Semana | Tipo | RA | Tema |\n|---|---|---|---|\n" + "\n".join(filas) + "\n"
    )
    return frontmatter, cuerpo


def generar_planeador(codigo: str, sin_llm: bool = False, forzar: bool = False) -> Path:
    nombre_pagina, asignatura, fm_asignatura = vault.localizar_asignatura(codigo)
    destino = vault.PLANEADOR / f"{codigo}-planeador.md"
    if destino.exists() and not forzar:
        raise FileExistsError(f"{destino} ya existe; usa --forzar para sobrescribirlo (perderías las ediciones a mano)")

    ras = vault.cargar_ras_de(fm_asignatura)
    cronograma = construir_cronograma(asignatura, ras)   # sin RA cargados: error, no un plan vacío

    if not sin_llm:
        for ra in ras:
            semanas_del_ra = [s for s in cronograma.semanas if s.ra == ra.codigo]
            for semana, tema in zip(semanas_del_ra, redactar_temas(asignatura, ra, len(semanas_del_ra))):
                semana.tema = tema

    frontmatter, cuerpo = renderizar_planeador(nombre_pagina, asignatura, cronograma)
    vault.escribir_pagina(destino, frontmatter, cuerpo)
    vault.anotar_log(f"/planeador {codigo}", [
        f"cronograma de 14 semanas, sesión de {cronograma.horas_sesion} h, {len(ras)} RA",
        "solo cronograma (sin LLM)" if sin_llm else "temas redactados por el LLM",
    ])
    return destino


if __name__ == "__main__":
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Genera el planeador (14 semanas) de una asignatura.")
    parser.add_argument("codigo", help="código de la asignatura (campo `codigo` de su página)")
    parser.add_argument("--sin-llm", action="store_true", help="solo el cronograma determinista")
    parser.add_argument("--forzar", action="store_true", help="sobrescribe un planeador ya existente")
    args = parser.parse_args()
    try:
        print(f"Planeador escrito en {generar_planeador(args.codigo, args.sin_llm, args.forzar)}")
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)
