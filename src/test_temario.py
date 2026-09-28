"""Prueba de la redaccion del temario en tres pasos: las figuras (figuras.py), la busqueda en las fuentes cargadas
(pasajes.py), los esquemas de lo que el LLM devuelve (schema_temario.py) y el flujo de temario.py con validacion y reintentos.

El LLM esta sustituido por respuestas fijas (_fixtures.responder_temario); aqui SI se dibuja con matplotlib de verdad
(los demas tests lo sustituyen por un PNG falso para ir mas rapido).

Uso (desde src/):  python test_temario.py
"""

import ast
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import _fixtures
import correlate_bibliografia
import figuras
import latex_seguro as ls
import pasajes
import planeador
import temario
import vault
from pydantic import ValidationError
from schema_planeador import minutos_por_bloque
from schema_temario import (
    Bloque,
    ClaseUnidad,
    ElementoPlan,
    CierreSesion,
    PlanSesion,
    ResultadoSesion,
    SeccionRedactada,
    UnidadPlan,
    celdas_de_tabla,
    elementos_de,
    palabras_de,
)

SRC = Path(__file__).resolve().parent
PNG = b"\x89PNG\r\n\x1a\n"


def esperar(excepcion, funcion, *args, **kwargs):
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


def grafica(**cambios) -> figuras.GraficaSpec:
    base = dict(tipo="lineas", titulo="Carga RC", etiqueta_x="Tiempo (s)", etiqueta_y="Tensión (V)", variable="t", dominio_min=0, dominio_max=5,
                parametros=[figuras.Parametro(nombre="V0", valor=5), figuras.Parametro(nombre="tau", valor=1)],
                series=[figuras.Serie(nombre="vC", expresion="V0*(1-exp(-t/tau))")])
    return figuras.GraficaSpec(**{**base, **cambios})


def diagrama(n: int = 4, **cambios) -> figuras.DiagramaSpec:
    nodos = [figuras.Nodo(id=f"n{i}", texto=f"Paso {i}") for i in range(n)]
    aristas = [figuras.Arista(origen=f"n{i}", destino=f"n{i + 1}") for i in range(n - 1)]
    return figuras.DiagramaSpec(**{**dict(nodos=nodos, aristas=aristas), **cambios})


# ---------------------------------------------------------------------------
# A. figuras.py (matplotlib de verdad)
# ---------------------------------------------------------------------------


def probar_figuras() -> None:
    assert figuras.disponible()
    g = grafica()
    xs, ys = figuras.puntos_de(g, g.series[0])
    assert len(xs) == figuras.MAX_PUNTOS == len(ys) and xs[0] == 0 and xs[-1] == 5 and ys[0] == 0 and abs(ys[-1] - 5 * (1 - 2.718281828459045 ** -5)) < 1e-9
    potencia = figuras.puntos_de(grafica(series=[figuras.Serie(nombre="p", expresion="2 * t ^ 2 + pi")]), figuras.Serie(nombre="p", expresion="2 * t ^ 2 + pi"))[1]
    assert abs(potencia[0] - 3.141592653589793) < 1e-9 and abs(potencia[-1] - (50 + 3.141592653589793)) < 1e-9             # `^` es potencia, pi existe
    raiz = grafica(dominio_min=-1, dominio_max=4, series=[figuras.Serie(nombre="r", expresion="sqrt(t)")])                   # no definida en t < 0: hueco, no error
    assert sum(1 for y in figuras.puntos_de(raiz, raiz.series[0])[1] if y != y) > 0
    datos = grafica(series=[figuras.Serie(nombre="d", x=[0, 1, 2], y=[0.0, 0.5, 0.9])])
    assert figuras.puntos_de(datos, datos.series[0]) == ([0, 1, 2], [0.0, 0.5, 0.9])
    print("A1. figuras: las expresiones se calculan en 300 puntos del dominio con un evaluador propio (`^` es potencia, hay pi y e, un punto sin definir es un hueco); los datos van tal cual -- OK")

    malas = {"2 t": "multiplicaci", "log(t)": "ln", "log10(": "no se entiende", "__import__('os').system('x')": "solo se admiten las funciones",
             "t.real": "solo se admiten", "open('f')": "solo se admiten las funciones", "foo(t)": "solo se admiten las funciones", "zeta*t": "no es la variable",
             "'texto'": "solo se admiten", "[1, 2]": "solo se admiten", "lambda: 1": "solo se admiten", "t**1000": "solo est", "5": "constante", "": "vac"}
    for expresion, motivo in malas.items():
        problemas = figuras.validar_grafica(figuras.GraficaSpec.model_construct(
            tipo="lineas", titulo="", etiqueta_x="", etiqueta_y="", variable="t", dominio_min=0, dominio_max=5, parametros=[], series=[figuras.Serie(nombre="s", expresion=expresion)],
            categorias=[], escala_log_x=False, escala_log_y=False, lineas_referencia=[]))
        assert problemas and motivo in problemas[0], (expresion, problemas)
        assert "eval" not in " ".join(problemas)
    assert "esta definida" not in " ".join(figuras.validar_grafica(grafica()))
    invalidas = [
        dict(dominio_min=None), dict(dominio_min=5, dominio_max=1), dict(tipo="dispersion"), dict(escala_log_x=True), dict(variable="sin"), dict(variable="1x"),
        dict(parametros=[figuras.Parametro(nombre="exp", valor=1)]), dict(series=[]), dict(series=[figuras.Serie(nombre=str(i), x=[0, 1], y=[0, 1]) for i in range(6)]),
        dict(series=[figuras.Serie(nombre="s", x=[0, 1], y=[0])]), dict(series=[figuras.Serie(nombre="s")]),
        dict(tipo="barras", categorias=[], series=[figuras.Serie(nombre="s", y=[1, 2])]),
        dict(tipo="barras", categorias=["a", "b"], series=[figuras.Serie(nombre="s", y=[1])]),
        dict(escala_log_y=True), dict(escala_log_x=True, dominio_min=0, dominio_max=10, series=[figuras.Serie(nombre="s", x=[0, 1], y=[1, 2])]),
    ]
    for cambio in invalidas:
        esperar(ValidationError, grafica, **cambio)
    grafica(tipo="barras", categorias=["a", "b"], series=[figuras.Serie(nombre="s", y=[1, 2])])                                 # y las buenas si pasan
    grafica(tipo="dispersion", series=[figuras.Serie(nombre="s", x=[1, 2], y=[3, 4])])
    grafica(escala_log_x=True, dominio_min=1, dominio_max=1000, parametros=[figuras.Parametro(nombre="V0", valor=5), figuras.Parametro(nombre="tau", valor=1)])
    print(f"A2. figuras: {len(malas)} expresiones peligrosas o mal escritas se rechazan con un mensaje util (nunca eval) y {len(invalidas)} especificaciones incoherentes no validan -- OK")

    probar_expresiones_desmesuradas()

    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        from matplotlib import image

        def azul_presente(ruta: Path) -> bool:
            im = image.imread(ruta)
            return bool(((abs(im[..., 0] - 0.0) < 0.05) & (abs(im[..., 1] - 0.678) < 0.05) & (abs(im[..., 2] - 0.906) < 0.05)).any())     # #00ADE7, el azul IUB

        figuras.dibujar_grafica(g, raiz / "g.png")
        assert (raiz / "g.png").read_bytes()[:8] == PNG and ls.dimensiones_png(raiz / "g.png") == (1280, 550) and azul_presente(raiz / "g.png")
        for spec in (grafica(tipo="barras", categorias=["A", "B", "C"], series=[figuras.Serie(nombre="1", y=[1, 2, 3]), figuras.Serie(nombre="2", y=[2, 3, 1])]),
                     grafica(tipo="dispersion", series=[figuras.Serie(nombre="m", x=[0, 1, 2, 3], y=[0, 1, 4, 9])]),
                     grafica(escala_log_x=True, dominio_min=1, dominio_max=10000, series=[figuras.Serie(nombre="f", expresion="1/sqrt(1+(t/tau)^2)")],
                             lineas_referencia=[figuras.LineaReferencia(eje="x", valor=1, etiqueta="fc"), figuras.LineaReferencia(eje="y", valor=0.7, etiqueta="-3 dB")])):
            figuras.dibujar_grafica(spec, raiz / "otra.png")
            assert ls.dimensiones_png(raiz / "otra.png") == (1280, 550)
        sucio = grafica(etiqueta_x="Tiempo $\\foo{x}$", titulo="Titulo con $ suelto")                                  # matematica que matplotlib no entiende: se repite sin ella
        figuras.dibujar_grafica(sucio, raiz / "sucio.png")
        assert (raiz / "sucio.png").read_bytes()[:8] == PNG
        figuras.dibujar_grafica(g, raiz / "g2.png")
        assert (raiz / "g.png").read_bytes() == (raiz / "g2.png").read_bytes()                                             # determinista: mismo PNG para la misma especificacion
    print("A3. figuras: las graficas (curvas, barras, dispersion, escala logaritmica, lineas de referencia) salen como PNG de 1280 x 550 con el azul IUB; un rotulo con matematica invalida no rompe el dibujo; es determinista -- OK")


