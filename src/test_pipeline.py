"""Prueba de mesa de los esquemas y de la logica de decision de /correlate.

Usa datos INVENTADOS (asignaturas TEO01 y TPR01, practicas Exp1..Exp5): no
representa ningun curriculo ni manual real.

No hay OPENAI_API_KEY ni lancedb en este entorno, asi que Recall y Judge se
simulan con valores fijos -- pero todo lo demas corre como CODIGO DE VERDAD
contra schema_extraccion.py, schema_correlacion.py y calcular_score_ra de
correlate.py. Es una prueba de la logica y del esquema, no una integracion en
vivo con un LLM externo. La logica propia de correlate.py sobre wiki/fuentes/
se prueba en test_correlate_fuentes.py.

Uso (desde src/):  python test_pipeline.py
"""

from pydantic import ValidationError

from correlate import UMBRAL_ACEPTAR, UMBRAL_REVISAR, calcular_score_ra
from schema_correlacion import EstadoCorrelacion, JuicioCorrelacion, RelacionPropuesta
from schema_extraccion import (
    Asignatura,
    CategoriaAccionCE,
    CategoriaLibro,
    ContenidoAprendizaje,
    CriterioEvaluacion,
    Libro,
    Practica,
    ResultadoAprendizajeModulo,
    ResultadoAprendizajePrograma,
    TipoAbordaje,
)


def ce(codigo: str, texto: str, categoria: CategoriaAccionCE, confianza: float) -> CriterioEvaluacion:
    return CriterioEvaluacion(codigo=codigo, texto=texto, categoria_accion=categoria, confianza=confianza)


def practica(codigo: str, nombre: str, pagina: int, base: str) -> Practica:
    """`equipos` se omite a proposito: es opcional."""
    return Practica(
        codigo=codigo, nombre_original=nombre, pagina_inicio=pagina,
        proposito=["Proposito de ejemplo."], principio_resumen=f"Resumen de {codigo}.",
        terminos_clave=[f"{base} a", f"{base} b", f"{base} c", f"{base} d"],
    )


def ra_teorico_practico(codigo: str, horas: int) -> ResultadoAprendizajeModulo:
    """RA de TPR01 con dos CE de manipulacion fisica (la senal que abre el gate)."""
    return ResultadoAprendizajeModulo(
        codigo=codigo, enunciado=f"Enunciado de ejemplo de {codigo}.", horas=horas,
        tipo_abordaje=TipoAbordaje.teorico_practica,
        criterios_evaluacion=[
            ce("CE1", "Identificar conceptos.", CategoriaAccionCE.cognitiva_conceptual, 0.8),
            ce("CE2", "Realizar mediciones en el circuito.", CategoriaAccionCE.manipulacion_fisica, 0.95),
            ce("CE3", "Realizar mediciones en el circuito serie o paralelo.", CategoriaAccionCE.manipulacion_fisica, 0.93),
        ],
        contenido=ContenidoAprendizaje(conceptual=[f"Tema de {codigo}"]),
    )


print("=" * 70)
print("1. TEO01 -- asignatura teorica (HP=0)")
print("=" * 70)

teo01 = Asignatura(
    codigo="TEO01", nombre="Asignatura teorica de ejemplo", programa="Programa de ejemplo",
    tipo_modulo="TRANSVERSAL", had_totales=23, hp_totales=0, hti_totales=52, creditos=2,
    tipo_abordaje=TipoAbordaje.teorica, docente_autor="Docente de ejemplo", fecha_aprobacion="2020-01-01",
    estrategia_practica_marcada=False, recurso_laboratorio_marcado=False,
)
print("Asignatura valida OK:", teo01.codigo, "-", teo01.tipo_abordaje.value)

teo01_ra1 = ResultadoAprendizajeModulo(
    codigo="TEO01-RA1", enunciado="Enunciado de ejemplo de un RA teorico.", horas=18,
    tipo_abordaje=TipoAbordaje.teorica,
    criterios_evaluacion=[
        ce("CE1", "Reconocer conceptos.", CategoriaAccionCE.cognitiva_conceptual, 0.85),
        ce("CE2", "Interpretar conceptos.", CategoriaAccionCE.cognitiva_conceptual, 0.85),
        ce("CE3", "Identificar elementos.", CategoriaAccionCE.cognitiva_conceptual, 0.8),
        ce("CE4", "Aplicar una ley.", CategoriaAccionCE.cognitiva_aplicada, 0.75),
    ],
    contenido=ContenidoAprendizaje(
        conceptual=["Tema A", "Tema B"],
        procedimental=["Calculo con la ley aplicada"],
        actitudinal=["Cuidado de los equipos"],
    ),
)
print("RA valido OK:", teo01_ra1.codigo)

