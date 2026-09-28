"""Prueba de la capa de generacion (planeador, temario, CORRELATE-PLANEADOR y
CORRELATE-BIBLIOGRAFIA) sobre un vault de muestra con datos INVENTADOS. El LLM se
sustituye por respuestas fijas: se prueba la logica propia de cada modulo (cronograma,
escritura de paginas, marcador, protecciones), no un LLM.

Uso (desde src/):  python test_generacion.py
"""

import os
import re
import tempfile
from pathlib import Path

import _fixtures
import correlate_bibliografia
import figuras
import correlate_planeador
import planeador
import temario
import vault
from correlate_bibliografia import EstadoBibliografia, JuicioBibliografia
from schema_extraccion import (
    Asignatura,
    CategoriaAccionCE,
    ContenidoAprendizaje,
    CriterioEvaluacion,
    ResultadoAprendizajeModulo,
    TipoAbordaje,
)
from schema_planeador import (
    EstadoPlaneador,
    JuicioPlaneador,
    TemasSemana,
    construir_cronograma,
    derivar_horas_sesion,
    minutos_por_bloque,
    repartir_semanas,
)
from schema_temario import CierreSesion, PlanSesion, SeccionRedactada
from temario import MARCADOR


def asignatura(codigo: str, had: int, hp: int) -> Asignatura:
    return Asignatura(
        codigo=codigo, nombre="X", programa="P", had_totales=had, hp_totales=hp, hti_totales=10, creditos=1,
        tipo_abordaje=TipoAbordaje.teorico_practica if hp > 0 else TipoAbordaje.teorica,
        estrategia_practica_marcada=hp > 0, recurso_laboratorio_marcado=hp > 0)


def ra(codigo: str, horas: int) -> ResultadoAprendizajeModulo:
    return ResultadoAprendizajeModulo(
        codigo=codigo, enunciado="E", horas=horas, tipo_abordaje=TipoAbordaje.teorico_practica,
        criterios_evaluacion=[CriterioEvaluacion(codigo="CE1", texto="t", categoria_accion=CategoriaAccionCE.manipulacion_fisica, confianza=0.9)],
        contenido=ContenidoAprendizaje())


def esperar(excepcion, funcion, *args, **kwargs):
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


# ---------------------------------------------------------------------------
# A. Cronograma determinista (sin vault, sin LLM)
# ---------------------------------------------------------------------------


def probar_cronograma() -> None:
    assert derivar_horas_sesion(asignatura("A", 23, 0)) == 2
    assert derivar_horas_sesion(asignatura("B", 42, 26)) == 4
    # Regresion: had_totales YA incluye las horas practicas -- incluso con hp_totales al
    # maximo permitido (== had_totales, todas las horas presenciales son practicas), la
    # duracion de la sesion sale solo de had_totales (antes se sumaban y se contaba dos veces).
    assert derivar_horas_sesion(asignatura("C", 14, 14)) == 2
    print("A1. horas_sesion sale solo de had_totales (ya incluye las HP): 23/14->2h; 42/14->4h; "
          "14/14 con hp_totales=had_totales->2h (HP no se suma aparte) -- OK")

    assert repartir_semanas([29, 29, 29, 30], 11) == [3, 3, 2, 3]
    assert repartir_semanas([1, 1], 11) == [6, 5]           # empate: gana el RA que va antes
    for horas in ([10], [5, 5, 5], [1, 2, 3, 4, 5], [40, 1, 1], [7] * 11):
        assert sum(repartir_semanas(horas, 11)) == 11, horas
    print("A2. reparto por mayor resto: [29,29,29,30] -> [3,3,2,3]; la suma siempre da 11 -- OK")

    crono = construir_cronograma(asignatura("B", 26, 26), [ra(f"B-RA{i}", h) for i, h in enumerate([29, 29, 29, 30], 1)])
    esperado = ["B-RA1"] * 3 + ["B-RA2", None] + ["B-RA2"] * 2 + ["B-RA3"] * 2 + [None] + ["B-RA4"] * 3 + [None]
    assert [s.ra for s in crono.semanas] == esperado, [s.ra for s in crono.semanas]
    assert [s.semana for s in crono.semanas if s.tipo.value == "examen"] == [5, 10, 14]
    print("A3. secuencia: S1-3 RA1 | S4 RA2 | examen S5 | S6-7 RA2 | S8-9 RA3 | examen S10 | S11-13 RA4 | examen S14 -- OK")

    esperar(ValueError, construir_cronograma, asignatura("B", 26, 26), [])
    esperar(ValueError, construir_cronograma, asignatura("B", 26, 26), [ra(f"B-RA{i}", 1) for i in range(12)])
    esperar(ValueError, repartir_semanas, [0, 0], 11)
    print("A4. sin RA, con mas RA que semanas de clase, o con 0 horas: ValueError (nunca un plan vacio o incompleto) -- OK")


