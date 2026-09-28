"""Prueba de ACTUALIZAR-ESTRUCTURA (src/actualizar_estructura.py y src/migraciones.py): no llama a ningun LLM.

Sobre plantillas SINTETICAS (una version vieja, una nueva, una copia con contenido y ediciones propias) comprueba que la actualizacion
lleva los cambios a la copia sin tocar su contenido, y sobre la plantilla REAL que su manifiesto esta al dia y que una copia de
`nuevo-cerebro.py` arranca sin diferencias:
  A. politicas por ruta, huellas (saltos de linea, BOM, titulo del README) y versiones;
  B. el manifiesto (generarlo, verificarlo) y el de la plantilla real;
  C. la clasificacion: nuevo, actualizar, conflicto, tuyo, obsoleto, semilla, y lo que NO se toca;
  D. la prueba en seco no escribe; aplicar respalda, deja `.nuevo`, conserva el titulo del README, anota el log y es idempotente;
  E. --sobrescribir, --conservar, --eliminar-obsoletos y --deshacer;
  F. las migraciones de contenido (renombrar, agregar y quitar campos, con respaldo y sin escribir en seco);
  G. paquetes ZIP (completo, parcial, con carpeta envolvente, rutas peligrosas) y delegar en el script del paquete;
  H. copias sin manifiesto, versiones anteriores y errores de uso;
  I. la plantilla real: manifiesto al dia, una copia de nuevo-cerebro.py sin diferencias, y una actualizacion real de punta a punta;
  J. seguridad y robustez: la prueba en seco no ejecuta codigo del paquete, solo se instalan rutas de la plantilla (`.claude/`, `.vscode/`,
     `.git/`, `.github/` y lo desconocido no; de `.obsidian/` solo sus 5 .json de configuracion, no plugins, snippets ni temas), y una
     migracion sin PyYAML no se da por hecha ni salta paginas en silencio.

Uso (desde src/):  python test_actualizar_estructura.py
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import actualizar_estructura as ae
import migraciones
import vault

SRC = Path(__file__).resolve().parent
RAIZ = SRC.parent
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
SCRIPT = SRC / "actualizar_estructura.py"


def escribir(raiz: Path, ruta: str, texto: str) -> None:
    destino = raiz / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8", newline="\n")


def esperar(excepcion, funcion, *args, **kwargs) -> str:
    try:
        funcion(*args, **kwargs)
    except excepcion as error:
        return str(error)
    raise AssertionError(f"debio lanzar {excepcion.__name__}")


def arbol(raiz: Path, excluir: tuple[str, ...] = ("memory_store",)) -> dict[str, str]:
    return {p.relative_to(raiz).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raiz.rglob("*"))
            if p.is_file() and p.relative_to(raiz).parts[0] not in excluir}


def cli(*args: str, cwd: Path | None = None, script: Path = SCRIPT, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(script), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          env={**ENTORNO, **(env or {})}, stdin=subprocess.DEVNULL)


# --- plantillas sinteticas -------------------------------------------------------------------------------------------------

SCHEMA = "---\ntipo: esquema\nversion: {v}\n---\n\n# Esquema\n"
V1 = {
    "CLAUDE.md": "# Reglas\n\n## Estructura\n\ntexto uno\n\n## Operaciones\n\nlas operaciones\n",
    "AGENTS.md": "# Agentes\n",
    "README.md": "# Cerebro Docente\n\nLeeme.\n",
    "requirements.txt": "pydantic\n",
    "config/SCHEMA.md": SCHEMA.format(v="1.1"),
    "config/framework_iub/beamerthemeiub.sty": "% tema institucional\n",
    "config/framework_iub/logos/logo.png": "png-falso",
    "src/lint.py": 'print("Sin hallazgos")\n',
    "src/diseno_iub.py": "VERSION = 2\n\n\ndef generar():\n    return 1\n",
    "src/propio.py": "X = 1\n",
    "correlaciones/matriz-a.md": "---\ntipo: vista_dataview\n---\n\n# Matriz A\n",
    "wiki/index.md": "---\ntipo: index\n---\n\n# Indice\n\nVer [[../correlaciones/matriz-a]].\n",
    "wiki/log.md": "# Log\n",
    "wiki/marco-pedagogico.md": "---\ntipo: marco_pedagogico\n---\n\n# Marco\n",
    ".obsidian/core-plugins.json": '["file-explorer"]\n',
    ".obsidian/workspace.json": '{"lastOpenFiles": []}\n',
    "raw/curriculos/.gitkeep": "",
}


def plantilla(raiz: Path, version: str = "1.1", cambios: dict | None = None, quitar: tuple[str, ...] = ()) -> Path:
    """Una plantilla sintetica: V1 con `cambios` encima y sin lo de `quitar`. Trae su manifiesto."""
    raiz.mkdir(parents=True, exist_ok=True)
    contenido = {**V1, "config/SCHEMA.md": SCHEMA.format(v=version), **(cambios or {})}
    for ruta, texto in contenido.items():
        if ruta not in quitar:
            escribir(raiz, ruta, texto)
    ae.escribir_manifiesto(raiz, ae.construir_manifiesto(raiz))
    return raiz


def copia_de(origen: Path, destino: Path) -> Path:
    """Una copia en uso: la plantilla mas contenido propio (que la actualizacion no debe tocar)."""
    shutil.copytree(origen, destino)
    escribir(destino, "raw/curriculos/Prog/TPR01.md", "# Curriculo\n\ntexto\n")
    escribir(destino, "wiki/asignaturas/A.md", "---\ntipo: asignatura\ncodigo: A\nnombre_viejo: x\n---\n\n# A\n")
    escribir(destino, "generacion/temarios/A-semana01.md", "---\ntipo: temario\nsemana: 1\ntotal_semanas: 14\n---\n\n# T\n")
    escribir(destino, "src/mio.py", "print('un script propio')\n")
    return destino


V2 = {
    "CLAUDE.md": "# Reglas\n\n## Estructura\n\ntexto uno\n\n## Operaciones\n\nlas operaciones cambiaron\n\n## Nueva\n\nalgo nuevo\n",
    "requirements.txt": "pydantic\nmatplotlib\n",
    "src/lint.py": 'print("Sin hallazgos")\n\n\ndef nueva():\n    return 2\n',
    "src/diseno_iub.py": "VERSION = 3\n\n\ndef generar():\n    return 1\n",
    "src/nuevo_script.py": "Y = 1\n",
    "correlaciones/matriz-b.md": "---\ntipo: vista_dataview\n---\n\n# Matriz B\n",
    ".obsidian/core-plugins.json": '["file-explorer", "graph"]\n',
    ".obsidian/graph.json": "{}\n",
    "wiki/index.md": "---\ntipo: index\n---\n\n# Indice nuevo\n",
    "README.md": "# Cerebro Docente\n\nLeeme, version 2.\n",
}


# --- A. politicas, huellas y versiones ---------------------------------------------------------------------------------


def probar_politicas() -> None:
    esperado = {
        "src/lint.py": "plantilla", "src/prompts/prompt-a.md": "plantilla", "correlaciones/matriz.md": "plantilla", "CLAUDE.md": "plantilla",
        "config/SCHEMA.md": "plantilla", "config/nuevo-cerebro.py": "plantilla", "requirements.txt": "plantilla",
        "config/manifiesto.json": "manifiesto", "config/framework_iub/beamerthemeiub.sty": "semilla",
        # de .obsidian/ solo son semilla los 5 archivos de configuracion que trae la plantilla
        ".obsidian/app.json": "semilla", ".obsidian/appearance.json": "semilla", ".obsidian/core-plugins.json": "semilla", ".obsidian/graph.json": "semilla",
        ".obsidian/workspace.json": "semilla",
        ".obsidian/plugins/x/main.js": "rechazada", ".obsidian/plugins/x/manifest.json": "rechazada", ".obsidian/community-plugins.json": "rechazada",
        ".obsidian/snippets/x.css": "rechazada", ".obsidian/themes/t/theme.css": "rechazada", ".obsidian/hotkeys.json": "rechazada",
        ".obsidian/bookmarks.json": "rechazada", ".obsidian/otro.json": "rechazada", ".obsidian/extra/x.json": "rechazada", ".obsidian/app.json.bak": "rechazada",
        "wiki/index.md": "semilla", "wiki/log.md": "semilla", "wiki/marco-pedagogico.md": "semilla", "wiki/asignaturas/A.md": "instancia",
        "raw/curriculos/x.md": "instancia", "raw/curriculos/.gitkeep": "semilla", "generacion/temarios/t.md": "instancia",
        "memory_store/lancedb/x.bin": "instancia", "src/__pycache__/a.pyc": "ignorar", "src/a.pyc": "ignorar",
        # lo unico que es plantilla es una lista: el resto es desconocido y no se instala nunca
        "src/nuevo.py": "plantilla", "src/prompts/p.md": "plantilla", "config/nuevo-cerebro.ps1": "plantilla", "GEMINI.md": "plantilla",
        "correlaciones/m.md": "plantilla", "otra/cosa.txt": "desconocida", "config/otro.py": "desconocida", "correlaciones/sub/x.md": "desconocida",
        "correlaciones/x.txt": "desconocida", "x.py": "desconocida", "config/notas.md": "desconocida", "docs/guia.md": "desconocida",
        # y lo que puede definir comandos que el asistente o el editor ejecutan solos, o salir de la copia, se rechaza siempre
        ".claude/settings.json": "rechazada", ".vscode/tasks.json": "rechazada", ".git/config": "rechazada", ".github/workflows/x.yml": "rechazada",
        "src/../../x.py": "rechazada", "../x.py": "rechazada", "/etc/passwd": "rechazada", "C:/x.py": "rechazada", "src\\x.py": "rechazada", "src//x.py": "rechazada",
    }
    for ruta, pol in esperado.items():
        assert ae.politica(ruta) == pol, (ruta, ae.politica(ruta), pol)
    peligrosas = (".obsidian/community-plugins.json", ".obsidian/plugins/x/main.js", ".obsidian/snippets/x.css", ".obsidian/themes/t/theme.css")
    assert all(p.startswith(ae.RECHAZADAS) for p in peligrosas)
    semillas = ae.OBSIDIAN_SEMILLAS
    ae.OBSIDIAN_SEMILLAS = (*semillas, *peligrosas)                      # aunque un dia alguien amplie la lista de semillas, RECHAZADAS manda
    try:
        assert [ae.politica(p) for p in peligrosas] == ["rechazada"] * 4
    finally:
        ae.OBSIDIAN_SEMILLAS = semillas
    assert set(ae.OBSIDIAN_SEMILLAS) == {".obsidian/app.json", ".obsidian/appearance.json", ".obsidian/core-plugins.json", ".obsidian/graph.json", ".obsidian/workspace.json"}
    reales = {p.relative_to(RAIZ).as_posix() for p in (RAIZ / ".obsidian").rglob("*") if p.is_file()}
    assert reales <= set(ae.OBSIDIAN_SEMILLAS), f"la plantilla trae archivos de .obsidian/ que una actualizacion no crearia: {sorted(reales - set(ae.OBSIDIAN_SEMILLAS))}"
    print("A1. cada ruta tiene su politica: codigo y reglas se actualizan, esqueletos y el tema se crean pero no se pisan, raw/wiki/generacion/memory_store nunca se tocan, "
          "lo que no esta en la lista de la plantilla es desconocido y `.claude/`, `.vscode/`, `.git/`, `.github/` y las rutas que salen de la copia se rechazan -- OK")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        escribir(base, "a.md", "linea uno\nlinea dos\n")
        (base / "b.md").write_bytes("﻿linea uno\r\nlinea dos\r\n".encode("utf-8"))
        assert ae.huella(base / "a.md", "a.md") == ae.huella(base / "b.md", "b.md"), "saltos de linea y BOM no cambian la huella"
        (base / "x.png").write_bytes(b"\x89PNG\r\n")
        (base / "y.png").write_bytes(b"\x89PNG\n")
        assert ae.huella(base / "x.png", "x.png") != ae.huella(base / "y.png", "y.png"), "un binario se compara byte a byte"
        escribir(base, "README.md", "# Cerebro Docente — Programa X\n\ntexto\n")
        escribir(base, "otro/README.md", "# Cerebro Docente — Programa X\n")
        assert ae.huella(base / "README.md", "README.md") == hashlib.sha256(b"# Cerebro Docente\n\ntexto\n").hexdigest(), "el titulo del README no cuenta"
        assert ae.huella(base / "otro/README.md", "otro/README.md") != hashlib.sha256(b"# Cerebro Docente\n").hexdigest(), "solo el README de la raiz"
    print("A2. la huella ignora saltos de linea y BOM en los textos, compara binarios byte a byte y no cuenta el titulo `— Programa X` del README -- OK")

    assert migraciones.version_tupla("1.9") < migraciones.version_tupla("1.10") < migraciones.version_tupla("2.0")
    assert "no valida" in esperar(ValueError, migraciones.version_tupla, "uno.dos")
    with tempfile.TemporaryDirectory() as tmp:
        escribir(Path(tmp), "config/SCHEMA.md", SCHEMA.format(v="1.10"))
        assert ae.version_de(Path(tmp)) == "1.10", "YAML leeria 1.10 como el numero 1.1: se lee como texto"
        assert ae.version_de(Path(tmp) / "no-existe") is None
    print("A3. las versiones se comparan por numeros (1.9 < 1.10) y se leen como texto (1.10 no es 1.1) -- OK")


# --- B. el manifiesto -------------------------------------------------------------------------------------------------------


def probar_manifiesto() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v1 = plantilla(Path(tmp) / "v1")
        manifiesto = ae.leer_manifiesto(v1)
        assert manifiesto["version"] == "1.1" and manifiesto["formato"] == 1 and manifiesto["actualizaciones"] == []
        assert set(manifiesto["archivos"]) == {r for r in V1 if ae.politica(r) == "plantilla"} | {"config/SCHEMA.md"}, sorted(manifiesto["archivos"])
        assert "config/manifiesto.json" not in manifiesto["archivos"] and "wiki/index.md" not in manifiesto["archivos"], "no lleva semillas ni a si mismo"
        assert ae.desfases_del_manifiesto(v1) == []
        escribir(v1, "src/lint.py", "print('otro')\n")
        escribir(v1, "src/nuevo.py", "1\n")
        (v1 / "AGENTS.md").unlink()
        problemas = ae.desfases_del_manifiesto(v1)
        assert "src/lint.py: cambio despues de generar el manifiesto" in problemas and "src/nuevo.py: no esta en el manifiesto" in problemas
        assert "AGENTS.md: esta en el manifiesto y ya no existe" in problemas
        r = cli("--verificar-manifiesto", "--destino", str(v1))
        assert r.returncode == 1 and "está viejo" in r.stdout, r.stdout
        r = cli("--generar-manifiesto", "--destino", str(v1))
        assert r.returncode == 0 and "versión 1.1" in r.stdout and ae.desfases_del_manifiesto(v1) == []
        assert cli("--verificar-manifiesto", "--destino", str(v1)).returncode == 0
        vacia = Path(tmp) / "vacia"
        vacia.mkdir()
        assert "no parece la plantilla" in esperar(ValueError, ae.construir_manifiesto, vacia)
        assert cli("--generar-manifiesto", "--destino", str(vacia)).returncode == 1
    print("B1. el manifiesto lleva la version y la huella de cada archivo de plantilla (no de semillas ni de si mismo); detecta lo que cambio, lo nuevo y lo borrado; se regenera y se verifica por linea de comandos -- OK")


# --- C. clasificacion ------------------------------------------------------------------------------------------------------


def escenario(tmp: str):
    """(paquete v2, copia en la version 1.1 con ediciones propias)."""
    v1 = plantilla(Path(tmp) / "v1")
    copia = copia_de(v1, Path(tmp) / "copia")
    escribir(copia, "CLAUDE.md", V1["CLAUDE.md"] + "\n## Regla de mi institucion\n\nla mia\n")     # editado en la copia y cambiado en la plantilla: conflicto
    escribir(copia, "src/propio.py", "X = 2  # editado en la copia\n")                             # editado en la copia y sin cambio en la plantilla: tuyo
    escribir(copia, "README.md", "# Cerebro Docente — Programa de prueba\n\nLeeme.\n")             # solo el titulo distinto: no cuenta
    escribir(copia, ".obsidian/workspace.json", '{"lastOpenFiles": ["wiki/asignaturas/A.md"]}\n')
    v2 = plantilla(Path(tmp) / "v2", "1.2", V2, quitar=("AGENTS.md",))
    return v2, copia


def probar_clasificacion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v2, copia = escenario(tmp)
        instalado = ae.leer_manifiesto(copia)
        entradas = {e.ruta: e for e in ae.clasificar(v2, copia, instalado, parcial=False)}
        acciones = {r: e.accion for r, e in entradas.items()}
        assert acciones["src/lint.py"] == "actualizar" and acciones["requirements.txt"] == "actualizar" and acciones["src/diseno_iub.py"] == "actualizar"
        assert acciones["CLAUDE.md"] == "conflicto" and acciones["src/propio.py"] == "propio"
        assert acciones["src/nuevo_script.py"] == "nuevo" and acciones["correlaciones/matriz-b.md"] == "nuevo" and acciones[".obsidian/graph.json"] == "nuevo"
        assert acciones["README.md"] == "actualizar", "el README cambio en la plantilla y en la copia solo cambio el titulo"
        assert acciones["AGENTS.md"] == "obsoleto"
        assert acciones[".obsidian/core-plugins.json"] == "conservar" and acciones["wiki/index.md"] == "conservar" and acciones[".obsidian/workspace.json"] == "conservar"
        assert acciones["config/framework_iub/beamerthemeiub.sty"] == "conservar" and acciones["config/SCHEMA.md"] == "actualizar"
        assert "config/manifiesto.json" not in acciones
        print("C1. de una plantilla nueva salen: los cambios sin editar se ACTUALIZAN, el archivo editado en ambos lados es un CONFLICTO, lo nuevo se crea, lo que ya no esta es OBSOLETO y las semillas existentes se CONSERVAN -- OK")

        assert not any(r.startswith(("raw/", "wiki/asignaturas", "generacion/", "src/mio.py")) for r in entradas), "el contenido y lo propio no aparecen"
        assert "+" in entradas["src/lint.py"].resumen and "agrega: nueva" in entradas["src/lint.py"].resumen, entradas["src/lint.py"].resumen
        assert "modifica: VERSION" in entradas["src/diseno_iub.py"].resumen
        assert "agrega: Nueva" in entradas["CLAUDE.md"].resumen and "modifica: Operaciones" in entradas["CLAUDE.md"].resumen, entradas["CLAUDE.md"].resumen
        print("C2. el contenido de la copia (raw/, wiki/, generacion/) y sus scripts propios no entran en la comparacion, y cada cambio trae su resumen: funciones o secciones que se agregan, quitan o modifican -- OK")

        editado = {**instalado, "archivos": {**instalado["archivos"]}}
        escribir(copia, "src/propio.py", "X = 2  # editado en la copia\n")
        escribir(v2, "src/propio.py", "X = 3\n")
        e = {x.ruta: x.accion for x in ae.clasificar(v2, copia, editado, parcial=False)}
        assert e["src/propio.py"] == "conflicto"
        escribir(v2, "src/propio.py", "X = 1\n")
        e = {x.ruta: x.accion for x in ae.clasificar(v2, copia, editado, parcial=False)}
        assert e["src/propio.py"] == "propio", "editado en la copia y sin cambio en la plantilla"
        print("C3. editado en la copia + cambiado en la plantilla = CONFLICTO; editado en la copia y sin cambio en la plantilla = TUYO (se deja) -- OK")

        efectos = ae.efectos(list(entradas.values()), v2, copia, [])
        texto = "\n".join(efectos)
        assert "pip install -r requirements.txt" in texto and "diseño de las diapositivas pasó a la versión 3" in texto
        assert "correlaciones/matriz-b.md" in texto and "[[../correlaciones/matriz-b]]" in texto, "una vista nueva se enlaza en el indice"
        assert "matriz-a" not in texto and "python src/analizar_cambios.py" in texto
        assert f"cuestan ~{ae.LLAMADAS_POR_PRESENTACION} llamadas al modelo por temario" in texto, "las de un diseño anterior al 5 no tienen plan en el formato actual"

        # una presentacion con su plan guardado en el formato actual (sin LLM) y una sin plan
        escribir(copia, "generacion/temarios/Z-semana01.md", "---\ntipo: temario\npresentacion_archivo: generacion/presentaciones/Z/Z-semana01.tex\n---\n\n# Z\n")
        escribir(copia, "generacion/temarios/Z-semana02.md", "---\ntipo: temario\npresentacion_archivo: 'generacion/presentaciones/Z/Z-semana02.tex'\n---\n\n# Z\n")
        escribir(copia, "generacion/presentaciones/Z/Z-semana01.plan.json", '{"formato": 2, "temario_hash": "abc", "partes": {}}\n')
        assert ae.presentaciones_por_plan(copia) == (1, 1)
        texto = "\n".join(ae.efectos(list(entradas.values()), v2, copia, []))
        assert "1 con plan, sin LLM; 1 sin plan: ~9 llamadas)" in texto, texto
        # un .plan.json corrupto (`{}`, o que no es JSON) o del formato del diseño 4 (`plan`) no evita las llamadas: cuenta como sin plan
        for semana, plan in ((3, "{}\n"), (4, "{no es json\n"), (5, '{"temario_hash": "abc", "plan": {"secciones": []}}\n')):
            escribir(copia, f"generacion/temarios/Z-semana0{semana}.md", f"---\ntipo: temario\npresentacion_archivo: generacion/presentaciones/Z/Z-semana0{semana}.tex\n---\n\n# Z\n")
            escribir(copia, f"generacion/presentaciones/Z/Z-semana0{semana}.plan.json", plan)
        assert ae.presentaciones_por_plan(copia) == (1, 4)
        texto = "\n".join(ae.efectos(list(entradas.values()), v2, copia, []))
        assert "1 con plan, sin LLM; 4 sin plan: ~36 llamadas)" in texto, texto
        assert ae._llamadas(1) == "1 llamada" and ae._llamadas(2) == "2 llamadas"
        print("C4. los efectos avisan de las dependencias, del nuevo diseño de las diapositivas (sin LLM las que tienen plan en el formato actual; ~9 llamadas por "
              "temario las demás, contadas en la copia), de una vista que falta en el indice y de como ver si lo generado quedo viejo -- OK")


# --- D. aplicar ------------------------------------------------------------------------------------------------------------


def probar_aplicar() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v2, copia = escenario(tmp)
        antes = arbol(copia)
        informe = ae.actualizar(v2, copia)
        assert not informe.aplicado and arbol(copia) == antes and not (copia / "memory_store").exists(), "la prueba en seco no escribe nada"
        print("D1. sin --aplicar solo se muestra lo que pasaria: la copia queda byte a byte igual -- OK")

        propio = {r: h for r, h in arbol(copia).items() if r.startswith(("raw/", "wiki/asignaturas", "generacion/")) or r == "src/mio.py"}
        informe = ae.actualizar(v2, copia, aplicar=True)
        assert informe.aplicado and informe.respaldo and informe.lint == "exit 0: Sin hallazgos", (informe.respaldo, informe.lint)
        despues = arbol(copia)
        assert {r: h for r, h in despues.items() if r in propio} == propio, "el contenido de la copia y sus scripts propios no se tocan"
        assert (copia / "src/lint.py").read_text(encoding="utf-8") == V2["src/lint.py"] and (copia / "src/nuevo_script.py").is_file()
        assert (copia / "requirements.txt").read_text(encoding="utf-8") == "pydantic\nmatplotlib\n"
        assert (copia / "CLAUDE.md").read_text(encoding="utf-8").endswith("la mia\n"), "el conflicto conserva tu archivo"
        assert (copia / "CLAUDE.md.nuevo").read_text(encoding="utf-8") == V2["CLAUDE.md"], "y deja la version nueva al lado"
        assert (copia / "wiki/index.md").read_text(encoding="utf-8") == V1["wiki/index.md"] and (copia / ".obsidian/core-plugins.json").read_text(encoding="utf-8") == V1[".obsidian/core-plugins.json"]
        assert (copia / ".obsidian/graph.json").is_file() and (copia / "AGENTS.md").is_file(), "una semilla nueva se crea; un obsoleto no se borra sin pedirlo"
        assert (copia / "README.md").read_text(encoding="utf-8").startswith("# Cerebro Docente — Programa de prueba\n") and "version 2" in (copia / "README.md").read_text(encoding="utf-8")
        assert (copia / "config/SCHEMA.md").read_text(encoding="utf-8") == SCHEMA.format(v="1.2")
        print("D2. aplicar actualiza lo no editado, crea lo nuevo, deja `.nuevo` en un conflicto, conserva semillas y el titulo del README, y no toca raw/, wiki/, generacion/ ni los scripts propios -- OK")

        respaldo = Path(informe.respaldo)
        guardados = json.loads((respaldo / "resumen.json").read_text(encoding="utf-8"))
        assert (respaldo / "src/lint.py").read_text(encoding="utf-8") == V1["src/lint.py"] and "config/manifiesto.json" in guardados["guardados"]
        assert "src/nuevo_script.py" in guardados["creados"] and "CLAUDE.md.nuevo" in guardados["creados"]
        manifiesto = ae.leer_manifiesto(copia)
        assert manifiesto["version"] == "1.2" and manifiesto["archivos"]["src/lint.py"] == ae.huella(v2 / "src/lint.py", "src/lint.py")
        assert manifiesto["archivos"]["CLAUDE.md"] == hashlib.sha256(V1["CLAUDE.md"].encode("utf-8")).hexdigest(), \
            "el conflicto conserva la huella vieja: la proxima corrida lo vuelve a marcar"
        assert manifiesto["actualizaciones"][-1]["desde"] == "1.1" and manifiesto["actualizaciones"][-1]["hasta"] == "1.2"
        log = (copia / "wiki/log.md").read_text(encoding="utf-8")
        assert "/actualizar-estructura 1.1 → 1.2" in log and "1 para revisar a mano" in log and "respaldo en" in log
        print("D3. el respaldo guarda lo que se cambio y lo que se creo, el manifiesto pasa a la 1.2 con la huella de lo instalado (el conflicto conserva la vieja) y el log anota la actualizacion -- OK")

        siguiente = ae.actualizar(v2, copia, aplicar=True)
        acciones = {e.ruta: e.accion for e in siguiente.entradas}
        assert acciones["CLAUDE.md"] == "conflicto" and acciones["src/lint.py"] == "igual" and siguiente.respaldo is None
        assert (copia / "wiki/log.md").read_text(encoding="utf-8").count("/actualizar-estructura") == 1, "sin cambios no se anota otra vez"
        assert len(ae.leer_manifiesto(copia)["actualizaciones"]) == 1
        print("D4. una segunda corrida es idempotente: nada que respaldar, nada que anotar, y el conflicto sigue a la vista -- OK")


# --- E. sobrescribir, conservar, obsoletos, deshacer -------------------------------------------------------------------------


def probar_opciones() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v2, copia = escenario(tmp)
        informe = ae.actualizar(v2, copia, aplicar=True, sobrescribir=True, eliminar_obsoletos=True)
        assert (copia / "CLAUDE.md").read_text(encoding="utf-8") == V2["CLAUDE.md"] and not (copia / "CLAUDE.md.nuevo").exists()
        assert not (copia / "AGENTS.md").exists()
        assert (Path(informe.respaldo) / "CLAUDE.md").read_text(encoding="utf-8").endswith("la mia\n") and (Path(informe.respaldo) / "AGENTS.md").is_file()
        despues = ae.actualizar(v2, copia).entradas
        assert despues and all(e.accion in ("igual", "conservar", "propio") for e in despues), {e.ruta: e.accion for e in despues}
        print("E1. --sobrescribir reemplaza el conflicto y --eliminar-obsoletos quita lo que ya no esta, los dos con respaldo; la copia queda igual a la plantilla -- OK")

    with tempfile.TemporaryDirectory() as tmp:
        v2, copia = escenario(tmp)
        ae.actualizar(v2, copia, aplicar=True)
        assert (copia / "CLAUDE.md.nuevo").is_file()
        assert "no es un archivo con conflicto" in esperar(ValueError, ae.actualizar, v2, copia, True, False, False, ("src/lint.py",))
        informe = ae.actualizar(v2, copia, aplicar=True, conservar=("CLAUDE.md",))
        assert not (copia / "CLAUDE.md.nuevo").exists() and (copia / "CLAUDE.md").read_text(encoding="utf-8").endswith("la mia\n")
        acciones = {e.ruta: e.accion for e in ae.actualizar(v2, copia).entradas}
        assert acciones["CLAUDE.md"] == "propio", "lo conservado deja de marcarse como conflicto"
        v3 = plantilla(Path(tmp) / "v3", "1.3", {**V2, "CLAUDE.md": V2["CLAUDE.md"] + "\n## Otra\n\nmas\n"})
        assert {e.ruta: e.accion for e in ae.actualizar(v3, copia).entradas}["CLAUDE.md"] == "conflicto", "si la plantilla vuelve a cambiar ese archivo, vuelve a ser un conflicto"
        print("E2. --conservar da por bueno tu archivo (sin `.nuevo`, ya no es conflicto) hasta que la plantilla lo cambie otra vez; un archivo sin conflicto no se puede conservar -- OK")

    with tempfile.TemporaryDirectory() as tmp:
        v2, copia = escenario(tmp)
        antes = arbol(copia)
        informe = ae.actualizar(v2, copia, aplicar=True, sobrescribir=True, eliminar_obsoletos=True)
        assert arbol(copia) != antes
        carpeta, restaurados, quitados = ae.deshacer(copia)
        assert carpeta.name == Path(informe.respaldo).name and restaurados > 0 and quitados > 0
        despues = arbol(copia)
        despues.pop("wiki/log.md")
        antes.pop("wiki/log.md")
        assert despues == antes, {r for r in set(despues) | set(antes) if despues.get(r) != antes.get(r)}
        r = cli("--deshacer", "--destino", str(copia))
        assert r.returncode == 0, r.stdout                             # otra vez: restaura lo mismo, sin romperse
        assert "no hay respaldos" in esperar(FileNotFoundError, ae.deshacer, Path(tmp) / "v1")
    print("E3. --deshacer devuelve la copia exactamente a como estaba (archivos cambiados, borrados, creados y el manifiesto) -- OK")


# --- F. migraciones --------------------------------------------------------------------------------------------------------


def probar_migraciones() -> None:
    def a_1_5(ctx: migraciones.Contexto) -> None:
        migraciones.renombrar_campo(ctx, "wiki/asignaturas", "nombre_viejo", "nombre_nuevo")

    def a_1_7(ctx: migraciones.Contexto) -> None:
        migraciones.agregar_campo(ctx, "generacion/temarios", "semanas_totales", 14, tipo="temario")
        migraciones.quitar_campo(ctx, "generacion/temarios", "total_semanas", tipo="temario")

    original = migraciones.MIGRACIONES
    migraciones.MIGRACIONES = [migraciones.Migracion("1.7", "el temario declara semanas_totales", a_1_7), migraciones.Migracion("1.5", "la asignatura llama nombre_nuevo a nombre_viejo", a_1_5),
                               migraciones.Migracion("1.1", "una migracion anterior a la version instalada: no corre", lambda c: (_ for _ in ()).throw(AssertionError("no debe correr")))]
    try:
        assert [m.version for m in migraciones.pendientes("1.1", "1.7")] == ["1.5", "1.7"], "en orden de version, no en el de la lista, y solo las posteriores a la instalada"
        assert migraciones.pendientes("1.7", "1.7") == [] and migraciones.pendientes(None, "1.7") == []
        with tempfile.TemporaryDirectory() as tmp:
            v2 = plantilla(Path(tmp) / "v2", "1.7", {})
            copia = copia_de(plantilla(Path(tmp) / "v1"), Path(tmp) / "copia")
            escribir(copia, "wiki/asignaturas/sin-frontmatter.md", "# sin cabecera\n")
            antes = arbol(copia)
            informe = ae.actualizar(v2, copia)
            assert arbol(copia) == antes, "en seco, las migraciones no escriben"
            assert [m["version"] for m in informe.migraciones] == ["1.5", "1.7"] and informe.migraciones[0]["cambios"] == ["wiki/asignaturas/A.md: `nombre_viejo` -> `nombre_nuevo`"]
            assert len(informe.migraciones[1]["cambios"]) == 2 and any("migración 1.5" in e for e in informe.efectos)
            print("F1. en seco, cada migracion pendiente dice que paginas tocaria (en orden de version) y no escribe; las de versiones ya instaladas no corren -- OK")

            informe = ae.actualizar(v2, copia, aplicar=True)
            fm, cuerpo = vault.leer_pagina(copia / "wiki/asignaturas/A.md")
            assert fm["nombre_nuevo"] == "x" and "nombre_viejo" not in fm and list(fm)[-1] == "nombre_nuevo" and cuerpo == "\n\n# A\n", (fm, cuerpo)
            fm, _ = vault.leer_pagina(copia / "generacion/temarios/A-semana01.md")
            assert fm["semanas_totales"] == 14 and "total_semanas" not in fm
            assert (copia / "wiki/asignaturas/sin-frontmatter.md").read_text(encoding="utf-8") == "# sin cabecera\n", "una pagina sin frontmatter no se toca"
            assert ae.leer_manifiesto(copia)["version"] == "1.7"
            respaldo = Path(informe.respaldo)
            assert "nombre_viejo" in (respaldo / "wiki/asignaturas/A.md").read_text(encoding="utf-8"), "la migracion respalda la pagina antes de tocarla"
            print("F2. aplicar corre las migraciones (renombrar, agregar y quitar campos), respalda cada pagina antes de tocarla y no toca las que no tienen frontmatter -- OK")

            otra = ae.actualizar(v2, copia, aplicar=True)
            assert otra.migraciones == [] and otra.respaldo is None
            ae.deshacer(copia)
            fm, _ = vault.leer_pagina(copia / "wiki/asignaturas/A.md")
            assert fm["nombre_viejo"] == "x" and "nombre_nuevo" not in fm, "--deshacer tambien revierte las paginas migradas"
            print("F3. la copia ya migrada no repite la migracion, y --deshacer restaura las paginas -- OK")

        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp)
            (copia / "wiki/asignaturas").mkdir(parents=True)
            vault.escribir_pagina(copia / "wiki/asignaturas/B.md", {"tipo": "asignatura", "nombre_nuevo": "ya", "nombre_viejo": "resto"}, "\n\ncuerpo\n")
            vault.escribir_pagina(copia / "wiki/asignaturas/C.md", {"tipo": "otra", "x": 1}, "\n\n")
            ctx = migraciones.Contexto(copia, simular=False)
            assert migraciones.renombrar_campo(ctx, "wiki/asignaturas", "nombre_viejo", "nombre_nuevo") == 1
            fm, _ = vault.leer_pagina(copia / "wiki/asignaturas/B.md")
            assert fm == {"tipo": "asignatura", "nombre_nuevo": "ya"}, "si ya tiene el campo nuevo, no se pisa y el viejo se quita"
            assert migraciones.agregar_campo(ctx, "wiki/asignaturas", "z", 0, tipo="asignatura") == 1 and migraciones.agregar_campo(ctx, "wiki/asignaturas", "z", 0, tipo="asignatura") == 0
            assert migraciones.quitar_campo(ctx, "wiki/asignaturas", "z", tipo="otra") == 0
            assert migraciones.renombrar_campo(migraciones.Contexto(copia, True), "no-existe", "a", "b") == 0
    finally:
        migraciones.MIGRACIONES = original
    assert migraciones.MIGRACIONES is original, "la lista real de migraciones queda como estaba"
    print("F4. las primitivas son idempotentes, no pisan un campo que ya existe y respetan el filtro por `tipo` -- OK")

    # la migracion real de la 1.20: el temario pierde `presentacion_framework` (el tema .sty desaparecio)
    reales = {m.version: m for m in migraciones.MIGRACIONES}
    assert "1.20" in reales and [m.version for m in migraciones.pendientes("1.19", "1.21")] == ["1.20"] and migraciones.pendientes("1.20", "1.21") == []
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp)
        (copia / "generacion/temarios").mkdir(parents=True)
        (copia / "wiki/asignaturas").mkdir(parents=True)
        vault.escribir_pagina(copia / "generacion/temarios/A-semana01.md",
                              {"tipo": "temario", "semana": 1, "presentacion_framework": "abc123", "presentacion_estado": "generada"}, "\n\n# A\n")
        vault.escribir_pagina(copia / "generacion/temarios/A-semana02.md", {"tipo": "temario", "semana": 2}, "\n\n# B\n")
        vault.escribir_pagina(copia / "wiki/asignaturas/A.md", {"tipo": "asignatura", "presentacion_framework": "no es de un temario"}, "\n\n")
        ctx = migraciones.Contexto(copia, simular=True)
        reales["1.20"].aplicar(ctx)
        assert ctx.cambios == ["generacion/temarios/A-semana01.md: quita `presentacion_framework`"], ctx.cambios
        assert "presentacion_framework" in vault.leer_pagina(copia / "generacion/temarios/A-semana01.md")[0], "en seco no escribe"
        ctx = migraciones.Contexto(copia, simular=False)
        reales["1.20"].aplicar(ctx)
        fm, cuerpo = vault.leer_pagina(copia / "generacion/temarios/A-semana01.md")
        assert fm == {"tipo": "temario", "semana": 1, "presentacion_estado": "generada"} and cuerpo == "\n\n# A\n", (fm, cuerpo)
        assert vault.leer_pagina(copia / "wiki/asignaturas/A.md")[0]["presentacion_framework"] == "no es de un temario", "solo los temarios"
        otra = migraciones.Contexto(copia, simular=False)
        reales["1.20"].aplicar(otra)
        assert otra.cambios == [], "idempotente"
    print("F5. la migracion 1.20 quita `presentacion_framework` de los temarios (solo de ellos), en seco no escribe y no se repite -- OK")


# --- G. paquetes ZIP y delegar ---------------------------------------------------------------------------------------------


def probar_zip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v1 = plantilla(Path(tmp) / "v1")
        v2 = plantilla(Path(tmp) / "v2", "1.2", V2, quitar=("AGENTS.md",))
        completo = Path(tmp) / "v2.zip"
        n, parcial = ae.empaquetar(v2, completo)
        assert not parcial and n == len(ae.archivos_de(v2))
        with zipfile.ZipFile(completo) as z:
            nombres = z.namelist()
            assert "config/manifiesto.json" in nombres and "CLAUDE.md" in nombres and not any(n.startswith(("raw/", "wiki/asignaturas")) for n in nombres)
        copia = copia_de(v1, Path(tmp) / "copia")
        r = cli("--origen", str(completo), "--destino", str(copia), "--aplicar", "--sin-delegar")
        assert r.returncode == 0 and "APLICADO" in r.stdout and (copia / "src/nuevo_script.py").is_file(), (r.stdout, r.stderr)
        print("G1. `--empaquetar` arma un ZIP con la plantilla (sin contenido de instancia) y `--origen ZIP --aplicar` lo aplica -- OK")

        envuelto = Path(tmp) / "envuelto.zip"
        with zipfile.ZipFile(envuelto, "w") as z:
            for rel, ruta in ae.archivos_de(v2).items():
                z.write(ruta, "plantilla-main/" + rel)
            z.write(v2 / "config/manifiesto.json", "plantilla-main/config/manifiesto.json")
        copia2 = copia_de(v1, Path(tmp) / "copia2")
        assert ae.actualizar(ae.abrir_paquete(envuelto, Path(tmp) / "x"), copia2).version_nueva == "1.2"
        print("G2. un ZIP con una carpeta envolvente (como el de GitHub) se abre igual -- OK")

        parcial_zip = Path(tmp) / "parche.zip"
        n, parcial = ae.empaquetar(v2, parcial_zip, desde=v1)
        assert parcial
        with zipfile.ZipFile(parcial_zip) as z:
            nombres = set(z.namelist())
            manifiesto = json.loads(z.read("config/manifiesto.json"))
        assert nombres == {"CLAUDE.md", "README.md", "requirements.txt", "src/lint.py", "src/diseno_iub.py", "src/nuevo_script.py", "correlaciones/matriz-b.md",
                           ".obsidian/graph.json", "config/SCHEMA.md", "config/manifiesto.json"}, nombres
        assert "src/propio.py" not in nombres and "wiki/log.md" not in nombres, "un parche solo lleva lo que cambio"
        assert manifiesto["parcial"] is True and manifiesto["elimina"] == ["AGENTS.md"] and set(manifiesto["archivos"]) <= nombres
        copia3 = copia_de(v1, Path(tmp) / "copia3")
        informe = ae.actualizar(ae.abrir_paquete(parcial_zip, Path(tmp) / "p"), copia3)
        acciones = {e.ruta: e.accion for e in informe.entradas}
        assert informe.parcial and acciones["src/lint.py"] == "actualizar" and acciones["AGENTS.md"] == "obsoleto" and "src/propio.py" not in acciones
        assert not any(a == "obsoleto" for r, a in acciones.items() if r != "AGENTS.md"), "un parche no marca como obsoleto lo que simplemente no trae"
        print("G3. un parche (`--desde`) lleva solo lo que cambio, y sus `elimina` marcan lo obsoleto sin dar por obsoleto lo que no trae -- OK")

        malo = Path(tmp) / "malo.zip"
        with zipfile.ZipFile(malo, "w") as z:
            z.writestr("../fuera.txt", "x")
            z.writestr("CLAUDE.md", "x")
        assert "sale de su carpeta" in esperar(ValueError, ae.abrir_paquete, malo, Path(tmp) / "m") and not (Path(tmp) / "fuera.txt").exists()
        (Path(tmp) / "noes.zip").write_text("no soy un zip", encoding="utf-8")
        assert "no es una carpeta ni un ZIP" in esperar(FileNotFoundError, ae.abrir_paquete, Path(tmp) / "noes.zip", Path(tmp) / "n")
        assert "no parece la plantilla" in esperar(ValueError, ae.abrir_paquete, Path(tmp), Path(tmp) / "t")
        print("G4. un ZIP con rutas que salen de su carpeta se rechaza antes de extraer, y un archivo que no es ZIP ni una plantilla da un error claro -- OK")

        # delegar: el paquete trae otra version de este script y se ejecuta esa
        v3 = plantilla(Path(tmp) / "v3", "1.3", {"src/actualizar_estructura.py": SCRIPT.read_text(encoding="utf-8") + "\n# version del paquete\n",
                                                 "src/migraciones.py": (SRC / "migraciones.py").read_text(encoding="utf-8")})
        copia4 = copia_de(v1, Path(tmp) / "copia4")
        r = cli("--origen", str(v3), "--destino", str(copia4), "--sin-lint")
        assert r.returncode == 0 and "Plantilla 1.3" in r.stdout and "Prueba en seco" in r.stdout, (r.stdout, r.stderr)
        assert "AVISO: el paquete trae otra versión de este script" in r.stdout and "El paquete trae otra versión" not in r.stdout, "en seco solo se avisa: no se delega"
        r = cli("--origen", str(v3), "--destino", str(copia4), "--sin-lint", "--sin-delegar")
        assert r.returncode == 0 and "otra versión de este script" not in r.stdout and "El paquete trae otra versión" not in r.stdout
        r = cli("--destino", str(copia4), "--sin-lint", script=v3 / "src/actualizar_estructura.py")
        assert r.returncode == 0 and "Plantilla 1.3" in r.stdout and "El paquete trae" not in r.stdout, (r.stdout, r.stderr)
        print("G5. si el paquete trae otra version del script, en seco solo se avisa (`--aplicar` ejecuta la del paquete y `--sin-delegar` usa la local), y correrlo desde el paquete con --destino sirve para la primera vez -- OK")

        zip_v3 = Path(tmp) / "plantilla-1.3.zip"
        ae.empaquetar(v3, zip_v3)
        copia5 = copia_de(v1, Path(tmp) / "copia5")
        r = cli("--origen", str(zip_v3), "--destino", str(copia5), "--aplicar", "--sin-lint")
        assert r.returncode == 0 and "El paquete trae otra versión" in r.stdout and "APLICADO" in r.stdout, (r.stdout, r.stderr)
        assert ae.leer_manifiesto(copia5)["actualizaciones"][-1]["paquete"] == "plantilla-1.3.zip", "el historial nombra lo que dio el usuario, no la carpeta temporal"
        assert "paquete: plantilla-1.3.zip" in (copia5 / "wiki/log.md").read_text(encoding="utf-8") and "(plantilla-1.3.zip)" in r.stdout
        assert (copia5 / "src/actualizar_estructura.py").read_text(encoding="utf-8").endswith("# version del paquete\n"), "el script tambien se actualiza"
        print("G6. un ZIP cuyo script es otra version se extrae, se delega en el del paquete y el historial y el log nombran el ZIP (no la carpeta temporal) -- OK")


# --- H. sin manifiesto, versiones y errores -------------------------------------------------------------------------------


def probar_casos_limite() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        v1 = plantilla(Path(tmp) / "v1")
        v2 = plantilla(Path(tmp) / "v2", "1.2", V2)
        copia = copia_de(v1, Path(tmp) / "copia")
        (copia / "config/manifiesto.json").unlink()                       # una copia hecha antes de que existieran los manifiestos
        escribir(copia, "CLAUDE.md", V1["CLAUDE.md"] + "\nmia\n")
        informe = ae.actualizar(v2, copia)
        acciones = {e.ruta: e.accion for e in informe.entradas}
        assert acciones["CLAUDE.md"] == "sin_base" and acciones["src/lint.py"] == "sin_base", "sin manifiesto no se sabe que se edito: nada se pisa"
        assert any("no tiene config/manifiesto.json" in a for a in informe.avisos) and informe.version_actual == "1.1"
        informe = ae.actualizar(v2, copia, aplicar=True)
        assert (copia / "src/lint.py.nuevo").is_file() and (copia / "src/lint.py").read_text(encoding="utf-8") == V1["src/lint.py"]
        assert ae.leer_manifiesto(copia)["archivos"].get("AGENTS.md") and "src/lint.py" not in ae.leer_manifiesto(copia)["archivos"], "las iguales quedan como base; las diferentes, sin base"
        informe = ae.actualizar(v2, copia, aplicar=True, sobrescribir=True)
        assert (copia / "src/lint.py").read_text(encoding="utf-8") == V2["src/lint.py"]
        print("H1. una copia sin manifiesto (anterior a esta version) no pisa nada por su cuenta: todo lo distinto queda «sin base»; --sobrescribir lo reemplaza con respaldo -- OK")

        # con la plantilla con que se hizo la copia (--base) si se sabe que se edito: solo eso es conflicto
        sin_manifiesto = copia_de(v1, Path(tmp) / "copia-base")
        (sin_manifiesto / "config/manifiesto.json").unlink()
        escribir(sin_manifiesto, "CLAUDE.md", V1["CLAUDE.md"] + "\nmia\n")
        informe = ae.actualizar(v2, sin_manifiesto, base=v1)
        acciones = {e.ruta: e.accion for e in informe.entradas}
        assert acciones["CLAUDE.md"] == "conflicto" and acciones["src/lint.py"] == "actualizar" and acciones["README.md"] == "actualizar"
        assert any("de --base" in a for a in informe.avisos) and informe.version_actual == "1.1"
        zip_base = Path(tmp) / "base.zip"
        ae.empaquetar(v1, zip_base)
        r = cli("--origen", str(v2), "--destino", str(sin_manifiesto), "--base", str(zip_base), "--sin-delegar", "--aplicar")
        assert r.returncode == 0 and "APLICADO" in r.stdout, (r.stdout, r.stderr)
        assert (sin_manifiesto / "src/lint.py").read_text(encoding="utf-8") == V2["src/lint.py"] and (sin_manifiesto / "CLAUDE.md.nuevo").is_file()
        assert (sin_manifiesto / "CLAUDE.md").read_text(encoding="utf-8").endswith("mia\n")
        manifiesto = ae.leer_manifiesto(sin_manifiesto)
        assert manifiesto["version"] == "1.2" and manifiesto["archivos"]["CLAUDE.md"] == hashlib.sha256(V1["CLAUDE.md"].encode("utf-8")).hexdigest()
        print("H1b. con `--base` (la plantilla con que se hizo una copia sin manifiesto) solo lo que editaste es conflicto y lo demas se actualiza; el manifiesto queda creado -- OK")

        copia_v2 = copia_de(v2, Path(tmp) / "copia-v2")
        assert "no se retrocede" in esperar(ValueError, ae.actualizar, v1, copia_v2)
        assert ae.actualizar(v1, copia_v2, permitir_anterior=True).version_nueva == "1.1"
        assert "misma carpeta" in esperar(ValueError, ae.actualizar, v2, v2)
        assert "no parece una copia" in esperar(ValueError, ae.actualizar, v2, Path(tmp) / "nada")
        r = cli("--origen", str(v2), "--destino", str(v2), "--sin-delegar")
        assert r.returncode == 1 and "misma carpeta" in r.stdout and "Traceback" not in r.stderr
        r = cli("--origen", str(Path(tmp) / "no-existe"), "--destino", str(copia_v2))
        assert r.returncode == 1 and "no es una carpeta ni un ZIP" in r.stdout
        print("H2. no se retrocede de version (salvo --permitir-anterior), el origen y el destino no pueden ser el mismo, y un error de uso da un mensaje, no un traceback -- OK")

        r = cli("--origen", str(v2), "--destino", str(copia), "--json", "--sin-delegar")
        datos = json.loads(r.stdout)
        assert datos["version_nueva"] == "1.2" and {e["accion"] for e in datos["entradas"]} >= {"igual", "conservar"}
        r = cli("--origen", str(v2), "--destino", str(copia), "--detalle", "--sin-delegar")
        assert "Prueba en seco" in r.stdout and "conservar" in r.stdout and cli("--help").returncode == 0
        print("H3. la salida en JSON y con --detalle funcionan, y sin --aplicar el resultado dice que es una prueba en seco -- OK")


# --- I. la plantilla real ------------------------------------------------------------------------------------------------


def probar_plantilla_real() -> None:
    problemas = ae.desfases_del_manifiesto(RAIZ)
    assert not problemas, f"config/manifiesto.json esta viejo: `python src/actualizar_estructura.py --generar-manifiesto` ({problemas[:3]})"
    manifiesto = ae.leer_manifiesto(RAIZ)
    assert manifiesto["version"] == ae.version_de(RAIZ) and manifiesto["actualizaciones"] == [] and len(manifiesto["archivos"]) > 40
    for esencial in ("CLAUDE.md", "config/SCHEMA.md", "src/actualizar_estructura.py", "src/migraciones.py", "src/lint.py", "config/nuevo-cerebro.py"):
        assert esencial in manifiesto["archivos"], esencial
    assert not [r for r in manifiesto["archivos"] if r.startswith(("wiki/", "raw/", "generacion/", "memory_store/", ".obsidian/", "config/framework_iub/"))]
    print(f"I1. el manifiesto de la plantilla real esta al dia (version {manifiesto['version']}, {len(manifiesto['archivos'])} archivos) y no lleva contenido ni semillas -- OK")

    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "copia"
        r = subprocess.run([sys.executable, "-B", str(RAIZ / "config/nuevo-cerebro.py"), str(copia), "--nombre", "Programa de prueba"], capture_output=True, text=True,
                           encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
        assert r.returncode == 0, r.stdout
        assert ae.desfases_del_manifiesto(copia) == [], "una copia de nuevo-cerebro.py arranca con el manifiesto al dia (aunque cambie el titulo del README)"
        assert (copia / "README.md").read_text(encoding="utf-8").startswith("# Cerebro Docente — Programa de prueba")
        informe = ae.actualizar(RAIZ, copia)
        assert all(e.accion in ("igual", "conservar") for e in informe.entradas) and informe.version_actual == informe.version_nueva and not informe.migraciones
        print("I2. una copia hecha con nuevo-cerebro.py no difiere de la plantilla (ni por el titulo del README): la actualizacion no tiene nada que hacer -- OK")

        # una version nueva de verdad: la plantilla real con un script cambiado y otro nuevo, contra la copia (que edito otro archivo)
        nueva = Path(tmp) / "nueva"
        shutil.copytree(RAIZ, nueva, ignore=shutil.ignore_patterns("memory_store", "__pycache__", ".git"))
        (nueva / "src/lint.py").write_text((RAIZ / "src/lint.py").read_text(encoding="utf-8") + "\n\ndef _nueva_regla():\n    return 1\n", encoding="utf-8", newline="\n")
        (nueva / "src/script_nuevo.py").write_text("X = 1\n", encoding="utf-8", newline="\n")
        (nueva / "config/SCHEMA.md").write_text((RAIZ / "config/SCHEMA.md").read_text(encoding="utf-8").replace(f"version: {manifiesto['version']}", "version: 99.0", 1), encoding="utf-8", newline="\n")
        ae.escribir_manifiesto(nueva, ae.construir_manifiesto(nueva))
        (copia / "src/planeador.py").write_text((copia / "src/planeador.py").read_text(encoding="utf-8") + "\n# ajuste propio\n", encoding="utf-8", newline="\n")
        r = cli("--origen", str(nueva), "--destino", str(copia), "--aplicar", "--sin-delegar")
        assert r.returncode == 0 and "APLICADO" in r.stdout and "lint.py: exit 0" in r.stdout, (r.stdout, r.stderr)
        assert "_nueva_regla" in (copia / "src/lint.py").read_text(encoding="utf-8") and (copia / "src/script_nuevo.py").is_file()
        assert (copia / "src/planeador.py").read_text(encoding="utf-8").endswith("# ajuste propio\n"), "lo que editaste y la plantilla no cambio se queda"
        assert ae.leer_manifiesto(copia)["version"] == "99.0" and (copia / "wiki/log.md").read_text(encoding="utf-8").count("/actualizar-estructura") == 1
        assert not list(copia.rglob("__pycache__"))
        print("I3. una actualizacion de punta a punta sobre la plantilla real y una copia de nuevo-cerebro.py: lo nuevo llega, lo que editaste se queda, lint sano y el log anotado -- OK")


# --- J. seguridad y robustez (auditoria) ------------------------------------------------------------------------------------


def copia_real(base: Path, nombre: str) -> Path:
    """Una copia de la plantilla REAL hecha con config/nuevo-cerebro.py, en una carpeta temporal."""
    destino = base / nombre
    r = subprocess.run([sys.executable, "-B", str(RAIZ / "config/nuevo-cerebro.py"), str(destino), "--nombre", "Prueba"], capture_output=True, text=True,
                       encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stdout
    return destino


def paquete_real(base: Path, nombre: str, cambios: dict[str, str]) -> Path:
    """Una plantilla nueva (version 99.0): una copia de nuevo-cerebro.py con `cambios` {ruta: texto} encima y su manifiesto al dia."""
    paquete = copia_real(base, nombre)
    schema = paquete / "config/SCHEMA.md"
    schema.write_text(schema.read_text(encoding="utf-8").replace(f"version: {ae.version_de(RAIZ)}", "version: 99.0", 1), encoding="utf-8", newline="\n")
    for ruta, texto in cambios.items():
        escribir(paquete, ruta, texto)
    ae.escribir_manifiesto(paquete, ae.construir_manifiesto(paquete))
    return paquete


def probar_no_ejecutar_en_seco() -> None:
    marcador_en_el_script = (SRC / "actualizar_estructura.py").read_text(encoding="utf-8").replace(
        "from __future__ import annotations\n",
        "from __future__ import annotations\n\nimport os as _os\nif _os.environ.get('MARCADOR_PAQUETE'):\n    open(_os.environ['MARCADOR_PAQUETE'], 'w').write('ejecutado')\n", 1)
    assert "MARCADOR_PAQUETE" in marcador_en_el_script
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        paquete = paquete_real(base, "paquete", {"src/actualizar_estructura.py": marcador_en_el_script})
        sha = hashlib.sha256((paquete / "src/actualizar_estructura.py").read_bytes()).hexdigest()
        marca = base / "marca.txt"
        env = {"MARCADOR_PAQUETE": str(marca)}

        seca = copia_real(base, "seca")
        antes = arbol(seca)
        r = cli("--origen", str(paquete), "--destino", str(seca), "--sin-lint", env=env)
        assert r.returncode == 0 and "Prueba en seco" in r.stdout and "Plantilla 99.0" in r.stdout, (r.stdout, r.stderr)
        assert not marca.exists(), "una prueba en seco NO ejecuta el codigo del paquete"
        assert "AVISO: el paquete trae otra versión de este script" in r.stdout and sha in r.stdout, r.stdout
        assert "al aplicar se ejecutará la del paquete" in r.stdout and "--sin-delegar" in r.stdout and "El paquete trae otra versión" not in r.stdout
        assert arbol(seca) == antes and not (seca / "memory_store").exists()
        datos = json.loads(cli("--origen", str(paquete), "--destino", str(seca), "--json", env=env).stdout)
        assert sha in datos["avisos"][0] and not marca.exists()
        print("J1. sin --aplicar un paquete cuyo script es otra version NO se ejecuta (el marcador no aparece): el informe sale con el script local y avisa, con el SHA-256 del del paquete -- OK")

        local = copia_real(base, "local")
        r = cli("--origen", str(paquete), "--destino", str(local), "--aplicar", "--sin-delegar", "--sin-lint", env=env)
        assert r.returncode == 0 and "APLICADO" in r.stdout and not marca.exists(), (r.stdout, r.stderr)

        delegada = copia_real(base, "delegada")
        r = cli("--origen", str(paquete), "--destino", str(delegada), "--aplicar", "--sin-lint", env=env)
        assert r.returncode == 0 and "APLICADO" in r.stdout and marca.exists(), (r.stdout, r.stderr)
        assert "El paquete trae otra versión" in r.stdout and sha in r.stdout and "ejecuta su código" in r.stdout, r.stdout
        assert r.stdout.index(sha) < r.stdout.index("APLICADO"), "la huella se imprime ANTES de ejecutar el script del paquete"
        print("J2. con --aplicar si delega (el marcador aparece) e imprime antes el SHA-256 de lo que ejecuta; con --aplicar --sin-delegar usa el script local -- OK")


def probar_solo_rutas_de_la_plantilla() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        paquete = paquete_real(base, "paquete", {".claude/settings.json": '{"hooks": {"SessionStart": []}}', ".vscode/tasks.json": "{}",
                                                 ".github/workflows/x.yml": "on: push", "otra/cosa.txt": "x", "src/nuevo_ok.py": "X = 1\n"})
        escribir(paquete, ".git/HEAD", "ref: refs/heads/main")
        antes_del_paquete = arbol(paquete)
        copia = copia_real(base, "copia")
        informe = ae.actualizar(paquete, copia)
        acciones = {e.ruta: e.accion for e in informe.entradas}
        for ruta in (".claude/settings.json", ".vscode/tasks.json", ".github/workflows/x.yml", ".git/"):
            assert acciones[ruta] == "rechazado", (ruta, acciones.get(ruta))
        assert acciones["otra/cosa.txt"] == "desconocido" and acciones["src/nuevo_ok.py"] == "nuevo"
        assert ".git/HEAD" not in acciones, "de .git/ se lista la carpeta, no sus archivos"
        assert any("5 archivos que no son de la plantilla y NO se instalan" in a for a in informe.avisos), informe.avisos

        informe = ae.actualizar(paquete, copia, aplicar=True, sobrescribir=True, eliminar_obsoletos=True, correr_lint=False)
        assert informe.aplicado and (copia / "src/nuevo_ok.py").is_file()
        for ruta in (".claude", ".vscode", ".github", "otra", ".git"):
            assert not (copia / ruta).exists(), f"{ruta} no debio instalarse"
        assert not [r for r in ae.leer_manifiesto(copia)["archivos"] if r.startswith((".claude", ".vscode", ".github", "otra", ".git"))]
        assert arbol(paquete) == antes_del_paquete, "el paquete queda intacto"
        r = cli("--origen", str(paquete), "--destino", str(copia_real(base, "otra")), "--sin-delegar")
        for esperado in ("RECHAZADO   .claude/settings.json", "RECHAZADO   .vscode/tasks.json", "DESCONOCIDO otra/cosa.txt", "NO se instalan nunca", "desconfía"):
            assert esperado in r.stdout, (esperado, r.stdout)
        print("J3. un paquete con .claude/settings.json, .vscode/tasks.json, .github/, .git/ y otra/cosa.txt no instala ninguno (los lista como rechazados o desconocidos, con aviso) y un archivo nuevo de src/ si -- OK")

        # un paquete parcial no puede hacer borrar nada fuera de la plantilla con `elimina`
        fuera = base / "fuera.txt"
        fuera.write_text("no me borres", encoding="utf-8")
        escribir(copia, "otra/cosa.txt", "mia")
        manifiesto = ae.leer_manifiesto(paquete)
        manifiesto.update({"parcial": True, "elimina": ["src/../../fuera.txt", "../fuera.txt", ".claude/x", "otra/cosa.txt", "wiki/index.md"]})
        ae.escribir_manifiesto(paquete, manifiesto)
        informe = ae.actualizar(paquete, copia, aplicar=True, eliminar_obsoletos=True, correr_lint=False)
        assert fuera.read_text(encoding="utf-8") == "no me borres" and (copia / "otra/cosa.txt").read_text(encoding="utf-8") == "mia" and (copia / "wiki/index.md").is_file()
        assert not [e for e in informe.entradas if e.accion in ("obsoleto", "obsoleto_editado")], "`elimina` solo puede quitar archivos de la plantilla"
        print("J4. la lista `elimina` de un paquete parcial nunca borra rutas que salen de la copia ni archivos que no son de la plantilla -- OK")


def probar_obsidian() -> None:
    maliciosas = {".obsidian/plugins/x/main.js": "require('child_process').exec('calc')", ".obsidian/plugins/x/manifest.json": '{"id": "x"}',
                  ".obsidian/community-plugins.json": '["x"]', ".obsidian/snippets/x.css": "body {}", ".obsidian/hotkeys.json": "{}"}
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        paquete = paquete_real(base, "paquete", {**maliciosas, ".obsidian/app.json": '{"paquete": true}'})
        copia = copia_real(base, "copia")
        (copia / ".obsidian/graph.json").unlink()                                   # le falta: se crea desde el paquete
        escribir(copia, ".obsidian/app.json", '{"mio": true}')                     # ya existe y es suyo: no se pisa
        assert (paquete / ".obsidian/graph.json").is_file() and not (copia / ".obsidian/graph.json").exists()

        informe = ae.actualizar(paquete, copia)
        acciones = {e.ruta: e.accion for e in informe.entradas}
        assert all(acciones[r] == "rechazado" for r in maliciosas), {r: acciones.get(r) for r in maliciosas}
        assert acciones[".obsidian/graph.json"] == "nuevo" and acciones[".obsidian/app.json"] == "conservar"
        assert any(f"{len(maliciosas)} archivos que no son de la plantilla y NO se instalan" in a for a in informe.avisos), informe.avisos

        r = cli("--origen", str(paquete), "--destino", str(copia), "--aplicar", "--sin-lint", "--sin-delegar")
        assert r.returncode == 0 and "APLICADO" in r.stdout, (r.stdout, r.stderr)
        for ruta in maliciosas:
            assert not (copia / ruta).exists(), f"{ruta} no debio instalarse"
            assert f"RECHAZADO   {ruta}" in r.stdout, (ruta, r.stdout)
        assert not (copia / ".obsidian/plugins").exists() and not (copia / ".obsidian/snippets").exists()
        assert (copia / ".obsidian/graph.json").read_bytes() == (paquete / ".obsidian/graph.json").read_bytes(), "una semilla que falta se crea desde el paquete"
        assert (copia / ".obsidian/app.json").read_text(encoding="utf-8") == '{"mio": true}', "una que ya existe no se pisa"
        assert not [r for r in ae.leer_manifiesto(copia)["archivos"] if r.startswith(".obsidian")], "ni las semillas ni lo rechazado llevan huella"
        assert sorted(p.name for p in (copia / ".obsidian").iterdir()) == sorted(Path(n).name for n in ae.OBSIDIAN_SEMILLAS)
        print("J7. de .obsidian/ solo se crean los 5 .json de la plantilla que falten (sin pisar los existentes): un paquete con plugins/x/main.js, su manifest.json, "
              "community-plugins.json, snippets/x.css y hotkeys.json no instala ninguno y los lista como rechazados -- OK")


def probar_migraciones_sin_dependencias() -> None:
    def agregar(ctx: migraciones.Contexto) -> None:
        migraciones.agregar_campo(ctx, "wiki/asignaturas", "campo_nuevo", 1)

    original = migraciones.MIGRACIONES
    migraciones.MIGRACIONES = [migraciones.Migracion("50.0", "la asignatura declara campo_nuevo", agregar)]
    yaml_original = sys.modules.get("yaml")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            paquete = paquete_real(base, "paquete", {})
            copia = copia_real(base, "copia")
            escribir(copia, "wiki/asignaturas/A.md", "---\ntipo: asignatura\ncodigo: A\n---\n\n# A\n")
            antes = arbol(copia)

            sys.modules["yaml"] = None                       # como si la copia no tuviera PyYAML
            try:
                mensaje = esperar(ValueError, ae.actualizar, paquete, copia, aplicar=True, correr_lint=False)
                assert "hay migraciones pendientes y la copia no tiene las dependencias: `pip install -r requirements.txt` y repite" in mensaje, mensaje
                assert arbol(copia) == antes and not (copia / "memory_store").exists(), "no escribe nada"
                assert ae.leer_manifiesto(copia)["version"] == ae.version_de(RAIZ), "ni cambia el manifiesto: la migracion se repetira"
                seca = ae.actualizar(paquete, copia)
                assert seca.migraciones == [] and any("no tiene las dependencias" in a for a in seca.avisos) and not seca.aplicado
                assert "yaml" in esperar(ImportError, migraciones.Contexto(copia, True).leer, copia / "wiki/asignaturas/A.md"), \
                    "leer una pagina sin PyYAML es un ImportError que se propaga, no «una pagina sin frontmatter»"
            finally:
                if yaml_original is None:
                    sys.modules.pop("yaml", None)
                else:
                    sys.modules["yaml"] = yaml_original
            print("J5. con migraciones pendientes y sin PyYAML, `--aplicar` se detiene antes de escribir nada, pide `pip install -r requirements.txt` y no toca el manifiesto; en seco avisa y sigue -- OK")

            informe = ae.actualizar(paquete, copia, aplicar=True, correr_lint=False)
            fm, _ = vault.leer_pagina(copia / "wiki/asignaturas/A.md")
            assert informe.aplicado and fm["campo_nuevo"] == 1 and ae.leer_manifiesto(copia)["version"] == "99.0", "con PyYAML la migracion si se aplica"
            assert ae.actualizar(paquete, copia).migraciones == [], "y ya no se repite"

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            paquete = paquete_real(base, "paquete", {})
            copia = copia_real(base, "copia")
            escribir(copia, "wiki/asignaturas/A.md", "---\ntipo: asignatura\ncodigo: A\n---\n\n# A\n")
            escribir(copia, "wiki/asignaturas/roto.md", "---\ntipo: [sin cerrar\n---\n\ncuerpo\n")
            escribir(copia, "wiki/asignaturas/abierta.md", "---\ntipo: asignatura\nsin cierre de la cabecera\n")
            escribir(copia, "wiki/asignaturas/sin-cabecera.md", "# solo texto\n")
            (copia / "wiki/asignaturas/binaria.md").write_bytes(b"---\ntipo: \xff\xfe\n---\n")
            roto = {p: (copia / p).read_bytes() for p in ("wiki/asignaturas/roto.md", "wiki/asignaturas/abierta.md", "wiki/asignaturas/binaria.md", "wiki/asignaturas/sin-cabecera.md")}
            informe = ae.actualizar(paquete, copia)
            aviso = next(a for a in informe.avisos if a.startswith("migración 50.0"))
            assert "3 páginas no se pudieron leer y no se migrarán" in aviso and "roto.md: " in aviso and "abierta.md: " in aviso and "binaria.md: " in aviso, aviso
            assert "sin-cabecera" not in aviso, "una pagina sin frontmatter no es un error: no hay nada que migrarle"
            assert informe.migraciones[0]["cambios"] == ["wiki/asignaturas/A.md: agrega `campo_nuevo`"]
            ae.actualizar(paquete, copia, aplicar=True, correr_lint=False)
            assert {p: (copia / p).read_bytes() for p in roto} == roto, "las paginas que no se pudieron leer quedan intactas"
            assert vault.leer_pagina(copia / "wiki/asignaturas/A.md")[0]["campo_nuevo"] == 1
            print("J6. una pagina con YAML roto, sin cerrar o en otra codificacion no se migra pero se INFORMA (no se salta en silencio) y queda intacta; una sin cabecera no es un error -- OK")
    finally:
        migraciones.MIGRACIONES = original
        if yaml_original is not None:
            sys.modules["yaml"] = yaml_original


def main() -> None:
    probar_politicas()
    probar_manifiesto()
    probar_clasificacion()
    probar_aplicar()
    probar_opciones()
    probar_migraciones()
    probar_zip()
    probar_casos_limite()
    probar_plantilla_real()
    probar_no_ejecutar_en_seco()
    probar_solo_rutas_de_la_plantilla()
    probar_migraciones_sin_dependencias()
    probar_obsidian()
    print("TODO OK -- ACTUALIZAR-ESTRUCTURA lleva una plantilla nueva a una copia sin tocar su contenido, con respaldo, migraciones y manera de deshacer.")


if __name__ == "__main__":
    main()