score_teo = calcular_score_ra(teo01_ra1, teo01)
print(f"score_ra(TEO01-RA1) = {score_teo:.3f}  (esperado < 0.40, gate cierra)")
assert score_teo < 0.40, "el gate deberia cerrar para una asignatura teorica"

print()
print("=" * 70)
print("2. TPR01 -- asignatura teorico-practica (HP=26)")
print("=" * 70)

tpr01 = Asignatura(
    codigo="TPR01", nombre="Asignatura teorico-practica de ejemplo", programa="Programa de ejemplo",
    tipo_modulo="TRANSVERSAL", had_totales=26, hp_totales=26, hti_totales=65, creditos=2,
    tipo_abordaje=TipoAbordaje.teorico_practica, docente_autor="Docente de ejemplo", fecha_aprobacion="2020-01-01",
    estrategia_practica_marcada=True, recurso_laboratorio_marcado=True,
)
print("Asignatura valida OK:", tpr01.codigo, "-", tpr01.tipo_abordaje.value)

tpr01_ra1 = ra_teorico_practico("TPR01-RA1", 29)
print("RA valido OK:", tpr01_ra1.codigo)

libro = Libro(autor="Apellido, Nombre", titulo="Titulo del libro", editorial="Editorial de ejemplo", categoria=CategoriaLibro.basica)
print("Libro valido OK:", libro.titulo)

score_ra1 = calcular_score_ra(tpr01_ra1, tpr01)
print(f"score_ra(TPR01-RA1) = {score_ra1:.3f}  (esperado >= 0.70, gate abre)")
assert score_ra1 >= 0.70, "el gate deberia abrir para una asignatura teorico-practica con CE de manipulacion fisica"

print()
print("=" * 70)
print("3. Colision de codigos RA-PROG vs RA de modulo (validador de patron)")
print("=" * 70)

ra_prog = ResultadoAprendizajePrograma(codigo="RA-PROG-1", enunciado="Enunciado de ejemplo de un RA de programa.")
print("RA-PROG valido OK:", ra_prog.codigo)

try:
    ResultadoAprendizajePrograma(codigo="RA1", enunciado="intento de colision")
    print("BUG: 'RA1' no deberia pasar el patron ^RA-PROG-\\d+$")
except ValidationError:
    print("Rechazado correctamente: 'RA1' no calza con el patron RA-PROG-{n} -- la regla de colision SI se aplica en codigo.")

print()
print("=" * 70)
print("4. Consistencia hp_totales <-> tipo_abordaje, y horas/creditos coherentes (model_validator)")
print("=" * 70)


def _asignatura_de_prueba(**over) -> dict:
    base = dict(codigo="TESTX", nombre="Caso de prueba", programa="Test",
                had_totales=10, hp_totales=0, hti_totales=10, creditos=1,
                tipo_abordaje=TipoAbordaje.teorica,
                estrategia_practica_marcada=False, recurso_laboratorio_marcado=False)
    base.update(over)
    return base


try:
    Asignatura(**_asignatura_de_prueba(had_totales=10, hp_totales=20, tipo_abordaje=TipoAbordaje.teorica,
                                       estrategia_practica_marcada=True, recurso_laboratorio_marcado=True))
    print("BUG: debio rechazar tipo_abordaje='teorica' con hp_totales=20")
except ValidationError as e:
    print("Rechazado correctamente:", str(e).splitlines()[-1])

# hp_totales no puede superar had_totales: had_totales YA incluye las horas practicas,
# asi que hp_totales > had_totales solo puede venir de un error de extraccion (p. ej.
# columnas confundidas al reconstruir una tabla de creditos rota del PDF).
try:
    Asignatura(**_asignatura_de_prueba(had_totales=20, hp_totales=40, tipo_abordaje=TipoAbordaje.teorico_practica,
                                       estrategia_practica_marcada=True, recurso_laboratorio_marcado=True))
    print("BUG: debio rechazar hp_totales=40 > had_totales=20")
except ValidationError as e:
    assert "hp_totales" in str(e) and "had_totales" in str(e)
    print("Rechazado correctamente (HAD=20 < HP=40):", str(e).splitlines()[-1])

# hp_totales == had_totales (todas las horas presenciales son practicas): valido, es el limite.
igualdad = Asignatura(**_asignatura_de_prueba(had_totales=20, hp_totales=20, tipo_abordaje=TipoAbordaje.teorico_practica,
                                              estrategia_practica_marcada=True, recurso_laboratorio_marcado=True))
print("Asignatura valida OK (hp_totales == had_totales, limite permitido):", igualdad.codigo)

