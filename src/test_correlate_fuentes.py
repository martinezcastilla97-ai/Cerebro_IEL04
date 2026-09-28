"""Prueba de correlate.py contra wiki/fuentes/ (sin LLM y sin lancedb).

Arma un vault temporal con manuales de banco (etiqueta `equipo-laboratorio` y
`practicas` en el frontmatter), sustituye Recall y Judge por respuestas fijas y
comprueba lo que SI es logica propia de este modulo: descubrir las Practicas en
wiki/fuentes/, identificarlas por (fuente, codigo), decidir el estado, escribir
requiere_practica / practica_experimentos en el frontmatter del RA y respetar
las decisiones del docente (correlacion_revisado_por_docente: true).

Los datos son inventados a proposito (PRU01, banco-uno...): no toca ni imita
ningun curriculo ni manual real.

Uso (desde src/):  python test_correlate_fuentes.py
"""

import os
import tempfile
from pathlib import Path

import yaml

import _fixtures
import correlate
import lint
import vault
from schema_correlacion import EstadoCorrelacion, JuicioCorrelacion, RelacionPropuesta

# Capturada ANTES de que ninguna prueba sustituya correlate.juzgar_correlacion (varias lo
# hacen con una funcion de prueba): probar_prompt_real_del_juez() necesita la funcion REAL.
_JUZGAR_CORRELACION_REAL = correlate.juzgar_correlacion
from schema_extraccion import (
    Asignatura,
    CategoriaAccionCE,
    ContenidoAprendizaje,
    CriterioEvaluacion,
    Practica,
    ResultadoAprendizajeModulo,
    TipoAbordaje,
)


def practica_yaml(codigo: str, nombre: str, minima: bool = False) -> str:
    """`minima=True` omite `equipos` y `capitulo`: muchos manuales no traen tabla de equipos."""
    return (
        f"  - codigo: {codigo}\n"
        f"    nombre_original: {nombre}\n"
        + ("" if minima else "    capitulo: Capitulo de prueba\n")
        + "    proposito: [uno]\n"
        f"    principio_resumen: Resumen de {codigo}.\n"
        + ("" if minima else "    equipos: []\n")
        + "    terminos_clave: [alfa, beta, gamma, delta]\n"
    )


def fuente(etiquetas: str, practicas: str = "") -> str:
    cabecera = f"---\ntipo: fuente\netiquetas: [{etiquetas}]\n"
    return cabecera + (f"practicas:\n{practicas}" if practicas else "") + "---\n\n# Pagina de prueba\n"


def armar_vault(raiz: Path) -> None:
    fuentes = raiz / "wiki" / "fuentes"
    fuentes.mkdir(parents=True)
    (raiz / "wiki" / "resultados-aprendizaje").mkdir(parents=True)
    # 'Exp1' existe en DOS manuales: la identidad es el par (fuente, codigo).
    (fuentes / "banco-uno.md").write_text(
        fuente("equipo-laboratorio, prueba", practica_yaml("Exp1", "Uno A") + practica_yaml("Exp2", "Uno B")), encoding="utf-8")
    (fuentes / "banco-dos.md").write_text(fuente("equipo-laboratorio", practica_yaml("Exp1", "Dos A", minima=True)), encoding="utf-8")
    (fuentes / "banco-vacio.md").write_text(fuente("equipo-laboratorio"), encoding="utf-8")   # sin 'practicas': no aporta
    (fuentes / "libro.md").write_text(fuente("libro", practica_yaml("Exp9", "No debe contar")), encoding="utf-8")  # no es banco
    (raiz / "wiki" / "resultados-aprendizaje" / "PRU01-RA1.md").write_text(
        "---\ntipo: resultado_aprendizaje\ncodigo: PRU01-RA1\nrequiere_practica: null\npractica_experimentos: []\n---\n\n"
        "# Cuerpo del RA\nTexto que no debe cambiar.\n", encoding="utf-8")
    (raiz / "wiki" / "log.md").write_text("# Log\n", encoding="utf-8")


def asignatura(hp: int) -> Asignatura:
    return Asignatura(
        codigo="PRU01", nombre="Prueba", programa="Programa de prueba",
        had_totales=max(10, hp), hp_totales=hp, hti_totales=10, creditos=1,  # had_totales ya incluye las HP: nunca puede ser menor
        tipo_abordaje=TipoAbordaje.teorico_practica if hp > 0 else TipoAbordaje.teorica,
        estrategia_practica_marcada=hp > 0, recurso_laboratorio_marcado=hp > 0,
    )


