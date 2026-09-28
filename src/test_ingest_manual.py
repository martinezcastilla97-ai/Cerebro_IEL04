"""Prueba de ingest_manual.py con un manual INVENTADO y el LLM sustituido por respuestas
fijas: la division en experimentos, la fusion en la pagina de wiki/fuentes/ (sin
duplicar ni pisar el resto de la pagina) y que lo escrito lo entiendan CORRELATE y LINT.

Uso (desde src/):  python test_ingest_manual.py
"""

import os
import tempfile
from pathlib import Path

import _fixtures
import correlate
import ingest_manual
import lint
import vault
from schema_extraccion import ExtraccionManual, Practica

MANUAL = """# Manual de ejemplo

## Chapter 1 Basic Experiments

### Experiment 1 Primera práctica
I The purpose of the experiment
- entender algo

### Experiment 2 Segunda práctica
Texto de la segunda.

## Chapter 2 Advanced Experiments

### Experiment 13 Tercera práctica
Texto de la tercera.

#### Sub-encabezado dentro de la tercera
Más texto de la tercera.

## Appendix
Esto no es un experimento.
"""

MANUAL_DUPLICADO = """# Manual con capitulos repetidos

## Chapter 1
### Experiment 1 Primera del capitulo 1
Texto A.

## Chapter 2
### Experiment 1 Primera del capitulo 2
Texto B.

### Experiment 3-1 Sub practica A
Texto C.

### Experiment 3-2 Sub practica B
Texto D.
"""

NOMBRE = {"1": "Primera", "2": "Segunda", "13": "Tercera"}
LLAMADAS: list[str] = []
VARIANTE = {"sufijo": ""}


def llm_falso(sistema, usuario, formato):
    assert formato is ExtraccionManual
    numero = usuario.split("### Experiment ", 1)[1].split()[0] if "### Experiment " in usuario else "?"
    LLAMADAS.append(numero)
    practica = Practica(
        codigo="LO-QUE-DIGA-EL-LLM", nombre_original=f"{NOMBRE.get(numero, 'Otra')} practica{VARIANTE['sufijo']}",
        proposito=["Proposito."], principio_resumen="Resumen.", terminos_clave=["uno", "dos", "tres", "cuatro"])
    return ExtraccionManual(banco_nombre="Banco de ejemplo", fabricante="Fabricante de ejemplo", idioma_original="en",
                            capitulo="", practicas=[practica])


