"""Prueba de ANALIZAR-CAMBIOS (src/analizar_cambios.py) sobre un vault de muestra con datos INVENTADOS: no llama a ningun LLM.

Comprueba que el analisis dice que actualizar y que NO, y que no escribe nada en wiki/ ni en generacion/:
  A. las secciones de un documento (encabezados, rotulos de un PDF convertido, negritas, tablas, codigo) y a que pagina del wiki va cada una;
  B. la linea base (fijarla entera o por archivos, ignorar lo que no cuenta, tolerar una base ilegible);
  C. la comparacion (nuevo, modificado, eliminado; secciones y experimentos; un cambio de saltos de linea no es un cambio);
  D. un curriculo modificado: solo hay que leer lo que cambio, y se sabe a que pagina toca;
  E. un manual de banco: que experimentos cambiaron, `ingest_manual.py --solo` y que RA volver a correlacionar;
  F. un libro o una norma: a que RA les sirve y que temarios podrian ganar;
  G. el wiki contra la generacion: cronograma, duracion, horas de trabajo independiente, alineacion y correlacion;
  H. `correlate.py --ra`;
  I. el informe, `--json`, `--confirmar`, los errores de uso y que el analisis es de solo lectura.

Uso (desde src/):  python test_analizar_cambios.py
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import _fixtures
import analizar_cambios as ac
import correlate
import ingest_manual
import planeador
import temario
import vault
from schema_extraccion import ExtraccionManual, Practica
from schema_planeador import construir_cronograma, horas_hti_semana

SRC = Path(__file__).resolve().parent
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}

RELLENO = " ".join(["palabra"] * 250)          # cada seccion de un curriculo real tiene texto de sobra
CURRICULO = f"""# Diseño y Planeamiento Curricular

Identificación del módulo
Nombre del módulo: Asignatura de ejemplo
Código: TPR01

## Información de Créditos Académicos

| HAD | HP | HTI | Créditos |
|---|---|---|---|
| 42 | 26 | 54 | 2 |

{RELLENO}

## Resultados de Aprendizaje

**RA1** Diseñar máquinas de estados finitos para el control secuencial.

| CE | Texto |
|---|---|
| CE1 | Identificar estados y transiciones. |

{RELLENO}

## Unidades de Competencia

UC1. Controlar procesos secuenciales.

{RELLENO}

## Estrategias Pedagógicas y Didácticas

- [x] Práctica de laboratorio

{RELLENO}

## Bibliografía

- Autor A. Máquinas de estados. Editorial X. ISBN 000.

{RELLENO}

## Webgrafía y Bases de Datos

- https://ejemplo.org/recurso

## Proceso de Aprobación

Docente autor: Docente de ejemplo
"""

MANUAL = """# Manual de ejemplo

## Chapter 1

### Experiment 1 Primer experimento

Texto del primero, con suficiente contenido para que sea una seccion.

### Experiment 2 Segundo experimento

Texto del segundo experimento.

### Experiment 3 Tercer experimento

Texto del tercero.
"""

LIBRO = """# Libro de máquinas de estados

## Capítulo 1: Máquinas de estados finitos

Las máquinas de estados finitos describen el comportamiento secuencial de un sistema: cada estado tiene transiciones hacia otros
estados según los eventos de entrada, y la codificación de transiciones en una tabla permite implementarlas de forma sistemática
en un controlador. Este capítulo presenta la codificación de transiciones con ejemplos resueltos paso a paso.

## Capítulo 2: Temporizadores y contadores

