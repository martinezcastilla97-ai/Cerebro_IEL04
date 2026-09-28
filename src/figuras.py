"""FIGURAS -- las graficas y los diagramas de un temario, dibujados por CODIGO a partir de una especificacion.

El LLM no dibuja nada ni inventa puntos: redacta una especificacion (los ejes, las funciones con sus parametros o los
datos de una tabla, o los nodos y las flechas de un diagrama) y este modulo la valida y la dibuja con matplotlib, con la
paleta institucional IUB. Asi una grafica siempre sale de una formula o de datos que estan a la vista, y un diagrama
siempre tiene todas sus flechas: lo que el modelo escribio mal se rechaza con un mensaje que se le devuelve para que lo
corrija, en vez de dibujarse mal.

    GraficaSpec   curvas de funciones (`expresion` en la variable indicada), lineas o puntos de datos, o barras
    DiagramaSpec  diagramas de flujo, de estados o de bloques (nodos con forma + flechas con etiqueta)

Las expresiones se evaluan con un evaluador propio sobre el arbol sintactico de Python (solo numeros, operadores, los
parametros declarados y una lista corta de funciones matematicas; de hasta 300 caracteres): nunca con eval().

matplotlib se importa cuando de verdad se dibuja, asi que importar este modulo (y `--help` de los scripts) no lo exige.
Sin dependencia de numpy directa: los puntos se calculan con `math`.
"""

from __future__ import annotations

import ast
import math
import operator
import textwrap
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, model_validator

# Paleta del Manual de Identidad IUB 2025 (la misma de las presentaciones, diseno_iub.COLORES), con fondos suaves para las graficas
OSCURO, AZUL, NARANJA, VERDE = "#121023", "#00ADE7", "#E39037", "#3B9C6D"
AZUL_FONDO, NARANJA_FONDO, VERDE_FONDO, GRIS_FONDO, GRIS_LINEA = "#EBF7FD", "#FDF4EA", "#EDF8F2", "#F4F6F9", "#D5DAE3"
COLORES_SERIE = [AZUL, NARANJA, VERDE, OSCURO, "#8E6BBF"]

DPI = 200
TAMANO_GRAFICA = (6.4, 2.75)         # pulgadas: la presentacion la muestra a ~4,8 cm de alto (escala ~0,7), asi que las letras van grandes
TAMANO_OBJETIVO_DIAGRAMA = (7.2, 3.0)
MAX_PUNTOS = 300
MAX_SERIES, MAX_NODOS, MAX_ARISTAS = 5, 12, 24
MAX_EXPRESION = 300                  # caracteres: una formula fisica cabe de sobra, y una cadena de miles de signos solo desborda el analizador
_FONDO_ROTULO = {"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.9}


def disponible() -> bool:
    """True si matplotlib esta instalado (pip install -r requirements.txt)."""
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        return False
    return True


# ---------------------------------------------------------------------------
# Evaluador de expresiones (sin eval)
# ---------------------------------------------------------------------------

_FUNCIONES = {
    "exp": math.exp, "ln": math.log, "log10": math.log10, "log2": math.log2, "sqrt": math.sqrt, "sin": math.sin,
    "cos": math.cos, "tan": math.tan, "asin": math.asin, "acos": math.acos, "atan": math.atan, "sinh": math.sinh,
    "cosh": math.cosh, "tanh": math.tanh, "abs": abs, "min": min, "max": max,
}
_CONSTANTES = {"pi": math.pi, "e": math.e}
_OPERADORES = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
_UNARIOS = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _compilar(expresion: str, permitidos: set[str]):
    """La expresion como un arbol sintactico ya comprobado (ValueError con un mensaje claro si algo no esta permitido).
    Siempre ValueError, tambien con una expresion desmesurada: quien llama solo captura ese, y otra excepcion detendria toda
    la generacion en vez de volver al modelo con el motivo."""
    largo = len(expresion.strip())
    if largo > MAX_EXPRESION:
        raise ValueError(f"la expresión tiene {largo} caracteres, es demasiado larga (máximo {MAX_EXPRESION}): simplifícala o divídela en varias series")
    texto = expresion.strip().replace("^", "**").replace("×", "*").replace("·", "*").replace("−", "-")
    if not texto:
        raise ValueError("la expresión está vacía")
    try:
        arbol = ast.parse(texto, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"no se entiende la expresión «{expresion}» (¿falta un `*` entre factores? no hay multiplicación implícita): {error.msg}") from error
    except (RecursionError, MemoryError) as error:              # demasiados niveles de anidacion para el analizador de Python
        raise ValueError(f"la expresión «{expresion}» está demasiado anidada para analizarla: simplifícala") from error
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name):
            if nodo.id == "log":
                raise ValueError(f"«{expresion}»: usa `ln` (logaritmo natural) o `log10`, no `log`")
            if nodo.id not in permitidos and nodo.id not in _FUNCIONES:
                raise ValueError(f"«{expresion}»: `{nodo.id}` no es la variable, un parámetro declarado, ni una función permitida "
                                 f"({', '.join(sorted(_FUNCIONES))}; constantes pi y e)")
        elif isinstance(nodo, ast.Call):
            if isinstance(nodo.func, ast.Name) and nodo.func.id == "log":
                raise ValueError(f"«{expresion}»: usa `ln` (logaritmo natural) o `log10`, no `log`")
            if not isinstance(nodo.func, ast.Name) or nodo.func.id not in _FUNCIONES or nodo.keywords:
                raise ValueError(f"«{expresion}»: solo se admiten las funciones {', '.join(sorted(_FUNCIONES))}")
        elif not isinstance(nodo, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Load, ast.Add, ast.Sub, ast.Mult,
                                   ast.Div, ast.Pow, ast.USub, ast.UAdd)):
            raise ValueError(f"«{expresion}»: solo se admiten números, operadores + - * / ** y funciones (no {type(nodo).__name__})")
        if isinstance(nodo, ast.Constant) and not isinstance(nodo.value, (int, float)):
            raise ValueError(f"«{expresion}»: solo se admiten números")
    return arbol


