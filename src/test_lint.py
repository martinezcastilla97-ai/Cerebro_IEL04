"""Prueba de lint.py sobre un vault de muestra con datos INVENTADOS: un vault sano no da
hallazgos, y cada defecto sembrado a proposito se detecta con su regla.

Uso (desde src/):  python test_lint.py
"""

import os
import tempfile
from pathlib import Path

import _fixtures
import correlate
import lint
import vault


def pagina(ruta: str, fm: dict, cuerpo: str = "\n\n# Pagina de prueba\n") -> None:
    vault.escribir_pagina(Path(ruta), fm, cuerpo)


def hay(hallazgos, regla: str, ruta_contiene: str, severidad: str | None = None) -> bool:
    return any(h.regla == regla and ruta_contiene in h.ruta and (severidad is None or h.severidad == severidad) for h in hallazgos)


def probar() -> None:
    limpio = lint.revisar()
    assert limpio == [], limpio
    print("1. un vault sano no da ningun hallazgo -- OK")

    # --- defectos sembrados -------------------------------------------------
    pagina("wiki/conceptos/tipo-erroneo.md", {"tipo": "fuente"})                                         # L01
    Path("wiki/conceptos/sin-frontmatter.md").write_text("# Sin frontmatter\n", encoding="utf-8")        # L01
    Path("wiki/conceptos/yaml-roto.md").write_text("---\ntipo: [concepto\n---\n\n# x\n", encoding="utf-8")  # L01
    pagina("wiki/asignaturas/MIS01 - Inconsistente.md", _fixtures._asignatura("MIS01", "Inconsistente", 10, 20, "teórica", []))  # L02
    pagina("wiki/asignaturas/HP01 - Horas invertidas.md", _fixtures._asignatura("HP01", "Horas invertidas", 20, 40, "teórico-práctica", []))  # L02 (hp_totales > had_totales, con tipo_abordaje ya consistente)
    fm_ra, cuerpo_ra = vault.leer_pagina(Path("wiki/resultados-aprendizaje/TEO01-RA1.md"))                # L03
    fm_ra["requiere_practica"] = "[[banco-uno]]"
    vault.escribir_pagina(Path("wiki/resultados-aprendizaje/TEO01-RA1.md"), fm_ra, cuerpo_ra)
    ra_mal = _fixtures._ra("RA9", _fixtures.TPR01, "teórico-práctica", 10, [_fixtures.ce("CE1", "t", "cognitiva_conceptual", 0.8)], [])
    pagina("wiki/resultados-aprendizaje/TPR01-RA9.md", ra_mal)                                            # L04 (codigo) + L05 (huerfano)
    ra_tipo = _fixtures._ra("TPR01-RA8", _fixtures.TPR01, "teórica", 10, [_fixtures.ce("CE1", "t", "cognitiva_conceptual", 0.8)], [])
    pagina("wiki/resultados-aprendizaje/TPR01-RA8.md", ra_tipo)                                           # L04 (tipo_abordaje)
    pagina("wiki/resultados-aprendizaje/TPR01-RA7.md", {"tipo": "resultado_aprendizaje", "codigo": "TPR01-RA7", "pertenece_a": f"[[{_fixtures.TPR01}]]"})  # L04 (incompleto)
    pagina("wiki/fuentes/libro-roto.md", {"tipo": "fuente", "etiquetas": ["libro"]}, "\n\n# Libro\nVer [[no-existe]] y `[[ejemplo-en-codigo]]`.\n\n```\n[[otro-ejemplo]]\n```\n")  # L06
    copia = _fixtures._ra("TPR01-RA1", _fixtures.TPR01, "teórico-práctica", 10, [_fixtures.ce("CE1", "t", "cognitiva_conceptual", 0.8)], [])
    pagina("wiki/resultados-aprendizaje/copia-de-ra1.md", copia)                                          # L07
    pagina("wiki/fuentes/banco-vacio.md", {"tipo": "fuente", "etiquetas": ["equipo-laboratorio"]})        # L08 aviso
    invalida = _fixtures.practica("Exp1", "A", "alfa")
    invalida["terminos_clave"] = ["uno"]
    pagina("wiki/fuentes/banco-malo.md", {"tipo": "fuente", "etiquetas": ["equipo-laboratorio"],
                                          "practicas": [invalida, _fixtures.practica("Exp2", "B", "beta"), _fixtures.practica("Exp2", "C", "gamma")]})  # L08 error x2
    pagina("generacion/planeador/TPR01-planeador.md", {"tipo": "planeador", "asignatura": f"[[{_fixtures.TPR01}]]", "semanas_examen": [5, 10, 14]})
    pagina("generacion/temarios/TPR01-semana05.md", {"tipo": "temario", "semana": 5})                     # L10 examen
    pagina("generacion/temarios/ZZZ01-semana01.md", {"tipo": "temario", "semana": 1})                     # L10 sin planeador
    pagina("wiki/asignaturas/ORF01 - Sin programa listado.md", _fixtures._asignatura("ORF01", "Sin programa listado", 10, 10, "teórico-práctica", []))  # L11
    pagina("wiki/asignaturas/CRE01 - Creditos descuadrados.md", _fixtures._asignatura("CRE01", "Créditos descuadrados", 20, 0, "teórica", []))  # L13 (20+60=80 != 2x48=96)
    ra_desalineado = _fixtures._ra("TPR01-RA6", _fixtures.TPR01, "teórico-práctica", 10, [_fixtures.ce("CE1", "t", "cognitiva_conceptual", 0.8)], [])
    pagina("wiki/resultados-aprendizaje/nombre-no-coincide.md", ra_desalineado)                                     # L12
    Path("wiki/conceptos/con-bom.md").write_bytes(
        "﻿".encode("utf-8") + b"---\ntipo: concepto\nfecha_creacion: '2020-01-01'\nfecha_actualizacion: '2020-01-01'\n---\n\n# x\n")  # NO debe dar L01

    hallazgos = lint.revisar()
    esperados = [
        ("L01", "tipo-erroneo.md", "ERROR"), ("L01", "sin-frontmatter.md", "ERROR"), ("L01", "yaml-roto.md", "ERROR"),
        ("L02", "MIS01", "ERROR"),
        ("L02", "HP01", "ERROR"),
        ("L03", "TEO01-RA1.md", "ERROR"),
        ("L04", "TPR01-RA9.md", "ERROR"), ("L05", "TPR01-RA9.md", "AVISO"),
        ("L04", "TPR01-RA8.md", "ERROR"), ("L04", "TPR01-RA7.md", "ERROR"),
        ("L06", "libro-roto.md", "ERROR"),
        ("L07", "resultados-aprendizaje", "ERROR"),
        ("L08", "banco-vacio.md", "AVISO"), ("L08", "banco-malo.md", "ERROR"),
        ("L10", "TPR01-semana05.md", "ERROR"), ("L10", "ZZZ01-semana01.md", "AVISO"),
        ("L11", "ORF01", "AVISO"),
        ("L12", "nombre-no-coincide.md", "AVISO"),
        ("L13", "CRE01", "AVISO"),
    ]
    for regla, ruta, severidad in esperados:
        assert hay(hallazgos, regla, ruta, severidad), f"no se detecto {regla} en {ruta}: {[h for h in hallazgos if h.regla == regla]}"
    assert not [h for h in hallazgos if "con-bom.md" in h.ruta], "un archivo con BOM no debe reportarse como 'sin frontmatter' (L01)"
    print(f"2. {len(esperados)} defectos sembrados (L01-L08, L10-L13): todos detectados con su regla y severidad; un BOM inicial no rompe L01 -- OK")

    rotos = [h for h in hallazgos if h.regla == "L06" and "libro-roto" in h.ruta]
    assert len(rotos) == 1 and "no-existe" in rotos[0].mensaje, rotos       # los [[...]] dentro de codigo no cuentan
    assert sum(h.regla == "L08" and "banco-malo" in h.ruta for h in hallazgos) == 2      # practica invalida + practica repetida
    print("3. los enlaces de ejemplo dentro de codigo no se cuentan como rotos; una practica invalida y una repetida son dos errores -- OK")

    # L09: con los pesos actuales no puede ocurrir (la senal estructural sola da 0.5); se prueba alterando los pesos.
    assert not any(h.regla == "L09" for h in hallazgos)
    pesos = (correlate.PESO_ESTRUCTURAL, correlate.PESO_CHECKLIST)
    correlate.PESO_ESTRUCTURAL, correlate.PESO_CHECKLIST = 0.1, 0.1
    try:
        assert hay(lint.revisar(), "L09", "TPR01-RA3.md", "AVISO")     # RA3 solo tiene un CE conceptual: 0.1 + 0.1 + 0 = 0.2
    finally:
        correlate.PESO_ESTRUCTURAL, correlate.PESO_CHECKLIST = pesos
    print("4. L09 no salta con los pesos actuales y si con pesos que dejen un RA teorico-practico bajo 0.40 -- OK")

    fm_ok = [h for h in hallazgos if h.ruta.endswith(("libro-a.md", "TPR01-RA2.md", "TEO01 - Asignatura teórica de prueba.md"))]
    assert not any(h.regla in ("L02", "L04", "L06") for h in fm_ok if "TEO01-RA1" not in h.ruta), fm_ok
    print("5. las paginas sanas no generan falsos positivos -- OK")


def main() -> None:
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))
        os.chdir(tmp)
        try:
            probar()
        finally:
            os.chdir(original)
    print("TODO OK -- lint.py detecta los defectos y no da falsos positivos en un vault sano.")


if __name__ == "__main__":
    main()
