"""Esquemas de TEMARIO: lo que el LLM devuelve en cada paso de la redaccion de una sesion.

Una sesion no se pide en una sola llamada (saldria corta y superficial): se pide en tres pasos, y cada uno tiene su esquema.

    PlanSesion        el esqueleto: titulo, resultados de la sesion, y las UNIDADES de contenido (introduccion, conceptos,
                      caso de estudio, analisis, implementacion, sintesis) con su peso, los terminos con que buscar en las
                      fuentes y que elementos (ecuaciones, tablas, graficas, diagramas, codigo) lleva cada una
    SeccionRedactada  el desarrollo de UNA unidad: una lista de bloques (parrafos, ecuaciones, tablas, figuras, codigo...)
    CierreSesion      la sintesis y la reflexion actitudinal

Los bloques son datos, no Markdown suelto: el codigo es quien escribe las tablas, numera las figuras y las dibuja
(figuras.py), asi que una tabla descuadrada, una ecuacion con `$` de mas o una grafica con una formula inexistente se
rechazan con un mensaje que se le devuelve al modelo para que la corrija (ver temario._redactar).

Los rangos y minimos se validan aqui o en temario.py con un mensaje claro, no con `Field(ge=...)`: algunas APIs rechazan
esas restricciones en el esquema (ver el README, "Configurar el modelo de IA").
"""

from __future__ import annotations

import re
from enum import Enum

from figuras import DiagramaSpec, GraficaSpec
from pydantic import BaseModel, model_validator

MIN_CONCEPTOS, MAX_CONCEPTOS = 3, 6
MIN_RESULTADOS, MAX_RESULTADOS = 3, 5
MIN_PRERREQUISITOS, MAX_PRERREQUISITOS = 3, 7
MIN_TERMINOS, MAX_TERMINOS = 4, 10
MIN_TABLAS, MIN_FIGURAS, MIN_ECUACIONES = 2, 2, 3      # de toda la sesion (las ecuaciones solo si el tema las usa)


class NivelBloom(str, Enum):
    recordar = "Recordar"
    comprender = "Comprender"
    aplicar = "Aplicar"
    analizar = "Analizar"
    evaluar = "Evaluar"
    crear = "Crear"


class ClaseUnidad(str, Enum):
    introduccion = "introduccion"
    concepto = "concepto"
    caso = "caso"
    analisis = "analisis"
    implementacion = "implementacion"
    sintesis = "sintesis"


class ElementoPlan(str, Enum):
    ecuacion = "ecuacion"
    tabla = "tabla"
    grafica = "grafica"          # curva de una funcion, datos o barras (matplotlib)
    diagrama = "diagrama"        # flujo, estados o bloques (matplotlib)
    codigo = "codigo"


class ResultadoSesion(BaseModel):
    enunciado: str               # empieza por un verbo en infinitivo (el codigo lo pone en negrita)
    nivel: NivelBloom
    criterios: list[str] = []    # codigos de los Criterios de Evaluacion del RA que desarrolla (CE1, CE2...)


class UnidadPlan(BaseModel):
    clase: ClaseUnidad
    titulo: str
    descripcion: str             # una linea para la columna «Contenido» del indice temporizado
    peso: int                    # importancia relativa; el codigo lo convierte en minutos
    terminos_busqueda: list[str]  # de 4 a 10, en espanol E ingles: con ellos se buscan pasajes en las fuentes cargadas
    elementos: list[ElementoPlan] = []