def _evaluar(nodo: ast.AST, entorno: dict[str, float]) -> float:
    if isinstance(nodo, ast.Expression):
        return _evaluar(nodo.body, entorno)
    if isinstance(nodo, ast.Constant):
        return float(nodo.value)
    if isinstance(nodo, ast.Name):
        return entorno[nodo.id]
    if isinstance(nodo, ast.UnaryOp):
        return _UNARIOS[type(nodo.op)](_evaluar(nodo.operand, entorno))
    if isinstance(nodo, ast.BinOp):
        izquierda, derecha = _evaluar(nodo.left, entorno), _evaluar(nodo.right, entorno)
        if isinstance(nodo.op, ast.Pow) and abs(derecha) > 200:
            raise OverflowError("exponente desmesurado")
        return _OPERADORES[type(nodo.op)](izquierda, derecha)
    if isinstance(nodo, ast.Call):
        return _FUNCIONES[nodo.func.id](*[_evaluar(a, entorno) for a in nodo.args])
    raise ValueError("expresión no permitida")


def _valor(arbol: ast.AST, entorno: dict[str, float]) -> float:
    """El valor de la expresion en un punto, o NaN si ahi no esta definida (division por cero, raiz de un negativo...). Una
    expresion tan anidada que desborda la pila no es un punto sin definir sino un error de la expresion: ValueError."""
    try:
        resultado = _evaluar(arbol, entorno)
        return float(resultado) if isinstance(resultado, (int, float)) and math.isfinite(resultado) else math.nan
    except (RecursionError, MemoryError) as error:
        raise ValueError("la expresión está demasiado anidada para evaluarla: simplifícala") from error
    except (ZeroDivisionError, OverflowError, ValueError, TypeError):
        return math.nan


# ---------------------------------------------------------------------------
# Graficas
# ---------------------------------------------------------------------------


class TipoGrafica(str, Enum):
    lineas = "lineas"                # curvas: funciones de la variable, o datos unidos por lineas
    dispersion = "dispersion"        # solo puntos (datos)
    barras = "barras"                # una barra por categoria


class EjeReferencia(str, Enum):
    x = "x"
    y = "y"


class Parametro(BaseModel):
    nombre: str
    valor: float


class Serie(BaseModel):
    nombre: str
    expresion: str | None = None     # funcion de la variable, p. ej. "V0*(1-exp(-t/tau))": el codigo calcula los puntos
    x: list[float] | None = None     # o datos explicitos (de una tabla de la fuente)
    y: list[float] | None = None     # en las barras, un valor por categoria


class LineaReferencia(BaseModel):
    eje: EjeReferencia               # `x`: linea vertical en x = valor; `y`: linea horizontal en y = valor
    valor: float
    etiqueta: str


class GraficaSpec(BaseModel):
    tipo: TipoGrafica
    titulo: str
    etiqueta_x: str
    etiqueta_y: str
    variable: str = "x"              # nombre de la variable independiente en las expresiones
    dominio_min: float | None = None
    dominio_max: float | None = None
    parametros: list[Parametro] = []
    series: list[Serie]
    categorias: list[str] = []       # solo barras
    escala_log_x: bool = False
    escala_log_y: bool = False
    lineas_referencia: list[LineaReferencia] = []

    @model_validator(mode="after")
    def es_dibujable(self) -> "GraficaSpec":
        problemas = validar_grafica(self)
        if problemas:
            raise ValueError("gráfica no válida: " + "; ".join(problemas))
        return self