RA = ResultadoAprendizajeModulo(
    codigo="PRU01-RA1", enunciado="Enunciado de prueba.", horas=10, tipo_abordaje=TipoAbordaje.teorico_practica,
    criterios_evaluacion=[CriterioEvaluacion(codigo="CE1", texto="Medir algo.", categoria_accion=CategoriaAccionCE.manipulacion_fisica, confianza=0.95)],
    contenido=ContenidoAprendizaje(conceptual=["tema"]),
)


def probar() -> None:
    # 1. Descubrimiento: solo bancos con 'practicas'; ni el libro ni el banco vacio cuentan.
    pares = [(f, p.codigo) for f, p in correlate.listar_practicas()]
    assert pares == [("banco-dos", "Exp1"), ("banco-uno", "Exp1"), ("banco-uno", "Exp2")], pares
    print("1. listar_practicas: 3 practicas, solo de fuentes etiquetadas equipo-laboratorio -- OK")

    # 2. Identidad por (fuente, codigo): el mismo 'Exp1' en dos manuales no se confunde.
    assert correlate.cargar_practica("banco-dos", "Exp1").nombre_original == "Dos A"
    assert correlate.cargar_practica("banco-uno", "Exp1").nombre_original == "Uno A"
    # Una practica sin `equipos` ni `capitulo` es valida (campos opcionales); con ellos, se conservan.
    minima = correlate.cargar_practica("banco-dos", "Exp1")
    assert minima.equipos == [] and minima.capitulo is None
    assert correlate.cargar_practica("banco-uno", "Exp1").capitulo == "Capitulo de prueba"
    try:
        correlate.cargar_practica("banco-uno", "Exp9")
    except KeyError:
        pass
    else:
        raise AssertionError("Exp9 no existe en banco-uno y debio dar KeyError")
    print("2. cargar_practica: distingue Exp1 de banco-uno y de banco-dos; KeyError si no existe -- OK")

    # 3. Un codigo repetido dentro de UNA misma pagina es ambiguo: se rechaza.
    repetido = Path("wiki/fuentes/banco-repetido.md")
    repetido.write_text(fuente("equipo-laboratorio", practica_yaml("Exp1", "A") + practica_yaml("Exp1", "B")), encoding="utf-8")
    try:
        correlate.listar_practicas()
    except ValueError:
        pass
    else:
        raise AssertionError("un codigo repetido en la misma fuente debio dar ValueError")
    repetido.unlink()
    print("3. codigo repetido en una misma fuente: ValueError -- OK")

    # 4. Decision con candidatos de DOS manuales (Recall y Judge sustituidos por valores fijos).
    confianzas = {("banco-uno", "Exp1"): 0.30, ("banco-dos", "Exp1"): 0.93, ("banco-uno", "Exp2"): 0.48}
    correlate.recall_practicas_candidatas = lambda ra, k=3: list(confianzas)

    def juez(ra, practica, fuente_):
        return JuicioCorrelacion(
            ra_codigo=ra.codigo, practica_codigo=practica.codigo, coincide=(fuente_ == "banco-dos"),
            justificacion="fijo", confianza_semantica=confianzas[(fuente_, practica.codigo)])

    correlate.juzgar_correlacion = juez
    relacion = correlate.correlacionar_ra(RA, asignatura(hp=26))
    assert relacion.estado == EstadoCorrelacion.aceptado
    assert (relacion.fuente, relacion.practica_codigo) == ("banco-dos", "Exp1")
    assert relacion.candidatos_alternativos == ["banco-uno#Exp1", "banco-uno#Exp2"], relacion.candidatos_alternativos
    assert abs(relacion.confianza_final - 0.985 * 0.93) < 1e-9
    print(f"4. correlacionar_ra: aceptado -> {relacion.fuente} / {relacion.practica_codigo}, confianza_final={relacion.confianza_final:.3f} -- OK")

    # 5. Escritura en el frontmatter del RA, sin tocar su cuerpo.
    assert correlate.escribir_relacion(relacion) is True     # el RA no tiene el campo del docente: se actualiza
    texto = Path("wiki/resultados-aprendizaje/PRU01-RA1.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(texto.split("---", 2)[1])
    assert fm["requiere_practica"] == "[[banco-dos]]", fm["requiere_practica"]
    assert fm["practica_experimentos"] == ["Exp1"]
    assert fm["correlacion_estado"] == "aceptado"
    assert fm["correlacion_justificacion"] == "fijo"             # la razon del juez queda en el RA, para el docente que revise
    assert fm["correlacion_alternativas"] == ["[[banco-uno]] — Exp1", "[[banco-uno]] — Exp2"], fm["correlacion_alternativas"]
    assert "Texto que no debe cambiar." in texto
    assert "PRU01-RA1" in Path("wiki/log.md").read_text(encoding="utf-8")
    print("5. escribir_relacion: requiere_practica=[[banco-dos]], practica_experimentos=[Exp1], cuerpo intacto -- OK")

    # 6. Gate cerrado (asignatura teorica): ni siquiera se busca practica.
    def no_debe_llamarse(*args, **kwargs):
        raise AssertionError("con el gate cerrado no se debe buscar practica")

    correlate.recall_practicas_candidatas = no_debe_llamarse
    cerrada = correlate.correlacionar_ra(RA, asignatura(hp=0))
    assert cerrada.estado == EstadoCorrelacion.sin_candidato
    assert cerrada.practica_codigo is None and cerrada.fuente is None
    print("6. gate cerrado: sin_candidato, sin buscar practica -- OK")

    # 7. Una practica sin su fuente no se escribe (seria un enlace roto).
    try:
        correlate.escribir_relacion(
            RelacionPropuesta(ra_codigo="PRU01-RA1", practica_codigo="Exp1", score_ra=0.9, estado=EstadoCorrelacion.aceptado))
    except ValueError:
        pass
    else:
        raise AssertionError("practica_codigo sin fuente debio dar ValueError")
    print("7. practica sin fuente: ValueError -- OK")

    # 8. Decision del docente: un RA con correlacion_revisado_por_docente: true NO se reescribe.
    decidido = Path("wiki/resultados-aprendizaje/PRU01-RA2.md")
    decidido.write_text(
        "---\n"
        "tipo: resultado_aprendizaje\n"
        "codigo: PRU01-RA2\n"
        "requiere_practica: '[[banco-uno]]'   # lo decidio el docente\n"
        "practica_experimentos: [Exp2]\n"
        "correlacion_estado: aceptado\n"
        "correlacion_revisado_por_docente: true\n"
        "correlacion_nota_docente: Aceptado con nota.\n"
        "---\n\n# RA revisado\nNo se toca.\n", encoding="utf-8")
    antes = decidido.read_bytes()
    log_antes = Path("wiki/log.md").read_text(encoding="utf-8")
    propuesta = RelacionPropuesta(
        ra_codigo="PRU01-RA2", practica_codigo="Exp1", fuente="banco-dos", score_ra=0.985,
        confianza_semantica=0.93, confianza_final=0.916, estado=EstadoCorrelacion.pendiente_revision)
    assert correlate.escribir_relacion(propuesta) is False
    assert decidido.read_bytes() == antes, "el RA revisado por el docente no debe cambiar, ni siquiera de formato"
    nuevo_log = Path("wiki/log.md").read_text(encoding="utf-8")[len(log_antes):]
    assert "/correlate PRU01-RA2 (omitido)" in nuevo_log, nuevo_log
    assert "correlacion_estado = aceptado" in nuevo_log and "banco-dos" in nuevo_log, nuevo_log
    # tambien cuando la propuesta automatica es 'sin candidato'
    sin_candidato = RelacionPropuesta(ra_codigo="PRU01-RA2", practica_codigo=None, score_ra=0.2, estado=EstadoCorrelacion.sin_candidato)
    assert correlate.escribir_relacion(sin_candidato) is False
    assert decidido.read_bytes() == antes
    assert "sin práctica" in Path("wiki/log.md").read_text(encoding="utf-8")
    print("8. RA con correlacion_revisado_por_docente: true: intacto byte a byte; la propuesta queda en el log -- OK")

    # 9. Con el campo en false SI se actualiza, y CORRELATE nunca lo escribe: se conserva.
    sin_revisar = Path("wiki/resultados-aprendizaje/PRU01-RA3.md")
    sin_revisar.write_text(
        "---\ntipo: resultado_aprendizaje\ncodigo: PRU01-RA3\ncorrelacion_estado: pendiente_revision\n"
        "correlacion_revisado_por_docente: false\n---\n\n# RA sin revisar\n", encoding="utf-8")
    aceptada = RelacionPropuesta(
        ra_codigo="PRU01-RA3", practica_codigo="Exp1", fuente="banco-dos", score_ra=0.985,
        confianza_semantica=0.93, confianza_final=0.916, estado=EstadoCorrelacion.aceptado)
    assert correlate.escribir_relacion(aceptada) is True
    fm3 = yaml.safe_load(sin_revisar.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm3["correlacion_estado"] == "aceptado" and fm3["requiere_practica"] == "[[banco-dos]]"
    assert fm3["correlacion_revisado_por_docente"] is False
    print("9. RA con el campo en false: se actualiza y el campo se conserva -- OK")

    # 10. Sin candidato: no queda rastro de una corrida anterior (el RA no sigue apuntando a una practica que ya no se propone).
    ruta_ra1 = Path("wiki/resultados-aprendizaje/PRU01-RA1.md")
    assert yaml.safe_load(ruta_ra1.read_text(encoding="utf-8").split("---", 2)[1])["requiere_practica"] == "[[banco-dos]]"
    sin = RelacionPropuesta(ra_codigo="PRU01-RA1", practica_codigo=None, score_ra=0.2, estado=EstadoCorrelacion.sin_candidato)
    assert correlate.escribir_relacion(sin) is True
    fm_sin = yaml.safe_load(ruta_ra1.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm_sin["correlacion_estado"] == "sin_candidato"
    assert fm_sin["requiere_practica"] is None and fm_sin["practica_experimentos"] == [] and fm_sin["correlacion_alternativas"] == []
    assert fm_sin["correlacion_semantica"] is None and fm_sin["correlacion_confianza"] is None and fm_sin["correlacion_justificacion"] is None
    print("10. sin candidato: se borra el rastro de la corrida anterior (practica, experimentos, confianza, justificacion) -- OK")

    # 11. 'coincide=False' con confianza alta NUNCA debe ganar: confianza_semantica mide
    # cuanto satisface el RA, no la seguridad del veredicto (ver src/prompts/prompt-correlate.md).
    correlate.recall_practicas_candidatas = lambda ra, k=3: [("banco-uno", "Exp1"), ("banco-uno", "Exp2")]
    correlate.juzgar_correlacion = lambda ra, practica, fuente_: JuicioCorrelacion(
        ra_codigo=ra.codigo, practica_codigo=practica.codigo, coincide=False, justificacion="No aplica.", confianza_semantica=0.95)
    descartado = correlate.correlacionar_ra(RA, asignatura(hp=26))
    assert descartado.estado == EstadoCorrelacion.sin_candidato
    assert descartado.practica_codigo is None and descartado.fuente is None
    print("11. un juez que dice 'coincide=False' con confianza 0.95 no puede ganar: sin_candidato -- OK")


def probar_vault_completo() -> None:
    """El bucle --all / --asignatura sobre un vault de muestra completo (asignaturas, RA, fuentes)."""
    confianzas = {"Exp1": 0.93, "Exp2": 0.30, "Exp3": 0.48}
    correlate.recall_practicas_candidatas = lambda ra, k=3: [("banco-uno", codigo) for codigo in confianzas]

    def juez(ra, practica, fuente_):
        return JuicioCorrelacion(ra_codigo=ra.codigo, practica_codigo=practica.codigo, coincide=practica.codigo == "Exp1",
                                 justificacion="fijo", confianza_semantica=confianzas[practica.codigo])

    correlate.juzgar_correlacion = juez
    rutas = {n: Path(f"wiki/resultados-aprendizaje/{n}.md") for n in ("TEO01-RA1", "TPR01-RA1", "TPR01-RA2", "TPR01-RA3")}

    antes = {n: r.read_bytes() for n, r in rutas.items()}
    resumen = correlate.correlacionar_vault(dry_run=True)
    assert (resumen["total"], resumen["gate_abierto"], resumen["gate_cerrado"], resumen["errores"]) == (4, 3, 1, [])
    assert {n: r.read_bytes() for n, r in rutas.items()} == antes and Path("wiki/log.md").read_text(encoding="utf-8") == "# Log\n"
    print("12. --all --dry-run: 4 RA, gate abierto 3 / cerrado 1, sin escribir nada ni tocar el log -- OK")

    resumen = correlate.correlacionar_vault()
    assert (resumen["aceptado"], resumen["pendiente_revision"], resumen["sin_candidato"], resumen["omitidos_por_docente"], resumen["errores"]) == (2, 1, 1, 0, [])
    fm = {n: vault.leer_pagina(r)[0] for n, r in rutas.items()}
    assert (fm["TPR01-RA1"]["correlacion_estado"], fm["TPR01-RA1"]["requiere_practica"], fm["TPR01-RA1"]["practica_experimentos"]) == ("aceptado", "[[banco-uno]]", ["Exp1"])
    assert fm["TPR01-RA3"]["correlacion_estado"] == "pendiente_revision"           # sin CE de manipulacion: 0.70 x 0.93 = 0.65 < 0.70
    assert (fm["TEO01-RA1"]["correlacion_estado"], fm["TEO01-RA1"]["requiere_practica"]) == ("sin_candidato", None)   # gate cerrado: sin LLM
    print("13. --all: 2 aceptados, 1 pendiente_revision (RA sin CE de manipulacion) y 1 sin_candidato (asignatura teorica, gate cerrado) -- OK")

    assert correlate.correlacionar_vault("TEO01")["total"] == 1 and correlate.correlacionar_vault("NO-EXISTE")["total"] == 0
    print("14. --asignatura filtra por codigo de asignatura -- OK")

    # Decision del docente: el RA no se reescribe y se cuenta aparte.
    fm_ra1, cuerpo_ra1 = vault.leer_pagina(rutas["TPR01-RA1"])
    fm_ra1["correlacion_revisado_por_docente"] = True
    vault.escribir_pagina(rutas["TPR01-RA1"], fm_ra1, cuerpo_ra1)
    bytes_ra1 = rutas["TPR01-RA1"].read_bytes()
    resumen = correlate.correlacionar_vault("TPR01")
    assert (resumen["omitidos_por_docente"], resumen["aceptado"], resumen["errores"]) == (1, 1, []) and rutas["TPR01-RA1"].read_bytes() == bytes_ra1
    print("15. el bucle respeta la decision del docente: 1 omitido, su pagina intacta -- OK")

    # Un RA incompleto se informa y no detiene el resto; un RA roto de OTRA asignatura no ensucia el informe.
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA5.md"), {"tipo": "resultado_aprendizaje", "codigo": "TPR01-RA5", "pertenece_a": f"[[{_fixtures.TPR01}]]"}, "\n\n# x\n")
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/TEO01-RA5.md"), {"tipo": "resultado_aprendizaje", "codigo": "TEO01-RA5", "pertenece_a": f"[[{_fixtures.TEO01}]]"}, "\n\n# x\n")
    resumen = correlate.correlacionar_vault("TPR01")
    assert resumen["total"] == 3 and len(resumen["errores"]) == 1 and "TPR01-RA5" in resumen["errores"][0], resumen
    print("16. un RA incompleto se informa sin detener el resto; el de otra asignatura no aparece al filtrar -- OK")

    # 17. Una ASIGNATURA rota (no solo un RA suyo) de OTRO codigo tampoco debe ensuciar el
    # informe al filtrar -- antes se validaba la asignatura antes de filtrar por codigo.
    vault.escribir_pagina(Path("wiki/asignaturas/ROT01 - Asignatura rota.md"),
                          _fixtures._asignatura("ROT01", "Asignatura rota", 10, 20, "teórica", ["ROT01-RA1"]), "\n\n# x\n")  # hp=20 con tipo_abordaje=teorica: invalida
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/ROT01-RA1.md"),
                          _fixtures._ra("ROT01-RA1", "ROT01 - Asignatura rota", "teórica", 10, [], []), "\n\n# x\n")
    resumen = correlate.correlacionar_vault("TPR01")
    assert resumen["total"] == 3 and len(resumen["errores"]) == 1 and "TPR01-RA5" in resumen["errores"][0], resumen
    assert not any("ROT01" in e for e in resumen["errores"]), resumen["errores"]
    resumen_rota = correlate.correlacionar_vault("ROT01")
    assert resumen_rota["total"] == 0 and len(resumen_rota["errores"]) == 1 and "ROT01" in resumen_rota["errores"][0], resumen_rota
    print("17. una asignatura rota de OTRO codigo no ensucia el informe al filtrar; al filtrar por ella si aparece -- OK")

    # 20. Un RA que apunta a una asignatura que NO EXISTE (ni siquiera la pagina) tampoco
    # debe ensuciar el informe al filtrar; sin filtro (--all) el error si debe aparecer.
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/ZZZ01-RA1.md"),
                          {"tipo": "resultado_aprendizaje", "codigo": "ZZZ01-RA1", "pertenece_a": "[[ZZZ01 - no existe]]"}, "\n\n# x\n")
    resumen = correlate.correlacionar_vault("TPR01")
    assert resumen["total"] == 3 and len(resumen["errores"]) == 1 and "TPR01-RA5" in resumen["errores"][0], resumen
    assert not any("ZZZ01" in e for e in resumen["errores"]), resumen["errores"]
    resumen_todos = correlate.correlacionar_vault()
    assert any("ZZZ01-RA1" in e for e in resumen_todos["errores"]), resumen_todos["errores"]
    print("20. un RA que apunta a una asignatura INEXISTENTE no ensucia el informe al filtrar; con --all si aparece -- OK")


def probar_teorica_no_busca_practica() -> None:
    """Regresion: una asignatura teorica con estrategia_practica_marcada=true y un CE de
    manipulacion_fisica con confianza alta supera UMBRAL_GATE (0.2 + 0.27 = 0.47), pero una
    asignatura teorica JAMAS debe terminar con requiere_practica (regla central de CLAUDE.md;
    antes solo se miraba el score, sin mirar tipo_abordaje)."""
    for carpeta in ("wiki/asignaturas", "wiki/resultados-aprendizaje", "wiki/fuentes"):
        Path(carpeta).mkdir(parents=True)
    Path("wiki/log.md").write_text("# Log\n", encoding="utf-8")

    nombre_pagina = "REG01 - Asignatura de regresion"
    vault.escribir_pagina(Path(f"wiki/asignaturas/{nombre_pagina}.md"), {
        "tipo": "asignatura", "codigo": "REG01", "nombre": "Asignatura de regresión", "programa": [],
        "tipo_modulo": "ESPECIFICO", "had_totales": 20, "hp_totales": 0, "hti_totales": 10, "creditos": 2,
        "tipo_abordaje": "teórica", "estrategia_practica_marcada": True, "recurso_laboratorio_marcado": False,
        "resultados_aprendizaje": ["[[REG01-RA1]]"], "competencias": [], "recursos_web": [],
        "fecha_creacion": "YYYY-MM-DD", "fecha_actualizacion": "YYYY-MM-DD",
    }, "\n\n# REG01\n")
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/REG01-RA1.md"), {
        "tipo": "resultado_aprendizaje", "codigo": "REG01-RA1", "enunciado": "Enunciado de regresión.",
        "pertenece_a": f"[[{nombre_pagina}]]", "tipo_abordaje": "teórica", "horas": 10,
        "criterios_evaluacion": [{"codigo": "CE1", "texto": "Medir algo.", "categoria_accion": "manipulacion_fisica", "confianza": 0.9}],
        "contenido_conceptual": [], "contenido_procedimental": [], "contenido_actitudinal": [],
        "bibliografia": [], "requiere_practica": None, "practica_experimentos": [],
        "correlacion_estado": None, "correlacion_revisado_por_docente": False,
        "fecha_creacion": "YYYY-MM-DD", "fecha_actualizacion": "YYYY-MM-DD",
    }, "\n\n# REG01-RA1\n")

    asignatura_reg, _ = vault.cargar_asignatura(nombre_pagina)
    ra_reg, _, _ = vault.cargar_ra(Path("wiki/resultados-aprendizaje/REG01-RA1.md"))
    score = correlate.calcular_score_ra(ra_reg, asignatura_reg)
    assert score >= correlate.UMBRAL_GATE, f"la reproduccion del bug exige score >= 0.40 y dio {score}"  # 0.2 + 0.27 = 0.47

    def no_debe_llamarse(*args, **kwargs):
        raise AssertionError("una asignatura teorica nunca debe buscar practica, sin importar el score")

    correlate.recall_practicas_candidatas = no_debe_llamarse
    relacion = correlate.correlacionar_ra(ra_reg, asignatura_reg)
    assert relacion.estado == EstadoCorrelacion.sin_candidato and relacion.practica_codigo is None
    correlate.escribir_relacion(relacion)

    hallazgos = lint.revisar()
    assert not [h for h in hallazgos if h.regla == "L03"], hallazgos
    print("18. asignatura teorica con score_RA >= 0.40 (checklist + CE de manipulacion): NUNCA busca practica y lint no da L03 -- OK")


