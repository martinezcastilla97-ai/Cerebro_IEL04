"""Prueba de PUNTA A PUNTA sobre un vault de muestra con datos INVENTADOS, con el LLM y los
embeddings sustituidos por respuestas fijas: lint -> correlate -> planeador -> temario ->
auditorias -> lint, y despues los scripts ejecutados como comandos reales (argparse, salida,
codigos de salida) para asegurar que ningun `__main__` esta roto.

Es el equivalente offline de "probar el vault con un programa pequeno": comprueba que las
piezas encajan entre si, no la calidad de lo que un LLM real escriba.

Uso (desde src/):  python test_flujo_completo.py
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import _fixtures
import correlate
import correlate_bibliografia
import correlate_planeador
import lint
import planeador
import presentaciones
import temario
import vault
from correlate_bibliografia import EstadoBibliografia, JuicioBibliografia
from schema_correlacion import JuicioCorrelacion
from schema_planeador import EstadoPlaneador, JuicioPlaneador, TemasSemana
from schema_presentacion import DiapositivasParte
from schema_temario import CierreSesion, PlanSesion, SeccionRedactada

SRC = Path(__file__).resolve().parent


def llm_falso(sistema, usuario, formato):
    if formato is TemasSemana:
        n = int(re.search(r"Semanas de clase de este RA: (\d+)", usuario).group(1))
        return TemasSemana(temas=[f"Tema {i}" for i in range(1, n + 1)])
    if formato in (PlanSesion, SeccionRedactada, CierreSesion):
        return _fixtures.responder_temario(usuario, formato)
    if formato is DiapositivasParte:
        return _fixtures.diapositivas_falsas(usuario)
    if formato is JuicioPlaneador:
        return JuicioPlaneador(estado=EstadoPlaneador.cubierto, confianza=0.9, semanas_con_problema=[], justificacion="Cubre el RA.")
    if formato is JuicioBibliografia:
        return JuicioBibliografia(estado=EstadoBibliografia.cubierta, justificacion="Las fuentes lo sostienen.")
    raise AssertionError(formato)


def comando(*argumentos: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", *argumentos], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})


def probar(raiz: Path) -> None:
    assert lint.revisar() == []
    print("1. el vault de muestra parte sano (lint sin hallazgos) -- OK")

    # --- scripts como comandos reales (sin LLM) ---------------------------------
    r = comando(str(SRC / "correlate.py"), "--all", "--dry-run", cwd=raiz)
    assert r.returncode == 0 and "4 RA: gate abierto 3, cerrado 1" in r.stdout, (r.returncode, r.stdout, r.stderr)
    r = comando(str(SRC / "planeador.py"), "TPR01", "--sin-llm", cwd=raiz)
    assert r.returncode == 0 and Path("generacion/planeador/TPR01-planeador.md").exists(), (r.stdout, r.stderr)
    r = comando(str(SRC / "planeador.py"), "TPR01", "--sin-llm", cwd=raiz)
    assert r.returncode == 1 and "ya existe" in r.stdout                        # no sobrescribe: error claro y codigo 1
    r = comando(str(SRC / "lint.py"), cwd=raiz)
    assert r.returncode == 0 and "Sin hallazgos" in r.stdout, (r.stdout, r.stderr)
    for script in ("correlate.py", "planeador.py", "temario.py", "correlate_planeador.py", "correlate_bibliografia.py", "ingest_manual.py",
                   "presentaciones.py"):
        r = comando(str(SRC / script), "--help", cwd=raiz)
        assert r.returncode == 0 and "usage" in r.stdout.lower(), (script, r.stderr)
    print("2. como comandos reales: correlate --dry-run, planeador (y su error al repetir), lint y --help de los 7 scripts -- OK")
    Path("generacion/planeador/TPR01-planeador.md").unlink()

    # --- flujo con el LLM y los embeddings sustituidos ------------------------------
    vault.pedir_estructurado = llm_falso
    confianzas = {"Exp1": 0.93, "Exp2": 0.30, "Exp3": 0.48}
    correlate.recall_practicas_candidatas = lambda ra, k=3: [("banco-uno", c) for c in confianzas]
    correlate.juzgar_correlacion = lambda ra, practica, fuente: JuicioCorrelacion(
        ra_codigo=ra.codigo, practica_codigo=practica.codigo, coincide=practica.codigo == "Exp1",
        justificacion="Coinciden los conceptos.", confianza_semantica=confianzas[practica.codigo])

    resumen = correlate.correlacionar_vault()
    assert (resumen["aceptado"], resumen["pendiente_revision"], resumen["sin_candidato"], resumen["errores"]) == (2, 1, 1, [])
    print("3. CORRELATE: 2 aceptados, 1 pendiente_revision, 1 sin_candidato -- OK")

    planeador.generar_planeador("TPR01")
    escritos, _ = temario.generar_temarios("TPR01")
    assert len(escritos) == 11
    figuras_temario = sorted(Path("generacion/temarios/figuras").glob("TPR01-semana01-fig*.png"))
    assert len(figuras_temario) == 3 and figuras_temario[0].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"        # el temario dibuja sus figuras (matplotlib de verdad)
    print("4. PLANEADOR y TEMARIO: planeador de 14 semanas y 11 temarios de tres pasos (uno por semana de clase, ninguno de examen), con sus figuras dibujadas -- OK")

    # El temario de la semana 1 (RA1, que ya tiene practica asignada por CORRELATE) debe anclarse en ella.
    assert "**Práctica de referencia:** [[banco-uno]] — Exp1" in vault.leer_pagina(Path("generacion/temarios/TPR01-semana01.md"))[1]
    print("5. el temario de un RA con practica aceptada por CORRELATE se ancla en ella (el flujo encadena los datos) -- OK")

    assert len(correlate_bibliografia.auditar_temarios("TPR01")) == 11
    assert len(correlate_planeador.auditar_planeador("TPR01")) == 3
    matriz_ra = vault.leer_pagina(Path("wiki/resultados-aprendizaje/TPR01-RA1.md"))[0]
    assert matriz_ra["correlacion_estado"] == "aceptado" and matriz_ra["planeador_estado"] == "cubierto"
    assert vault.leer_pagina(Path("generacion/temarios/TPR01-semana01.md"))[0]["bibliografia_estado"] == "cubierta"
    print("6. CORRELATE-BIBLIOGRAFIA y CORRELATE-PLANEADOR: cada RA/temario queda con su estado de auditoria -- OK")

    resultados = presentaciones.generar_presentaciones("TPR01")           # despues de los temarios y de sus auditorias
    assert len(resultados) == 11 and {e for _, e, _ in resultados} == {"generada"} and all(n >= 5 for _, _, n in resultados)   # una llamada por parte
    fm_t1 = vault.leer_pagina(Path("generacion/temarios/TPR01-semana01.md"))[0]
    assert fm_t1["presentacion_estado"] == "generada" and fm_t1["bibliografia_estado"] == "cubierta"      # cada etapa conserva los campos de las demas
    tex = Path("generacion/presentaciones/TPR01/TPR01-semana01.tex").read_text(encoding="utf-8")
    assert "\\includegraphics" not in tex and "\\bloque{01}" in tex and "\\begin{tikzpicture}" in tex     # sin imagenes: las figuras van en TikZ
    assert not Path("generacion/presentaciones/TPR01/figuras").exists() and not Path("generacion/presentaciones/TPR01/logos").exists()
    print("7. PRESENTACIONES: 11 presentaciones .tex (una llamada por parte de cada temario, con su plan), sin imágenes, sin pisar los campos de la auditoría bibliográfica -- OK")

    hallazgos = lint.revisar()
    assert not [h for h in hallazgos if h.severidad == lint.ERROR], hallazgos
    assert not [h for h in hallazgos if h.regla == "L14"], hallazgos
    print("8. tras todo el flujo, lint no encuentra errores ni presentaciones desactualizadas (los datos de cada etapa son coherentes) -- OK")

    r = comando(str(SRC / "correlate.py"), "--all", cwd=raiz)               # comando real, sin los sustitutos: aun no existe el indice de practicas
    assert r.returncode == 1 and "--indexar" in r.stdout and r.stdout.count("ERROR:") == 3, (r.returncode, r.stdout, r.stderr)
    print("9. sin indice, el comando real falla de forma controlada: codigo 1 y, por cada RA afectado, un error que dice que hay que correr --indexar -- OK")


def main() -> None:
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        _fixtures.armar_vault_muestra(Path(tmp))           # sin config/framework_iub: las presentaciones ya no usan los logos
        os.chdir(tmp)
        try:
            probar(Path(tmp))
        finally:
            os.chdir(original)
    print("TODO OK -- el flujo completo encaja de punta a punta.")


if __name__ == "__main__":
    main()
