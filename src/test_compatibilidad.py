"""Validacion de la ESTRUCTURA del cerebro: que la plantilla este limpia y lista para replicarse, y que no dependa de un
sistema operativo, de una version de Python o de un modelo de IA en concreto. No llama a ningun LLM.

Comprueba, sobre la plantilla real:
  A. las instrucciones para asistentes de IA (CLAUDE.md, AGENTS.md, GEMINI.md) y que no dependan de un modelo;
  B. que el arbol de carpetas de CLAUDE.md exista tal cual;
  C. que el codigo corra en Python 3.10+ (sintaxis y dependencias) y sin nada propio de un sistema operativo;
  D. que las llamadas al LLM pasen por un unico punto y que todos los esquemas se puedan enviar en un prompt;
  E. que la plantilla no lleve datos de una instancia (documentos, paginas, log, rutas personales, restos de Obsidian);
  F. que la documentacion coincida con el codigo (suites, scripts, variables de entorno, indice del wiki);
  G. que una copia que perdio las carpetas vacias (ZIP, git, Drive) arranque sana.

Uso (desde src/):  python test_compatibilidad.py
"""

import ast
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
sys.path.insert(0, str(SRC))

TEXTO = {".md", ".py", ".ps1", ".json", ".txt", ".yml", ".yaml", ".toml"}
NOMBRES_DE_MODELO = ("Claude Code", "anthropic", "ChatGPT", "GPT-4", "Gemini CLI")


def leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def archivos_de_texto():
    """Los archivos de texto de la plantilla, sin raw/ (contenido del usuario), memory_store/ ni el tema de terceros."""
    for p in RAIZ.rglob("*"):
        partes = p.relative_to(RAIZ).parts
        if p.is_file() and p.suffix.lower() in TEXTO and partes[0] not in ("raw", "memory_store") and partes[:2] != ("config", "framework_iub"):
            yield p


def scripts_python():
    return sorted([*SRC.glob("*.py"), *(RAIZ / "config").glob("*.py")])


# --- A. instrucciones para asistentes de IA -------------------------------------------------------------------------