def probar_prompt_real_del_juez() -> None:
    """A diferencia del resto de las pruebas (que sustituyen juzgar_correlacion entera),
    esta llama a la funcion REAL: solo se sustituye vault.pedir_estructurado, asi que se
    arma de verdad el prompt de src/prompts/prompt-correlate.md. Si alguien cambia un
    nombre de campo de la plantilla, esto lo detecta aqui -- no en la primera corrida
    real contra la API. No necesita vault en disco: juzgar_correlacion no lee wiki/."""
    capturado: dict[str, str] = {}

    def llm_falso(sistema, usuario, formato):
        capturado["sistema"] = sistema
        capturado["usuario"] = usuario
        # Codigos DISTINTOS a proposito: correlate.py debe fijarlos igual, sin confiar en el LLM.
        return JuicioCorrelacion(ra_codigo="OTRO-CODIGO", practica_codigo="OTRO-EXP",
                                 coincide=True, justificacion="Justificación fija.", confianza_semantica=0.8)

    vault.pedir_estructurado = llm_falso
    ra_prueba = ResultadoAprendizajeModulo(
        codigo="PRU02-RA1", enunciado="Enunciado de prueba para el prompt real.", horas=10,
        tipo_abordaje=TipoAbordaje.teorico_practica,
        criterios_evaluacion=[CriterioEvaluacion(codigo="CE1", texto="Medir algo en el banco.",
                                                  categoria_accion=CategoriaAccionCE.manipulacion_fisica, confianza=0.9)],
        contenido=ContenidoAprendizaje(conceptual=["Tema conceptual de prueba"]),
    )
    practica_prueba = Practica(codigo="Exp3-1", nombre_original="Sub práctica de prueba",   # codigo compuesto a proposito
                               proposito=["Propósito de prueba."], principio_resumen="Resumen de prueba.",
                               terminos_clave=["alfa", "beta", "gamma", "delta"])

    juicio = _JUZGAR_CORRELACION_REAL(ra_prueba, practica_prueba, "fuente-de-prueba")

    assert capturado["sistema"] and capturado["sistema"].strip(), "el mensaje de sistema no debe estar vacío"
    usuario = capturado["usuario"]
    for esperado in ("PRU02-RA1", "Enunciado de prueba para el prompt real.", "Tema conceptual de prueba",
                     "Medir algo en el banco.", "Exp3-1", "fuente-de-prueba", "Sub práctica de prueba", "alfa"):
        assert esperado in usuario, f"'{esperado}' no aparece en el prompt real armado: {usuario!r}"

    # Los codigos los fija correlate.py, no el LLM sustituido (que devolvio 'OTRO-CODIGO'/'OTRO-EXP').
    assert juicio.ra_codigo == "PRU02-RA1" and juicio.practica_codigo == "Exp3-1"
    print("19. juzgar_correlacion arma de verdad el prompt real (prompt-correlate.md) con el RA y la práctica "
          "(código compuesto incluido); los códigos los fija correlate.py, no el LLM -- OK")


def main() -> None:
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        armar_vault(Path(tmp))
        os.chdir(tmp)
        try:
            probar()
        finally:
            os.chdir(original)
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar_vault_completo()
        finally:
            os.chdir(original)
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            probar_teorica_no_busca_practica()
        finally:
            os.chdir(original)
    probar_prompt_real_del_juez()   # no toca disco: no necesita tempdir
    print("TODO OK -- correlate.py lee de wiki/fuentes/ y escribe requiere_practica + practica_experimentos.")


if __name__ == "__main__":
    main()