def _entorno_base(spec: GraficaSpec) -> dict[str, float]:
    return {**_CONSTANTES, **{p.nombre: p.valor for p in spec.parametros}}


def _permitidos(spec: GraficaSpec) -> set[str]:
    return {spec.variable, *(p.nombre for p in spec.parametros), *_CONSTANTES}


def puntos_de(spec: GraficaSpec, serie: Serie) -> tuple[list[float], list[float]]:
    """(x, y) de una serie: los datos tal cual, o la expresion calculada en MAX_PUNTOS puntos del dominio (los puntos donde
    no esta definida quedan como NaN, y matplotlib deja ahi un hueco)."""
    if serie.expresion is None:
        return list(serie.x or []), list(serie.y or [])
    a, b = float(spec.dominio_min), float(spec.dominio_max)
    if spec.escala_log_x:
        xs = [a * (b / a) ** (k / (MAX_PUNTOS - 1)) for k in range(MAX_PUNTOS)]
    else:
        xs = [a + (b - a) * k / (MAX_PUNTOS - 1) for k in range(MAX_PUNTOS)]
    arbol = _compilar(serie.expresion, _permitidos(spec))
    entorno = _entorno_base(spec)
    ys = []
    for x in xs:
        entorno[spec.variable] = x
        ys.append(_valor(arbol, entorno))
    return xs, ys


def validar_grafica(spec: GraficaSpec) -> list[str]:
    """Lo que impide dibujar la grafica (lista vacia si esta bien). El mensaje se le devuelve al modelo para que la corrija."""
    problemas: list[str] = []
    if not spec.series:
        return ["no tiene series"]
    if len(spec.series) > MAX_SERIES:
        problemas.append(f"demasiadas series ({len(spec.series)}; máximo {MAX_SERIES})")
    if not spec.variable.isidentifier() or spec.variable in _FUNCIONES or spec.variable in _CONSTANTES:
        problemas.append(f"`variable` («{spec.variable}») debe ser un nombre simple que no sea una función ni pi/e")
    for p in spec.parametros:
        if not p.nombre.isidentifier() or p.nombre in _FUNCIONES or p.nombre == spec.variable:
            problemas.append(f"el parámetro «{p.nombre}» no es un nombre válido o choca con la variable o una función")
    if spec.tipo == TipoGrafica.barras:
        if not spec.categorias:
            problemas.append("las barras necesitan `categorias`")
        for s in spec.series:
            if s.expresion is not None or s.y is None or len(s.y) != len(spec.categorias):
                problemas.append(f"la serie «{s.nombre}» de barras necesita `y` con un valor por categoría ({len(spec.categorias)}) y sin `expresion`")
        return problemas
    if spec.dominio_min is not None and spec.dominio_max is not None and not spec.dominio_min < spec.dominio_max:
        problemas.append("`dominio_min` debe ser menor que `dominio_max`")
    for s in spec.series:
        if s.expresion is not None:
            if spec.dominio_min is None or spec.dominio_max is None:
                problemas.append(f"la serie «{s.nombre}» tiene `expresion`: declara `dominio_min` y `dominio_max`")
                continue
            if spec.escala_log_x and spec.dominio_min <= 0:
                problemas.append("con escala logarítmica en x, `dominio_min` debe ser mayor que 0")
                continue
            if spec.tipo == TipoGrafica.dispersion:
                problemas.append("una gráfica de dispersión usa datos (`x`, `y`), no expresiones")
                continue
            try:
                xs, ys = puntos_de(spec, s)
            except ValueError as error:
                problemas.append(str(error))
                continue
            finitos = [y for y in ys if math.isfinite(y)]
            if len(finitos) < MAX_PUNTOS * 0.6:
                problemas.append(f"la serie «{s.nombre}» solo está definida en {len(finitos)} de {MAX_PUNTOS} puntos del dominio: revisa la expresión y el dominio")
            elif max(finitos) - min(finitos) < 1e-12:
                problemas.append(f"la serie «{s.nombre}» es constante en todo el dominio: revisa la expresión o los parámetros")
        else:
            if not s.x or not s.y or len(s.x) != len(s.y) or len(s.x) < 2:
                problemas.append(f"la serie «{s.nombre}» necesita `expresion`, o `x` e `y` con la misma longitud (al menos 2 puntos)")
            elif (spec.escala_log_x and min(s.x) <= 0) or (spec.escala_log_y and min(s.y) <= 0):
                problemas.append(f"la serie «{s.nombre}» tiene valores <= 0 y la escala es logarítmica")
    if spec.escala_log_y and any(s.expresion is not None for s in spec.series):
        problemas.append("no se combina una escala logarítmica en y con series de expresión (pueden salir valores <= 0): usa una tabla de datos")
    return problemas