# Ningun campo de horas o creditos puede ser negativo.
for campo in ("had_totales", "hp_totales", "hti_totales", "creditos"):
    try:
        Asignatura(**_asignatura_de_prueba(**{campo: -1}))
        print(f"BUG: debio rechazar {campo}=-1")
    except ValidationError as e:
        assert campo in str(e)
        print(f"Rechazado correctamente ({campo}=-1):", str(e).splitlines()[-1])

print()
print("=" * 70)
print("5. Practicas de un manual de ejemplo (Exp1, Exp2, Exp3)")
print("=" * 70)

exp1 = practica("Exp1", "Practica de ejemplo A", 51, "alfa")
exp2 = practica("Exp2", "Practica de ejemplo B", 54, "beta")
exp3 = practica("Exp3", "Practica de ejemplo C", 58, "gamma")
for p in (exp1, exp2, exp3):
    print("Practica valida OK:", p.codigo, "-", p.nombre_original)

print()
print("=" * 70)
print("6. JUDGE simulado: TPR01-RA1 contra los 3 candidatos del mismo manual")
print("=" * 70)
print("(Los juicios son valores fijos; no hay llamada a ninguna API)")
print()


def decidir(ra_codigo: str, score_ra: float, juicios: list[JuicioCorrelacion]) -> RelacionPropuesta:
    """Misma logica de decision que correlate.correlacionar_ra(): el mejor candidato se
    elige SOLO entre los que el juez dice que coinciden -- confianza_semantica mide cuanto
    satisface el RA, no la seguridad del veredicto, asi que un 'coincide=False' con
    confianza alta nunca debe ganar (ver src/prompts/prompt-correlate.md)."""
    coincidentes = [j for j in juicios if j.coincide]
    if not coincidentes:
        return RelacionPropuesta(ra_codigo=ra_codigo, practica_codigo=None, score_ra=score_ra,
                                 candidatos_alternativos=[j.practica_codigo for j in juicios],
                                 estado=EstadoCorrelacion.sin_candidato)
    mejor = max(coincidentes, key=lambda j: j.confianza_semantica)
    confianza_final = score_ra * mejor.confianza_semantica
    if confianza_final >= UMBRAL_ACEPTAR:
        estado = EstadoCorrelacion.aceptado
    elif confianza_final >= UMBRAL_REVISAR:
        estado = EstadoCorrelacion.pendiente_revision
    else:
        estado = EstadoCorrelacion.sin_candidato
    return RelacionPropuesta(
        ra_codigo=ra_codigo,
        practica_codigo=mejor.practica_codigo if estado != EstadoCorrelacion.sin_candidato else None,
        score_ra=score_ra,
        confianza_semantica=mejor.confianza_semantica,
        confianza_final=confianza_final,
        candidatos_alternativos=[j.practica_codigo for j in juicios if j is not mejor],
        estado=estado,
    )


def juicio(ra: str, practica_codigo: str, confianza: float, coincide: bool = False, texto: str = "Juicio fijo de ejemplo.") -> JuicioCorrelacion:
    return JuicioCorrelacion(ra_codigo=ra, practica_codigo=practica_codigo, coincide=coincide, justificacion=texto, confianza_semantica=confianza)


juicios = [
    juicio("TPR01-RA1", "Exp1", 0.93, coincide=True, texto="Coincidencia directa con CE2 y CE3."),
    juicio("TPR01-RA1", "Exp2", 0.30),
    juicio("TPR01-RA1", "Exp3", 0.48),
]
for j in juicios:
    print(f"  {j.practica_codigo}: coincide={j.coincide}  confianza_semantica={j.confianza_semantica:.2f}  -- {j.justificacion}")

relacion_ra1 = decidir("TPR01-RA1", score_ra1, juicios)
print()
print(f"confianza_final = {score_ra1:.3f} x {max(juicios, key=lambda j: j.confianza_semantica).confianza_semantica:.2f} = {relacion_ra1.confianza_final:.3f}")
print(f"RelacionPropuesta valida OK -> estado = {relacion_ra1.estado.value}, practica = {relacion_ra1.practica_codigo}")
assert relacion_ra1.estado == EstadoCorrelacion.aceptado
assert relacion_ra1.practica_codigo == "Exp1"

print()
print("=" * 70)
print("7-9. Extendiendo a TPR01-RA2, RA3 y RA4 con dos practicas mas (Exp4, Exp5)")
print("=" * 70)
print("Ninguna practica es un buen candidato para RA2 y RA3: eso tambien es un resultado, no un error.")
print()

exp4 = practica("Exp4", "Practica de ejemplo D", 49, "delta")
exp5 = practica("Exp5", "Practica de ejemplo E", 62, "epsilon")
for p in (exp4, exp5):
    print("Practica valida OK:", p.codigo, "-", p.nombre_original)

resultados_finales = [relacion_ra1]