def probar_instrucciones() -> None:
    for nombre in ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "README.md"):
        assert (RAIZ / nombre).is_file(), f"falta {nombre}"
    claude, agents, gemini = (leer(RAIZ / n) for n in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"))
    assert "CLAUDE.md" in agents and "CLAUDE.md" in gemini and "AGENTS.md" in gemini                  # los punteros llevan a las reglas
    for esencial in ("raw/", "solo lectura", "espa\u00f1ol", "--docente", "--programa", "CEREBRO_", "lint.py"):
        assert esencial in agents, f"AGENTS.md no menciona {esencial!r}: es el resumen para un asistente que solo lea ese archivo"
    for nombre, texto in (("CLAUDE.md", claude), ("AGENTS.md", agents), ("GEMINI.md", gemini)):
        for modelo in NOMBRES_DE_MODELO:
            assert modelo not in texto, f"{nombre} depende de {modelo}: las reglas deben valer para cualquier asistente"
    assert "cualquier asistente de IA" in claude
    print("A. CLAUDE.md, AGENTS.md y GEMINI.md existen, los dos punteros llevan a las reglas, AGENTS.md trae lo esencial y ninguno depende de un modelo -- OK")


# --- B. el arbol de carpetas de CLAUDE.md ---------------------------------------------------------------------------


def probar_arbol() -> None:
    bloque = re.search(r"## Estructura de directorios\s+```\n(.*?)```", leer(RAIZ / "CLAUDE.md"), re.S).group(1)
    pila: list[str] = []
    rutas: list[str] = []
    for linea in bloque.splitlines():
        m = re.match(r"^((?:\u2502   |    )*)[\u251c\u2514]\u2500\u2500 (\S+)", linea)
        if not m:
            continue
        nivel, nombre = len(m.group(1)) // 4, m.group(2)
        if nombre.startswith("..."):
            continue
        del pila[nivel:]
        pila.append(nombre.rstrip("/"))
        rutas.append("/".join(pila))
    faltan = [r for r in rutas if not (RAIZ / r).exists()]
    assert not faltan, f"el arbol de CLAUDE.md lista rutas que no existen: {faltan}"
    assert len(rutas) >= 25 and "generacion/presentaciones" in rutas and "config/framework_iub" in rutas and "AGENTS.md" in rutas, rutas
    print(f"B. las {len(rutas)} rutas del arbol de directorios de CLAUDE.md existen tal cual -- OK")


# --- C. Python 3.10+ y sin nada propio de un sistema operativo -------------------------------------------------------


def anidamientos_de_comillas(fuente: str) -> list[int]:
    """Lineas con un f-string que reutiliza dentro de una expresion la misma comilla que lo delimita: valido desde
    Python 3.12, error de sintaxis en 3.10 y 3.11."""
    if sys.version_info < (3, 12):
        return []                                        # aqui ese codigo ni siquiera se habria podido importar
    lineas, pila = [], []
    for tok in tokenize.generate_tokens(io.StringIO(fuente).readline):
        if tok.type == tokenize.FSTRING_START:
            if pila and tok.string.lstrip("rRfFbBuU").startswith(pila[-1]):
                lineas.append(tok.start[0])
            pila.append(tok.string.lstrip("rRfFbBuU"))
        elif tok.type == tokenize.FSTRING_END:
            pila.pop()
        elif tok.type == tokenize.STRING and pila and tok.string.lstrip("rRfFbBuU").startswith(pila[-1]):
            lineas.append(tok.start[0])
    return lineas


def barras_en_expresiones(fuente: str) -> list[int]:
    """Lineas con una barra invertida dentro de una expresion {..} de un f-string (`f"{'\\\\'.join(x)}"`): valido desde
    Python 3.12, error de sintaxis en 3.10 y 3.11. El texto literal del f-string (FSTRING_MIDDLE) si puede llevarla; un
    FSTRING_MIDDLE de un f-string anidado dentro de la expresion de otro, no."""
    if sys.version_info < (3, 12):
        return []
    lineas, llaves = [], []                              # por cada f-string abierto, cuantas llaves de expresion tiene abiertas
    for tok in tokenize.generate_tokens(io.StringIO(fuente).readline):
        if tok.type == tokenize.FSTRING_START:
            if any(llaves) and "\\" in tok.string:
                lineas.append(tok.start[0])
            llaves.append(0)
            continue
        if tok.type == tokenize.FSTRING_END:
            llaves.pop()
            continue
        if not llaves:
            continue
        if tok.type == tokenize.OP and tok.string == "{":
            llaves[-1] += 1
        elif tok.type == tokenize.OP and tok.string == "}":
            llaves[-1] -= 1
        elif "\\" in tok.string:
            dentro = any(llaves[:-1]) if tok.type == tokenize.FSTRING_MIDDLE else any(llaves)
            if dentro:
                lineas.append(tok.start[0])
    return sorted(set(lineas))


def probar_python() -> None:
    if sys.version_info >= (3, 12):                      # la deteccion misma: un caso malo y uno bueno
        assert barras_en_expresiones(r'''x = f"{'\\'.join(a)}"''' + "\n") == [1]
        assert barras_en_expresiones(r'''x = f"{f'\\n{b}'}"''' + "\n") == [1]
        assert barras_en_expresiones(r'''x = rf"\node {{{a}}} \\ {b:>3}"''' + "\n") == []
    scripts = scripts_python()
    assert len(scripts) >= 20
    for ruta in scripts:
        fuente = leer(ruta)
        arbol = ast.parse(fuente, feature_version=(3, 10))
        assert not anidamientos_de_comillas(fuente), f"{ruta.name}: f-string con la misma comilla dentro (solo Python 3.12+), lineas {anidamientos_de_comillas(fuente)}"
        assert not barras_en_expresiones(fuente), f"{ruta.name}: barra invertida dentro de una expresion de un f-string (solo Python 3.12+), lineas {barras_en_expresiones(fuente)}"
        for nodo in ast.walk(arbol):
            assert not isinstance(nodo, getattr(ast, "TypeAlias", ())), f"{ruta.name}: `type X = ...` es solo de Python 3.12+"
            assert not isinstance(nodo, getattr(ast, "TryStar", ())), f"{ruta.name}: `except*` es solo de Python 3.11+"
            assert not getattr(nodo, "type_params", None), f"{ruta.name}: genericos PEP 695, solo Python 3.12+"
        for prohibido in ("os.startfile", "powershell", "cmd.exe", "C:\\\\"):
            assert prohibido not in fuente or ruta.name.startswith("test_"), f"{ruta.name} usa {prohibido!r}: propio de Windows"
    print(f"C1. los {len(scripts)} scripts de src/ y config/ son validos en Python 3.10 (sintaxis, f-strings, sin nada propio de un sistema operativo) -- OK")

    stdlib, locales = set(sys.stdlib_module_names), {p.stem for p in SRC.glob("*.py")}
    externos: set[str] = set()
    for ruta in scripts:
        for nodo in ast.walk(ast.parse(leer(ruta))):
            if isinstance(nodo, ast.Import):
                externos |= {a.name.split(".")[0] for a in nodo.names}
            elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
                externos.add(nodo.module.split(".")[0])
    externos -= stdlib | locales
    requeridos = {re.split(r"[<>=!~ #]", linea.strip(), maxsplit=1)[0].lower() for linea in leer(RAIZ / "requirements.txt").splitlines()
                  if linea.strip() and not linea.lstrip().startswith("#")}
    nombres_pip = {"yaml": "pyyaml"}
    assert {nombres_pip.get(e, e) for e in externos} == requeridos, (externos, requeridos)         # ni falta ninguna, ni sobra
    print(f"C2. las dependencias externas del codigo ({', '.join(sorted(externos))}) son exactamente las de requirements.txt -- OK")


# --- D. un unico punto de llamada al LLM ---------------------------------------------------------------------------


def probar_llm() -> None:
    codigo = [p for p in SRC.glob("*.py") if not p.name.startswith("test_")]
    for ruta in codigo:
        arbol = ast.parse(leer(ruta))
        importa_openai = any((isinstance(n, ast.Import) and any(a.name.split(".")[0] == "openai" for a in n.names))
                             or (isinstance(n, ast.ImportFrom) and n.level == 0 and (n.module or "").split(".")[0] == "openai") for n in ast.walk(arbol))
        assert not importa_openai or ruta.name == "vault.py", f"{ruta.name} importa openai: solo vault.py puede hablar con el proveedor"
        assert "chat.completions" not in leer(ruta) or ruta.name == "vault.py", f"{ruta.name} llama al chat sin pasar por vault.pedir_estructurado"
    assert "embeddings.create" not in "".join(leer(p) for p in codigo if p.name not in ("correlate.py", "vault.py"))

    formatos = set()
    for ruta in codigo:
        for nodo in ast.walk(ast.parse(leer(ruta))):
            if (isinstance(nodo, ast.Call) and isinstance(nodo.func, (ast.Attribute, ast.Name))
                    and getattr(nodo.func, "attr", getattr(nodo.func, "id", "")) == "pedir_estructurado" and len(nodo.args) >= 3
                    and isinstance(nodo.args[2], ast.Name)):
                formatos.add((ruta.stem, nodo.args[2].id))
    resueltos = 0
    for modulo, nombre in sorted(formatos):
        clase = getattr(importlib.import_module(modulo), nombre, None)
        if clase is None or not hasattr(clase, "model_json_schema"):
            continue                                       # no es un esquema resoluble (p. ej. un parametro `formato`)
        json.dumps(clase.model_json_schema())               # lo que el modo json/texto le pone al modelo en el prompt
        resueltos += 1
    assert resueltos >= 5, formatos
    print(f"D. solo vault.py habla con el proveedor y los {resueltos} esquemas de salida se pueden serializar al prompt (modo json/texto) -- OK")


# --- E. la plantilla no lleva datos de una instancia ---------------------------------------------------------------


def probar_limpieza() -> None:
    assert not [p for p in (RAIZ / "raw").rglob("*") if p.is_file()], "raw/ debe estar vacia en la plantilla"
    paginas = {p.relative_to(RAIZ / "wiki").as_posix() for p in (RAIZ / "wiki").rglob("*") if p.is_file()}
    assert paginas == {"index.md", "log.md", "marco-pedagogico.md"}, paginas
    assert not [p for p in (RAIZ / "generacion").rglob("*") if p.is_file()], "generacion/ debe estar vacia en la plantilla"
    assert not (RAIZ / "memory_store").exists() and not list(RAIZ.rglob("__pycache__")) and not list(RAIZ.rglob("*.pyc"))
    assert not re.search(r"(?m)^## \[\d{4}-\d{2}-\d{2}\]", leer(RAIZ / "wiki" / "log.md")), "wiki/log.md tiene entradas"
    assert all((RAIZ / "config" / "framework_iub" / logo).is_file() for logo in ("logos/logo_iub_blanco.png", "logos/logo_iub_azul.png"))

    personales = [(re.compile(r"[A-Za-z]:\\+(Users|Mi unidad)"), "una ruta absoluta de un equipo"),
                  (re.compile(r"/(home|Users)/[A-Za-z]"), "una ruta absoluta de un equipo"),
                  (re.compile(r"\b[\w.+-]+@(gmail|hotmail|outlook|yahoo)\.\w+"), "un correo personal"),
                  (re.compile(r"Programa_Mecatronica"), "el nombre de una instancia previa")]
    for ruta in archivos_de_texto():
        if ruta.name.startswith("test_"):
            continue                                       # los tests inventan datos de prueba a proposito (y este cita los patrones)
        texto = leer(ruta)
        for patron, que in personales:
            hallado = patron.search(texto)
            assert not hallado, f"{ruta.relative_to(RAIZ)} lleva {que}: {hallado.group(0)!r}"

    espacio = RAIZ / ".obsidian" / "workspace.json"
    if espacio.exists():
        recientes = json.loads(leer(espacio)).get("lastOpenFiles", [])
        assert all((RAIZ / r).exists() for r in recientes), f".obsidian/workspace.json recuerda archivos que ya no existen: {recientes}"
    print("E. la plantilla no lleva datos de una instancia: raw/ y generacion/ vacias, wiki/ solo con su esqueleto, log sin entradas, sin rutas ni correos personales ni restos de Obsidian -- OK")

    for ruta in [*archivos_de_texto(), *(RAIZ / "config").glob("*")]:
        if not ruta.is_file() or ruta.suffix.lower() not in TEXTO:
            continue
        datos = ruta.read_bytes()
        texto = datos.decode("utf-8")                       # debe ser UTF-8
        assert not datos.startswith(b"\xef\xbb\xbf") and "\ufffd" not in texto, f"{ruta.relative_to(RAIZ)}: BOM o caracteres rotos"
        if ruta.suffix.lower() == ".ps1":
            assert texto.isascii(), f"{ruta.name} debe ser ASCII (Windows PowerShell 5.1 lee como ANSI un .ps1 sin BOM)"
    print("E2. todos los archivos de texto son UTF-8 sin BOM (y el .ps1, ASCII), asi que se leen igual en Windows, macOS y Linux -- OK")


# --- F. la documentacion coincide con el codigo --------------------------------------------------------------------


def probar_documentacion() -> None:
    readme = leer(RAIZ / "README.md")
    suites = len(list(SRC.glob("test_*.py")))
    palabra = re.search(r"\b(\w+) suites en `src/`", readme).group(1)
    numeros = {"Nueve": 9, "Diez": 10, "Once": 11, "Doce": 12, "Trece": 13, "Catorce": 14, "Quince": 15, "Dieciseis": 16, "Diecisiete": 17}
    assert numeros.get(palabra) == suites, f"el README dice {palabra} suites y hay {suites} en src/"

    for doc in ("README.md", "CLAUDE.md", "AGENTS.md", "config/SCHEMA.md"):
        for script in set(re.findall(r"python src/(\w+)\.py", leer(RAIZ / doc))):
            assert (SRC / f"{script}.py").is_file(), f"{doc} menciona src/{script}.py, que no existe"
    for script in set(re.findall(r"python config/([\w-]+\.py)", readme)):
        assert (RAIZ / "config" / script).is_file(), script

    en_codigo = set()
    for ruta in scripts_python():
        if not ruta.name.startswith("test_"):
            en_codigo |= set(re.findall(r"\bCEREBRO_[A-Z_]+", leer(ruta)))
    en_readme = set(re.findall(r"\bCEREBRO_[A-Z_]+", readme))
    prefijos = {v for v in en_codigo if v.endswith("_")}            # CEREBRO_EMBEDDINGS_ + BASE_URL / API_KEY: el codigo lo compone
    exactas = en_codigo - prefijos
    sin_documentar = {v for v in exactas if v not in en_readme} | {p for p in prefijos if not any(r.startswith(p) for r in en_readme)}
    inexistentes = {r for r in en_readme if r not in exactas and not any(r.startswith(p) for p in prefijos)}
    assert en_codigo and not sin_documentar and not inexistentes, f"sin documentar: {sin_documentar}; documentadas pero inexistentes: {inexistentes}"

    indice = leer(RAIZ / "wiki" / "index.md")
    for vista in (RAIZ / "correlaciones").glob("*.md"):
        assert vista.stem in indice, f"wiki/index.md no enlaza la vista correlaciones/{vista.name}"
    assert "generacion/presentaciones" in indice

    marca = leer(SRC / "diseno_iub.py") + leer(SRC / "presentaciones.py")    # la marca IUB fija que el README declara como convencion de la institucion
    for nombre in ("COLORES", "MARCA", "INSTITUCION", "PROGRAMA_POR_DEFECTO"):
        assert nombre in readme and f"{nombre} = " in marca, f"el README cita {nombre} como marca IUB, y ya no esta en src/diseno_iub.py ni src/presentaciones.py"
    assert "diseno_iub.py" in readme
    print(f"F. el README cuenta bien las {suites} suites, todo `python src/X.py` de las docs existe, las {len(en_codigo)} variables CEREBRO_* estan documentadas y wiki/index.md enlaza cada vista -- OK")


# --- G. una copia sin carpetas vacias arranca sana ------------------------------------------------------------------


def comando(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})