def _estilo_ejes(ax) -> None:
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(OSCURO)
    ax.grid(True, color=GRIS_LINEA, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=OSCURO, labelsize=10)


def _texto_plano(texto: str) -> str:
    """El texto sin la sintaxis matematica (si matplotlib no la entiende): sin $, sin barras invertidas ni llaves."""
    for basura in ("$", "\\", "{", "}"):
        texto = texto.replace(basura, "")
    return texto


def _dibujar_grafica(spec: GraficaSpec, destino: Path, plano: bool) -> None:
    from matplotlib.figure import Figure

    def T(texto: str) -> str:
        return _texto_plano(texto) if plano else texto

    fig = Figure(figsize=TAMANO_GRAFICA, dpi=DPI, layout="constrained", facecolor="white")
    ax = fig.add_subplot(111)
    _estilo_ejes(ax)
    if spec.tipo == TipoGrafica.barras:
        n = len(spec.series)
        ancho = 0.8 / n
        for k, serie in enumerate(spec.series):
            posiciones = [i + (k - (n - 1) / 2) * ancho for i in range(len(spec.categorias))]
            barras = ax.bar(posiciones, serie.y, width=ancho * 0.92, color=COLORES_SERIE[k % len(COLORES_SERIE)], label=T(serie.nombre))
            ax.bar_label(barras, fmt="%g", fontsize=9, color=OSCURO, padding=2)
        ax.set_xticks(range(len(spec.categorias)), [T(c) for c in spec.categorias])
        ax.margins(y=0.15)
        ax.grid(False, axis="x")
    else:
        for k, serie in enumerate(spec.series):
            xs, ys = puntos_de(spec, serie)
            color = COLORES_SERIE[k % len(COLORES_SERIE)]
            if spec.tipo == TipoGrafica.dispersion:
                ax.scatter(xs, ys, s=26, color=color, label=T(serie.nombre), zorder=3)
            else:
                ax.plot(xs, ys, color=color, linewidth=2.2, label=T(serie.nombre), marker="o" if serie.expresion is None else None, markersize=4.5)
        if spec.escala_log_x:
            ax.set_xscale("log")
        if spec.escala_log_y:
            ax.set_yscale("log")
        if spec.dominio_min is not None and spec.dominio_max is not None:
            ax.set_xlim(spec.dominio_min, spec.dominio_max)
    for ref in spec.lineas_referencia:
        dibujar = ax.axvline if ref.eje == EjeReferencia.x else ax.axhline
        dibujar(ref.valor, color="#7C8598", linestyle="--", linewidth=1.3, zorder=1)
        if ref.eje == EjeReferencia.x:
            ax.annotate(T(ref.etiqueta), (ref.valor, 1.0), xycoords=("data", "axes fraction"), xytext=(5, -5), textcoords="offset points",
                        ha="left", va="top", fontsize=8.5, color="#4B5468", bbox=_FONDO_ROTULO)
        else:
            ax.annotate(T(ref.etiqueta), (1.0, ref.valor), xycoords=("axes fraction", "data"), xytext=(-4, 3), textcoords="offset points",
                        ha="right", va="bottom", fontsize=8.5, color="#4B5468", bbox=_FONDO_ROTULO)
    ax.set_xlabel(T(spec.etiqueta_x), fontsize=11, color=OSCURO)
    ax.set_ylabel(T(spec.etiqueta_y), fontsize=11, color=OSCURO)
    if spec.titulo.strip():
        ax.set_title(T(spec.titulo), fontsize=12, fontweight="bold", color=OSCURO, loc="left")
    if len(spec.series) > 1 or spec.series[0].nombre.strip():
        ax.legend(frameon=False, fontsize=10, labelcolor=OSCURO)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=DPI, facecolor="white")


def dibujar_grafica(spec: GraficaSpec, destino: Path) -> None:
    """Dibuja la grafica en un PNG. Si el texto de un rotulo lleva matematicas que matplotlib no entiende, la repite sin ellas."""
    try:
        _dibujar_grafica(spec, destino, plano=False)
    except ValueError:
        _dibujar_grafica(spec, destino, plano=True)


# ---------------------------------------------------------------------------
# Diagramas
# ---------------------------------------------------------------------------


class FormaNodo(str, Enum):
    caja = "caja"                    # un paso o un bloque
    estado = "estado"                # un estado (esquinas redondeadas)
    decision = "decision"            # una pregunta o condicion (rombo)
    terminal = "terminal"            # inicio o fin (capsula)


class Nodo(BaseModel):
    id: str
    texto: str
    forma: FormaNodo = FormaNodo.caja


