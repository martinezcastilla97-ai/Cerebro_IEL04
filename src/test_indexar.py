"""Prueba de indexar_practicas() y recall_practicas_candidatas() con LanceDB REAL y un
cliente de embeddings SIMULADO (vectores por hashing de palabras): no llama a OpenAI.
Se omite si `lancedb` no esta instalado (pip install -r requirements.txt).

Uso (desde src/):  python test_indexar.py
"""

import hashlib
import io
import math
import os
import sys
import tempfile
import types
from contextlib import redirect_stdout
from pathlib import Path

try:
    import lancedb
except ImportError:
    print("SKIP -- lancedb no esta instalado (pip install -r requirements.txt)")
    sys.exit(0)

import _fixtures
import correlate
import vault
from schema_extraccion import ContenidoAprendizaje, ResultadoAprendizajeModulo, TipoAbordaje

DIM = 64


def embeber(texto: str) -> list[float]:
    v = [0.0] * DIM
    for palabra in texto.lower().replace(",", " ").replace(".", " ").split():
        v[int(hashlib.md5(palabra.encode()).hexdigest(), 16) % DIM] += 1.0
    norma = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norma for x in v]


class EmbeddingsFalsos:
    def create(self, model, input):
        assert model == correlate.modelo_embeddings(), model
        textos = input if isinstance(input, list) else [input]
        return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=embeber(t)) for t in textos])


class ClienteFalso:
    embeddings = EmbeddingsFalsos()


def esperar(excepcion, funcion, *args):
    try:
        funcion(*args)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


def probar() -> None:
    vault.get_client = lambda para="llm": ClienteFalso()
    ra = ResultadoAprendizajeModulo(codigo="X-RA1", enunciado="alfa", horas=10, tipo_abordaje=TipoAbordaje.teorico_practica,
                                    criterios_evaluacion=[], contenido=ContenidoAprendizaje(conceptual=["alfa a"]))

    assert "--indexar" in esperar(FileNotFoundError, correlate.recall_practicas_candidatas, ra)
    print("1. sin indice, el recall da un error que dice que hay que correr --indexar -- OK")

    # Segundo manual con el MISMO codigo Exp1 (identidad = (fuente, codigo)) y un banco sin practicas.
    vault.escribir_pagina(Path("wiki/fuentes/banco-dos.md"), {"tipo": "fuente", "etiquetas": ["equipo-laboratorio"],
                          "practicas": [_fixtures.practica("Exp1", "Otra practica", "delta")]}, "\n\n# Banco dos\n")
    vault.escribir_pagina(Path("wiki/fuentes/banco-vacio.md"), {"tipo": "fuente", "etiquetas": ["equipo-laboratorio"]}, "\n\n# Vacio\n")

    salida = io.StringIO()
    with redirect_stdout(salida):
        n = correlate.indexar_practicas()
    assert n == 4 and "banco-vacio" in salida.getvalue() and "AVISO" in salida.getvalue(), (n, salida.getvalue())
    print("2. indexar_practicas: 4 filas (3 de banco-uno + 1 de banco-dos) y aviso por el banco sin practicas -- OK")

    tabla = lancedb.connect(str(correlate.DB_PATH)).open_table("practicas")
    filas = tabla.search(embeber("x")).limit(10).to_list()
    assert tabla.count_rows() == 4 and {(f["fuente"], f["codigo"]) for f in filas} == {
        ("banco-uno", "Exp1"), ("banco-uno", "Exp2"), ("banco-uno", "Exp3"), ("banco-dos", "Exp1")}
    print("3. el store real de LanceDB guarda fuente/codigo/vector, y Exp1 de dos manuales no se confunde -- OK")

    pares = correlate.recall_practicas_candidatas(ra, k=3)
    assert len(pares) == 3 and all(isinstance(p, tuple) and len(p) == 2 for p in pares) and pares[0] == ("banco-uno", "Exp1"), pares
    print(f"4. recall: el mas cercano a un RA sobre 'alfa' es {pares[0]} -- OK")

    assert correlate.indexar_practicas() == 4 and lancedb.connect(str(correlate.DB_PATH)).open_table("practicas").count_rows() == 4
    print("5. reindexar es idempotente (overwrite): sigue en 4 filas, no 8 -- OK")

    assert (correlate.DB_PATH.parent / correlate.ARCHIVO_MODELO).read_text(encoding="utf-8").strip() == correlate.MODELO_EMBEDDINGS
    os.environ["CEREBRO_MODELO_EMBEDDINGS"] = "otro-modelo"
    try:
        assert "--indexar" in esperar(RuntimeError, correlate.recall_practicas_candidatas, ra)       # vectores de otro modelo: error claro
        assert correlate.indexar_practicas() == 4 and len(correlate.recall_practicas_candidatas(ra, k=3)) == 3      # reindexar con el nuevo modelo lo arregla
    finally:
        del os.environ["CEREBRO_MODELO_EMBEDDINGS"]
    print("6. el indice recuerda con que modelo de embeddings se hizo: cambiar CEREBRO_MODELO_EMBEDDINGS sin reindexar da un error claro -- OK")


def main() -> None:
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar()
        finally:
            os.chdir(original)
    print("TODO OK -- indexar y recall funcionan contra LanceDB real.")


if __name__ == "__main__":
    main()