class PlanSesion(BaseModel):
    titulo: str
    plataforma_referencia: str | None = None
    continuidad: str
    prerrequisitos: list[str]
    resultados_sesion: list[ResultadoSesion]
    usa_ecuaciones: bool
    usa_graficas: bool
    unidades: list[UnidadPlan]
    referencias_cargadas: list[str] = []   # una entrada IEEE por cada fuente cargada, en el orden en que se entregan

    @model_validator(mode="after")
    def esqueleto_valido(self) -> "PlanSesion":
        def rango(nombre: str, valores: list, minimo: int, maximo: int) -> None:
            if not minimo <= len(valores) <= maximo:
                raise ValueError(f"se piden de {minimo} a {maximo} {nombre} y llegaron {len(valores)}")

        if not 20 <= len(self.titulo.strip()) <= 200:
            raise ValueError(f"el título debe tener de 20 a 200 caracteres y tiene {len(self.titulo.strip())}")
        if not self.continuidad.strip():
            raise ValueError("falta el texto de continuidad curricular")
        rango("prerrequisitos", self.prerrequisitos, MIN_PRERREQUISITOS, MAX_PRERREQUISITOS)
        rango("resultados de aprendizaje de la sesión", self.resultados_sesion, MIN_RESULTADOS, MAX_RESULTADOS)
        cuenta = {c: sum(1 for u in self.unidades if u.clase == c) for c in ClaseUnidad}
        rango("conceptos clave (unidades de clase `concepto`)", [None] * cuenta[ClaseUnidad.concepto], MIN_CONCEPTOS, MAX_CONCEPTOS)
        for clase, minimo, maximo in ((ClaseUnidad.introduccion, 1, 1), (ClaseUnidad.caso, 1, 1), (ClaseUnidad.sintesis, 1, 1),
                                      (ClaseUnidad.analisis, 0, 1), (ClaseUnidad.implementacion, 0, 1)):
            if not minimo <= cuenta[clase] <= maximo:
                raise ValueError(f"debe haber {minimo if minimo == maximo else f'de {minimo} a {maximo}'} unidad(es) de clase `{clase.value}` y llegaron {cuenta[clase]}")
        for u in self.unidades:
            if not u.titulo.strip() or not 10 <= len(u.descripcion.strip()) <= 200:
                raise ValueError(f"la unidad «{u.titulo}» necesita título y una descripción de 10 a 200 caracteres")
            if u.peso <= 0:
                raise ValueError(f"la unidad «{u.titulo}» necesita un peso mayor que 0")
            if not MIN_TERMINOS <= len(u.terminos_busqueda) <= MAX_TERMINOS:
                raise ValueError(f"la unidad «{u.titulo}» necesita de {MIN_TERMINOS} a {MAX_TERMINOS} términos de búsqueda y tiene {len(u.terminos_busqueda)}")
            if u.clase == ClaseUnidad.implementacion and ElementoPlan.codigo not in u.elementos:
                raise ValueError(f"la unidad de implementación «{u.titulo}» debe llevar el elemento `codigo`")
            if u.clase in (ClaseUnidad.caso, ClaseUnidad.analisis) and ElementoPlan.tabla not in u.elementos:
                raise ValueError(f"la unidad «{u.titulo}» ({u.clase.value}) debe llevar el elemento `tabla`")
            if u.clase == ClaseUnidad.caso and self.usa_ecuaciones and ElementoPlan.ecuacion not in u.elementos:
                raise ValueError(f"el caso de estudio «{u.titulo}» debe llevar el elemento `ecuacion` (el tema usa ecuaciones)")
            if not self.usa_graficas and ElementoPlan.grafica in u.elementos:
                raise ValueError(f"la unidad «{u.titulo}» pide una `grafica` pero `usa_graficas` es falso: usa `diagrama`")
        con = {e: sum(1 for u in self.unidades if e in u.elementos) for e in ElementoPlan}
        if con[ElementoPlan.tabla] < MIN_TABLAS:
            raise ValueError(f"la sesión debe planear al menos {MIN_TABLAS} unidades con `tabla` y planea {con[ElementoPlan.tabla]}")
        if con[ElementoPlan.grafica] + con[ElementoPlan.diagrama] < MIN_FIGURAS:
            raise ValueError(f"la sesión debe planear al menos {MIN_FIGURAS} figuras (`grafica` o `diagrama`) y planea {con[ElementoPlan.grafica] + con[ElementoPlan.diagrama]}")
        if self.usa_ecuaciones and con[ElementoPlan.ecuacion] < MIN_ECUACIONES:
            raise ValueError(f"el tema usa ecuaciones: planea al menos {MIN_ECUACIONES} unidades con `ecuacion` y planea {con[ElementoPlan.ecuacion]}")
        return self