def probar_expresiones_desmesuradas() -> None:
    """Una expresion enorme o anidada hasta desbordar la pila del analizador no puede escapar como RecursionError/MemoryError:
    temario._redactar solo captura ValueError, y una excepcion asi detendria toda la generacion en vez de volver al modelo."""
    assert figuras.MAX_EXPRESION == 300
    largas = {"-" * 3000 + "1": "demasiado larga", "1" + "+t" * 200: "demasiado larga"}                                   # 3001 y 401 caracteres
    for expresion, motivo in largas.items():
        mensaje = esperar(ValueError, figuras._compilar, expresion, {"t"})
        assert motivo in mensaje and str(len(expresion)) in mensaje and len(mensaje) < 300                                  # el mensaje no repite los 3000 signos
        esperar(ValidationError, grafica, series=[figuras.Serie(nombre="s", expresion=expresion)])
        assert any(motivo in p for p in figuras.validar_grafica(figuras.GraficaSpec.model_construct(
            tipo="lineas", titulo="", etiqueta_x="", etiqueta_y="", variable="t", dominio_min=0, dominio_max=5, parametros=[], series=[figuras.Serie(nombre="s", expresion=expresion)],
            categorias=[], escala_log_x=False, escala_log_y=False, lineas_referencia=[])))                                   # el motivo llega a la lista que se le devuelve al modelo
    con_espacios = "  " + "10" + "+t" * 149 + "  "                                                                           # 300 caracteres sin los espacios de los bordes: cabe
    figuras._compilar(con_espacios, {"t"})
    esperar(ValueError, figuras._compilar, "10" + "+t" * 150, {"t"})                                                          # 302: no cabe
    grafica(series=[figuras.Serie(nombre="s", expresion="1" + "+t" * 100)])                                                   # una suma larga pero razonable sigue valiendo

    # sin el limite de largo, el analizador de Python tambien se desborda con una cadena de signos (segun la version de Python,
    # con RecursionError o MemoryError): compile o no, lo unico que puede salir de _compilar es un ValueError
    normal = figuras.MAX_EXPRESION
    figuras.MAX_EXPRESION = 10 ** 6
    try:
        for expresion in ("-" * 3000 + "1", "(" * 190 + "1" + ")" * 190, "1" + "+t" * 20000, "t" + "**t" * 3000):
            try:
                figuras._compilar(expresion, {"t"})
            except ValueError as error:
                assert "no se entiende" in str(error) or "anidada" in str(error), str(error)
    finally:
        figuras.MAX_EXPRESION = normal

    # y al evaluar: un arbol de 5000 niveles (que ninguna expresion de <= 300 caracteres produce) no debe escapar como RecursionError
    nodo = ast.Constant(1)
    for _ in range(5000):
        nodo = ast.UnaryOp(ast.USub(), nodo)
    arbol_profundo = ast.Expression(nodo)
    mensaje = esperar(ValueError, figuras._valor, arbol_profundo, {})
    assert "anidada" in mensaje and "evalu" in mensaje
    spec = grafica()
    compilar = figuras._compilar
    figuras._compilar = lambda expresion, permitidos: arbol_profundo
    try:
        problemas = figuras.validar_grafica(spec)
    finally:
        figuras._compilar = compilar
    assert len(problemas) == 1 and "anidada" in problemas[0] and "solo está definida" not in problemas[0]                    # el motivo real, no "definida en 0 de 300 puntos"
    hueco = figuras._valor(figuras._compilar("1/t", {"t"}), {"t": 0})
    assert hueco != hueco                                                                                                    # la division por cero sigue siendo un hueco (NaN), no un error
    print("A2b. figuras: una expresion de mas de 300 caracteres, o anidada hasta desbordar el analizador o el evaluador, se rechaza con un ValueError claro (y un GraficaSpec con ella, con ValidationError); no detiene la generacion -- OK")