class Arista(BaseModel):
    origen: str
    destino: str
    etiqueta: str = ""


class DiagramaSpec(BaseModel):
    nodos: list[Nodo]
    aristas: list[Arista]

    @model_validator(mode="after")
    def es_dibujable(self) -> "DiagramaSpec":
        problemas = validar_diagrama(self)
        if problemas:
            raise ValueError("diagrama no válido: " + "; ".join(problemas))
        return self


def validar_diagrama(spec: DiagramaSpec) -> list[str]:
    problemas: list[str] = []
    ids = [n.id for n in spec.nodos]
    if not 2 <= len(ids) <= MAX_NODOS:
        problemas.append(f"un diagrama lleva de 2 a {MAX_NODOS} nodos y llegaron {len(ids)}")
    if len(set(ids)) != len(ids):
        problemas.append("hay identificadores de nodo repetidos")
    for n in spec.nodos:
        if not n.texto.strip():
            problemas.append(f"el nodo «{n.id}» no tiene texto")
        elif len(n.texto) > 60:
            problemas.append(f"el texto del nodo «{n.id}» es demasiado largo ({len(n.texto)} caracteres; máximo 60): usa 2 a 5 palabras")
    if not spec.aristas:
        problemas.append("no tiene flechas (`aristas`)")
    if len(spec.aristas) > MAX_ARISTAS:
        problemas.append(f"demasiadas flechas ({len(spec.aristas)}; máximo {MAX_ARISTAS})")
    for a in spec.aristas:
        for extremo in (a.origen, a.destino):
            if extremo not in ids:
                problemas.append(f"una flecha usa el nodo «{extremo}», que no existe")
    conectados = {x for a in spec.aristas for x in (a.origen, a.destino)}
    sueltos = [i for i in ids if i not in conectados]
    if sueltos and spec.aristas:
        problemas.append(f"nodos sin ninguna flecha: {', '.join(sueltos)}")
    return problemas


def _clasificar_aristas(ids: list[str], pares: list[tuple[str, str]]) -> set[int]:
    """Indices de las aristas que cierran un ciclo (aristas de retorno): al ordenar en capas se ignoran, y se dibujan curvas."""
    salientes: dict[str, list[tuple[str, int]]] = {i: [] for i in ids}
    entradas = {i: 0 for i in ids}
    for k, (o, d) in enumerate(pares):
        if o != d:
            salientes[o].append((d, k))
            entradas[d] += 1
    estado: dict[str, int] = {}
    retorno: set[int] = set()

    def visitar(u: str) -> None:
        estado[u] = 1
        for v, k in salientes[u]:
            if estado.get(v, 0) == 0:
                visitar(v)
            elif estado[v] == 1:
                retorno.add(k)
        estado[u] = 2

    for raiz in [i for i in ids if entradas[i] == 0] + ids:
        if estado.get(raiz, 0) == 0:
            visitar(raiz)
    return retorno


def _capas(ids: list[str], pares: list[tuple[str, str]], retorno: set[int]) -> dict[str, int]:
    """Capa (0, 1, 2...) de cada nodo: el camino mas largo desde un nodo sin entradas, sin contar las aristas de retorno."""
    directas = [(o, d) for k, (o, d) in enumerate(pares) if o != d and k not in retorno]
    capa = {i: 0 for i in ids}
    for _ in range(len(ids)):
        cambio = False
        for o, d in directas:
            if capa[d] < capa[o] + 1:
                capa[d] = capa[o] + 1
                cambio = True
        if not cambio:
            break
    return capa


def _ordenar_capas(capas: list[list[str]], pares: list[tuple[str, str]]) -> list[list[str]]:
    """Reduce los cruces con el metodo del baricentro (unas pasadas de arriba abajo y de abajo arriba)."""
    vecinos: dict[str, list[str]] = {}
    for o, d in pares:
        if o != d:
            vecinos.setdefault(o, []).append(d)
            vecinos.setdefault(d, []).append(o)
    for paso in range(6):
        rango = range(1, len(capas)) if paso % 2 == 0 else range(len(capas) - 2, -1, -1)
        for c in rango:
            referencia = capas[c - 1] if paso % 2 == 0 else capas[c + 1]
            posicion = {n: k for k, n in enumerate(referencia)}
            def baricentro(n: str, actual=capas[c]) -> float:
                ps = [posicion[v] for v in vecinos.get(n, []) if v in posicion]
                return sum(ps) / len(ps) if ps else actual.index(n)
            capas[c] = sorted(capas[c], key=baricentro)
    return capas


