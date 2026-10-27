"""Esquema y cronograma DETERMINISTA del planeador (sin LLM).

El cronograma -- que RA se ve en que semana -- lo calcula codigo, no un LLM: el LLM
solo redacta el texto de cada semana (planeador.py) y de cada sesion (temario.py).

Reglas (ver CLAUDE.md, "Capa de generacion"):
    horas_sesion   = 4 si had_totales / 14 >= 3, si no 2   # had_totales YA incluye las
                     horas practicas del modulo -- no se suma hp_totales aparte, o se
                     contarian dos veces. hp_totales sigue siendo la senal que deriva
                     tipo_abordaje y alimenta score_RA (ver correlate.py), solo no entra
                     aqui.
    semanas_examen = {5, 10, 14}          # aplicacion practica, Student Outcomes ABET
    las 11 semanas de clase restantes se reparten entre los RA, proporcional a
    `horas`, por metodo de mayor resto (la suma da exacto). Los RA se ven en orden.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from schema_extraccion import Asignatura, ResultadoAprendizajeModulo

SEMANAS_TOTALES = 14
SEMANAS_EXAMEN = (5, 10, 14)
HORAS_SEMANALES_PARA_SESION_LARGA = 3

# Los minutos de una sesion (TEMARIO) se reparten entre sus bloques de contenido en multiplos de CUANTO_MINUTOS, con
# un minimo de un cuanto por bloque (ver minutos_por_bloque()): el LLM solo da el peso relativo de cada bloque.
CUANTO_MINUTOS = 5


class TipoSemana(str, Enum):
    clase = "clase"
    examen = "examen"


class SemanaPlan(BaseModel):
    semana: int
    tipo: TipoSemana
    ra: str | None = None      # codigo del RA (solo en semanas de clase)
    tema: str | None = None    # lo redacta el LLM; el cronograma no lo decide


class Cronograma(BaseModel):
    asignatura: str
    horas_sesion: int
    semanas_examen: list[int]
    semanas: list[SemanaPlan]


class EstadoPlaneador(str, Enum):
    """Resultado de CORRELATE-PLANEADOR para un RA."""

    cubierto = "cubierto"
    revisar = "revisar"
    desviado = "desviado"


class TemasSemana(BaseModel):
    """Salida del LLM en PLANEADOR: un tema por cada semana de clase de un RA, en orden."""

    temas: list[str]


class JuicioPlaneador(BaseModel):
    """Salida del LLM en CORRELATE-PLANEADOR: ¿el texto de las semanas de un RA cumple ese RA?"""

    estado: EstadoPlaneador
    confianza: float
    semanas_con_problema: list[int]
    justificacion: str


def derivar_horas_sesion(asignatura: Asignatura) -> int:
    """had_totales YA incluye las horas practicas del modulo (no son columnas
    independientes que deban sumarse -- eso las contaria dos veces), asi que la duracion
    de la sesion sale solo de had_totales."""
    horas_por_semana = asignatura.had_totales / SEMANAS_TOTALES
    return 4 if horas_por_semana >= HORAS_SEMANALES_PARA_SESION_LARGA else 2


def repartir_semanas(horas: list[int], semanas: int) -> list[int]:
    """Metodo de mayor resto: proporcional a `horas`, la suma da exactamente `semanas`.
    Aritmetica entera (sin decimales), asi los empates se resuelven siempre igual:
    gana el RA que va antes."""
    total = sum(horas)
    if total <= 0:
        raise ValueError("los RA suman 0 horas: no se pueden repartir las semanas")
    reparto = [semanas * h // total for h in horas]
    restos = [semanas * h % total for h in horas]
    por_resto = sorted(range(len(horas)), key=lambda i: (-restos[i], i))
    for i in por_resto[: semanas - sum(reparto)]:
        reparto[i] += 1
    return reparto


def corte_evaluativo(semana: int) -> int:
    """1, 2 o 3: en que corte evaluativo cae la semana, segun SEMANAS_EXAMEN (5, 10, 14)."""
    for indice, examen in enumerate(SEMANAS_EXAMEN, start=1):
        if semana <= examen:
            return indice
    return len(SEMANAS_EXAMEN)


def horas_hti_semana(asignatura: Asignatura) -> int:
    """Horas de trabajo independiente por semana (hti_totales es del semestre), redondeadas."""
    return round(asignatura.hti_totales / SEMANAS_TOTALES)


def minutos_por_bloque(pesos: list[int], horas_sesion: int) -> list[int]:
    """Minutos de cada bloque de contenido de una sesion: multiplos de CUANTO_MINUTOS (5), al menos uno por bloque, y la suma
    da exactamente horas_sesion x 60. El LLM da solo el peso relativo de cada bloque; el reparto (mismo metodo de mayor resto
    que repartir_semanas) lo hace el codigo."""
    cuantos = horas_sesion * 60 // CUANTO_MINUTOS
    if not pesos or any(p <= 0 for p in pesos):
        raise ValueError("cada bloque necesita un peso mayor que 0")
    if len(pesos) > cuantos:
        raise ValueError(f"{len(pesos)} bloques no caben en {horas_sesion * 60} minutos (mínimo {CUANTO_MINUTOS} por bloque)")
    extra = repartir_semanas(pesos, cuantos - len(pesos))
    return [(1 + e) * CUANTO_MINUTOS for e in extra]


def construir_cronograma(asignatura: Asignatura, ras: list[ResultadoAprendizajeModulo]) -> Cronograma:
    if not ras:
        raise ValueError(f"{asignatura.codigo}: no hay RA cargados; no se genera un plan vacío")
    semanas_de_clase = SEMANAS_TOTALES - len(SEMANAS_EXAMEN)
    reparto = repartir_semanas([ra.horas for ra in ras], semanas_de_clase)
    sin_semanas = [ra.codigo for ra, n in zip(ras, reparto) if n == 0]
    if sin_semanas:
        raise ValueError(f"{asignatura.codigo}: con {len(ras)} RA y {semanas_de_clase} semanas de clase, "
                         f"{', '.join(sin_semanas)} recibiría 0 semanas; hay que decidir a mano")

    orden_de_clases = iter([ra.codigo for ra, n in zip(ras, reparto) for _ in range(n)])
    semanas = [
        SemanaPlan(semana=n, tipo=TipoSemana.examen) if n in SEMANAS_EXAMEN
        else SemanaPlan(semana=n, tipo=TipoSemana.clase, ra=next(orden_de_clases))
        for n in range(1, SEMANAS_TOTALES + 1)
    ]
    return Cronograma(
        asignatura=asignatura.codigo,
        horas_sesion=derivar_horas_sesion(asignatura),
        semanas_examen=list(SEMANAS_EXAMEN),
        semanas=semanas,
    )