def probar_diagramas() -> None:
    esperar(ValidationError, diagrama, 1, aristas=[])
    esperar(ValidationError, diagrama, 13)
    esperar(ValidationError, figuras.DiagramaSpec, nodos=[figuras.Nodo(id="a", texto="A"), figuras.Nodo(id="a", texto="B")], aristas=[figuras.Arista(origen="a", destino="a")])
    esperar(ValidationError, figuras.DiagramaSpec, nodos=[figuras.Nodo(id="a", texto="A"), figuras.Nodo(id="b", texto="B")], aristas=[figuras.Arista(origen="a", destino="z")])
    esperar(ValidationError, figuras.DiagramaSpec, nodos=[figuras.Nodo(id="a", texto="A"), figuras.Nodo(id="b", texto="B"), figuras.Nodo(id="c", texto="C")],
            aristas=[figuras.Arista(origen="a", destino="b")])                                                              # `c` sin ninguna flecha
    esperar(ValidationError, diagrama, 3, nodos=[figuras.Nodo(id="n0", texto="x" * 61), figuras.Nodo(id="n1", texto="B"), figuras.Nodo(id="n2", texto="C")])
    esperar(ValidationError, diagrama, 3, aristas=[])
    print("A4. diagramas: menos de 2 o mas de 12 nodos, ids repetidos, flechas a nodos que no existen, nodos sueltos, textos largos y sin flechas no validan -- OK")

    formas = list(figuras.FormaNodo)
    palabras = ["Leer", "sensor", "Activar válvula", "Temporizador", "Falla térmica", "Contactor", "ok", "Arranque del motor"]
    azar = random.Random(3)
    for caso in range(25):
        n = azar.randint(3, 10)
        nodos = [figuras.Nodo(id=f"n{i}", texto=" ".join(azar.choice(palabras) for _ in range(azar.randint(1, 3))), forma=azar.choice(formas)) for i in range(n)]
        aristas = [figuras.Arista(origen=f"n{i}", destino=f"n{i + 1}", etiqueta=azar.choice(["", "sí", "no", "t ≥ 3 s"])) for i in range(n - 1)]
        for _ in range(azar.randint(0, 4)):                                                                                # retornos, bucles y flechas de ida y vuelta
            aristas.append(figuras.Arista(origen=f"n{azar.randrange(n)}", destino=f"n{azar.randrange(n)}", etiqueta=azar.choice(["", "otra"])))
        spec = figuras.DiagramaSpec(nodos=nodos, aristas=aristas)
        posiciones, tam, retorno, (x0, x1, y0, y1) = figuras._mejor_disposicion(spec)
        assert set(posiciones) == {nd.id for nd in nodos}
        for a in range(n):
            for b in range(a + 1, n):
                (xa, ya), (xb, yb) = posiciones[f"n{a}"], posiciones[f"n{b}"]
                separados = abs(xa - xb) >= (tam[f"n{a}"][0] + tam[f"n{b}"][0]) / 2 - 1e-6 or abs(ya - yb) >= (tam[f"n{a}"][1] + tam[f"n{b}"][1]) / 2 - 1e-6
                assert separados, (caso, a, b)                                                                              # ningun nodo tapa a otro
        assert x1 - x0 < 60 and y1 - y0 < 60
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        fsm = figuras.DiagramaSpec(
            nodos=[figuras.Nodo(id="r", texto="REPOSO", forma="estado"), figuras.Nodo(id="a", texto="ARRANQUE", forma="estado"), figuras.Nodo(id="f", texto="FALLA", forma="estado"),
                   figuras.Nodo(id="d", texto="¿Presión lista?", forma="decision"), figuras.Nodo(id="t", texto="Fin", forma="terminal")],
            aristas=[figuras.Arista(origen="r", destino="a", etiqueta="START"), figuras.Arista(origen="a", destino="d"), figuras.Arista(origen="d", destino="t", etiqueta="sí"),
                     figuras.Arista(origen="d", destino="a", etiqueta="no"), figuras.Arista(origen="a", destino="f", etiqueta="falla"), figuras.Arista(origen="f", destino="f", etiqueta="alarma"),
                     figuras.Arista(origen="f", destino="r", etiqueta="rearme"), figuras.Arista(origen="t", destino="r")])
        figuras.dibujar_diagrama(fsm, raiz / "d.png")
        figuras.dibujar_diagrama(fsm, raiz / "d2.png")
        assert (raiz / "d.png").read_bytes()[:8] == PNG and (raiz / "d.png").read_bytes() == (raiz / "d2.png").read_bytes()
        ancho, alto = ls.dimensiones_png(raiz / "d.png")
        assert 300 < ancho < 3000 and 200 < alto < 2000
        figuras.dibujar_diagrama(diagrama(3, nodos=[figuras.Nodo(id="n0", texto="$\\foo{x}$ roto"), figuras.Nodo(id="n1", texto="B"), figuras.Nodo(id="n2", texto="C")]), raiz / "e.png")
        assert (raiz / "e.png").exists()
    print("A5. diagramas: 25 grafos al azar (ciclos, bucles, flechas de ida y vuelta) se disponen sin que un nodo tape a otro; un diagrama de estados con decision, terminal y bucle se dibuja (determinista) -- OK")


# ---------------------------------------------------------------------------
# B. pasajes.py
# ---------------------------------------------------------------------------

LIBRO = """# Control secuencial

## Capítulo 1: Máquinas de estado

A finite state machine (FSM) is a model of computation with a finite number of states. The machine is in exactly one state at a time and
changes state in response to inputs, which are called transitions. In sequential control the FSM replaces long chains of if statements.

Una máquina de estados finitos es un modelo con un número finito de estados. En control secuencial sustituye a las cadenas de condicionales.

## Capítulo 2: Temporización

Non-blocking timing uses the millis function: the program stores a reference time and compares the difference against the interval. Using delay
stops the whole program, so emergency inputs are ignored while the delay lasts.

| Función | Bloquea | Uso |
|---|---|---|
| delay | sí | pruebas simples |
| millis | no | control industrial |

## Capítulo 3: Motores

Three-phase induction motors draw a starting current between five and eight times the rated current, so thermal relays use trip class 10.
"""