for codigo, horas, juicios_ra, etiqueta in [
    # El mejor candidato de cada RA SI coincide (aunque con confianza media): un candidato
    # con 'coincide=False' -- por alta que sea su confianza_semantica -- nunca podria ganar.
    ("TPR01-RA2", 29, [juicio("TPR01-RA2", "Exp1", 0.35), juicio("TPR01-RA2", "Exp2", 0.58, coincide=True), juicio("TPR01-RA2", "Exp3", 0.15), juicio("TPR01-RA2", "Exp5", 0.25)], "A"),
    ("TPR01-RA3", 29, [juicio("TPR01-RA3", "Exp1", 0.38), juicio("TPR01-RA3", "Exp3", 0.20), juicio("TPR01-RA3", "Exp5", 0.42, coincide=True)], "B"),
    ("TPR01-RA4", 30, [juicio("TPR01-RA4", "Exp4", 0.55), juicio("TPR01-RA4", "Exp3", 0.68, coincide=True), juicio("TPR01-RA4", "Exp5", 0.20)], "C"),
]:
    ra = ra_teorico_practico(codigo, horas)
    score_ra = calcular_score_ra(ra, tpr01)
    relacion = decidir(ra.codigo, score_ra, juicios_ra)
    resultados_finales.append(relacion)
    print(f"\n{ra.codigo} (tema {etiqueta}) -- score_ra={score_ra:.3f}")
    for j in juicios_ra:
        print(f"  {j.practica_codigo}: confianza_semantica={j.confianza_semantica:.2f} -- {j.justificacion}")
    print(f"  => confianza_final={relacion.confianza_final:.3f}  estado={relacion.estado.value}  mejor_candidato={relacion.practica_codigo}")

print()
print("=" * 70)
print("Resumen -- los 4 RA de TPR01")
print("=" * 70)
for r in resultados_finales:
    print(f"  {r.ra_codigo:12s} -> {r.estado.value:20s} practica={str(r.practica_codigo):8s} confianza_final={r.confianza_final:.3f}")

assert [r.estado for r in resultados_finales] == [
    EstadoCorrelacion.aceptado, EstadoCorrelacion.pendiente_revision,
    EstadoCorrelacion.pendiente_revision, EstadoCorrelacion.pendiente_revision,
]
print()
print("TODO OK -- ningun RA salio 'aceptado' sin merecerlo ni quedo forzado;")
print("RA1 cierra solo, RA2/RA3/RA4 quedan honestamente en pendiente_revision.")
print("=" * 70)

print()
print("=" * 70)
print("10. Resolucion humana de RA2/RA3/RA4 (decision del docente, no de /correlate)")
print("=" * 70)

decisiones_docente = [
    RelacionPropuesta(
        ra_codigo="TPR01-RA4", practica_codigo="Exp3", score_ra=0.985,
        confianza_semantica=0.68, confianza_final=0.670,
        candidatos_alternativos=["Exp4", "Exp5"],
        estado=EstadoCorrelacion.aceptado,
        revisado_por_docente=True,
        nota_docente="Nota de ejemplo: el alcance de la practica es mas estrecho que el enunciado del RA, "
                      "pero se acepta como la aplicacion practica de referencia.",
    ),
    RelacionPropuesta(
        ra_codigo="TPR01-RA2", practica_codigo=None, score_ra=0.985,
        candidatos_alternativos=["Exp2"],
        estado=EstadoCorrelacion.sin_candidato,
        revisado_por_docente=True,
        nota_docente="Nota de ejemplo: el mejor candidato tiene otro enfoque; se descarta como practica "
                      "principal y queda pendiente cargar una practica dedicada.",
    ),
    RelacionPropuesta(
        ra_codigo="TPR01-RA3", practica_codigo=None, score_ra=0.985,
        candidatos_alternativos=["Exp5"],
        estado=EstadoCorrelacion.sin_candidato,
        revisado_por_docente=True,
        nota_docente="Nota de ejemplo: ninguna practica del manual cubre el tema; pendiente cargar otro banco.",
    ),
]
for d in decisiones_docente:
    print(f"  {d.ra_codigo}: estado={d.estado.value}  practica={d.practica_codigo}  revisado_por_docente={d.revisado_por_docente}")
    print(f"    nota: {d.nota_docente}")

assert all(d.revisado_por_docente for d in decisiones_docente)
assert decisiones_docente[0].estado == EstadoCorrelacion.aceptado   # RA4
assert decisiones_docente[1].estado == EstadoCorrelacion.sin_candidato  # RA2
assert decisiones_docente[2].estado == EstadoCorrelacion.sin_candidato  # RA3
print()
print("RelacionPropuesta con revisado_por_docente/nota_docente valida OK para los 3 casos.")
print("=" * 70)
