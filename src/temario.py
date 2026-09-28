"""TEMARIO -- una sesion de clase por semana de clase (nunca por semana de examen).

Lee el planeador (generacion/planeador/{codigo}-planeador.md), el RA que le toca a la semana, sus fuentes cargadas y las
competencias de la asignatura, y escribe la sesion completa en generacion/temarios/{codigo}-semanaNN.md.

La sesion sigue la estructura de una guia de sesion universitaria (docs: CLAUDE.md, "Paginas de temario"):

    # Titulo  +  cabecera (modulos, duracion, nivel, plataforma, semana y RA)
    1. Metadatos de la Sesion (continuidad curricular, prerrequisitos)   2. Resultados de Aprendizaje
    3. Indice Temporizado   4. Desarrollo Teorico (introduccion + conceptos clave)   5. Caso de Estudio Aplicado
    6. Analisis cuantitativo (opcional)   7. Implementacion de referencia (opcional)   8. Sintesis   9. Bibliografia IEEE

Se redacta en TRES pasos (una sola llamada saldria corta y superficial):
    1. el PLAN (PlanSesion): titulo, resultados de la sesion y las unidades de contenido, cada una con su peso, los terminos
       con que buscar en las fuentes y los elementos (ecuaciones, tablas, graficas, diagramas, codigo) que debe llevar;
    2. cada UNIDAD (SeccionRedactada), con los pasajes de las fuentes cargadas mas relevantes para ella (pasajes.py: BM25 sobre
       el texto completo de raw/ y las paginas de wiki/fuentes/) y un minimo de palabras de prosa;
    3. el CIERRE (CierreSesion): la sintesis y la reflexion actitudinal.
Lo que el LLM devuelve no es Markdown suelto sino bloques (schema_temario.py): el codigo escribe las tablas, numera las figuras y
las dibuja (figuras.py). Lo que no cumple (una tabla descuadrada, una formula inexistente, menos palabras que el minimo, una cita
[n] que no existe) se devuelve al modelo con el motivo, hasta REINTENTOS veces.

Separa lo determinista de lo generativo, igual que el resto del vault: la cabecera, la alineacion con el RA (enunciado, criterios y
competencias), los minutos de cada bloque del indice (schema_planeador.minutos_por_bloque), la numeracion, la lista de sesiones
vecinas y la bibliografia las arma el codigo; el LLM solo redacta. Toda cita a una fuente que no esta cargada se marca en linea con
`[FUENTE NO CARGADA EN raw/]`, asi CORRELATE-BIBLIOGRAFIA detecta los huecos con un grep.

Uso (desde la raiz del vault):
    python src/temario.py ABC01 --semana 3
    python src/temario.py ABC01 --todas          # todas las semanas de clase que aun no tengan temario
    python src/temario.py ABC01 --semana 3 --forzar
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

import correlate
import figuras
import pasajes
import vault
from schema_extraccion import Asignatura, Practica, ResultadoAprendizajeModulo, TipoAbordaje
from schema_planeador import SEMANAS_TOTALES, corte_evaluativo, horas_hti_semana, minutos_por_bloque
from schema_temario import (
    Bloque,
    CierreSesion,
    ClaseUnidad,
    ElementoPlan,
    PlanSesion,
    SeccionRedactada,
    TipoBloque,
    UnidadPlan,
    celdas_de_tabla,
    elementos_de,
    palabras_de,
)

MARCADOR = "[FUENTE NO CARGADA EN raw/]"

REINTENTOS = 2                       # cuantas veces se le devuelve al modelo lo que no cumplio (ademas del primer intento)
PALABRAS_MINIMAS = {                 # de prosa por unidad en una sesion de 2 h; con 4 h se multiplican (ver factor_profundidad)
    ClaseUnidad.introduccion: 220, ClaseUnidad.concepto: 320, ClaseUnidad.caso: 380,
    ClaseUnidad.analisis: 220, ClaseUnidad.implementacion: 180,
}
PALABRAS_MINIMAS_SINTESIS = 110
PASAJES_POR_UNIDAD, CARACTERES_DE_PASAJES = 5, 7000
_MIN_SUBTITULOS_CASO = 2

TITULO_INTRODUCCION = "Introducción Conceptual"
_ORDEN_CLASES = [ClaseUnidad.introduccion, ClaseUnidad.concepto, ClaseUnidad.caso, ClaseUnidad.analisis, ClaseUnidad.implementacion, ClaseUnidad.sintesis]


def factor_profundidad(horas_sesion: int) -> float:
    """2 h -> 1.0; 4 h -> 1.4: una sesion mas larga pide mas desarrollo por unidad."""
    return 1 + 0.2 * (horas_sesion - 2)


def palabras_minimas(clase: ClaseUnidad, horas_sesion: int) -> int:
    base = PALABRAS_MINIMAS_SINTESIS if clase == ClaseUnidad.sintesis else PALABRAS_MINIMAS[clase]
    return round(base * factor_profundidad(horas_sesion))


# ---------------------------------------------------------------------------
# Lo que se lee del vault
# ---------------------------------------------------------------------------


def _resumen(cuerpo: str, maximo: int = 1800) -> str:
    """'## Resumen' + '## Puntos clave' de una fuente (o el inicio de la pagina si no
    tiene esas secciones), recortado. Este texto es el contexto que ve tanto el LLM de
    TEMARIO como el juez de respaldo de CORRELATE-BIBLIOGRAFIA -- si se recorta demasiado
    corto, el juez no puede evaluar cobertura real y todo termina en 'revisar'."""
    def _seccion(nombre: str) -> str:
        if f"## {nombre}" not in cuerpo:
            return ""
        return cuerpo.split(f"## {nombre}", 1)[1].split("\n## ", 1)[0]

    resumen, puntos_clave = _seccion("Resumen"), _seccion("Puntos clave")
    texto = f"{resumen}\n{puntos_clave}" if (resumen or puntos_clave) else cuerpo
    return " ".join(texto.split())[:maximo]


def _cabecera(cuerpo: str, maximo: int = 450) -> str:
    """El titulo y los datos de una fuente (lo que hay antes del primer `##`): de ahi sale su referencia IEEE."""
    return " ".join(cuerpo.split("\n## ", 1)[0].split())[:maximo]


def fuentes_del_ra(fm_ra: dict) -> list[tuple[str, str]]:
    """(nombre, resumen) de las fuentes de wiki/fuentes/ que el RA enlaza en `bibliografia`."""
    fuentes = []
    for nombre in vault.enlaces(fm_ra.get("bibliografia")):
        ruta = vault.FUENTES / f"{nombre}.md"
        if ruta.exists():
            fuentes.append((nombre, _resumen(vault.leer_pagina(ruta)[1])))
    return fuentes


def competencias_de(fm_asignatura: dict) -> list[tuple[str, str]]:
    """(nombre, texto) de las competencias que la asignatura enlaza en `competencias`."""
    competencias = []
    for nombre in vault.enlaces(fm_asignatura.get("competencias")):
        ruta = vault.COMPETENCIAS / f"{nombre}.md"
        if ruta.exists():
            fm, _ = vault.leer_pagina(ruta)
            competencias.append((nombre, fm.get("texto") or ""))
    return competencias


def practica_de_referencia(asignatura: Asignatura, fm_ra: dict) -> tuple[str, str | None, str | None, Practica | None]:
    """(texto para el prompt, enlace para el cuerpo, fuente, practica) de la practica que el RA requiere."""
    if asignatura.tipo_abordaje != TipoAbordaje.teorico_practica:
        return "(ninguna: la asignatura es teórica)", None, None, None
    fuente = vault.enlace(fm_ra.get("requiere_practica"))
    experimentos = fm_ra.get("practica_experimentos") or []
    if not fuente or not experimentos:
        return "(ninguna: el RA no tiene una práctica asignada)", None, None, None
    practica = correlate.cargar_practica(fuente, experimentos[0])
    texto = (f"{practica.codigo} — {practica.nombre_original} (manual: {fuente}). "
             f"Propósito: {'; '.join(practica.proposito)}. Principio: {practica.principio_resumen}")
    return texto, f"[[{fuente}]] — {practica.codigo}", fuente, practica


def fuentes_de_la_sesion(fm_ra: dict, fuente_practica: str | None) -> list[pasajes.FuenteTexto]:
    """Las fuentes con las que se escribe la sesion (y que se numeran [1], [2]... para citarlas): las que el RA enlaza en
    `bibliografia` y el manual de la practica de referencia, si la hay. Solo las que ya tienen pagina en wiki/fuentes/."""
    nombres: list[str] = []
    for nombre in [*vault.enlaces(fm_ra.get("bibliografia")), *([fuente_practica] if fuente_practica else [])]:
        if nombre not in nombres and (vault.FUENTES / f"{nombre}.md").exists():
            nombres.append(nombre)
    return [pasajes.cargar_fuente(n) for n in nombres]


def _describir_fuentes(fuentes: list[pasajes.FuenteTexto], detallado: bool) -> str:
    lineas = []
    for i, f in enumerate(fuentes, 1):
        if not detallado:
            lineas.append(f"[{i}] {f.nombre}")
            continue
        cuerpo = vault.leer_pagina(vault.FUENTES / f"{f.nombre}.md")[1]
        texto_completo = f"texto completo disponible ({len(f.pasajes)} pasajes)" if f.archivos else "solo la página del wiki (sin texto completo)"
        lineas.append(f"[{i}] {f.nombre} — datos: {_cabecera(cuerpo)} — resumen: {_resumen(cuerpo, 900)} — {texto_completo}")
    return "\n".join(lineas) or "(ninguna: el RA no tiene fuentes enlazadas en `bibliografia`)"


def _modulos(nombre_pagina: str, asignatura: Asignatura, fm_asignatura: dict) -> str:
    """'ABC01 — Nombre · XYZ02 — Otro': la asignatura y los modulos que comparten con ella su curriculo (`modulo_homologo`)."""
    modulos = [f"{asignatura.codigo} — {asignatura.nombre}"]
    homologos = list(vault.enlaces(fm_asignatura.get("modulo_homologo")))
    for ruta in sorted(vault.ASIGNATURAS.glob("*.md")):
        if ruta.stem != nombre_pagina and nombre_pagina in vault.enlaces(vault.leer_pagina(ruta)[0].get("modulo_homologo")):
            homologos.append(ruta.stem)
    for nombre in dict.fromkeys(homologos):
        ruta = vault.ASIGNATURAS / f"{nombre}.md"
        if ruta.exists():
            fm, _ = vault.leer_pagina(ruta)
            modulos.append(f"{fm.get('codigo')} — {fm.get('nombre')}")
    return " · ".join(modulos)


def _nivel(fm_asignatura: dict) -> str | None:
    """El `nivel` de la pagina del primer programa de la asignatura que lo indique (no se inventa: sin dato, no hay linea)."""
    for programa in vault.enlaces(fm_asignatura.get("programa")):
        ruta = vault.WIKI / "programas" / f"{vault.destino_pagina(programa)}.md"
        if ruta.exists():
            nivel = vault.leer_pagina(ruta)[0].get("nivel")
            if nivel:
                return str(nivel)
    return None


def _sesion_vecina(filas: dict[int, dict], semana: int) -> str:
    fila = filas.get(semana)
    if fila is None:
        return "(no hay: fuera del semestre)"
    if fila["tipo"] == "examen":
        return f"semana {semana}: evaluación (semana de examen)"
    return f"semana {semana}: {fila.get('tema') or 'sin tema redactado'}"


# ---------------------------------------------------------------------------
# Llamadas al LLM con validacion y reintentos
# ---------------------------------------------------------------------------


def _correccion(problemas: list[str]) -> str:
    lista = "\n".join(f"- {p}" for p in problemas)
    return ("Tu respuesta anterior NO cumplió lo pedido. Corrígelo y devuelve el objeto completo de nuevo:\n" + lista)[:2500]


def _redactar(sistema: str, usuario: str, formato, validar: Callable, contexto: str):
    """Pide `formato` al LLM; si no valida (esquema o `validar`), le devuelve el motivo y repite, hasta REINTENTOS veces. El ultimo
    intento no aplica las comprobaciones blandas (`blando=False`): algo que solo afecta a la presentacion no detiene la sesion."""
    problemas: list[str] = []
    for intento in range(REINTENTOS + 1):
        pedido = usuario if not problemas else f"{usuario}\n\n{_correccion(problemas)}"
        try:
            salida = vault.pedir_estructurado(sistema, pedido, formato)
            problemas = validar(salida, intento < REINTENTOS) if salida is not None else ["el modelo no devolvió un objeto (¿rechazó la petición?)"]
        except ValueError as error:                    # el esquema (Pydantic) o el JSON no valen
            problemas = [str(error)[:900]]
        if not problemas:
            return salida
    raise ValueError(f"{contexto}: el modelo no cumplió lo pedido tras {REINTENTOS + 1} intentos: " + "; ".join(problemas)[:900])


def _validar_plan(plan: PlanSesion, ra: ResultadoAprendizajeModulo, n_fuentes: int) -> list[str]:
    problemas: list[str] = []
    codigos = {ce.codigo for ce in ra.criterios_evaluacion}
    citados: set[str] = set()
    for r in plan.resultados_sesion:
        ajenos = sorted(set(r.criterios) - codigos)
        if ajenos:
            problemas.append(f"un resultado de la sesión cita criterios que el RA no tiene: {', '.join(ajenos)} (los del RA son {', '.join(sorted(codigos))})")
        citados |= set(r.criterios)
    if codigos and not codigos <= citados:
        problemas.append(f"los resultados de la sesión no cubren los criterios de evaluación {', '.join(sorted(codigos - citados))}: cada criterio del RA debe estar en `criterios` de algún resultado")
    if len(plan.referencias_cargadas) != n_fuentes:
        problemas.append(f"`referencias_cargadas` debe tener {n_fuentes} entradas (una por fuente cargada, en el mismo orden) y tiene {len(plan.referencias_cargadas)}")
    return problemas


_CITA = re.compile(r"(?<![\w\]])\[(\d{1,2})\](?!\()")
_MATE_EN_LINEA = re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$")
_TIPOS_DE_PROSA = (TipoBloque.parrafo, TipoBloque.lista, TipoBloque.nota)


def _texto_de(bloques: list[Bloque], con_codigo: bool = False) -> str:
    partes = []
    for b in bloques:
        if b.tipo in _TIPOS_DE_PROSA or b.tipo == TipoBloque.subtitulo:
            partes.append(b.contenido)
        if b.tipo == TipoBloque.tabla:
            partes.append(f"{b.leyenda} {b.contenido}")
        if b.tipo in (TipoBloque.grafica, TipoBloque.diagrama, TipoBloque.codigo):
            partes.append(b.leyenda)
        if b.tipo == TipoBloque.nota:
            partes.append(b.leyenda)
        if con_codigo and b.tipo == TipoBloque.codigo:
            partes.append(b.contenido)
    return "\n".join(partes)


def _validar_unidad(unidad: UnidadPlan, s: SeccionRedactada, plan: PlanSesion, horas_sesion: int, n_fuentes: int,
                    practica: Practica | None, blando: bool) -> list[str]:
    problemas: list[str] = []
    if not s.bloques:
        return ["la unidad no tiene bloques"]
    palabras, minimo = palabras_de(s.bloques), palabras_minimas(unidad.clase, horas_sesion)
    if palabras < minimo:
        problemas.append(f"la prosa tiene {palabras} palabras y el mínimo de esta unidad es {minimo}: desarrolla más (deducciones paso a paso, ejemplos con números, límites y errores frecuentes)")
    cuenta = elementos_de(s.bloques)
    for elemento in unidad.elementos:
        if not cuenta[elemento]:
            problemas.append(f"falta un bloque de tipo `{elemento.value}`, que el plan asigna a esta unidad")
    if not plan.usa_graficas and cuenta[ElementoPlan.grafica]:
        problemas.append("el plan dice que el tema no usa gráficas: usa un `diagrama` en su lugar")
    subtitulos = sum(1 for b in s.bloques if b.tipo == TipoBloque.subtitulo)
    if unidad.clase in (ClaseUnidad.introduccion, ClaseUnidad.concepto) and subtitulos:
        problemas.append("esta clase de unidad no lleva `subtitulo`: el título ya lo pone el código")
    if unidad.clase == ClaseUnidad.caso and subtitulos < _MIN_SUBTITULOS_CASO:
        problemas.append(f"el caso de estudio necesita al menos {_MIN_SUBTITULOS_CASO} bloques `subtitulo` (descripción del sistema, cálculos, resultados…) y tiene {subtitulos}")
    if s.bloques[0].tipo == TipoBloque.subtitulo and unidad.clase != ClaseUnidad.caso and unidad.clase != ClaseUnidad.analisis and unidad.clase != ClaseUnidad.implementacion:
        problemas.append("la unidad no puede empezar con un subtítulo")
    texto = _texto_de(s.bloques)
    invalidas = sorted({int(n) for n in _CITA.findall(texto) if not 1 <= int(n) <= n_fuentes})
    if invalidas:
        problemas.append(f"citas [n] a fuentes que no existen: {', '.join(f'[{n}]' for n in invalidas)} (hay {n_fuentes} fuente(s) cargada(s); para otra fuente usa el marcador {MARCADOR} y `referencias_externas`)")
    if unidad.clase == ClaseUnidad.caso and practica and practica.codigo not in _texto_de(s.bloques, con_codigo=True):
        problemas.append(f"el caso debe apoyarse en la práctica de referencia: nombra su código {practica.codigo} y sus mismas mediciones")
    if blando:
        from latex_seguro import comandos_no_permitidos

        formulas = [b.contenido for b in s.bloques if b.tipo == TipoBloque.ecuacion]
        formulas += [m for b in s.bloques if b.tipo in _TIPOS_DE_PROSA for m in _MATE_EN_LINEA.findall(b.contenido)]
        malos = sorted({c for f in formulas for c in comandos_no_permitidos(f)})
        if malos:
            problemas.append("comandos LaTeX poco comunes que la presentación no admite: " + ", ".join(malos) + " (reescribe esas fórmulas con LaTeX estándar de amsmath)")
    return problemas


def _validar_cierre(c: CierreSesion, horas_sesion: int) -> list[str]:
    problemas = []
    palabras, minimo = len(re.findall(r"\w+", c.sintesis)), palabras_minimas(ClaseUnidad.sintesis, horas_sesion)
    if palabras < minimo:
        problemas.append(f"la síntesis tiene {palabras} palabras y el mínimo es {minimo}")
    if not 15 <= len(re.findall(r"\w+", c.reflexion_actitudinal)) <= 90:
        problemas.append("la reflexión actitudinal debe tener de 25 a 60 palabras")
    if "$$" in c.sintesis or len(re.findall(r"(?<!\\)\$", c.sintesis)) % 2 != 0:
        problemas.append("la síntesis lleva `$$` o signos `$` sin cerrar")
    return problemas


# ---------------------------------------------------------------------------
# Escritura del Markdown
# ---------------------------------------------------------------------------


def _tabla_md(encabezados: list[str], filas: list[list[str]]) -> str:
    def fila(celdas: list[str]) -> str:
        return "| " + " | ".join(str(c).replace("\n", " ").replace("|", "\\|") for c in celdas) + " |"

    return "\n".join([fila(encabezados), fila(["---"] * len(encabezados)), *[fila(f) for f in filas]])


def _sin_numero(entrada: str) -> str:
    return re.sub(r"^\[\d+\]\s*", "", entrada.strip())


class _Numeracion:
    """Numera tablas, figuras y listados en el orden en que aparecen, y junta las figuras que hay que dibujar."""

    def __init__(self, codigo: str, semana: int):
        self.prefijo = f"{codigo}-semana{semana:02d}"
        self.tablas = self.figuras = self.listados = 0
        self.por_dibujar: list[tuple[str, object]] = []     # (nombre del PNG, especificacion)


def _bloques_md(bloques: list[Bloque], numeracion: _Numeracion, seccion: str) -> str:
    """Los bloques de una unidad como Markdown. `seccion` ('5') numera los subtitulos ('### 5.1 ...')."""
    partes: list[str] = []
    subtitulos = 0
    for b in bloques:
        c = b.contenido.strip()
        if b.tipo == TipoBloque.parrafo:
            partes.append(" ".join(c.split()))
        elif b.tipo == TipoBloque.lista:
            lineas = [re.sub(r"^\s*([-*•]|\d+[.)])\s+", "", l).strip() for l in c.splitlines() if l.strip()]
            partes.append("\n".join(f"- {l}" for l in lineas))
        elif b.tipo == TipoBloque.ecuacion:
            partes.append(f"$$\n{c}\n$$")
        elif b.tipo == TipoBloque.tabla:
            numeracion.tablas += 1
            encabezados, filas = celdas_de_tabla(c)
            partes.append(f"**Tabla {numeracion.tablas}.** {' '.join(b.leyenda.split())}\n\n{_tabla_md(encabezados, filas)}")
        elif b.tipo == TipoBloque.nota:
            etiqueta = b.leyenda.strip().rstrip(":") or "Nota"
            partes.append(f"> **{etiqueta}:** {' '.join(c.split())}")
        elif b.tipo == TipoBloque.codigo:
            numeracion.listados += 1
            titulo = f"**Listado {numeracion.listados}.** {' '.join(b.leyenda.split())}\n\n" if b.leyenda.strip() else ""
            partes.append(f"{titulo}```{b.lenguaje.strip().lower()}\n{c}\n```")
        elif b.tipo in (TipoBloque.grafica, TipoBloque.diagrama):
            numeracion.figuras += 1
            nombre = f"{numeracion.prefijo}-fig{numeracion.figuras}.png"
            numeracion.por_dibujar.append((nombre, b.grafica if b.tipo == TipoBloque.grafica else b.diagrama))
            pie = " ".join(b.leyenda.split())
            alt = pie.replace("[", "(").replace("]", ")")
            partes.append(f"![Figura {numeracion.figuras}. {alt}](figuras/{nombre})\n\n*Figura {numeracion.figuras}. {pie}*")
        elif b.tipo == TipoBloque.subtitulo:
            subtitulos += 1
            partes.append(f"### {seccion}.{subtitulos} {c}")
    return "\n\n".join(partes)


def _lista_numerada(items: list[str]) -> str:
    return "\n".join(f"{i}. {t}" for i, t in enumerate(items, 1))


def _negrita_al_inicio(texto: str) -> str:
    texto = texto.strip()
    return texto if texto.startswith("**") else re.sub(r"^(\S+)", r"**\1**", texto, count=1)


def _alineacion(ra: ResultadoAprendizajeModulo, competencias: list[tuple[str, str]]) -> str:
    criterios = "\n".join(f"- **{ce.codigo}** ({ce.categoria_accion.value}): {ce.texto}" for ce in ra.criterios_evaluacion) \
        or "(sin criterios de evaluación cargados)"
    partes = [f"**RA {ra.codigo}:** {ra.enunciado}", f"**Criterios de evaluación:**\n{criterios}"]
    if competencias:
        partes.append("**Unidades de competencia de la asignatura:**\n" + "\n".join(f"- [[{n}]]: {t}" for n, t in competencias))
    return "\n\n".join(partes)


def renderizar_temario(nombre_pagina: str, codigo: str, asignatura: Asignatura, fm_asignatura: dict, ra: ResultadoAprendizajeModulo,
                       competencias: list[tuple[str, str]], semana: int, filas_plan: dict[int, dict], horas_sesion: int,
                       plan: PlanSesion, unidades: list[tuple[UnidadPlan, SeccionRedactada]], cierre: CierreSesion,
                       enlace_practica: str | None, pasajes_usados: int) -> tuple[dict, str, list[tuple[str, object]]]:
    """(frontmatter, cuerpo, figuras por dibujar) de la sesion. Los minutos del indice y toda la numeracion salen de aqui."""
    hoy = vault.hoy()
    hti_semana = horas_hti_semana(asignatura)
    minutos = minutos_por_bloque([u.peso for u, _ in unidades], horas_sesion)
    numeracion = _Numeracion(codigo, semana)
    externas = [e for _, s in unidades for e in s.referencias_externas]

    def unidad_de(clase: ClaseUnidad) -> list[tuple[int, UnidadPlan, SeccionRedactada]]:
        return [(k, u, s) for k, (u, s) in enumerate(unidades, 1) if u.clase == clase]

    (k_intro, u_intro, s_intro), = unidad_de(ClaseUnidad.introduccion)
    conceptos = unidad_de(ClaseUnidad.concepto)
    (k_caso, u_caso, s_caso), = unidad_de(ClaseUnidad.caso)
    extras = unidad_de(ClaseUnidad.analisis) + unidad_de(ClaseUnidad.implementacion)
    (k_sintesis, _u_sintesis, _), = unidad_de(ClaseUnidad.sintesis)

    # --- cabecera ---
    cabecera = [f"> **Módulos:** {_modulos(nombre_pagina, asignatura, fm_asignatura)}",
                f"> **Duración:** {horas_sesion * 60} minutos (sesión {asignatura.tipo_abordaje.value})"]
    if nivel := _nivel(fm_asignatura):
        cabecera.append(f"> **Nivel:** {nivel}")
    if plan.plataforma_referencia and plan.plataforma_referencia.strip():
        cabecera.append(f"> **Plataforma de referencia:** {plan.plataforma_referencia.strip()}")
    cabecera.append(f"> **Semana:** {semana} de {SEMANAS_TOTALES} (corte evaluativo {corte_evaluativo(semana)}) · "
                    f"**Resultado de aprendizaje del módulo:** [[{ra.codigo}]] · **Trabajo independiente:** {hti_semana} h/semana")

    # --- 1. metadatos ---
    anterior, presente, siguiente = (_sesion_vecina(filas_plan, semana - 1) if semana > 1 else None,
                                     f"**→ Presente sesión (semana {semana}):** {filas_plan.get(semana, {}).get('tema') or ra.enunciado}",
                                     _sesion_vecina(filas_plan, semana + 1) if semana < SEMANAS_TOTALES else None)
    secuencia = _lista_numerada([x[0].upper() + x[1:] if x else x for x in (anterior, presente, siguiente) if x])
    metadatos = (f"## 1. Metadatos de la Sesión\n\n### 1.1 Continuidad curricular\n\n{' '.join(plan.continuidad.split())}\n\n{secuencia}\n\n"
                 f"### 1.2 Prerrequisitos\n\n" + "\n".join(f"- {p.strip()}" for p in plan.prerrequisitos))

    # --- 2. resultados de aprendizaje ---
    filas_resultados = [
        [f"RA{i}", _negrita_al_inicio(r.enunciado) + (f" ({', '.join(r.criterios)})" if r.criterios else ""), r.nivel.value]
        for i, r in enumerate(plan.resultados_sesion, 1)
    ]
    resultados = (f"## 2. Resultados de Aprendizaje\n\n{_alineacion(ra, competencias)}\n\n"
                  "Al finalizar la sesión, el estudiante estará en capacidad de lograr los siguientes resultados, que desarrollan el RA del módulo:\n\n"
                  + _tabla_md(["#", "Resultado de aprendizaje", "Nivel (Taxonomía de Bloom)"], filas_resultados))

    # --- 3. indice temporizado ---
    filas_indice = [[str(k), u.descripcion.strip(), f"{m} min"] for k, ((u, _), m) in enumerate(zip(unidades, minutos), 1)]
    filas_indice.append(["", "**Total**", f"**{sum(minutos)} min**"])
    indice = f"## 3. Índice Temporizado ({horas_sesion * 60} minutos)\n\n" + _tabla_md(["Bloque", "Contenido", "Duración"], filas_indice)

    # --- 4. desarrollo teorico ---
    desarrollo = [f"## 4. Desarrollo Teórico\n\n### 4.1 {TITULO_INTRODUCCION} (Bloque {k_intro})\n\n{_bloques_md(s_intro.bloques, numeracion, '4.1')}",
                  "### 4.2 Conceptos Clave"]
    for i, (k, u, s) in enumerate(conceptos, 1):
        desarrollo.append(f"#### 4.2.{i} {u.titulo.strip()} (Bloque {k})\n\n{_bloques_md(s.bloques, numeracion, f'4.2.{i}')}")

    # --- 5..n. caso, analisis, implementacion, sintesis ---
    practica = f"**Práctica de referencia:** {enlace_practica}\n\n" if enlace_practica else ""
    secciones = [f"## 5. Caso de Estudio Aplicado: {u_caso.titulo.strip()} (Bloque {k_caso})\n\n{practica}{_bloques_md(s_caso.bloques, numeracion, '5')}"]
    numero = 5
    for k, u, s in extras:
        numero += 1
        secciones.append(f"## {numero}. {u.titulo.strip()} (Bloque {k})\n\n{_bloques_md(s.bloques, numeracion, str(numero))}")
    numero += 1
    secciones.append(f"## {numero}. Síntesis (Bloque {k_sintesis})\n\n{' '.join(cierre.sintesis.split())}\n\n### Componente Actitudinal\n\n"
                     f"> *{' '.join(cierre.reflexion_actitudinal.split())}*")

    # --- bibliografia ---
    entradas = [f"[{i}] {_sin_numero(e)}" for i, e in enumerate(plan.referencias_cargadas, 1)]
    vistas: set[str] = set()
    for e in externas:
        limpio = _sin_numero(e)
        clave = re.sub(r"\W+", "", limpio.lower())
        if clave and clave not in vistas:
            vistas.add(clave)
            entradas.append(f"[{len(entradas) + 1}] {limpio} {MARCADOR}")
    numero += 1
    bibliografia = f"## {numero}. Bibliografía (Formato IEEE)\n\n" + ("\n\n".join(entradas) if entradas else "(la sesión no cita fuentes)")

    todos_los_bloques = [b for _, s in unidades for b in s.bloques]
    cuenta = elementos_de(todos_los_bloques)
    palabras = sum(palabras_de(s.bloques) for _, s in unidades) + len(re.findall(r"\w+", cierre.sintesis))
    frontmatter = {
        "tipo": "temario",
        "asignatura": f"[[{nombre_pagina}]]",
        "resultado_aprendizaje": f"[[{ra.codigo}]]",
        "semana": semana,
        "total_semanas": SEMANAS_TOTALES,
        "corte_evaluativo": corte_evaluativo(semana),
        "horas_sesion": horas_sesion,
        "horas_trabajo_independiente": hti_semana,
        "estadisticas": {
            "palabras": palabras, "ecuaciones": cuenta[ElementoPlan.ecuacion], "tablas": cuenta[ElementoPlan.tabla],
            "figuras": cuenta[ElementoPlan.grafica] + cuenta[ElementoPlan.diagrama], "pasajes": pasajes_usados,
        },
        "bibliografia_estado": None,   # lo escribe CORRELATE-BIBLIOGRAFIA
        "fecha_creacion": hoy,
        "fecha_actualizacion": hoy,
    }
    separador = "\n\n---\n\n"
    cuerpo = ("\n\n# " + " ".join(plan.titulo.split()) + "\n\n" + "\n".join(cabecera) + separador + metadatos + separador + resultados + separador + indice
              + separador + "\n\n".join(desarrollo) + separador + separador.join(secciones) + separador + bibliografia + "\n")
    return frontmatter, cuerpo, numeracion.por_dibujar


# ---------------------------------------------------------------------------
# La sesion
# ---------------------------------------------------------------------------


def _ordenar(unidades: list[UnidadPlan]) -> list[UnidadPlan]:
    """Introduccion, conceptos (en su orden), caso, analisis, implementacion y sintesis: el orden del documento."""
    return sorted(unidades, key=lambda u: _ORDEN_CLASES.index(u.clase))      # sorted es estable: los conceptos conservan su orden


def _esqueleto(unidades: list[UnidadPlan], actual: int | None) -> str:
    return "\n".join(f"{'→' if k == actual else ' '} {k}. ({u.clase.value}) {u.titulo} — {u.descripcion}" for k, u in enumerate(unidades, 1))


def _resumen_de_unidades(unidades: list[tuple[UnidadPlan, SeccionRedactada]]) -> str:
    lineas = []
    for u, s in unidades:
        cuenta = elementos_de(s.bloques)
        primero = next((b.contenido for b in s.bloques if b.tipo == TipoBloque.parrafo), "")
        pies = [b.leyenda for b in s.bloques if b.tipo in (TipoBloque.tabla, TipoBloque.grafica, TipoBloque.diagrama) and b.leyenda]
        lineas.append(f"- {u.titulo} ({u.clase.value}; {cuenta[ElementoPlan.ecuacion]} ecuaciones, {cuenta[ElementoPlan.tabla]} tablas, "
                      f"{cuenta[ElementoPlan.grafica] + cuenta[ElementoPlan.diagrama]} figuras): {' '.join(primero.split())[:220]}"
                      + (f" — figuras y tablas: {'; '.join(pies)[:300]}" if pies else ""))
    return "\n".join(lineas)


def _dibujar_figuras(por_dibujar: list[tuple[str, object]], codigo: str, semana: int) -> list[Path]:
    """Dibuja los PNG (y quita los de una version anterior de esta sesion). Si algo falla, no deja figuras a medias."""
    carpeta = vault.TEMARIOS / "figuras"
    for vieja in carpeta.glob(f"{codigo}-semana{semana:02d}-fig*.png"):
        vieja.unlink()
    hechas: list[Path] = []
    try:
        for nombre, spec in por_dibujar:
            destino = carpeta / nombre
            (figuras.dibujar_grafica if isinstance(spec, figuras.GraficaSpec) else figuras.dibujar_diagrama)(spec, destino)
            hechas.append(destino)
    except Exception:
        for parcial in hechas:
            parcial.unlink(missing_ok=True)
        raise
    return hechas


def generar_temario(codigo: str, semana: int, forzar: bool = False, progreso: Callable[[str], None] | None = None) -> Path:
    def avisar(mensaje: str) -> None:
        if progreso:
            progreso(f"  [{codigo} semana {semana}] {mensaje}")

    nombre_pagina, asignatura, fm_asignatura = vault.localizar_asignatura(codigo)
    ruta_plan = vault.PLANEADOR / f"{codigo}-planeador.md"
    if not ruta_plan.exists():
        raise FileNotFoundError(f"No hay planeador de {codigo}: corre `python src/planeador.py {codigo}` primero")
    fm_plan, _ = vault.leer_pagina(ruta_plan)
    filas = {s["semana"]: s for s in fm_plan["semanas"]}
    if semana not in filas:
        raise ValueError(f"{codigo}: el planeador no tiene la semana {semana}")
    fila = filas[semana]
    if fila["tipo"] == "examen":
        raise ValueError(f"La semana {semana} de {codigo} es de examen: no se genera temario")

    destino = vault.TEMARIOS / f"{codigo}-semana{semana:02d}.md"
    if destino.exists() and not forzar:
        raise FileExistsError(f"{destino} ya existe; usa --forzar para sobrescribirlo")
    if not figuras.disponible():
        raise RuntimeError("Falta matplotlib, que dibuja las gráficas y los diagramas del temario: `pip install -r requirements.txt`")

    ra, fm_ra, _ = vault.cargar_ra(vault.RESULTADOS / f"{fila['ra']}.md")
    tema = fila.get("tema") or ra.enunciado
    texto_practica, enlace_practica, fuente_practica, practica = practica_de_referencia(asignatura, fm_ra)
    fuentes = fuentes_de_la_sesion(fm_ra, fuente_practica)
    for f in fuentes:
        for motivo in f.omitidos:
            avisar(f"aviso: de la fuente {f.nombre} no se lee el original: {motivo}")
    numeros = {f.nombre: i for i, f in enumerate(fuentes, 1)}
    indice = pasajes.Indice(fuentes)
    competencias = competencias_de(fm_asignatura)
    horas_sesion = fm_plan["horas_sesion"]

    # --- 1. el plan ---
    avisar("plan de la sesión")
    sistema, plantilla = vault.cargar_prompt("prompt-temario-plan.md")
    usuario = plantilla.format(
        codigo_asignatura=asignatura.codigo, nombre_asignatura=asignatura.nombre, tipo_abordaje=asignatura.tipo_abordaje.value,
        programas=", ".join(vault.enlaces(fm_asignatura.get("programa"))) or "(sin programa enlazado)",
        aprendizajes_previos=asignatura.aprendizajes_previos or "(no se indican)",
        minutos_sesion=horas_sesion * 60, horas_sesion=horas_sesion, semana=semana, total_semanas=SEMANAS_TOTALES,
        corte_evaluativo=corte_evaluativo(semana), tema=tema,
        sesion_anterior=_sesion_vecina(filas, semana - 1) if semana > 1 else "(es la primera semana)",
        sesion_siguiente=_sesion_vecina(filas, semana + 1) if semana < SEMANAS_TOTALES else "(es la última semana)",
        codigo_ra=ra.codigo, enunciado=ra.enunciado,
        criterios="; ".join(f"{ce.codigo}: {ce.texto}" for ce in ra.criterios_evaluacion) or "(sin criterios)",
        conceptual="; ".join(ra.contenido.conceptual) or "(sin contenido conceptual)",
        procedimental="; ".join(ra.contenido.procedimental) or "(sin contenido procedimental)",
        actitudinal="; ".join(ra.contenido.actitudinal) or "(sin contenido actitudinal)",
        competencias="; ".join(f"{n}: {t}" for n, t in competencias) or "(sin competencias enlazadas)",
        practica=texto_practica, n_fuentes=len(fuentes), fuentes=_describir_fuentes(fuentes, detallado=True),
    )
    plan = _redactar(sistema, usuario, PlanSesion, lambda p, blando: _validar_plan(p, ra, len(fuentes)), f"semana {semana}: el plan")
    unidades_plan = _ordenar(plan.unidades)
    if len(unidades_plan) > horas_sesion * 60 // 5:
        raise ValueError(f"semana {semana}: el plan tiene {len(unidades_plan)} unidades, demasiadas para {horas_sesion * 60} minutos")

    # --- 2. cada unidad ---
    sistema_u, plantilla_u = vault.cargar_prompt("prompt-temario-seccion.md")
    redactadas: list[tuple[UnidadPlan, SeccionRedactada]] = []
    usados: set[int] = set()
    for k, unidad in enumerate(unidades_plan, 1):
        if unidad.clase == ClaseUnidad.sintesis:
            continue
        avisar(f"unidad {k}/{len(unidades_plan)}: {unidad.titulo}")
        terminos = [unidad.titulo, *unidad.terminos_busqueda, *(practica.terminos_clave if practica and unidad.clase == ClaseUnidad.caso else [])]
        encontrados = indice.buscar(terminos, PASAJES_POR_UNIDAD, CARACTERES_DE_PASAJES, usados)
        usados |= {i for i, _ in encontrados}
        requisitos = ("al menos 2 subtítulos (`subtitulo`)" if unidad.clase == ClaseUnidad.caso else
                      "puede llevar subtítulos (`subtitulo`)" if unidad.clase in (ClaseUnidad.analisis, ClaseUnidad.implementacion) else "sin subtítulos")
        usuario_u = plantilla_u.format(
            codigo_asignatura=asignatura.codigo, nombre_asignatura=asignatura.nombre, tipo_abordaje=asignatura.tipo_abordaje.value,
            minutos_sesion=horas_sesion * 60, semana=semana, total_semanas=SEMANAS_TOTALES, codigo_ra=ra.codigo, enunciado=ra.enunciado,
            criterios="; ".join(f"{ce.codigo}: {ce.texto}" for ce in ra.criterios_evaluacion) or "(sin criterios)",
            titulo_sesion=plan.titulo, plataforma=plan.plataforma_referencia or "(ninguna)",
            usa_ecuaciones="sí" if plan.usa_ecuaciones else "no", usa_graficas="sí" if plan.usa_graficas else "no", practica=texto_practica,
            esqueleto=_esqueleto(unidades_plan, k), clase=unidad.clase.value, titulo_unidad=unidad.titulo, descripcion=unidad.descripcion,
            elementos=", ".join(e.value for e in unidad.elementos) or "(ninguno en particular)",
            palabras_minimas=palabras_minimas(unidad.clase, horas_sesion), requisitos=requisitos,
            fuentes=_describir_fuentes(fuentes, detallado=False), pasajes=pasajes.formatear(encontrados, numeros),
        )
        seccion = _redactar(
            sistema_u, usuario_u, SeccionRedactada,
            lambda s, blando, u=unidad: _validar_unidad(u, s, plan, horas_sesion, len(fuentes), practica, blando),
            f"semana {semana}: la unidad «{unidad.titulo}»")
        redactadas.append((unidad, seccion))
    sintesis = next(u for u in unidades_plan if u.clase == ClaseUnidad.sintesis)

    # --- 3. el cierre ---
    avisar("síntesis y cierre")
    sistema_c, plantilla_c = vault.cargar_prompt("prompt-temario-cierre.md")
    usuario_c = plantilla_c.format(
        codigo_asignatura=asignatura.codigo, nombre_asignatura=asignatura.nombre, titulo_sesion=plan.titulo, codigo_ra=ra.codigo,
        enunciado=ra.enunciado, actitudinal="; ".join(ra.contenido.actitudinal) or "(sin contenido actitudinal)",
        palabras_minimas=palabras_minimas(ClaseUnidad.sintesis, horas_sesion), resumen_unidades=_resumen_de_unidades(redactadas))
    cierre = _redactar(sistema_c, usuario_c, CierreSesion, lambda c, blando: _validar_cierre(c, horas_sesion), f"semana {semana}: el cierre")

    # --- escritura ---
    todas = [*redactadas, (sintesis, SeccionRedactada(bloques=[]))]
    frontmatter, cuerpo, por_dibujar = renderizar_temario(
        nombre_pagina, codigo, asignatura, fm_asignatura, ra, competencias, semana, filas, horas_sesion, plan, todas, cierre,
        enlace_practica, len(usados))
    avisar(f"dibujando {len(por_dibujar)} figuras")
    _dibujar_figuras(por_dibujar, codigo, semana)
    vault.escribir_pagina(destino, frontmatter, cuerpo)
    est = frontmatter["estadisticas"]
    vault.anotar_log(f"/temario {codigo} semana {semana}", [
        f"RA: {ra.codigo}", f"tema: {tema}",
        f"{est['palabras']} palabras, {est['ecuaciones']} ecuaciones, {est['tablas']} tablas, {est['figuras']} figuras; "
        f"{est['pasajes']} pasajes de {len(fuentes)} fuente(s) cargada(s)",
        *([f"solo con su página del wiki (sin texto completo en raw/): {', '.join(f.nombre for f in fuentes if not f.archivos)}"] if any(not f.archivos for f in fuentes) else [])])
    return destino


def generar_temarios(codigo: str, forzar: bool = False, progreso: Callable[[str], None] | None = None) -> tuple[list[Path], list[int]]:
    """Todas las semanas de clase. Devuelve (temarios escritos, semanas omitidas por ya tener temario)."""
    fm_plan, _ = vault.leer_pagina(vault.PLANEADOR / f"{codigo}-planeador.md")
    escritos, omitidas = [], []
    for fila in fm_plan["semanas"]:
        if fila["tipo"] != "clase":
            continue
        if (vault.TEMARIOS / f"{codigo}-semana{fila['semana']:02d}.md").exists() and not forzar:
            omitidas.append(fila["semana"])
            continue
        escritos.append(generar_temario(codigo, fila["semana"], forzar, progreso))
    return escritos, omitidas


if __name__ == "__main__":
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Genera el temario (una sesión) de una semana de clase.")
    parser.add_argument("codigo", help="código de la asignatura")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--semana", type=int, help="número de semana (1-14)")
    grupo.add_argument("--todas", action="store_true", help="todas las semanas de clase que aún no tengan temario")
    parser.add_argument("--forzar", action="store_true", help="sobrescribe un temario ya existente")
    args = parser.parse_args()
    try:
        if args.todas:
            escritos, omitidas = generar_temarios(args.codigo, args.forzar, print)
            print(f"{len(escritos)} temarios escritos; omitidas por ya existir: {omitidas or 'ninguna'}")
        else:
            print(f"Temario escrito en {generar_temario(args.codigo, args.semana, args.forzar, print)}")
    except (FileExistsError, FileNotFoundError, KeyError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}")
        sys.exit(1)