def probar_pasajes() -> None:
    trozos = pasajes.trocear(LIBRO, "raw: libro.md")
    ubicaciones = [u for u, _ in trozos]
    assert any("Capítulo 1: Máquinas de estado" in u for u in ubicaciones) and all(u.startswith("raw: libro.md") for u in ubicaciones)
    assert not any("finite state" in t and "Non-blocking" in t for _, t in trozos)                        # un pasaje no mezcla dos secciones
    assert any("| millis | no | control industrial |" in t for _, t in trozos)                          # las tablas se conservan enteras
    largo = "Frase larga de relleno para partir. " * 200
    partido = pasajes.trocear("## Uno\n\n" + largo, "raw: x.md")
    assert len(partido) > 3 and all(len(t) <= pasajes.PASAJE_MAXIMO for _, t in partido)
    assert pasajes.trocear("## Solo titulo\n\ncorto", "raw: x.md") == []                                # un pasaje casi vacio no dice nada
    print("B1. pasajes: el texto se parte en pasajes de <= 1400 caracteres que respetan los encabezados (con su ubicacion), conservan las tablas y descartan lo vacio -- OK")

    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        os.chdir(tmp)
        try:
            (raiz / "raw" / "bibliografia").mkdir(parents=True)
            (raiz / "raw" / "bibliografia" / "libro.md").write_text(LIBRO, encoding="utf-8")
            (raiz / "raw" / "bibliografia" / "escaneado.pdf").write_bytes(b"%PDF-1.4 no es texto")
            (raiz / "raw" / "manuales" / "banco").mkdir(parents=True)
            (raiz / "raw" / "manuales" / "banco" / "cap1.md").write_text("# Capitulo uno\n\n" + "Experimento de medicion de resistencias con puente de Wheatstone. " * 4, encoding="utf-8")
            (raiz / "raw" / "manuales" / "banco" / "cap2.txt").write_text("# Capitulo dos\n\n" + "Experimento de medicion de capacitancia con puente de Schering. " * 4, encoding="utf-8")
            (raiz / "raw" / "manuales" / "banco" / "figura.png").write_bytes(PNG)
            (raiz / "wiki" / "fuentes").mkdir(parents=True)
            vault.escribir_pagina(Path("wiki/fuentes/libro.md"), {"tipo": "fuente", "etiquetas": ["libro"], "origen": "archivo"},
                                  "\n\n# Libro de control\n\n**Origen:** `raw/bibliografia/libro.md`\n\n## Resumen\nLibro sobre control secuencial con máquinas de estado, temporización industrial y motores trifásicos para automatización.\n\n"
                                  "## Puntos clave\n- FSM y millis\n")
            vault.escribir_pagina(Path("wiki/fuentes/escaneado.md"), {"tipo": "fuente", "origen": "archivo"},
                                  "\n\n# Escaneado\n\n**Origen:** raw/bibliografia/escaneado.pdf\n\n## Resumen\nUn libro escaneado del que solo hay resumen, con algo de texto de relleno suficiente para contar como pasaje del wiki.\n")
            vault.escribir_pagina(Path("wiki/fuentes/banco.md"), {"tipo": "fuente", "etiquetas": ["equipo-laboratorio"], "origen": "manual"},
                                  "\n\n# Banco\n\n**Origen:** `raw/manuales/banco` y `raw/manuales/falta.md`\n\n## Resumen\nManual de un banco de laboratorio de medidas electricas con varios experimentos, sus equipos y sus procedimientos.\n")
            vault.escribir_pagina(Path("wiki/fuentes/web.md"), {"tipo": "fuente", "origen": "url"},
                                  "\n\n# Web\n\n**Origen:** https://ejemplo.org/recurso\n\n## Resumen\nUna pagina web con un resumen lo bastante largo para contar como pasaje del wiki, aunque su origen sea una URL.\n")

            libro = pasajes.cargar_fuente("libro")
            assert pasajes.cargar_fuente("libro") is libro                                                                   # en memoria mientras nada cambie
            assert libro.archivos == ["raw/bibliografia/libro.md"] and libro.omitidos == [] and any(p.ubicacion.startswith("wiki") for p in libro.pasajes)
            assert any(p.ubicacion.startswith("raw: libro.md › Control secuencial › Capítulo 1") for p in libro.pasajes)
            escaneado = pasajes.cargar_fuente("escaneado")
            assert escaneado.archivos == [] and "no es un archivo de texto" in escaneado.omitidos[0] and escaneado.pasajes           # un PDF no se lee: queda su pagina del wiki
            banco = pasajes.cargar_fuente("banco")
            assert sorted(a.rsplit("/", 1)[-1] for a in banco.archivos) == ["cap1.md", "cap2.txt"] and any("no existe" in o for o in banco.omitidos)   # una carpeta aporta sus textos
            (raiz / "raw" / "bibliografia" / "libro.md").write_text(LIBRO + "\n## Capítulo 4\n\nUn capítulo nuevo sobre relés y contactores industriales, con bastante texto para que cuente como un pasaje de verdad.\n", encoding="utf-8")
            assert pasajes.cargar_fuente("libro") is not libro and any("contactores" in p.texto for p in pasajes.cargar_fuente("libro").pasajes)   # cambia el original: se relee
            (raiz / "raw" / "bibliografia" / "libro.md").write_text(LIBRO, encoding="utf-8")
            libro = pasajes.cargar_fuente("libro")
            web = pasajes.cargar_fuente("web")
            assert web.archivos == [] and web.omitidos == [] and web.pasajes                                                 # una URL no es una ruta: se ignora sin queja
            print("B2. pasajes: de cada fuente se lee su pagina del wiki y su original de raw/ (un .md o .txt, o una carpeta de ellos); un PDF, un archivo que falta o una URL no rompen nada -- OK")

            indice = pasajes.Indice([libro, escaneado, banco, web])
            encontrados = indice.buscar(["máquina de estados finitos", "finite state machine", "FSM"], k=3)
            assert encontrados and "finite state machine" in encontrados[0][1].texto.lower() and encontrados[0][1].fuente == "libro"     # el puente ES/EN
            assert indice.buscar(["MAQUINA DE ESTADOS"])[0][1].fuente == "libro"                                            # sin tildes ni mayusculas
            temporizacion = indice.buscar(["temporización no bloqueante", "millis", "delay"], k=2)
            assert any("millis" in p.texto for _, p in temporizacion)
            assert "Wheatstone" in indice.buscar(["puente de Wheatstone"])[0][1].texto and indice.buscar(["puente de Wheatstone"])[0][1].fuente == "banco"
            assert indice.buscar(["zzz inexistente qqq"]) == [] and indice.buscar([]) == [] and indice.buscar(["el", "de la"]) == []
            todos = indice.buscar(["motor", "control", "estado", "millis", "experimento", "resumen"], k=50, presupuesto=10 ** 6)
            assert len(todos) == len({i for i, _ in todos}) and all(len(p.texto) >= 1 for _, p in todos)                         # sin repetidos
            pocos = indice.buscar(["motor", "control", "estado", "millis", "experimento", "resumen"], k=50, presupuesto=1500)
            assert 1 <= len(pocos) < len(todos) and sum(len(p.texto) for _, p in pocos) <= 1500 + max(len(p.texto) for _, p in pocos)
            primero = encontrados[0][0]
            otros = indice.buscar(["máquina de estados finitos", "finite state machine", "FSM"], k=1, evitar={primero})
            assert otros and otros[0][0] != primero or len(indice.pasajes) == 1                                           # lo ya usado solo vuelve si no hay otra cosa
            solo = pasajes.Indice([web])
            volvio = solo.buscar(["pagina web resumen"], k=2, evitar={0})
            assert volvio and volvio[0][0] == 0                                                                            # ...y si no hay otra cosa, vuelve
            print("B3. pasajes: BM25 sin tildes ni mayusculas; encuentra en ingles lo pedido en espanol (los terminos de busqueda son el puente), respeta el presupuesto de caracteres y no repite pasajes -- OK")

            texto = pasajes.formatear(encontrados[:1], {"libro": 2})
            assert texto.startswith("[2] libro — raw: libro.md › Control secuencial › Capítulo 1") and "finite state machine" in texto
            assert "ninguno" in pasajes.formatear([], {})
            print("B4. pasajes: el LLM ve cada pasaje como `[n] fuente — ubicacion` con el numero con que debe citarla -- OK")
        finally:
            os.chdir(original)


def enlazar(enlace: Path, destino: Path) -> str | None:
    """Crea `enlace` apuntando a `destino`: un enlace simbolico o, en Windows sin ese privilegio, una union de directorios.
    Devuelve cual de los dos fue, o None si el sistema no deja crear ninguno."""
    try:
        os.symlink(destino, enlace, target_is_directory=destino.is_dir())
        return "simbólico"
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt" and destino.is_dir():
        hecho = subprocess.run(["cmd", "/c", "mklink", "/J", str(enlace), str(destino)], capture_output=True)
        if hecho.returncode == 0:
            return "unión"
    return None