def probar_resumen_fuente() -> None:
    resumen_texto = "Resumen de prueba. " * 25   # ~500 caracteres: mas que el limite viejo (400), menos que el nuevo (1800)
    cuerpo = (
        "\n\n# Fuente\n\n**Origen:** x\n\n"
        f"## Resumen\n{resumen_texto}\n\n"
        "## Puntos clave\n- Punto uno\n- Punto dos\n\n"
        "## Citas relevantes\n> cita que no debe aparecer\n"
    )
    resumen = temario._resumen(cuerpo)
    assert "Punto uno" in resumen and "Punto dos" in resumen, resumen   # ahora SI se suman los Puntos clave
    assert "cita que no debe aparecer" not in resumen                   # pero no las secciones siguientes
    assert 400 < len(resumen) <= 1800, len(resumen)                     # el limite subio de 400: ya no trunca aqui

    sin_secciones = "\n\n# Fuente\n\nTexto plano sin secciones tituladas.\n"
    assert temario._resumen(sin_secciones) == "# Fuente Texto plano sin secciones tituladas."
    print("A5. _resumen (contexto del juez de CORRELATE-BIBLIOGRAFIA): junta Resumen + Puntos clave, "
          "limite ~1800 (no 400); sin esas secciones, cae al cuerpo completo -- OK")


# ---------------------------------------------------------------------------
# B. Modulos sobre un vault de muestra, con el LLM sustituido
# ---------------------------------------------------------------------------

LLAMADAS: list[str] = []
ULTIMO_USUARIO: dict[str, str] = {}


def llm_falso(sistema, usuario, formato):
    LLAMADAS.append(formato.__name__)
    ULTIMO_USUARIO[formato.__name__] = usuario
    if formato is TemasSemana:
        n = int(re.search(r"Semanas de clase de este RA: (\d+)", usuario).group(1))
        return TemasSemana(temas=[f"Tema {i}" for i in range(1, n + 1)])
    if formato in (PlanSesion, SeccionRedactada, CierreSesion):
        return _fixtures.responder_temario(usuario, formato)
    if formato is JuicioPlaneador:
        codigo_ra = re.search(r"RA (\S+):", usuario).group(1)
        if codigo_ra == "TPR01-RA2":
            return JuicioPlaneador(estado=EstadoPlaneador.desviado, confianza=0.4, semanas_con_problema=[99, 6], justificacion="Incluye temas ajenos.")
        return JuicioPlaneador(estado=EstadoPlaneador.cubierto, confianza=1.4, semanas_con_problema=[], justificacion="Cubre el RA.")
    if formato is JuicioBibliografia:
        return JuicioBibliografia(estado=EstadoBibliografia.cubierta, justificacion="Las fuentes lo sostienen.")
    raise AssertionError(f"llamada inesperada al LLM: {formato}")