def probar_copia_sin_carpetas_vacias() -> None:
    """Un ZIP, un repositorio git o Google Drive pueden perder las carpetas vacias: los scripts no deben depender de ellas."""
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "copia"
        shutil.copytree(RAIZ, copia, ignore=shutil.ignore_patterns("memory_store", "__pycache__", ".git", "*.pyc"))
        for carpeta in sorted((p for p in copia.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            if not any(carpeta.iterdir()):
                carpeta.rmdir()
        assert not (copia / "wiki" / "asignaturas").exists() and not (copia / "raw").exists()        # de verdad se perdieron

        r = comando("src/lint.py", cwd=copia)
        assert r.returncode == 0 and "Sin hallazgos" in r.stdout, (r.stdout, r.stderr)
        r = comando("src/correlate.py", "--all", "--dry-run", cwd=copia)
        assert r.returncode == 0, (r.stdout, r.stderr)
        for script in ("analizar_cambios", "actualizar_estructura", "correlate", "correlate_bibliografia", "correlate_planeador", "ingest_manual", "planeador",
                       "presentaciones", "temario"):
            r = comando(f"src/{script}.py", "--help", cwd=copia)
            assert r.returncode == 0 and "usage" in r.stdout.lower(), (script, r.stdout, r.stderr)
        r = comando("src/analizar_cambios.py", cwd=copia)                                  # sin raw/, wiki/ ni generacion/: nada que analizar, no un error
        assert r.returncode == 0 and "Todo al día" in r.stdout and "Traceback" not in r.stderr, (r.stdout, r.stderr)
        assert not (copia / "memory_store").exists(), "analizar_cambios.py solo lee: no crea memory_store/ sin --confirmar"
        r = comando("src/actualizar_estructura.py", "--verificar-manifiesto", cwd=copia)   # la copia sin carpetas vacias sigue teniendo el manifiesto al dia
        assert r.returncode == 0 and "al día" in r.stdout, (r.stdout, r.stderr)
        r = comando("src/planeador.py", "NOEXISTE", "--sin-llm", cwd=copia)
        assert r.returncode != 0 and "Traceback" not in r.stderr, (r.stdout, r.stderr)                # falla con un mensaje, no con un traceback
    print("G. una copia sin carpetas vacias (ZIP, git, Drive): lint sano, correlate --dry-run, analizar_cambios y el --help de cada script funcionan, el manifiesto sigue al dia, y un error de uso da un mensaje, no un traceback -- OK")


def main() -> None:
    probar_instrucciones()
    probar_arbol()
    probar_python()
    probar_llm()
    probar_limpieza()
    probar_documentacion()
    probar_copia_sin_carpetas_vacias()
    print("TODO OK -- la estructura esta lista para replicarse y no depende de un sistema, una version de Python ni un modelo de IA en concreto.")


if __name__ == "__main__":
    main()