def probar_originales_fuera_de_raw() -> None:
    """El original de una fuente viaja al proveedor de IA: solo puede leerse si esta DENTRO de raw/, sea cual sea la ruta que
    diga la pagina (con `..`, absoluta o por un enlace)."""
    secreto = "CONTRASENA-DEL-DECANO"
    relleno = " Texto de relleno lo bastante largo para que cuente como un pasaje de verdad y no se descarte por corto."
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        boveda = base / "vault"
        (base / "secreto.txt").write_text(f"{secreto}.{relleno}\n", encoding="utf-8")
        (base / "externa").mkdir()
        (base / "externa" / "otro.md").write_text(f"# Ajeno\n\n{secreto} en una carpeta ajena al vault.{relleno}\n", encoding="utf-8")
        (boveda / "raw" / "bibliografia").mkdir(parents=True)
        (boveda / "raw" / "carpeta").mkdir()
        (boveda / "wiki" / "fuentes").mkdir(parents=True)
        (boveda / "raw" / "bibliografia" / "libro.md").write_text(LIBRO, encoding="utf-8")
        (boveda / "raw" / "carpeta" / "ok.md").write_text(f"# Propio\n\nContenido propio del vault, con su lugar en raw/.{relleno}\n", encoding="utf-8")
        (boveda / "notas-privadas.md").write_text(f"# Privado\n\n{secreto} en la raiz del vault, fuera de raw/.{relleno}\n", encoding="utf-8")
        os.chdir(boveda)
        try:
            def fuente(nombre: str, origen: str):
                vault.escribir_pagina(Path(f"wiki/fuentes/{nombre}.md"), {"tipo": "fuente", "origen": "archivo"},
                                      f"\n\n# {nombre}\n\n**Origen:** {origen}\n\n## Resumen\nResumen de la fuente {nombre}, lo bastante largo para contar como pasaje del wiki y nada más.\n")
                return pasajes.cargar_fuente(nombre)

            fugas = {
                "relativa": "`../secreto.txt`",
                "sin-comillas": "../secreto.txt",
                "con-raw-y-subida": "`raw/../../secreto.txt`",
                "absoluta": f"`{base / 'secreto.txt'}`",                                                   # con las barras de la plataforma
                "absoluta-posix": f"`{(base / 'secreto.txt').as_posix()}`",
                "en-el-vault-fuera-de-raw": "`raw/../notas-privadas.md`",
                "carpeta-ajena": "`raw/../../externa`",
                "carpeta-ajena-absoluta": f"`{base / 'externa'}`",
            }
            for nombre, origen in fugas.items():
                f = fuente(nombre, origen)
                assert f.archivos == [], (nombre, f.archivos)
                assert all(secreto not in p.texto for p in f.pasajes), nombre
                assert len(f.omitidos) == 1 and pasajes.FUERA_DE_RAW in f.omitidos[0] and "fuera de raw/: no se lee" in f.omitidos[0], (nombre, f.omitidos)
                assert f.pasajes and all(p.ubicacion.startswith("wiki") for p in f.pasajes), nombre     # de la fuente solo queda su pagina del wiki
            mezcla = fuente("mezcla", "`raw/bibliografia/libro.md` y `../secreto.txt`")
            assert mezcla.archivos == ["raw/bibliografia/libro.md"] and len(mezcla.omitidos) == 1 and "fuera de raw/" in mezcla.omitidos[0]        # lo de dentro se lee; lo de fuera, no
            assert any("finite state machine" in p.texto for p in mezcla.pasajes) and all(secreto not in p.texto for p in mezcla.pasajes)

            dentro = {
                "simple": "`raw/bibliografia/libro.md`",
                "con-puntos": "`raw/bibliografia/../bibliografia/libro.md`",                             # un `..` que se queda en raw/ vale
                "carpeta": "`raw/bibliografia`",
                "absoluta": f"`{boveda / 'raw' / 'bibliografia' / 'libro.md'}`",                         # una ruta absoluta que cae en raw/ tambien
            }
            for nombre, origen in dentro.items():
                f = fuente(f"dentro-{nombre}", origen)
                assert len(f.archivos) == 1 and f.omitidos == [], (nombre, f.archivos, f.omitidos)
                assert any("finite state machine" in p.texto for p in f.pasajes), nombre
            assert fuente("url", "https://ejemplo.org/recurso").omitidos == []                          # ni una URL ni texto que no es una ruta: sin queja
            assert fuente("texto", "un libro impreso, capítulo 3").omitidos == []
            assert fuente("no-existe", "`raw/falta.md`").omitidos == ["raw/falta.md (no existe)"]      # lo que falta dentro de raw/ sigue diciendo "no existe"

            for ruta, esperado in (("raw", True), ("raw/x.md", True), ("raw/a/../b.md", True), ("raw/../x.md", False), ("raw2/x.md", False), ("x.md", False), (str(base / "secreto.txt"), False)):
                assert pasajes._dentro_de_raw(Path(ruta)) is esperado, ruta                            # `raw2` no es raw/: el prefijo del nombre no basta
            indice = pasajes.Indice([pasajes.cargar_fuente(n) for n in [*fugas, "mezcla"]])
            assert indice.buscar([secreto, "contrasena decano"], k=10) == []                              # ni una busqueda lo encuentra
            print(f"B5. pasajes: {len(fugas)} rutas que salen de raw/ (`..`, absolutas, carpetas, la raiz del vault) no se leen y quedan en `omitidos` («fuera de raw/: no se lee»); lo que esta dentro se lee, con o sin `..` -- OK")

            # enlaces: uno dentro de raw/ que apunta fuera no debe servir de puerta
            tipo_enlace = enlazar(boveda / "raw" / "salida", base / "externa")
            if tipo_enlace is None:
                print("B6. pasajes: enlaces que salen de raw/ -- OMITIDA (este sistema no deja crear enlaces simbólicos ni uniones de directorios)")
            else:
                f = fuente("enlace-a-carpeta", "`raw/salida`")                                          # la carpeta citada es, ella misma, un enlace hacia fuera
                assert f.archivos == [] and len(f.omitidos) == 1 and "fuera de raw/: no se lee" in f.omitidos[0], f.omitidos
                enlazar(boveda / "raw" / "carpeta" / "salida", base / "externa")                        # y un enlace hacia fuera dentro de una carpeta legitima
                archivo_enlazado = enlazar(boveda / "raw" / "carpeta" / "enlace.md", base / "secreto.txt") is not None      # (un archivo enlazado: solo con enlace simbolico)
                f = fuente("carpeta-con-enlaces", "`raw/carpeta`")
                assert [Path(a).name for a in f.archivos] == ["ok.md"], f.archivos                      # ok.md se lee; lo que enlaza hacia fuera, no
                assert all(secreto not in p.texto for p in f.pasajes)
                alcanzado = archivo_enlazado or any(p.name == "otro.md" for p in (boveda / "raw" / "carpeta").rglob("*"))    # rglob de esta version de Python llega por el enlace
                assert not alcanzado or any("fuera de raw/: no se lee" in o for o in f.omitidos), f.omitidos                # si llego, el guardia lo filtro y lo dijo
                print(f"B6. pasajes: un enlace ({tipo_enlace}) dentro de raw/ que apunta fuera no sirve de puerta: ni como original ni dentro de una carpeta -- OK")
        finally:
            os.chdir(original)


# ---------------------------------------------------------------------------
# C. esquemas y reparto de minutos
# ---------------------------------------------------------------------------