def probar_generacion() -> None:
    vault.pedir_estructurado = llm_falso
    figuras.dibujar_grafica = figuras.dibujar_diagrama = lambda spec, destino: _fixtures.png_falso(destino)      # aqui no se prueba matplotlib (ver test_temario.py)

    # --- planeador ---------------------------------------------------------
    esperar(FileNotFoundError, temario.generar_temario, "TEO01", 1)          # aun no hay planeador
    destino = planeador.generar_planeador("TPR01", sin_llm=True)
    fm, cuerpo = vault.leer_pagina(destino)
    assert fm["tipo"] == "planeador" and fm["horas_sesion"] == 4 and fm["semanas_examen"] == [5, 10, 14]
    assert len(fm["semanas"]) == 14 and all(s["tema"] is None for s in fm["semanas"])
    clases = [s["ra"] for s in fm["semanas"] if s["tipo"] == "clase"]
    assert (clases.count("TPR01-RA1"), clases.count("TPR01-RA2"), clases.count("TPR01-RA3")) == (4, 3, 4), clases
    assert LLAMADAS == []
    print("B1. planeador --sin-llm: 14 semanas, examenes 5/10/14, sesion 4 h, reparto 4/3/4, sin llamar al LLM -- OK")

    esperar(FileExistsError, planeador.generar_planeador, "TPR01", sin_llm=True)
    planeador.generar_planeador("TPR01", forzar=True)
    fm, cuerpo = vault.leer_pagina(destino)
    assert LLAMADAS == ["TemasSemana"] * 3, LLAMADAS                        # una llamada por RA
    assert all(s["tema"] for s in fm["semanas"] if s["tipo"] == "clase") and "| 1 | clase | [[TPR01-RA1]] | Tema 1 |" in cuerpo
    print("B2. no sobrescribe sin --forzar; con LLM escribe un tema por semana de clase (3 llamadas, una por RA) -- OK")

    fm_teo, _ = vault.leer_pagina(planeador.generar_planeador("TEO01"))
    assert fm_teo["horas_sesion"] == 2 and [s["tema"] for s in fm_teo["semanas"] if s["tipo"] == "clase"] == [f"Tema {i}" for i in range(1, 12)]
    vault.escribir_pagina(Path("wiki/asignaturas/VAC01 - Vacía.md"), _fixtures._asignatura("VAC01", "Vacía", 10, 10, "teórico-práctica", []), "\n\n# x\n")
    assert "no hay RA" in esperar(ValueError, planeador.generar_planeador, "VAC01")
    esperar(FileNotFoundError, planeador.generar_planeador, "NO-EXISTE")
    print("B3. asignatura teorica -> sesion de 2 h con un solo RA; sin RA cargados o inexistente: error, no un plan vacio -- OK")

    # --- temario -----------------------------------------------------------
    esperar(ValueError, temario.generar_temario, "TPR01", 5)                # semana de examen
    esperar(ValueError, temario.generar_temario, "TPR01", 99)
    fm_ra, cuerpo_ra = vault.leer_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA1.md"))
    fm_ra.update({"requiere_practica": "[[banco-uno]]", "practica_experimentos": ["Exp1"]})
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA1.md"), fm_ra, cuerpo_ra)

    destino_t1 = temario.generar_temario("TPR01", 1)
    fm_t, cuerpo_t = vault.leer_pagina(destino_t1)
    assert destino_t1.name == "TPR01-semana01.md"
    assert (fm_t["tipo"], fm_t["semana"], fm_t["resultado_aprendizaje"], fm_t["horas_sesion"], fm_t["bibliografia_estado"]) == \
        ("temario", 1, "[[TPR01-RA1]]", 4, None)
    assert LLAMADAS.count("PlanSesion") == 1 and LLAMADAS.count("SeccionRedactada") == 7 and LLAMADAS.count("CierreSesion") == 1, LLAMADAS   # tres pasos: plan, 7 unidades (la sintesis va en el cierre) y cierre
    for titulo in ("## 1. Metadatos de la Sesión", "### 1.1 Continuidad curricular", "### 1.2 Prerrequisitos", "## 2. Resultados de Aprendizaje",
                   "## 3. Índice Temporizado (240 minutos)", "## 4. Desarrollo Teórico", "### 4.1 Introducción Conceptual (Bloque 1)", "### 4.2 Conceptos Clave",
                   "#### 4.2.1 Concepto 1 del tema (Bloque 2)", "#### 4.2.3 Concepto 3 del tema (Bloque 4)",
                   "## 5. Caso de Estudio Aplicado: Estación de prensado de ejemplo (Bloque 5)", "### 5.1 Descripción del sistema", "### 5.2 Cálculos",
                   "## 6. Selección con justificación cuantitativa (Bloque 6)", "## 7. Implementación de referencia (Bloque 7)", "## 8. Síntesis (Bloque 8)",
                   "### Componente Actitudinal", "## 9. Bibliografía (Formato IEEE)"):
        assert titulo in cuerpo_t, titulo
    assert "\n\n# Título descriptivo de la sesión sobre Tema 1\n\n> **Módulos:** TPR01 — Asignatura teórico-práctica de prueba\n> **Duración:** 240 minutos (sesión teórico-práctica)\n" in cuerpo_t
    assert "> **Plataforma de referencia:** Plataforma de ejemplo X1" in cuerpo_t and "**Nivel:**" not in cuerpo_t          # sin `nivel` en el programa no se inventa
    assert "**Resultado de aprendizaje del módulo:** [[TPR01-RA1]]" in cuerpo_t and "1. **→ Presente sesión (semana 1):** Tema 1" in cuerpo_t and "2. Semana 2: Tema 2" in cuerpo_t
    assert "| RA1 | **Distinguir** los conceptos de Tema 1 (CE1, CE2) | Analizar |" in cuerpo_t                                     # los criterios del RA, cubiertos
    assert "|  | **Total** | **240 min** |" in cuerpo_t and "| 5 | Descripción de Estación de prensado de ejemplo, unidad de la sesión. | " in cuerpo_t
    minutos = [int(m) for m in re.findall(r"\| (\d+) min \|", cuerpo_t)]
    assert len(minutos) == 8 and sum(minutos) == 240 and all(m % 5 == 0 and m >= 5 for m in minutos), minutos            # 8 bloques, multiplos de 5, suman la sesion
    assert "**Práctica de referencia:** [[banco-uno]] — Exp1" in cuerpo_t and "Se retoma la práctica Exp1" in cuerpo_t
    assert "[1] Autor 1, Título 1, Editorial, 2020." in cuerpo_t and "[2] Autor 2, Título 2, Editorial, 2020." in cuerpo_t   # libro-a y el manual de la practica
    assert "$$\nV = I \\, R\n$$" in cuerpo_t and "**Tabla 1.** Datos del ejemplo" in cuerpo_t and "```cpp\nint x = 0;" in cuerpo_t and "> **Nota pedagógica:** " in cuerpo_t
    assert "![Figura 1. Flujo del ejemplo](figuras/TPR01-semana01-fig1.png)\n\n*Figura 1. Flujo del ejemplo*" in cuerpo_t
    assert len(list(Path("generacion/temarios/figuras").glob("TPR01-semana01-fig*.png"))) == 3
    estadisticas = fm_t["estadisticas"]
    assert (estadisticas["ecuaciones"], estadisticas["tablas"], estadisticas["figuras"]) == (3, 3, 3) and estadisticas["palabras"] > 1000, estadisticas
    plan_pedido, unidad_pedida = ULTIMO_USUARIO["PlanSesion"], ULTIMO_USUARIO["SeccionRedactada"]
    assert "Duración de la sesión: 240 minutos (4 h)" in plan_pedido and "Exp1" in plan_pedido and "libro-a" in plan_pedido and "banco-uno" in plan_pedido
    assert "Semana 1 de 14" in plan_pedido and "Tema de la semana: Tema 1" in plan_pedido and "Fuentes cargadas (2;" in plan_pedido
    assert "UNIDAD A DESARROLLAR" in unidad_pedida and "Práctica de referencia: Exp1" in unidad_pedida and "Mínimo de palabras de prosa:" in unidad_pedida
    print("B4. temario de tres pasos (plan, 7 unidades, cierre): la estructura de la guia de sesion, indice de 240 min en multiplos de 5, criterios cubiertos, "
          "figuras dibujadas, practica anclada (Exp1) y las dos fuentes numeradas -- OK")

    temario.generar_temario("TPR01", 6)                                     # RA2: sin practica y sin bibliografia
    cuerpo6 = vault.leer_pagina(Path("generacion/temarios/TPR01-semana06.md"))[1]
    assert "Práctica de referencia" not in cuerpo6 and "(la sesión no cita fuentes)" in cuerpo6
    assert "el RA no tiene una práctica asignada" in ULTIMO_USUARIO["PlanSesion"] and "ninguna: el RA no tiene fuentes enlazadas" in ULTIMO_USUARIO["PlanSesion"]
    esperar(FileExistsError, temario.generar_temario, "TPR01", 1)
    temario.generar_temario("TPR01", 1, forzar=True)
    assert len(list(Path("generacion/temarios/figuras").glob("TPR01-semana01-fig*.png"))) == 3                       # --forzar reemplaza las figuras, no las acumula
    _fixtures.CONFIG_TEMARIO["conceptos"] = 2
    assert "conceptos clave" in esperar(ValueError, temario.generar_temario, "TPR01", 2)
    assert not Path("generacion/temarios/TPR01-semana02.md").exists() and not list(Path("generacion/temarios/figuras").glob("TPR01-semana02-fig*"))
    _fixtures.CONFIG_TEMARIO["conceptos"] = 3
    escritos, omitidas = temario.generar_temarios("TPR01")
    assert len(escritos) == 9 and omitidas == [1, 6], (len(escritos), omitidas)
    assert len(list(Path("generacion/temarios").glob("TPR01-semana*.md"))) == 11
    print("B5. sin practica/bibliografia se avisa al LLM y el temario lo dice; no sobrescribe; --forzar reemplaza las figuras; exige 3-6 conceptos; "
          "--todas omite las que ya existen -- OK")

    # --- CORRELATE-BIBLIOGRAFIA -------------------------------------------
    ruta_marcado = Path("generacion/temarios/TPR01-semana02.md")
    fm_m, cuerpo_m = vault.leer_pagina(ruta_marcado)
    vault.escribir_pagina(ruta_marcado, fm_m, cuerpo_m + f"\nSegún Autor X (2019) {MARCADOR}, el sistema se modela así.\n")
    antes = len([c for c in LLAMADAS if c == "JuicioBibliografia"])
    resultados = {nombre: (estado, via) for nombre, estado, via in correlate_bibliografia.auditar_temarios("TPR01")}
    llamadas_juez = len([c for c in LLAMADAS if c == "JuicioBibliografia"]) - antes
    assert resultados["TPR01-semana02"] == ("vacio_detectado", "marcador")
    assert resultados["TPR01-semana01"] == ("cubierta", "juez")
    assert resultados["TPR01-semana06"] == ("revisar", "sin_bibliografia")
    assert llamadas_juez == 7, llamadas_juez            # RA1 sin marcador (3) + RA3 (4); RA2 no tiene fuentes y la semana 2 tiene marcador
    fm_m, _ = vault.leer_pagina(ruta_marcado)
    assert len(fm_m["bibliografia_faltantes"]) == 1 and MARCADOR in fm_m["bibliografia_faltantes"][0]
    assert vault.leer_pagina(Path("generacion/temarios/TPR01-semana01.md"))[0]["bibliografia_via"] == "juez"
    print("B6. CORRELATE-BIBLIOGRAFIA: marcador -> vacio_detectado sin LLM; sin fuentes -> revisar sin LLM; el resto, juez (7 llamadas) -- OK")

    # --- CORRELATE-PLANEADOR ----------------------------------------------
    assert sorted(correlate_planeador.auditar_planeador("TPR01")) == ["TPR01-RA1", "TPR01-RA2", "TPR01-RA3"]
    ra1, _ = vault.leer_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA1.md"))
    ra2, _ = vault.leer_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA2.md"))
    assert (ra1["planeador_estado"], ra1["planeador_semanas"], ra1["planeador_confianza"]) == ("cubierto", [1, 2, 3, 4], 1.0)
    assert (ra2["planeador_estado"], ra2["planeador_semanas_con_problema"]) == ("desviado", [6])   # la semana 99 no es del RA: se descarta
    planeador.generar_planeador("TEO01", sin_llm=True, forzar=True)
    assert "no tiene temas" in esperar(ValueError, correlate_planeador.auditar_planeador, "TEO01")
    assert correlate_planeador.codigos_con_planeador() == ["TEO01", "TPR01"]
    print("B7. CORRELATE-PLANEADOR: escribe planeador_* en cada RA (confianza acotada a 1, semanas ajenas descartadas); sin temas: error -- OK")

    log = Path("wiki/log.md").read_text(encoding="utf-8")
    for esperado in ("/planeador TPR01", "/temario TPR01 semana 1", "/correlate-bibliografia TPR01", "/correlate-planeador TPR01"):
        assert esperado in log, esperado
    print("B8. cada operacion deja su entrada en wiki/log.md -- OK")


def main() -> None:
    probar_cronograma()
    probar_resumen_fuente()
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar_generacion()
        finally:
            os.chdir(original)
    print("TODO OK -- la capa de generacion funciona de punta a punta con el LLM sustituido.")


if __name__ == "__main__":
    main()