def probar() -> None:
    vault.pedir_estructurado = llm_falso

    secciones = ingest_manual.dividir_experimentos(MANUAL)
    assert [s.numero for s in secciones] == ["1", "2", "13"]
    assert [s.capitulo for s in secciones] == ["Chapter 1 Basic Experiments", "Chapter 1 Basic Experiments", "Chapter 2 Advanced Experiments"]
    assert "Sub-encabezado dentro de la tercera" in secciones[2].texto and "Appendix" not in secciones[2].texto
    assert "Segunda" not in secciones[0].texto and "tercera" not in secciones[1].texto
    print("1. dividir_experimentos: 3 experimentos, capitulo = encabezado padre, subencabezados incluidos, el apendice no -- OK")

    otro = ingest_manual.dividir_experimentos("# M\n## Project 07\ntexto\n## Project 08\notro\n", r"^#+\s*Project\s+(\d+)")
    assert [s.numero for s in otro] == ["07", "08"]
    assert ingest_manual.dividir_experimentos("# Sin experimentos\ntexto\n") == []
    print("2. --patron para otros encabezados; un manual sin experimentos da lista vacia -- OK")

    Path("raw/manuales-laboratorio/BANCO").mkdir(parents=True)
    ruta_manual = Path("raw/manuales-laboratorio/BANCO/Manual de Ejemplo.md")
    ruta_manual.write_text(MANUAL, encoding="utf-8")

    destino, n = ingest_manual.ingest_manual(ruta_manual)
    fm, cuerpo = vault.leer_pagina(destino)
    assert destino.name == "manual-de-ejemplo.md" and n == 3 and LLAMADAS == ["1", "2", "13"]     # una llamada por experimento
    assert fm["tipo"] == "fuente" and "equipo-laboratorio" in fm["etiquetas"]
    assert [p["codigo"] for p in fm["practicas"]] == ["Exp1", "Exp2", "Exp13"]                    # el codigo sale del encabezado
    assert [p["capitulo"] for p in fm["practicas"]][2] == "Chapter 2 Advanced Experiments"
    assert "**Origen:** `raw/manuales-laboratorio/BANCO/Manual de Ejemplo.md`" in cuerpo and "Fabricante de ejemplo" in cuerpo
    print("3. ingest_manual: pagina wiki/fuentes/manual-de-ejemplo.md con Exp1, Exp2, Exp13 (codigo del encabezado, no del LLM) -- OK")

    nuevas = [(f, p.codigo) for f, p in correlate.listar_practicas() if f == "manual-de-ejemplo"]      # el vault de muestra ya trae `banco-uno`
    assert nuevas == [("manual-de-ejemplo", "Exp1"), ("manual-de-ejemplo", "Exp2"), ("manual-de-ejemplo", "Exp13")]
    assert [h for h in lint.revisar() if "manual-de-ejemplo" in h.ruta] == []
    print("4. lo escrito lo leen correlate.listar_practicas() y lint sin hallazgos -- OK")

    # Re-ingesta: reemplaza por codigo, no duplica, y no toca el resto de la pagina.
    fm["etiquetas"] = ["dolang-de-ejemplo"]
    vault.escribir_pagina(destino, fm, cuerpo + "\n## Notas del docente\nTexto que no debe cambiar.\n")
    VARIANTE["sufijo"] = " (revisada)"
    LLAMADAS.clear()
    ingest_manual.ingest_manual(ruta_manual, "manual-de-ejemplo", limite=2)
    fm2, cuerpo2 = vault.leer_pagina(destino)
    assert LLAMADAS == ["1", "2"] and len(fm2["practicas"]) == 3, (LLAMADAS, len(fm2["practicas"]))
    assert fm2["practicas"][0]["nombre_original"] == "Primera practica (revisada)" and fm2["practicas"][2]["nombre_original"] == "Tercera practica"
    assert fm2["etiquetas"] == ["dolang-de-ejemplo", "equipo-laboratorio"]                        # conserva las suyas y agrega la de banco
    assert "Texto que no debe cambiar." in cuerpo2
    print("5. re-ingesta con --limite 2: reemplaza Exp1/Exp2, conserva Exp13, no duplica, conserva etiquetas y cuerpo -- OK")

    ruta_vacia = Path("raw/manuales-laboratorio/BANCO/sin-experimentos.md")
    ruta_vacia.write_text("# Nada\ntexto\n", encoding="utf-8")
    assert "ningún experimento" in str(_esperar(ValueError, ingest_manual.ingest_manual, ruta_vacia))
    print("6. un manual sin experimentos detectables da un error claro (no una pagina vacia) -- OK")

    log = Path("wiki/log.md").read_text(encoding="utf-8")
    assert "/ingest manual-de-ejemplo" in log and "correlate.py --indexar" in log
    print("7. la ingesta queda en wiki/log.md con el recordatorio de reindexar -- OK")

    # 8. Numeros compuestos ("3-1", "3-2"): el patron los distingue, no colisionan en "3".
    secciones_dup = ingest_manual.dividir_experimentos(MANUAL_DUPLICADO)
    assert [s.numero for s in secciones_dup] == ["1", "1", "3-1", "3-2"], [s.numero for s in secciones_dup]
    print("8. dividir_experimentos acepta numeros compuestos ('3-1', '3-2') sin confundirlos con '3' -- OK")

    # 9. Codigos repetidos DENTRO DE LA MISMA CORRIDA ("Exp1" en dos capitulos): error
    # claro, sugiere --patron/--prefijo, y NUNCA llega a llamar al LLM.
    repetidos = ingest_manual.codigos_repetidos(secciones_dup, "Exp")
    assert list(repetidos) == ["Exp1"] and len(repetidos["Exp1"]) == 2, repetidos
    print("9. codigos_repetidos detecta 'Exp1' repetido (la misma logica que usa --solo-dividir para avisar) -- OK")

    Path("raw/manuales-laboratorio/BANCO2").mkdir(parents=True)
    ruta_dup = Path("raw/manuales-laboratorio/BANCO2/manual-duplicado.md")
    ruta_dup.write_text(MANUAL_DUPLICADO, encoding="utf-8")
    LLAMADAS.clear()
    error = _esperar(ValueError, ingest_manual.ingest_manual, ruta_dup)
    assert "Exp1" in str(error) and "--patron" in str(error) and "--prefijo" in str(error), error
    assert LLAMADAS == [], "con codigos repetidos en la corrida no se debe llamar al LLM"
    print("10. ingest_manual con codigos repetidos en la corrida: ValueError claro, sin llamar al LLM -- OK")

    # Fuera del choque de capitulos, "3-1" y "3-2" sí se distinguen y se ingieren normalmente.
    ruta_compuesto = Path("raw/manuales-laboratorio/BANCO2/manual-compuesto.md")
    ruta_compuesto.write_text("\n".join(MANUAL_DUPLICADO.splitlines()[10:]), encoding="utf-8")  # solo Experiment 3-1 / 3-2
    LLAMADAS.clear()
    destino_c, n_c = ingest_manual.ingest_manual(ruta_compuesto, "manual-compuesto")
    fm_c, _ = vault.leer_pagina(destino_c)
    assert n_c == 2 and [p["codigo"] for p in fm_c["practicas"]] == ["Exp3-1", "Exp3-2"], fm_c["practicas"]
    print("11. sin choque, los numeros compuestos se separan: Exp3-1 y Exp3-2 se ingieren cada uno por su lado -- OK")


def _esperar(excepcion, funcion, *args, **kwargs):
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return error
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


def main() -> None:
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar()
        finally:
            os.chdir(original)
    print("TODO OK -- ingest_manual.py divide, extrae, fusiona y deja una fuente que CORRELATE y LINT entienden.")


if __name__ == "__main__":
    main()