def probar_esquemas() -> None:
    assert celdas_de_tabla("| a | b |\n|---|---|\n| 1 | 2 |\n| 3 \\| 4 | 5 |") == (["a", "b"], [["1", "2"], ["3 | 4", "5"]])
    assert celdas_de_tabla("| a | b |\n| 1 | 2 |")[1] == [["1", "2"]]                                                           # la linea separadora es opcional
    for mala in ("a | b\n1 | 2", "| solo |\n|---|\n| x |", "| a | b |\n|---|---|", "| a | b |\n|---|---|\n| 1 | 2 | 3 |"):
        esperar(ValueError, celdas_de_tabla, mala)
    print("C1. schema: una tabla Markdown se lee con o sin separador y con `\\|` dentro de una celda; una descuadrada, de una columna o sin datos se rechaza -- OK")

    ok = Bloque(tipo="ecuacion", contenido="$$ x^2 $$")
    assert ok.contenido == "x^2"                                                                                             # el LaTeX se guarda sin $$
    Bloque(tipo="ecuacion", contenido=r"f(x) = \left\{ \begin{aligned} 1 & x > 0 \\ 0 & x \leq 0 \end{aligned} \right.")      # `\{` sin su `\}` no es un grupo sin cerrar
    import json
    for modelo in (PlanSesion, SeccionRedactada, CierreSesion):
        json.dumps(modelo.model_json_schema())                                                                               # lo que el modo json/texto le pone al modelo en el prompt
    assert Bloque(tipo="parrafo", contenido="Vale \\$5 y $x$.").tipo == "parrafo"                                             # un \\$ es dinero, no una formula
    malos = [
        dict(tipo="parrafo", contenido=""), dict(tipo="parrafo", contenido="cuesta $5 en total"), dict(tipo="parrafo", contenido="una $$formula$$ en bloque"),
        dict(tipo="parrafo", contenido="# un titulo"), dict(tipo="parrafo", contenido="| a | b |"), dict(tipo="parrafo", contenido="```\ncodigo\n```"),
        dict(tipo="lista", contenido="uno solo"), dict(tipo="ecuacion", contenido="a $b$ c"), dict(tipo="ecuacion", contenido="\\frac{a}{b"),
        dict(tipo="tabla", contenido="| a | b |\n|---|---|\n| 1 | 2 |"), dict(tipo="tabla", contenido="| a | b |\n|---|---|\n| 1 |", leyenda="x"),
        dict(tipo="codigo", contenido="\n".join(["x"] * 121)), dict(tipo="subtitulo", contenido="s" * 101), dict(tipo="grafica", leyenda="x"), dict(tipo="grafica", grafica=grafica()),
        dict(tipo="diagrama", leyenda="x"), dict(tipo="nota", contenido=""),
    ]
    for datos in malos:
        esperar(ValidationError, Bloque, **datos)
    assert Bloque(tipo="grafica", grafica=grafica(), leyenda="Pie").grafica.variable == "t" and Bloque(tipo="diagrama", diagrama=diagrama(), leyenda="Pie")
    print(f"C2. schema: un bloque valida por tipo ({len(malos)} defectos: `$` sin cerrar, `$$` en un parrafo, tablas descuadradas, graficas sin especificacion o sin pie...); el LaTeX se guarda sin `$$` -- OK")

    def unidad(clase: str, elementos: list[str], titulo: str = "U") -> UnidadPlan:
        return UnidadPlan(clase=clase, titulo=titulo, descripcion="Una descripción suficiente.", peso=10, terminos_busqueda=["a", "b", "c", "d"], elementos=elementos)

    def plan(unidades: list[UnidadPlan], **cambios) -> PlanSesion:
        base = dict(titulo="Un título descriptivo de la sesión de prueba", continuidad="Continuidad.", prerrequisitos=["a", "b", "c"], usa_ecuaciones=True, usa_graficas=True,
                    resultados_sesion=[ResultadoSesion(enunciado="Aplicar x", nivel="Aplicar")] * 3, unidades=unidades)
        return PlanSesion(**{**base, **cambios})

    buenas = [unidad("introduccion", ["diagrama"]), unidad("concepto", ["ecuacion", "grafica"]), unidad("concepto", ["ecuacion"]), unidad("concepto", ["tabla"]),
              unidad("caso", ["tabla", "ecuacion"]), unidad("sintesis", [])]
    plan(buenas)
    variantes = {
        "faltan conceptos": buenas[:2] + buenas[4:], "dos introducciones": [buenas[0], *buenas],
        "sin caso": [u for u in buenas if u.clase != ClaseUnidad.caso], "caso sin tabla": [*buenas[:4], unidad("caso", ["ecuacion"]), buenas[5]],
        "caso sin ecuacion": [*buenas[:4], unidad("caso", ["tabla"]), buenas[5]], "implementacion sin codigo": [*buenas[:5], unidad("implementacion", ["tabla"]), buenas[5]],
        "analisis sin tabla": [*buenas[:5], unidad("analisis", ["ecuacion"]), buenas[5]], "una sola figura": [unidad("introduccion", []), *buenas[1:2], buenas[2], buenas[3], *buenas[4:]],
        "pocas ecuaciones": [buenas[0], unidad("concepto", ["grafica"]), unidad("concepto", []), unidad("concepto", ["tabla"]), unidad("caso", ["tabla", "ecuacion"]), buenas[5]],
        "peso cero": [buenas[0], UnidadPlan(clase="concepto", titulo="P", descripcion="Una descripción suficiente.", peso=0, terminos_busqueda=["a", "b", "c", "d"]), *buenas[2:]],
        "pocos terminos": [buenas[0], UnidadPlan(clase="concepto", titulo="P", descripcion="Una descripción suficiente.", peso=5, terminos_busqueda=["a"]), *buenas[2:]],
    }
    for nombre, unidades in variantes.items():
        esperar(ValidationError, plan, unidades)
    esperar(ValidationError, plan, buenas, titulo="corto")
    esperar(ValidationError, plan, buenas, prerrequisitos=["a"])
    esperar(ValidationError, plan, buenas, resultados_sesion=[])
    esperar(ValidationError, plan, [unidad("introduccion", ["diagrama"]), unidad("concepto", ["grafica"]), *buenas[2:]], usa_graficas=False)      # una `grafica` con usa_graficas falso
    plan([unidad("introduccion", ["diagrama"]), unidad("concepto", ["diagrama"]), unidad("concepto", []), unidad("concepto", ["tabla"]), unidad("caso", ["tabla"]), buenas[5]],
         usa_ecuaciones=False, usa_graficas=False)                                                                              # un tema conceptual: sin ecuaciones ni graficas
    print(f"C3. schema: el plan exige 1 introduccion, 3-6 conceptos, 1 caso, 1 sintesis, tablas y figuras minimas y, si el tema usa ecuaciones, 3 unidades con ecuacion ({len(variantes)} variantes rechazadas) -- OK")

    assert minutos_por_bloque([10, 10, 20], 2) == [30, 30, 60] and minutos_por_bloque([1, 1, 1], 2) == [40, 40, 40]
    for pesos in ([8, 15, 15, 15, 22, 12, 10, 5], [1] * 24, [100, 1, 1], [3, 7, 11, 13]):
        for horas in (2, 4):
            minutos = minutos_por_bloque(pesos, horas)
            assert sum(minutos) == horas * 60 and all(m % 5 == 0 and m >= 5 for m in minutos), (pesos, minutos)
    esperar(ValueError, minutos_por_bloque, [1] * 25, 2)
    esperar(ValueError, minutos_por_bloque, [1, 0], 2)
    print("C4. minutos por bloque: multiplos de 5, al menos 5 cada uno, suman exactamente la sesion (2 h o 4 h) y son proporcionales al peso -- OK")

    assert temario.palabras_minimas(ClaseUnidad.concepto, 2) == 320 and temario.palabras_minimas(ClaseUnidad.concepto, 4) == 448
    bloques = [Bloque(tipo="parrafo", contenido="uno dos tres $x^2$ cuatro"), Bloque(tipo="lista", contenido="a b\nc d e"), Bloque(tipo="ecuacion", contenido="a b c"),
               Bloque(tipo="codigo", contenido="int x = 1;", leyenda="dos palabras"), Bloque(tipo="tabla", contenido="| a | b |\n| c d | e |", leyenda="tres palabras aqui")]
    assert palabras_de(bloques) == 4 + 5 + 2 + 3 and elementos_de(bloques)[ElementoPlan.ecuacion] == 1 and elementos_de(bloques)[ElementoPlan.tabla] == 1
    print("C5. schema: una sesion de 4 h pide 1,4 veces mas palabras por unidad; las palabras cuentan prosa, listas, notas y pies (no el codigo, las ecuaciones ni las celdas) -- OK")


# ---------------------------------------------------------------------------
# D. el flujo de temario.py con validacion y reintentos
# ---------------------------------------------------------------------------

LLAMADAS: list[tuple[str, str]] = []
REGLAS: list[dict] = []


def llm(sistema, usuario, formato):
    LLAMADAS.append((formato.__name__, usuario))
    for regla in REGLAS:
        if regla["formato"] == formato.__name__ and regla["veces"] > 0 and regla["cuando"](usuario):
            regla["veces"] -= 1
            return regla["accion"](usuario)
    if formato.__name__ == "TemasSemana":
        raise AssertionError("no se usa")
    return _fixtures.responder_temario(usuario, formato)