class TipoBloque(str, Enum):
    parrafo = "parrafo"
    lista = "lista"
    ecuacion = "ecuacion"
    tabla = "tabla"
    nota = "nota"
    codigo = "codigo"
    grafica = "grafica"
    diagrama = "diagrama"
    subtitulo = "subtitulo"


_SEPARADOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def celdas_de_tabla(contenido: str) -> tuple[list[str], list[list[str]]]:
    """(encabezados, filas) de una tabla Markdown (con o sin la linea separadora). ValueError si no esta bien formada."""
    lineas = [l.strip() for l in contenido.strip().splitlines() if l.strip()]
    if len(lineas) < 2 or not all(l.startswith("|") for l in lineas):
        raise ValueError("una tabla se escribe con una línea por fila, cada una entre `|`")
    filas = []
    for l in lineas:
        cuerpo = l[1:-1] if l.endswith("|") and not l.endswith("\\|") else l[1:]
        filas.append([c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", cuerpo)])
    if len(filas) > 1 and _SEPARADOR.match(lineas[1]):
        filas.pop(1)
    encabezados, cuerpo = filas[0], filas[1:]
    if len(encabezados) < 2:
        raise ValueError("una tabla necesita al menos 2 columnas")
    if not cuerpo:
        raise ValueError("una tabla necesita al menos una fila de datos")
    for k, fila in enumerate(cuerpo, 1):
        if len(fila) != len(encabezados):
            raise ValueError(f"la fila {k} de la tabla tiene {len(fila)} celdas y el encabezado {len(encabezados)}")
    return encabezados, cuerpo


def _dolares_balanceados(texto: str) -> bool:
    return len(re.findall(r"(?<!\\)\$", texto)) % 2 == 0


class Bloque(BaseModel):
    """Una pieza del desarrollo. Que campos lleva depende de `tipo`:
        parrafo    contenido = el texto (Markdown en linea; ecuaciones en linea con $...$; citas [n])
        lista      contenido = un elemento por linea
        ecuacion   contenido = el LaTeX de la ecuacion, sin $$ (la explicacion de sus variables va en un `parrafo` que siga)
        tabla      contenido = la tabla Markdown (| a | b |); leyenda = su titulo
        nota       contenido = el texto; leyenda = la etiqueta («Nota pedagógica», «Advertencia de seguridad»...)
        codigo     contenido = el codigo; lenguaje = cpp, python...; leyenda = su titulo
        grafica    grafica = la especificacion; leyenda = el pie de figura
        diagrama   diagrama = la especificacion; leyenda = el pie de figura
        subtitulo  contenido = el titulo de un apartado (solo en el caso, el analisis y la implementacion)"""

    tipo: TipoBloque
    contenido: str = ""
    leyenda: str = ""
    lenguaje: str = ""
    grafica: GraficaSpec | None = None
    diagrama: DiagramaSpec | None = None

    @model_validator(mode="after")
    def coherente(self) -> "Bloque":
        t, c = self.tipo, self.contenido.strip()
        if t in (TipoBloque.parrafo, TipoBloque.nota, TipoBloque.subtitulo, TipoBloque.lista, TipoBloque.ecuacion, TipoBloque.tabla, TipoBloque.codigo) and not c:
            raise ValueError(f"el bloque `{t.value}` no tiene contenido")
        if t in (TipoBloque.parrafo, TipoBloque.nota, TipoBloque.lista):
            if "$$" in c:
                raise ValueError("las ecuaciones en bloque van en un bloque `ecuacion`, no dentro de un párrafo, nota o lista (con `$$`)")
            if not _dolares_balanceados(c):
                raise ValueError(f"hay un número impar de signos `$` en: «{c[:80]}…»")
            if t != TipoBloque.lista and re.match(r"^(#{1,6}\s|\||```|>\s)", c):
                raise ValueError(f"el párrafo «{c[:60]}…» empieza como un título, una tabla, un bloque de código o una cita: usa el `tipo` que corresponde")
        if t == TipoBloque.lista and len([l for l in c.splitlines() if l.strip()]) < 2:
            raise ValueError("una lista necesita al menos 2 elementos (uno por línea)")
        if t == TipoBloque.ecuacion:
            latex = re.sub(r"^\s*(\$\$|\\\[)|(\$\$|\\\])\s*$", "", c).strip()
            if "$" in latex:
                raise ValueError("el LaTeX de una `ecuacion` va sin signos `$`")
            sin_escapadas = re.sub(r"\\[{}]", "", latex)                       # `\{` y `\}` (p. ej. `\left\{ ... \right.`) no abren ni cierran grupos
            if sin_escapadas.count("{") != sin_escapadas.count("}") or len(latex) > 700:
                raise ValueError(f"la ecuación «{latex[:60]}…» tiene llaves sin cerrar o es demasiado larga")
            self.contenido = latex
        if t == TipoBloque.tabla:
            celdas_de_tabla(c)
            if not self.leyenda.strip():
                raise ValueError("una `tabla` necesita `leyenda` (su título)")
        if t == TipoBloque.codigo and len(c.splitlines()) > 120:
            raise ValueError("un bloque de código admite hasta 120 líneas: divídelo en dos")
        if t == TipoBloque.subtitulo and len(c) > 100:
            raise ValueError("un subtítulo admite hasta 100 caracteres")
        if t == TipoBloque.grafica and (self.grafica is None or not self.leyenda.strip()):
            raise ValueError("un bloque `grafica` necesita `grafica` (la especificación) y `leyenda` (el pie de figura)")
        if t == TipoBloque.diagrama and (self.diagrama is None or not self.leyenda.strip()):
            raise ValueError("un bloque `diagrama` necesita `diagrama` (la especificación) y `leyenda` (el pie de figura)")
        return self


class SeccionRedactada(BaseModel):
    bloques: list[Bloque]
    referencias_externas: list[str] = []      # entradas IEEE de las fuentes citadas que NO estan cargadas (llevan el marcador en el texto)


class CierreSesion(BaseModel):
    sintesis: str                             # 1 a 3 parrafos que integran la sesion
    reflexion_actitudinal: str                # una o dos frases


# ---------------------------------------------------------------------------
# Lo que los bloques contienen (para validar y para las estadisticas del frontmatter)
# ---------------------------------------------------------------------------


def _palabras(texto: str) -> int:
    return len(re.findall(r"\w+", re.sub(r"\$[^$]*\$", " ", texto)))


def palabras_de(bloques: list[Bloque]) -> int:
    """Palabras de prosa (parrafos, listas, notas y pies de figura y de tabla); el codigo, las ecuaciones y las celdas no cuentan."""
    total = 0
    for b in bloques:
        if b.tipo in (TipoBloque.parrafo, TipoBloque.lista, TipoBloque.nota):
            total += _palabras(b.contenido)
        if b.tipo in (TipoBloque.tabla, TipoBloque.grafica, TipoBloque.diagrama, TipoBloque.codigo):
            total += _palabras(b.leyenda)
    return total


def elementos_de(bloques: list[Bloque]) -> dict[ElementoPlan, int]:
    """Cuantas ecuaciones, tablas, graficas, diagramas y bloques de codigo hay."""
    cuenta = {e: 0 for e in ElementoPlan}
    for b in bloques:
        if b.tipo.value in {e.value for e in ElementoPlan}:
            cuenta[ElementoPlan(b.tipo.value)] += 1
    return cuenta