def _tamano_nodo(nodo: Nodo, ancho_texto: int) -> tuple[float, float, list[str]]:
    """(ancho, alto en pulgadas, lineas del texto) de un nodo."""
    lineas = textwrap.wrap(nodo.texto.strip(), width=ancho_texto, break_long_words=False) or [nodo.texto]
    ancho = max(len(l) for l in lineas) * 0.093 + 0.34
    alto = len(lineas) * 0.21 + 0.26
    if nodo.forma == FormaNodo.decision:
        ancho, alto = ancho * 1.5, alto * 1.7
    elif nodo.forma == FormaNodo.terminal:
        ancho += 0.2
    return ancho, alto, lineas


def _colocar(nodos: list[Nodo], capas: list[list[str]], horizontal: bool, ancho_texto: int, max_capas: int, largo_rotulo: int = 0):
    """Posicion (centro, en pulgadas) y tamano de cada nodo. El flujo va de izquierda a derecha (o de arriba a abajo) por
    capas; los nodos de una misma capa se apilan en el eje transversal. Si hay mas capas que `max_capas`, se pliega en
    bandas en serpentina (la siguiente banda va en sentido contrario) para que el diagrama no quede desmesuradamente largo."""
    por_id = {n.id: n for n in nodos}
    total = len(capas)
    tam = {n.id: _tamano_nodo(n, ancho_texto) for n in nodos}
    flujo = {i: tam[i][0] if horizontal else tam[i][1] for i in tam}            # lo que mide un nodo a lo largo del flujo
    trans = {i: tam[i][1] if horizontal else tam[i][0] for i in tam}            # y a lo ancho
    separacion = 0.3

    pasos = min(total, max_capas)
    bandas = math.ceil(total / pasos)

    def celda(c: int) -> tuple[int, int]:
        banda, k = divmod(c, pasos)
        return (k if banda % 2 == 0 else pasos - 1 - k), banda

    ancho_paso = [0.0] * pasos
    alto_banda = [0.0] * bandas
    for c, nodos_capa in enumerate(capas):
        k, banda = celda(c)
        ancho_paso[k] = max(ancho_paso[k], max(flujo[i] for i in nodos_capa))
        alto_banda[banda] = max(alto_banda[banda], sum(trans[i] for i in nodos_capa) + separacion * (len(nodos_capa) - 1))
    espacio_rotulo = 0.3 + 0.075 * largo_rotulo                # entre dos capas cabe el rotulo mas largo de las flechas
    hueco_flujo, hueco_banda = (max(0.62, espacio_rotulo), 0.55) if horizontal else (0.55, max(0.62, espacio_rotulo))
    centro_paso, acumulado = [], 0.0
    for k in range(pasos):
        centro_paso.append(acumulado + ancho_paso[k] / 2)
        acumulado += ancho_paso[k] + hueco_flujo
    centro_banda, acumulado = [], 0.0
    for b in range(bandas):
        centro_banda.append(acumulado + alto_banda[b] / 2)
        acumulado += alto_banda[b] + hueco_banda

    posiciones: dict[str, tuple[float, float]] = {}
    for c, nodos_capa in enumerate(capas):
        k, banda = celda(c)
        altura = sum(trans[i] for i in nodos_capa) + separacion * (len(nodos_capa) - 1)
        t = centro_banda[banda] - altura / 2
        for i in nodos_capa:
            t_centro = t + trans[i] / 2
            posiciones[i] = (centro_paso[k], -t_centro) if horizontal else (t_centro, -centro_paso[k])
            t += trans[i] + separacion
    return posiciones, tam


def _extension(posiciones, tam) -> tuple[float, float, float, float]:
    xs0 = [posiciones[i][0] - tam[i][0] / 2 for i in posiciones]
    xs1 = [posiciones[i][0] + tam[i][0] / 2 for i in posiciones]
    ys0 = [posiciones[i][1] - tam[i][1] / 2 for i in posiciones]
    ys1 = [posiciones[i][1] + tam[i][1] / 2 for i in posiciones]
    return min(xs0), max(xs1), min(ys0), max(ys1)


def _curva_de(k: int, o: str, d: str, retorno: set[int], pares: list[tuple[str, str]]) -> float:
    """El `rad` de arc3 de la flecha k: 0 (recta) salvo que cierre un ciclo o exista tambien la flecha contraria."""
    if k in retorno:
        return 0.3
    return 0.22 if (d, o) in pares else 0.0