def llamadas(formato: str) -> list[str]:
    return [u for f, u in LLAMADAS if f == formato]


def regla(formato: str, cuando, accion, veces: int = 1) -> None:
    REGLAS.append({"formato": formato, "cuando": cuando, "accion": accion, "veces": veces})


def reiniciar() -> None:
    LLAMADAS.clear()
    REGLAS.clear()
    _fixtures.CONFIG_TEMARIO.update({"conceptos": 3, "analisis": True, "implementacion": True, "usa_graficas": True, "usa_ecuaciones": True, "externas": False})
    for f in Path("generacion/temarios").glob("*.md"):
        f.unlink()
    for f in Path("generacion/temarios/figuras").glob("*.png"):
        f.unlink()


def probar_flujo() -> None:
    vault.pedir_estructurado = llm
    figuras.dibujar_grafica, figuras.dibujar_diagrama = DIBUJAR_REAL
    planeador.generar_planeador("TPR01", sin_llm=True)
    fm_ra, cuerpo_ra = vault.leer_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA1.md"))
    fm_ra.update({"requiere_practica": "[[banco-uno]]", "practica_experimentos": ["Exp1"]})
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA1.md"), fm_ra, cuerpo_ra)

    # --- D1: el tema sale del RA, las figuras se dibujan de verdad, el cuerpo es Markdown coherente ---
    reiniciar()
    destino = temario.generar_temario("TPR01", 1)
    fm, cuerpo = vault.leer_pagina(destino)
    assert "Tema de la semana: Enunciado de ejemplo de TPR01-RA1." in llamadas("PlanSesion")[0]                               # sin tema redactado, el del planeador es el enunciado del RA
    figuras_png = sorted(Path("generacion/temarios/figuras").glob("TPR01-semana01-fig*.png"))
    assert [f.name for f in figuras_png] == [f"TPR01-semana01-fig{i}.png" for i in (1, 2, 3)] and all(f.read_bytes()[:8] == PNG for f in figuras_png)
    assert ls.dimensiones_png(figuras_png[1]) == (1280, 550)                                                                # la de la grafica, con la paleta y el tamano de figuras.py
    assert re.findall(r"!\[Figura (\d)\.", cuerpo) == ["1", "2", "3"] and cuerpo.count("**Tabla ") == 3 and cuerpo.count("```cpp") == 1
    print("D1. temario: los tres pasos, las figuras dibujadas con matplotlib de verdad (PNG de 1280 x 550 para las graficas) y el Markdown numerado en orden -- OK")

    # --- D2: una unidad corta se devuelve al modelo con el motivo, y la version buena es la que queda ---
    def corta(usuario):
        s = _fixtures.unidad_falsa(usuario)
        s.bloques[-1] = Bloque(tipo="parrafo", contenido="Muy corto.")
        return s

    reiniciar()
    regla("SeccionRedactada", lambda u: "Clase: introduccion" in u, corta)
    temario.generar_temario("TPR01", 1)
    intro = [u for u in llamadas("SeccionRedactada") if "Clase: introduccion" in u]
    assert len(intro) == 2 and "NO cumplió" in intro[1] and "la prosa tiene" in intro[1] and "mínimo" in intro[1] and "NO cumplió" not in intro[0]
    assert "Muy corto." not in vault.leer_pagina(Path("generacion/temarios/TPR01-semana01.md"))[1]
    reiniciar()
    regla("SeccionRedactada", lambda u: "Clase: introduccion" in u, corta, veces=9)
    mensaje = esperar(ValueError, temario.generar_temario, "TPR01", 1)
    assert "tras 3 intentos" in mensaje and "Introducción de la sesión" in mensaje and len([u for u in llamadas("SeccionRedactada")]) == 3
    assert not Path("generacion/temarios/TPR01-semana01.md").exists() and not list(Path("generacion/temarios/figuras").glob("*")), "no se deja nada a medias"
    print("D2. temario: una unidad con menos palabras que el minimo se devuelve al modelo con el motivo (y la buena es la que queda); tras 3 intentos falla con un mensaje claro y sin dejar archivos -- OK")

    # --- D3: citas inventadas, la practica ignorada, criterios sin cubrir ---
    def cita_falsa(usuario):
        s = _fixtures.unidad_falsa(usuario)
        s.bloques[0].contenido += " Ver [9]."
        return s

    def sin_practica(usuario):
        s = _fixtures.unidad_falsa(usuario)
        for b in s.bloques:
            b.contenido = b.contenido.replace("Exp1", "otra practica")
        return s

    def sin_ce2(usuario):
        p = _fixtures.plan_falso(usuario)
        p.resultados_sesion[0].criterios = ["CE1"]
        return p

    def ce_ajeno(usuario):
        p = _fixtures.plan_falso(usuario)
        p.resultados_sesion[1].criterios = ["CE7"]
        return p

    reiniciar()
    regla("SeccionRedactada", lambda u: "Título: Concepto 2 del tema" in u, cita_falsa)
    regla("SeccionRedactada", lambda u: "Clase: caso" in u, sin_practica)
    regla("PlanSesion", lambda u: True, sin_ce2)
    temario.generar_temario("TPR01", 1)
    plan_llamadas = llamadas("PlanSesion")
    assert len(plan_llamadas) == 2 and "CE2" in plan_llamadas[1] and "cubren los criterios" in plan_llamadas[1]
    concepto2 = [u for u in llamadas("SeccionRedactada") if "Título: Concepto 2 del tema" in u]
    assert len(concepto2) == 2 and "[9]" in concepto2[1] and "hay 2 fuente(s) cargada(s)" in concepto2[1]                       # RA1: libro-a y el manual de la practica
    caso = [u for u in llamadas("SeccionRedactada") if "Clase: caso" in u]
    assert len(caso) == 2 and "código Exp1" in caso[1]
    reiniciar()
    regla("PlanSesion", lambda u: True, ce_ajeno, veces=9)
    assert "CE7" in esperar(ValueError, temario.generar_temario, "TPR01", 1)
    print("D3. temario: una cita [9] a una fuente que no existe, un caso que ignora la practica de referencia y un plan que no cubre todos los criterios (o cita uno ajeno) se devuelven al modelo -- OK")

    # --- D4: lo blando (comandos LaTeX que la presentacion no admite) se reintenta, pero no detiene la sesion ---
    def mathscr(usuario):
        s = _fixtures.unidad_falsa(usuario)
        s.bloques.insert(1, Bloque(tipo="ecuacion", contenido=r"\mathscr{L} = 1"))
        return s

    reiniciar()
    regla("SeccionRedactada", lambda u: "Título: Concepto 1 del tema" in u, mathscr, veces=9)
    destino = temario.generar_temario("TPR01", 1)
    concepto1 = [u for u in llamadas("SeccionRedactada") if "Título: Concepto 1 del tema" in u]
    assert len(concepto1) == 3 and "mathscr" in concepto1[1] and "no admite" in concepto1[1]                                   # se le pidio corregir...
    assert "\\mathscr{L} = 1" in vault.leer_pagina(destino)[1]                                                                  # ...y en el ultimo intento se acepta (la presentacion lo marcara `revisar`)
    print("D4. temario: un comando LaTeX que la presentacion no admite se devuelve al modelo dos veces; si insiste, se acepta (afecta solo a la presentacion) -- OK")

    # --- D5: fuentes no cargadas: marcador en linea y en la bibliografia, y CORRELATE-BIBLIOGRAFIA lo detecta sin LLM ---
    reiniciar()
    _fixtures.CONFIG_TEMARIO["externas"] = True
    destino = temario.generar_temario("TPR01", 1)
    cuerpo = vault.leer_pagina(destino)[1]
    assert cuerpo.count("La norma X 123 [FUENTE NO CARGADA EN raw/] fija el límite.") == 3
    assert "[3] Comité X, Norma X 123, 2019. [FUENTE NO CARGADA EN raw/]" in cuerpo and cuerpo.count("Norma X 123, 2019.") == 1          # la externa, una sola vez, tras las 2 cargadas
    assert correlate_bibliografia.auditar_temario(destino) == ("vacio_detectado", "marcador")
    faltantes = vault.leer_pagina(destino)[0]["bibliografia_faltantes"]
    assert len(faltantes) == 4 and all("[FUENTE NO CARGADA EN raw/]" in f for f in faltantes)
    print("D5. temario: una fuente no cargada lleva el marcador en su linea y en la bibliografia (numerada tras las cargadas, sin repetirse) y CORRELATE-BIBLIOGRAFIA la detecta sin LLM -- OK")

    # --- D6: con texto en raw/, el prompt de cada unidad lleva los pasajes relevantes y la sesion cuenta cuantos uso ---
    reiniciar()
    Path("raw/bibliografia").mkdir(parents=True)
    Path("raw/bibliografia/libro-a.md").write_text(
        "# Libro A\n\n## Capítulo uno\n\n" + "El sistema de ejemplo con alfa, beta, gamma y delta se comporta de forma estable bajo carga nominal. " * 6
        + "\n\n## Capítulo dos\n\n" + "Otro sistema de ejemplo relaciona alfa con delta mediante un factor constante de proporcionalidad. " * 6 + "\n", encoding="utf-8")
    fm_a, cuerpo_a = vault.leer_pagina(Path("wiki/fuentes/libro-a.md"))
    vault.escribir_pagina(Path("wiki/fuentes/libro-a.md"), fm_a, cuerpo_a.replace("# Libro A\n", "# Libro A\n\n**Origen:** `raw/bibliografia/libro-a.md`\n", 1))
    destino = temario.generar_temario("TPR01", 1)
    unidad = llamadas("SeccionRedactada")[1]
    assert "Pasajes de las fuentes relevantes para esta unidad:\n[1] libro-a — raw: libro-a.md › Libro A › Capítulo" in unidad and "alfa, beta, gamma y delta" in unidad
    assert "texto completo disponible" in llamadas("PlanSesion")[0] and "solo la página del wiki" in llamadas("PlanSesion")[0]              # libro-a con texto; el manual, solo su pagina
    estadisticas = vault.leer_pagina(destino)[0]["estadisticas"]
    assert estadisticas["pasajes"] >= 2 and set(estadisticas) == {"palabras", "ecuaciones", "tablas", "figuras", "pasajes"}
    for u in llamadas("SeccionRedactada"):
        assert len(u.split("Pasajes de las fuentes relevantes para esta unidad:\n", 1)[1]) < 8500                               # el contexto no crece sin limite
    print("D6. temario: cada unidad recibe los pasajes de raw/ mas relevantes para ella (con su fuente y su numero para citarla) y el frontmatter cuenta cuantos se usaron -- OK")

    # --- D7: sin matplotlib no se gasta ni una llamada; una figura que falla no deja nada a medias ---
    reiniciar()
    disponible = figuras.disponible
    figuras.disponible = lambda: False
    try:
        assert "matplotlib" in esperar(RuntimeError, temario.generar_temario, "TPR01", 1) and LLAMADAS == []
    finally:
        figuras.disponible = disponible
    dibujadas = []

    def falla_la_segunda(spec, destino):
        dibujadas.append(destino)
        if len(dibujadas) == 2:
            raise RuntimeError("fallo simulado al dibujar")
        DIBUJAR_REAL[0](spec, destino) if isinstance(spec, figuras.GraficaSpec) else DIBUJAR_REAL[1](spec, destino)

    figuras.dibujar_grafica = figuras.dibujar_diagrama = falla_la_segunda
    assert "fallo simulado" in esperar(RuntimeError, temario.generar_temario, "TPR01", 1)
    assert not list(Path("generacion/temarios/figuras").glob("*")) and not Path("generacion/temarios/TPR01-semana01.md").exists()
    figuras.dibujar_grafica, figuras.dibujar_diagrama = DIBUJAR_REAL
    print("D7. temario: sin matplotlib falla antes de llamar al LLM (con la instruccion de instalarlo); si una figura falla, no queda ninguna a medias ni un temario sin figuras -- OK")

    # --- D8: cabecera con los modulos homologos y el nivel del programa; una sesion conceptual sin ecuaciones ni graficas ---
    reiniciar()
    homologa = _fixtures._asignatura("TPR02", "Homóloga de prueba", 42, 26, "teórico-práctica", ["TPR01-RA1"], hti=54)
    homologa["modulo_homologo"] = "[[" + _fixtures.TPR01 + "]]"
    vault.escribir_pagina(Path("wiki/asignaturas/TPR02 - Homóloga de prueba.md"), homologa, "\n\n# x\n")
    fm_p, cuerpo_p = vault.leer_pagina(Path(f"wiki/programas/{_fixtures.PROGRAMA}.md"))
    fm_p["nivel"] = "Pregrado avanzado"
    vault.escribir_pagina(Path(f"wiki/programas/{_fixtures.PROGRAMA}.md"), fm_p, cuerpo_p)
    _fixtures.CONFIG_TEMARIO.update({"usa_ecuaciones": False, "usa_graficas": False, "analisis": False, "implementacion": False, "conceptos": 4})
    cuerpo = vault.leer_pagina(temario.generar_temario("TPR01", 1))[1]
    assert "> **Módulos:** TPR01 — Asignatura teórico-práctica de prueba · TPR02 — Homóloga de prueba\n" in cuerpo and "> **Nivel:** Pregrado avanzado\n" in cuerpo
    assert "$$" not in cuerpo and "**Tabla 1.**" in cuerpo and cuerpo.count("![Figura ") == 3 and "## 6. Síntesis (Bloque 7)" in cuerpo and "## 6. Selección" not in cuerpo   # 4 conceptos, sin analisis ni implementacion
    assert re.findall(r"\| (\d+) min \|", cuerpo) and sum(int(m) for m in re.findall(r"\| (\d+) min \|", cuerpo)) == 240
    print("D8. temario: la cabecera lista los modulos homologos y el nivel del programa (sin inventarlo si falta); una sesion conceptual (sin ecuaciones ni graficas, 4 conceptos, sin analisis ni implementacion) se numera bien -- OK")

    r = subprocess.run([sys.executable, "-B", str(SRC / "temario.py"), "--help"], capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    assert r.returncode == 0 and "--semana" in r.stdout and "--todas" in r.stdout
    print("D9. temario.py --help funciona (matplotlib se importa solo al dibujar) -- OK")


DIBUJAR_REAL = (figuras.dibujar_grafica, figuras.dibujar_diagrama)


def main() -> None:
    probar_figuras()
    probar_diagramas()
    probar_pasajes()
    probar_originales_fuera_de_raw()
    probar_esquemas()
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar_flujo()
        finally:
            os.chdir(original)
    print("TODO OK -- el temario se redacta en tres pasos con las fuentes cargadas, figuras dibujadas por codigo y cada respuesta del modelo validada y reintentada.")


if __name__ == "__main__":
    main()