Los temporizadores y contadores se combinan con las máquinas de estados finitos para medir tiempos entre transiciones y contar
eventos; su uso en el control secuencial se ilustra con casos de un sistema de llenado de tanques y un semáforo.
"""


def escribir(ruta: str, texto: str) -> Path:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8", newline="\n")
    return destino


def editar(ruta: str, **cambios) -> None:
    """Cambia campos del frontmatter de una pagina del wiki o de generacion."""
    fm, cuerpo = vault.leer_pagina(Path(ruta))
    fm.update(cambios)
    vault.escribir_pagina(Path(ruta), fm, cuerpo)


def huella_de_arbol(*carpetas: str) -> dict[str, str]:
    return {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for c in carpetas for p in sorted(Path(c).rglob("*")) if p.is_file()}


def esperar(excepcion, funcion, *args, **kwargs) -> str:
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


# --- A. secciones ----------------------------------------------------------------------------------------------------


def probar_secciones() -> None:
    secciones = {s.clave: s for s in ac.dividir_secciones(CURRICULO)}
    claves = list(secciones)
    assert claves[0] == "Diseño y Planeamiento Curricular", claves
    assert "Diseño y Planeamiento Curricular › Información de Créditos Académicos" in secciones
    creditos = secciones["Diseño y Planeamiento Curricular › Información de Créditos Académicos"]
    assert creditos.destino == "creditos" and "| 42 | 26 | 54 | 2 |" in creditos.texto            # las filas de una tabla no abren secciones
    assert secciones["Diseño y Planeamiento Curricular › Bibliografía"].destino == "bibliografia"
    assert secciones["Diseño y Planeamiento Curricular › Webgrafía y Bases de Datos"].destino == "webgrafia"
    assert secciones["Diseño y Planeamiento Curricular › Proceso de Aprobación"].destino == "aprobacion"
    assert secciones["Diseño y Planeamiento Curricular › Estrategias Pedagógicas y Didácticas"].destino == "estrategias"
    # «Nombre del módulo: X» es un dato, no un rotulo; el rotulo suelto «Identificación del módulo» si abre seccion
    assert "Diseño y Planeamiento Curricular › Identificación del módulo" in secciones
    assert not any("Nombre del módulo" in c for c in claves), claves
    print("A1. un curriculo se parte por sus encabezados y rotulos, las tablas no abren secciones y cada seccion sabe a que pagina del wiki toca -- OK")

    pdf = "INFORMACIÓN GENERAL\nNombre\n\n**Resultados de Aprendizaje**\n### RA1\nTexto uno\n### RA2\nTexto dos\n\n## Bibliografía\n- Libro\n"
    por_clave = {s.clave: s for s in ac.dividir_secciones(pdf)}
    assert por_clave["Resultados de Aprendizaje › RA1"].destino == "ra", list(por_clave)       # RA1 hereda el destino del rotulo
    assert por_clave["Resultados de Aprendizaje › RA2"].destino == "ra"
    assert por_clave["INFORMACIÓN GENERAL"].destino == "identificacion"                        # dos rotulos son hermanos: el segundo cierra al primero
    assert next(s for k, s in por_clave.items() if k.endswith("Bibliografía")).destino == "bibliografia"
    dos = ac.dividir_secciones("**Uno**\ntexto\n**Dos**\ntexto\n")
    assert [s.clave for s in dos] == ["Uno", "Dos"], [s.clave for s in dos]                                            # dos rotulos seguidos son hermanos
    repetidas = ac.dividir_secciones("## A\nx\n## A\ny\n")
    assert [s.clave for s in repetidas] == ["A", "A (2)"]
    print("A2. un rotulo en negrita o suelto (un PDF convertido) cuelga del ultimo encabezado, sus RA heredan destino y una clave repetida se numera -- OK")

    en_codigo = ac.dividir_secciones("## Real\ntexto\n```\n## Falso encabezado\n```\n")
    assert [s.clave for s in en_codigo] == ["Real"], [s.clave for s in en_codigo]
    libro = ac.dividir_secciones("# Libro\n## Cap 1\ntexto\n### Sec 1.1\nmas\n**Negrita**\notra\n", ac.NIVEL_DE_LIBROS)
    assert [s.clave for s in libro] == ["Libro", "Libro › Cap 1"], [s.clave for s in libro]          # de un libro solo se siguen los capitulos
    assert "Sec 1.1" in libro[-1].texto and "Negrita" in libro[-1].texto
    print("A3. un encabezado dentro de un bloque de codigo no cuenta y de un libro solo se siguen los capitulos -- OK")

    assert ac._sha("a  \r\nb\r\n") == ac._sha("a\nb") == ac._sha("﻿a\nb".lstrip("﻿")), "los saltos de linea y los espacios finales no cambian la huella"
    print("A4. la huella no cambia por saltos de linea de Windows ni espacios al final -- OK")


# --- B y C. linea base y comparacion -----------------------------------------------------------------------------------


def probar_linea_base() -> None:
    escribir("raw/curriculos/Prog/TPR01.md", CURRICULO)
    escribir("raw/bibliografia/libro.md", LIBRO)
    escribir("raw/assets/figura.png", "no cuenta")
    escribir("raw/bibliografia/.gitkeep", "")
    Path("raw/bibliografia/x.pdf").write_bytes(b"%PDF-1.4 falso")
    actual = ac.instantanea()
    assert sorted(actual) == ["raw/bibliografia/libro.md", "raw/bibliografia/x.pdf", "raw/curriculos/Prog/TPR01.md"], sorted(actual)
    assert "secciones" in actual["raw/curriculos/Prog/TPR01.md"] and "secciones" not in actual["raw/bibliografia/x.pdf"]
    assert ac.instantanea() == actual, "la instantanea es estable"
    assert ac.leer_base() is None and not Path("memory_store").exists(), "analizar no crea nada"
    print("B1. la instantanea cubre raw/ sin assets ni archivos ocultos, distingue texto de binarios y es estable; sin --confirmar no se crea memory_store -- OK")

    n, ruta = ac.confirmar()
    assert n == 3 and ruta == ac.ESTADO and ac.leer_base()["archivos"] == actual
    escribir("raw/bibliografia/otro.md", "# Otro\n\ntexto")
    escribir("raw/bibliografia/libro.md", LIBRO + "\n\n## Capítulo 3\n\nNuevo capítulo con contenido suficiente para ser una sección propia del libro de ejemplo.\n")
    n, _ = ac.confirmar(["raw/bibliografia/otro.md"])
    base = ac.leer_base()["archivos"]
    assert n == 1 and "raw/bibliografia/otro.md" in base and base["raw/bibliografia/libro.md"] == actual["raw/bibliografia/libro.md"], "confirmar un archivo no fija los demas"
    Path("raw/bibliografia/otro.md").unlink()
    n, _ = ac.confirmar(["raw/bibliografia"])                     # una carpeta: incluye lo que ya no esta (sale de la base)
    base = ac.leer_base()["archivos"]
    assert "raw/bibliografia/otro.md" not in base and base["raw/bibliografia/libro.md"] != actual["raw/bibliografia/libro.md"]
    assert "no es un archivo ni una carpeta" in esperar(FileNotFoundError, ac.confirmar, ["raw/no-existe.md"])
    print("B2. --confirmar fija todo raw/, solo un archivo o una carpeta (lo borrado sale de la base) y un nombre que no existe es un error -- OK")

    ac.ESTADO.write_text("{esto no es json", encoding="utf-8")
    assert ac.leer_base() is None
    ac.ESTADO.write_text('{"archivos": 5}', encoding="utf-8")
    assert ac.leer_base() is None
    ac.confirmar()
    escribir("raw/bibliografia/libro.md", LIBRO)                   # vuelve a la version anterior
    print("B3. una linea base ilegible se trata como una primera corrida, no como un error -- OK")


def probar_comparacion() -> None:
    base = ac.instantanea()
    assert ac.comparar(base, base) == []
    texto = Path("raw/bibliografia/libro.md").read_text(encoding="utf-8")
    escribir("raw/bibliografia/libro.md", texto.replace("\n", "\r\n"))
    assert ac.comparar(base, ac.instantanea()) == [], "reescribir con saltos de linea de Windows no es un cambio"
    escribir("raw/bibliografia/libro.md", texto.replace("semáforo", "semáforo de cuatro vías") + "\n## Capítulo 3\n\nCapítulo nuevo con texto suficiente para contar.\n")
    Path("raw/bibliografia/x.pdf").unlink()
    escribir("raw/curriculos/Prog/NUEVO.md", "# Nuevo\n\ntexto")
    cambios = {c.ruta: c for c in ac.comparar(base, ac.instantanea())}
    libro = cambios["raw/bibliografia/libro.md"]
    assert libro.estado == "modificado" and libro.secciones_nuevas == ["Libro de máquinas de estados › Capítulo 3"], libro
    assert libro.secciones_modificadas == ["Libro de máquinas de estados › Capítulo 2: Temporizadores y contadores"]
    assert cambios["raw/bibliografia/x.pdf"].estado == "eliminado"
    assert cambios["raw/curriculos/Prog/NUEVO.md"].estado == "nuevo" and cambios["raw/curriculos/Prog/NUEVO.md"].categoria == "curriculo"
    assert "raw/curriculos/Prog/TPR01.md" not in cambios
    escribir("raw/bibliografia/libro.md", LIBRO)
    escribir("raw/bibliografia/x.pdf", "%PDF")
    Path("raw/curriculos/Prog/NUEVO.md").unlink()
    print("C1. nuevo, modificado (con sus secciones) y eliminado se distinguen; reescribir con \\r\\n no es un cambio -- OK")


# --- D. un curriculo modificado -----------------------------------------------------------------------------------------


def probar_curriculo() -> None:
    ruta_pagina = "wiki/asignaturas/" + _fixtures.TPR01 + ".md"
    fm, cuerpo = vault.leer_pagina(Path(ruta_pagina))
    vault.escribir_pagina(Path(ruta_pagina), fm, cuerpo + "\n**Origen:** `raw/curriculos/Prog/TPR01.md`\n")
    ac.confirmar()

    assert ac.analizar_raw(ac.leer_base()) == [], "sin cambios: nada que informar"
    nuevo = (CURRICULO.replace("| 42 | 26 | 54 | 2 |", "| 42 | 30 | 54 | 2 |")
             .replace("Autor A. Máquinas de estados.", "Autor A. Máquinas de estados. Autor B. Redes industriales.")
             .replace("## Webgrafía y Bases de Datos\n\n- https://ejemplo.org/recurso\n\n", ""))
    escribir("raw/curriculos/Prog/TPR01.md", nuevo)
    (cambio,) = ac.analizar_raw(ac.leer_base())
    assert cambio.estado == "modificado" and cambio.categoria == "curriculo" and cambio.paginas == [ruta_pagina]
    por_destino = {d["destino"]: d for d in cambio.destinos}
    assert set(por_destino) == {"creditos", "bibliografia", "webgrafia"}, por_destino.keys()
    assert por_destino["webgrafia"]["secciones"] == ["Diseño y Planeamiento Curricular › Webgrafía y Bases de Datos"]      # la que se quito
    assert "hp_totales" in por_destino["creditos"]["actualizar"] and "horas_sesion" in por_destino["creditos"]["efecto"]
    assert 0 < cambio.tokens_a_leer < 0.5 * cambio.tokens_totales, (cambio.tokens_a_leer, cambio.tokens_totales)     # 2 de 6 secciones largas
    print(f"D1. un curriculo con 3 secciones cambiadas dice a que pagina toca cada una y hay que leer ≈{cambio.tokens_a_leer} tokens de ≈{cambio.tokens_totales} -- OK")

    escribir("raw/curriculos/Prog/OTRO.md", CURRICULO.replace("TPR01", "OTRO1"))
    (otro,) = [c for c in ac.analizar_raw(ac.leer_base()) if c.ruta.endswith("OTRO.md")]
    assert otro.estado == "nuevo" and otro.paginas == [] and otro.tokens_a_leer == otro.tokens_totales > 0        # nuevo: se lee entero
    Path("raw/curriculos/Prog/OTRO.md").unlink()
    escribir("raw/curriculos/Prog/TPR01.md", CURRICULO)
    print("D2. un curriculo nuevo sin pagina en el wiki se marca para INGEST-CURRICULAR completo -- OK")

    Path("memory_store/estado-cambios.json").unlink()
    (sin_base,) = [c for c in ac.analizar_raw(None) if c.ruta.endswith("TPR01.md")]
    assert sin_base.estado == "sin_base", "el documento que ya tiene pagina, sin linea base, se supone incorporado"
    otros = [c for c in ac.analizar_raw(None) if not c.ruta.endswith("TPR01.md")]
    assert otros and all(c.estado == "nuevo" for c in otros)
    ac.confirmar()
    print("D3. sin linea base, lo que ya tiene pagina en el wiki se supone incorporado y lo demas es nuevo -- OK")


# --- E. un manual de banco ----------------------------------------------------------------------------------------------


def llm_falso(sistema, usuario, formato):
    assert formato is ExtraccionManual
    numero = re.search(r"Experiment (\d+)", usuario).group(1)
    LLAMADAS.append(numero)
    practica = Practica(codigo="X", nombre_original=f"Experimento {numero}", proposito=["Proposito."], principio_resumen="Resumen.",
                        terminos_clave=["uno", "dos", "tres", "cuatro"])
    return ExtraccionManual(banco_nombre="Banco de ejemplo", idioma_original="en", capitulo="Chapter 1", practicas=[practica])


LLAMADAS: list[str] = []


def probar_manual() -> None:
    vault.pedir_estructurado = llm_falso
    escribir("raw/manuales-laboratorio/banco/manual.md", MANUAL)
    destino, n = ingest_manual.ingest_manual(Path("raw/manuales-laboratorio/banco/manual.md"), "banco-dos")
    assert n == 3 and LLAMADAS == ["1", "2", "3"]
    ac.confirmar()

    LLAMADAS.clear()
    destino, n = ingest_manual.ingest_manual(Path("raw/manuales-laboratorio/banco/manual.md"), "banco-dos", solo=["Exp2"])
    assert n == 1 and LLAMADAS == ["2"], LLAMADAS
    LLAMADAS.clear()
    ingest_manual.ingest_manual(Path("raw/manuales-laboratorio/banco/manual.md"), "banco-dos", solo=["1", "Exp3"])
    assert LLAMADAS == ["1", "3"], "por numero o por codigo, en el orden del manual"
    assert "el manual no tiene Exp9" in esperar(ValueError, ingest_manual.ingest_manual, Path("raw/manuales-laboratorio/banco/manual.md"), "banco-dos", solo=["Exp9"])
    fm, _ = vault.leer_pagina(Path("wiki/fuentes/banco-dos.md"))
    assert [p["codigo"] for p in fm["practicas"]] == ["Exp1", "Exp2", "Exp3"], "la fusion por codigo no pierde los experimentos que no se procesaron"
    print("E1. `ingest_manual --solo` extrae unicamente los experimentos pedidos (por codigo o numero), un experimento inexistente es un error y el resto de la pagina no se toca -- OK")

    escribir("raw/manuales-laboratorio/banco/manual.md", MANUAL.replace("Texto del segundo experimento.", "Texto del segundo experimento, corregido.")
             + "\n### Experiment 4 Cuarto experimento\n\nNuevo.\n")
    # RA: TPR01-RA1 apunta a Exp2 del manual (aceptado); TPR01-RA2 sin practica; TPR01-RA3 revisado por el docente
    editar("wiki/resultados-aprendizaje/TPR01-RA1.md", correlacion_estado="aceptado", requiere_practica="[[banco-dos]]", practica_experimentos=["Exp2"])
    editar("wiki/resultados-aprendizaje/TPR01-RA3.md", correlacion_revisado_por_docente=True)
    (cambio,) = ac.analizar_raw(ac.leer_base())
    assert cambio.categoria == "manual" and cambio.fuente == "banco-dos" and cambio.paginas == ["wiki/fuentes/banco-dos.md"]
    assert cambio.experimentos_modificados == ["2"] and cambio.experimentos_nuevos == ["4"] and cambio.experimentos_eliminados == []
    assert set(cambio.ras_a_correlacionar) == {"TPR01-RA1", "TPR01-RA2"}, cambio.ras_a_correlacionar          # ni la teorica (gate cerrado) ni la del docente
    assert "cambió en el manual" in cambio.ras_a_correlacionar["TPR01-RA1"] and "no tiene práctica aceptada" in cambio.ras_a_correlacionar["TPR01-RA2"]
    pasos, llamadas, _ = ac._comandos([cambio], [])
    comandos = [p["comando"] for p in pasos]
    assert "python src/ingest_manual.py raw/manuales-laboratorio/banco/manual.md --fuente banco-dos --solo Exp2 Exp4" in comandos, comandos
    assert "python src/correlate.py --indexar" in comandos and llamadas == 2
    print("E2. de un manual modificado sale el comando `--solo Exp2 Exp4`, y solo se vuelven a correlacionar los RA de gate abierto sin practica aceptada o que apuntan a lo que cambio -- OK")

    escribir("raw/manuales-laboratorio/banco/manual.md", MANUAL.replace("### Experiment 3 Tercer experimento\n\nTexto del tercero.\n", ""))
    (cambio,) = ac.analizar_raw(ac.leer_base())
    assert cambio.experimentos_eliminados == ["3"] and "Exp3" not in " ".join(c["comando"] for c in ac._comandos([cambio], [])[0] if "ingest" in c["comando"])
    escribir("raw/manuales-laboratorio/banco/manual.md", MANUAL)
    editar("wiki/resultados-aprendizaje/TPR01-RA1.md", correlacion_estado=None, requiere_practica=None, practica_experimentos=[])
    editar("wiki/resultados-aprendizaje/TPR01-RA3.md", correlacion_revisado_por_docente=False)
    print("E3. un experimento que desaparece del manual se informa (sigue en `practicas:`) y no se manda a extraer -- OK")


# --- F. libros y normas -----------------------------------------------------------------------------------------------


def probar_libro() -> None:
    editar("wiki/resultados-aprendizaje/TPR01-RA1.md", contenido_conceptual=["Máquinas de estados finitos", "Codificación de transiciones", "Temporizadores y contadores"])
    editar("wiki/resultados-aprendizaje/TPR01-RA2.md", contenido_conceptual=["Redes de comunicación industrial", "Protocolo Modbus"])
    ras = ac._ras_del_vault()
    cob = ac.cobertura_de_ras([LIBRO], ras, set())
    assert [c["ra"] for c in cob] == ["TPR01-RA1"], cob                       # ni el otro RA con conceptos distintos, ni los de contenido generico
    assert cob[0]["cubiertos"] == 3 and cob[0]["total"] == 3 and not cob[0]["ya_la_cita"]
    assert ac.cobertura_de_ras(["Texto que no dice nada de lo que busca ningún RA " * 5], ras, set()) == []
    assert ac.cobertura_de_ras([""], ras, set()) == []
    print("F1. un libro nuevo solo se relaciona con el RA cuyos conceptos aparecen en su texto (3 de 3), no con los demas -- OK")

    # temarios de TPR01, escritos a mano (sin LLM): los del RA1 sin apoyo en las fuentes
    planeador.generar_planeador("TPR01", sin_llm=True)
    escribir_temarios("TPR01", sin_apoyo={"TPR01-RA1"})
    escribir("raw/bibliografia/libro-de-maquinas-de-estados.md", LIBRO)
    fm_t = next(iter(sorted(Path("generacion/temarios").glob("TPR01-semana*.md"))))
    editar(fm_t.as_posix(), bibliografia_faltantes=[f"[3] A. Autor, «Libro de máquinas de estados», Editorial X. {temario.MARCADOR}"])
    cambios = ac.analizar_raw(ac.leer_base())
    (libro,) = [c for c in cambios if c.ruta.endswith("libro-de-maquinas-de-estados.md")]
    assert libro.estado == "nuevo" and libro.paginas == [] and [c["ra"] for c in libro.cobertura] == ["TPR01-RA1"]
    assert libro.faltantes_que_cubre and fm_t.stem in libro.faltantes_que_cubre[0], libro.faltantes_que_cubre
    plan = ac.analizar_generacion("TPR01", cambios)[0]
    semanas_ra1 = sorted(s.semana for s in construir_cronograma(*_asig("TPR01")).semanas if s.ra == "TPR01-RA1")
    assert sorted(plan.a_considerar) == semanas_ra1, (plan.a_considerar, semanas_ra1)
    assert all("sin apoyo suficiente" in m[-1] for m in plan.a_considerar.values())
    assert not plan.temarios, "una fuente nueva no obliga a rehacer nada: es opcional"
    pasos = ac._comandos(cambios, [plan])[0]
    assert all(p.get("opcional") for p in pasos if p["comando"].startswith("python src/temario.py"))
    print(f"F2. los temarios del RA que la fuente cubre (semanas {semanas_ra1}) salen como opcionales y marcados si se escribieron sin apoyo; una referencia sin cargar que se parece al libro se senala -- OK")

    escribir("raw/bibliografia/dato.pdf", "%PDF-falso")
    (pdf,) = [c for c in ac.analizar_raw(ac.leer_base()) if c.ruta.endswith("dato.pdf")]
    assert pdf.texto is False and pdf.cobertura == [] and pdf.tokens_a_leer == 0
    Path("raw/bibliografia/dato.pdf").unlink()
    Path("raw/bibliografia/libro-de-maquinas-de-estados.md").unlink()
    print("F3. un PDF no se lee: se avisa, sin analisis de relevancia -- OK")


# --- G. el wiki contra la generacion ---------------------------------------------------------------------------------


def _asig(codigo: str):
    nombre, asignatura, fm = vault.localizar_asignatura(codigo)
    return asignatura, vault.cargar_ras_de(fm)


def escribir_temarios(codigo: str, sin_apoyo: set[str] = frozenset()) -> None:
    """Un temario por semana de clase, como los dejaria TEMARIO (a mano: aqui no hay LLM ni dibujo)."""
    nombre, asignatura, fm_asig = vault.localizar_asignatura(codigo)
    fm_plan, _ = vault.leer_pagina(vault.PLANEADOR / f"{codigo}-planeador.md")
    competencias = temario.competencias_de(fm_asig)
    ras = {ra.codigo: ra for ra in vault.cargar_ras_de(fm_asig)}
    for fila in fm_plan["semanas"]:
        if fila["tipo"] != "clase":
            continue
        cuerpo = f"\n\n# Sesión de prueba\n\n## 2. Resultados de Aprendizaje\n\n{temario._alineacion(ras[fila['ra']], competencias)}\n\nAl finalizar...\n"
        fm = {"tipo": "temario", "asignatura": f"[[{nombre}]]", "resultado_aprendizaje": f"[[{fila['ra']}]]", "semana": fila["semana"],
              "horas_sesion": fm_plan["horas_sesion"], "horas_trabajo_independiente": horas_hti_semana(asignatura),
              "estadisticas": {"pasajes": 0 if fila["ra"] in sin_apoyo else 3}}
        vault.escribir_pagina(vault.TEMARIOS / f"{codigo}-semana{fila['semana']:02d}.md", fm, cuerpo)


def correlaciones_vigentes() -> None:
    """Todos los RA de TPR01 correlacionados y al dia (el score guardado es el actual)."""
    asignatura, ras = _asig("TPR01")
    for ra in ras:
        editar(f"wiki/resultados-aprendizaje/{ra.codigo}.md", correlacion_estado="aceptado", correlacion_fecha="2026-03-01",
               correlacion_score_ra=round(correlate.calcular_score_ra(ra, asignatura), 4))


def plan_de(codigo: str) -> ac.PlanAsignatura:
    return ac.analizar_generacion(codigo, [])[0]


def probar_desfases() -> None:
    editar("wiki/resultados-aprendizaje/TPR01-RA1.md", correlacion_revisado_por_docente=False)
    correlaciones_vigentes()
    plan = plan_de("TPR01")
    assert not (plan.avisos or plan.duracion or plan.semanas_distintas or plan.correlacionar or plan.temarios or plan.leves or plan.a_considerar), plan
    assert plan.clases == 11 and plan.ras == ["TPR01-RA1", "TPR01-RA2", "TPR01-RA3"] and len(plan.ras_gate) == 3 and not plan.sin_temario
    print("G1. con el wiki y la generacion consistentes no hay ningun desfase (11 clases, 3 RA, gate abierto en los 3) -- OK")

    asig_pagina = f"wiki/asignaturas/{_fixtures.TPR01}.md"
    editar(asig_pagina, hti_totales=68)
    plan = plan_de("TPR01")
    assert sorted(plan.leves) == list(plan.leves) and len(plan.leves) == 11 and not plan.temarios
    assert all("trabajo independiente: 4 h/semana en el temario, 5 ahora" in m[0] for m in plan.leves.values())
    pasos = ac._comandos([], [plan])[0]
    assert all(p.get("opcional") for p in pasos if "temario.py" in p["comando"]), "un desfase solo de cabecera nunca obliga a rehacer una sesion"
    editar(asig_pagina, hti_totales=54)
    print("G2. cambiar las horas de trabajo independiente deja un desfase leve en los 11 temarios (opcional): no cuesta rehacer las sesiones -- OK")

    editar(asig_pagina, had_totales=28)
    plan = plan_de("TPR01")
    assert plan.duracion == "planeador 4 h, ahora 2 h" and len(plan.temarios) == 11
    assert all("duración: el temario es de 4 h y la sesión es de 2 h" in m[0] for m in plan.temarios.values())
    pasos, llamadas, todo = ac._comandos([], [plan])
    assert any("planeador.py TPR01 --forzar" in p["comando"] for p in pasos) and llamadas == 3 + 11 * 10 + 11 * 9 and todo == 11 * (10 + 9) + 3 * 2 + 3 * 3
    assert next(p for p in pasos if "presentaciones.py" in p["comando"])["llm"] == 11 * 9, "~9 llamadas por presentacion rehecha (una por parte)"
    editar(asig_pagina, had_totales=42)
    print("G3. una sesion que pasa de 4 h a 2 h obliga a rehacer el planeador y las 11 sesiones (y el costo se calcula) -- OK")

    antes = {s.semana: s.ra for s in construir_cronograma(*_asig("TPR01")).semanas}
    editar("wiki/resultados-aprendizaje/TPR01-RA3.md", horas=88)
    despues = {s.semana: s.ra for s in construir_cronograma(*_asig("TPR01")).semanas}
    cambian = sorted(n for n in antes if antes[n] != despues[n])
    assert cambian, "el cambio de horas debe mover semanas"
    plan = plan_de("TPR01")
    assert len(plan.semanas_distintas) == len(cambian) and sorted(plan.temarios) == [n for n in cambian if despues[n]], (plan.temarios, cambian)
    assert all("el RA de la semana es ahora" in m[0] for m in plan.temarios.values())
    assert len(plan.temarios) < 11, "solo se rehacen las semanas cuyo RA cambio, no todas"
    editar("wiki/resultados-aprendizaje/TPR01-RA3.md", horas=30)
    print(f"G4. si las horas de un RA mueven el cronograma, solo se rehacen las {len(cambian)} semanas cuyo RA cambio (no las 11) -- OK")

    editar("wiki/resultados-aprendizaje/TPR01-RA1.md", enunciado="Enunciado nuevo del RA1.")
    plan = plan_de("TPR01")
    ra1 = sorted(s for s, ra in antes.items() if ra == "TPR01-RA1")
    assert sorted(plan.leves) == ra1 and not plan.temarios, (plan.leves, ra1)
    assert all("alineación con el RA" in m[0] for m in plan.leves.values())
    editar("wiki/resultados-aprendizaje/TPR01-RA1.md", enunciado="Enunciado de ejemplo de TPR01-RA1.")
    print("G5. reformular el enunciado de un RA deja un desfase leve solo en las sesiones de ese RA -- OK")

    editar(f"wiki/resultados-aprendizaje/TPR01-RA2.md", correlacion_score_ra=0.5)
    editar(f"wiki/resultados-aprendizaje/TPR01-RA3.md", correlacion_estado="pendiente_revision", correlacion_fecha="2026-01-01")
    editar("wiki/fuentes/banco-uno.md", fecha_actualizacion="2026-06-01")
    editar(f"wiki/resultados-aprendizaje/TPR01-RA1.md", correlacion_revisado_por_docente=True, correlacion_score_ra=0.1)
    editar("wiki/resultados-aprendizaje/TEO01-RA1.md", requiere_practica="[[banco-uno]]", practica_experimentos=["Exp1"], correlacion_estado="aceptado")
    plan = ac.analizar_generacion(None, [])
    tpr = next(p for p in plan if p.codigo == "TPR01")
    teo = next(p for p in plan if p.codigo == "TEO01")
    assert set(tpr.correlacionar) == {"TPR01-RA2", "TPR01-RA3"}, tpr.correlacionar                     # el RA1 es del docente: no se toca
    assert "el score cambió" in tpr.correlacionar["TPR01-RA2"] and f"un manual se actualizó el {vault.hoy()}, después de su última correlación (2026-01-01)" in tpr.correlacionar["TPR01-RA3"], tpr.correlacionar        # banco-dos (E1) es de hoy
    assert "el gate se cerró" in teo.correlacionar["TEO01-RA1"] and teo.sin_planeador
    pasos = ac._comandos([], plan)[0]
    assert "python src/correlate.py --asignatura TPR01 --ra TPR01-RA2 TPR01-RA3" in [p["comando"] for p in pasos]
    for ra in ("TPR01-RA1", "TPR01-RA2", "TPR01-RA3"):
        editar(f"wiki/resultados-aprendizaje/{ra}.md", correlacion_revisado_por_docente=False)
    editar("wiki/resultados-aprendizaje/TEO01-RA1.md", requiere_practica=None, practica_experimentos=[], correlacion_estado="sin_candidato")
    editar("wiki/fuentes/banco-uno.md", fecha_actualizacion="YYYY-MM-DD")
    correlaciones_vigentes()
    print("G6. la correlacion se marca desactualizada si cambio el score, un manual es mas nuevo o el gate se cerro; la decision del docente no se toca; solo esos RA van a `--ra` -- OK")

    for archivo in Path("generacion/temarios").glob("TPR01-semana0[1-2].md"):
        archivo.unlink()
    assert plan_de("TPR01").sin_temario == [1, 2], "una asignatura con temarios a medias dice cuales le faltan"
    editar(asig_pagina, resultados_aprendizaje=[f"[[TPR01-RA1]]", "[[TPR01-RA9]]"])
    plan = plan_de("TPR01")
    assert any("TPR01-RA9" in a and "no tiene página" in a for a in plan.avisos), plan.avisos
    print("G7. las semanas sin temario y un RA que la asignatura lista pero no existe se informan -- OK")


# --- H. correlate --ra -----------------------------------------------------------------------------------------------------


def probar_correlate_ra() -> None:
    editar(f"wiki/asignaturas/{_fixtures.TPR01}.md", resultados_aprendizaje=["[[TPR01-RA1]]", "[[TPR01-RA2]]", "[[TPR01-RA3]]"])
    todos = correlate.correlacionar_vault("TPR01", dry_run=True)
    assert todos["total"] == 3
    dos = correlate.correlacionar_vault("TPR01", dry_run=True, codigos_ra=["TPR01-RA2", "TPR01-RA3"])
    assert dos["total"] == 2 and dos["gate_abierto"] == 2 and not dos["errores"], dos
    assert correlate.correlacionar_vault(None, dry_run=True, codigos_ra=["TEO01-RA1"])["total"] == 1
    falta = correlate.correlacionar_vault("TPR01", dry_run=True, codigos_ra=["TPR01-RA2", "TPR01-RA7"])
    assert falta["total"] == 1 and falta["errores"] == ["TPR01-RA7: no hay ningún RA con ese código en wiki/resultados-aprendizaje/"], falta
    r = subprocess.run([sys.executable, "-B", str(SRC / "correlate.py"), "--asignatura", "TPR01", "--ra", "TPR01-RA1", "--dry-run"],
                       capture_output=True, text=True, encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
    assert r.returncode == 0 and "1 RA: gate abierto 1" in r.stdout, (r.stdout, r.stderr)
    r = subprocess.run([sys.executable, "-B", str(SRC / "correlate.py"), "--indexar", "--ra", "X"], capture_output=True, text=True,
                       encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
    assert r.returncode != 0 and "--ra no se combina con --indexar" in r.stderr
    print("H1. `correlate.py --ra` correlaciona solo esos RA, un codigo que no existe es un error y no se combina con --indexar -- OK")


# --- I. informe, JSON, CLI y solo lectura ---------------------------------------------------------------------------------


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(SRC / "analizar_cambios.py"), *args], capture_output=True, text=True, encoding="utf-8",
                          env=ENTORNO, stdin=subprocess.DEVNULL)


def probar_informe() -> None:
    ac.confirmar()
    r = cli()
    assert r.returncode == 0 and "Todo al día" in r.stdout and "Sin cambios en raw/" in r.stdout, r.stdout
    print("I1. con la linea base fijada y el wiki consistente el informe dice `Todo al día` -- OK")

    escribir("raw/curriculos/Prog/TPR01.md", CURRICULO.replace("| 42 | 26 | 54 | 2 |", "| 42 | 30 | 54 | 2 |"))
    escribir("raw/bibliografia/libro-de-maquinas-de-estados.md", LIBRO)
    editar(f"wiki/asignaturas/{_fixtures.TPR01}.md", hti_totales=68)
    antes = huella_de_arbol("wiki", "generacion", "raw")
    r = cli("--detalle")
    assert r.returncode == 0, (r.stdout, r.stderr)
    for esperado in ("MODIFICADO", "raw/curriculos/Prog/TPR01.md", "hp_totales", "arrastra:", "NUEVO", "raw/bibliografia/libro-de-maquinas-de-estados.md",
                     "TPR01-RA1: 3 de 3 conceptos", "== 2. wiki/ contra generacion/", "desfase solo de cabecera", "== 3. Plan mínimo ==",
                     "(opcional)", "| 42 | 30 | 54 | 2 |", "Al terminar: `python src/analizar_cambios.py --confirmar`"):
        assert esperado in r.stdout, (esperado, r.stdout)
    assert huella_de_arbol("wiki", "generacion", "raw") == antes, "el analisis es de solo lectura: no toca wiki/, generacion/ ni raw/"
    print("I2. el informe de texto trae los cambios, a que RA sirve el libro, los desfases, el plan y (con --detalle) el texto de la seccion que cambio; no escribe nada -- OK")

    r = cli("--json")
    informe = json.loads(r.stdout)
    assert informe["base"] and {c["ruta"] for c in informe["cambios"]} == {"raw/curriculos/Prog/TPR01.md", "raw/bibliografia/libro-de-maquinas-de-estados.md"}
    assert informe["al_dia"] is False and any(p["comando"] == "python src/lint.py" for p in informe["pasos"])
    assert cli("--asignatura", "TEO01", "--json").returncode == 0
    r = cli("--asignatura", "NOEXISTE")
    assert r.returncode == 1 and "No hay ninguna asignatura con codigo NOEXISTE" in r.stdout and "Traceback" not in r.stderr, (r.stdout, r.stderr)
    r = cli("--confirmar", "raw/curriculos/Prog/TPR01.md")
    assert r.returncode == 0 and "Línea base fijada: 1 archivos" in r.stdout, r.stdout
    assert all(c["ruta"] != "raw/curriculos/Prog/TPR01.md" for c in json.loads(cli("--json").stdout)["cambios"])
    r = cli("--confirmar", "raw/no-existe")
    assert r.returncode == 1 and "no es un archivo ni una carpeta" in r.stdout
    assert cli("--help").returncode == 0
    print("I3. `--json` es el mismo informe, `--asignatura` acota, un codigo que no existe da un mensaje (no un traceback) y `--confirmar RUTA` fija solo ese documento -- OK")


def main() -> None:
    probar_secciones()
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar_linea_base()
            probar_comparacion()
            probar_curriculo()
            probar_manual()
            probar_libro()
            probar_desfases()
            probar_correlate_ra()
            probar_informe()
        finally:
            os.chdir(original)
    print("TODO OK -- ANALIZAR-CAMBIOS dice que actualizar y que no, sin LLM y sin escribir en el wiki.")


if __name__ == "__main__":
    main()