def _extension_con_flechas(posiciones, tam, aristas: list[Arista], retorno: set[int]) -> tuple[float, float, float, float]:
    """Como _extension, pero incluyendo hasta donde se abomban las flechas curvas y los bucles sobre un mismo nodo."""
    x0, x1, y0, y1 = _extension(posiciones, tam)
    pares = [(a.origen, a.destino) for a in aristas]
    for k, a in enumerate(aristas):
        if a.origen == a.destino:
            y1 = max(y1, posiciones[a.origen][1] + tam[a.origen][1] / 2 + 0.62)
            continue
        curva = _curva_de(k, a.origen, a.destino, retorno, pares)
        if curva:
            (ox, oy), (dx, dy) = posiciones[a.origen], posiciones[a.destino]
            mx, my = (ox + dx) / 2 + 0.5 * curva * (dy - oy), (oy + dy) / 2 - 0.5 * curva * (dx - ox)
            x0, x1, y0, y1 = min(x0, mx - 0.2), max(x1, mx + 0.2), min(y0, my - 0.2), max(y1, my + 0.2)
    return x0, x1, y0, y1


def _orientacion(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _se_cruzan(a, b, c, d) -> bool:
    """True si los segmentos ab y cd se cruzan de verdad (no solo se tocan en un extremo)."""
    o1, o2, o3, o4 = _orientacion(a, b, c), _orientacion(a, b, d), _orientacion(c, d, a), _orientacion(c, d, b)
    return o1 * o2 < -1e-9 and o3 * o4 < -1e-9


def _atraviesa(a, b, centro, tam) -> bool:
    """True si el segmento ab pasa por dentro de la caja de un nodo (algo encogida: rozarla no cuenta)."""
    x0, x1 = centro[0] - tam[0] / 2 + 0.06, centro[0] + tam[0] / 2 - 0.06
    y0, y1 = centro[1] - tam[1] / 2 + 0.06, centro[1] + tam[1] / 2 - 0.06
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return False
    return True


def _costo(posiciones, tam, aristas: list[Arista], retorno: set[int]) -> float:
    """Que tan mala es una disposicion: tamano frente al rectangulo objetivo, flechas que se cruzan, flechas que atraviesan
    un nodo ajeno y longitud total de las flechas."""
    pares = [(a.origen, a.destino) for a in aristas]
    x0, x1, y0, y1 = _extension_con_flechas(posiciones, tam, aristas, retorno)
    ancho, alto = x1 - x0, y1 - y0
    objetivo_x, objetivo_y = TAMANO_OBJETIVO_DIAGRAMA
    costo = 4.0 * max(ancho / objetivo_x, alto / objetivo_y) + 0.3 * abs(math.log((ancho / alto) / (objetivo_x / objetivo_y)))
    segmentos = [(o, d, posiciones[o], posiciones[d]) for o, d in pares if o != d]
    for k, (o1, d1, a, b) in enumerate(segmentos):
        costo += 0.05 * math.dist(a, b)
        for i, c in posiciones.items():
            if i not in (o1, d1) and _atraviesa(a, b, c, tam[i]):
                costo += 2.5
        for o2, d2, c, d in segmentos[k + 1:]:
            if len({o1, d1, o2, d2}) == 4 and _se_cruzan(a, b, c, d):
                costo += 0.8
    return costo


def _mejor_disposicion(spec: DiagramaSpec):
    """Genera muchas disposiciones (flujo horizontal o vertical, con distintos plegados, anchos de texto y ordenes de los
    nodos dentro de cada capa) y se queda con la de menor costo. Es determinista: siempre elige la misma para la misma spec."""
    import random

    ids = [n.id for n in spec.nodos]
    pares = [(a.origen, a.destino) for a in spec.aristas]
    retorno = _clasificar_aristas(ids, pares)
    capa = _capas(ids, pares, retorno)
    total = max(capa.values()) + 1
    base = _ordenar_capas([[i for i in ids if capa[i] == c] for c in range(total)], pares)
    largo_rotulo = min(max((len(a.etiqueta) for a in spec.aristas), default=0), 14)
    azar = random.Random(7)
    ordenes = [base] + [[azar.sample(c, len(c)) for c in base] for _ in range(14)]
    mejor, costo_mejor = None, math.inf
    for horizontal in (True, False):
        for max_capas in sorted({total, 6, 5, 4, 3}, reverse=True):
            if max_capas > total:
                continue
            for ancho_texto in (18, 14, 11):
                for capas in ordenes:
                    posiciones, tam = _colocar(spec.nodos, capas, horizontal, ancho_texto, max_capas, largo_rotulo)
                    costo = _costo(posiciones, tam, spec.aristas, retorno)
                    if costo < costo_mejor - 1e-9:
                        mejor, costo_mejor = (posiciones, tam, retorno, _extension_con_flechas(posiciones, tam, spec.aristas, retorno)), costo
    return mejor


def _sitio_de_etiqueta(a, b, curva: float, etiqueta: str, posiciones, tam, extremos: tuple[str, str]) -> tuple[float, float]:
    """Donde poner el rotulo de una flecha: el punto de su trazo (el medio, o uno cercano) que no cae sobre ningun nodo."""
    cx, cy = (a[0] + b[0]) / 2 + curva * (b[1] - a[1]), (a[1] + b[1]) / 2 - curva * (b[0] - a[0])     # punto de control de arc3
    mitad = len(etiqueta) * 0.05 + 0.1
    primero = None
    for t in (0.5, 0.4, 0.6, 0.3, 0.7, 0.25, 0.75):
        x = (1 - t) ** 2 * a[0] + 2 * t * (1 - t) * cx + t * t * b[0]
        y = (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * cy + t * t * b[1]
        primero = primero or (x, y)
        if not any(abs(x - c[0]) < tam[i][0] / 2 + mitad and abs(y - c[1]) < tam[i][1] / 2 + 0.12 for i, c in posiciones.items()):
            return x, y
    return primero


def _dibujar_diagrama(spec: DiagramaSpec, destino: Path, plano: bool) -> None:
    from matplotlib.figure import Figure
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

    def T(texto: str) -> str:
        return _texto_plano(texto) if plano else texto

    posiciones, tam, retorno, (x0, x1, y0, y1) = _mejor_disposicion(spec)
    margen = 0.28
    ancho, alto = x1 - x0 + 2 * margen, y1 - y0 + 2 * margen
    fig = Figure(figsize=(ancho, alto), dpi=DPI, facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(x0 - margen, x1 + margen)
    ax.set_ylim(y0 - margen, y1 + margen)
    ax.set_aspect("equal")
    ax.axis("off")

    relleno = {FormaNodo.caja: (AZUL_FONDO, AZUL), FormaNodo.estado: (AZUL_FONDO, AZUL), FormaNodo.decision: (NARANJA_FONDO, NARANJA),
               FormaNodo.terminal: (VERDE_FONDO, VERDE)}
    parches = {}
    for nodo in spec.nodos:
        cx, cy = posiciones[nodo.id]
        w, h, lineas = tam[nodo.id]
        fondo, borde = relleno[nodo.forma]
        if nodo.forma == FormaNodo.decision:
            parche = Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fondo, ec=borde, lw=1.8, zorder=2)
        else:
            estilo = {FormaNodo.caja: "round,pad=0,rounding_size=0.04", FormaNodo.estado: "round,pad=0,rounding_size=0.12",
                      FormaNodo.terminal: f"round,pad=0,rounding_size={h / 2:.3f}"}[nodo.forma]
            parche = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=estilo, fc=fondo, ec=borde, lw=1.8, zorder=2)
        ax.add_patch(parche)
        parches[nodo.id] = parche
        ax.text(cx, cy, T("\n".join(lineas)), ha="center", va="center", fontsize=10, color=OSCURO, zorder=3, linespacing=1.15)

    pares = [(a.origen, a.destino) for a in spec.aristas]
    for k, arista in enumerate(spec.aristas):
        (ox, oy), (dx_, dy_) = posiciones[arista.origen], posiciones[arista.destino]
        if arista.origen == arista.destino:                                    # bucle sobre el mismo nodo
            w, h, _ = tam[arista.origen]
            arriba = oy + h / 2
            flecha = FancyArrowPatch((ox - w * 0.22, arriba), (ox + w * 0.22, arriba), connectionstyle="arc3,rad=-2.0", arrowstyle="-|>",
                                     mutation_scale=12, lw=1.5, color=OSCURO, zorder=1, shrinkA=0, shrinkB=0)
            ax.add_patch(flecha)
            if arista.etiqueta:
                ax.text(ox, arriba + 0.36, T(arista.etiqueta), ha="center", va="bottom", fontsize=9, color="#4B5468", zorder=4)
            continue
        curva = _curva_de(k, arista.origen, arista.destino, retorno, pares)
        flecha = FancyArrowPatch((ox, oy), (dx_, dy_), patchA=parches[arista.origen], patchB=parches[arista.destino], connectionstyle=f"arc3,rad={curva}",
                                 arrowstyle="-|>", mutation_scale=12, lw=1.5, color=OSCURO, zorder=1, shrinkA=0, shrinkB=1)
        ax.add_patch(flecha)
        if arista.etiqueta:
            mx, my = _sitio_de_etiqueta((ox, oy), (dx_, dy_), curva, arista.etiqueta, posiciones, tam, (arista.origen, arista.destino))
            ax.text(mx, my, T(arista.etiqueta), ha="center", va="center", fontsize=9, color="#4B5468", zorder=4,
                    bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.92})
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=DPI, facecolor="white")


def dibujar_diagrama(spec: DiagramaSpec, destino: Path) -> None:
    try:
        _dibujar_diagrama(spec, destino, plano=False)
    except ValueError:
        _dibujar_diagrama(spec, destino, plano=True)
