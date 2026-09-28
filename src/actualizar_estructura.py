"""ACTUALIZAR-ESTRUCTURA -- pone una copia (instancia) del cerebro al dia con una version nueva de la plantilla, sin tocar su contenido.

La plantilla evoluciona (scripts, prompts, matrices de correlaciones/, reglas de CLAUDE.md, esquema) y cada copia de `nuevo-cerebro.py`
se queda en la version con que se hizo. Este script lleva los cambios de una carpeta o un ZIP con la plantilla nueva (`--origen`) a una
copia (`--destino`, por defecto la carpeta actual), decidiendo archivo por archivo con tres politicas, segun la ruta:

  plantilla   codigo y reglas (src/, prompts, correlaciones/*.md, CLAUDE.md, README.md, config/SCHEMA.md, requirements.txt...): se
              actualizan. Si el archivo NO se ha editado en la copia (su huella es la del manifiesto de lo instalado) se reemplaza; si se
              edito y la plantilla tambien cambio es un CONFLICTO: se deja el tuyo y la version nueva queda al lado como `archivo.nuevo`.
  semilla     esqueletos que una copia hace suyos (wiki/index.md, log.md, marco-pedagogico.md, los 5 .json de configuracion de .obsidian/ que
              trae la plantilla —app, appearance, core-plugins, graph y workspace— y los logos de config/framework_iub/): se crean si faltan
              y NUNCA se pisan. Cualquier otra ruta bajo .obsidian/ (plugins/, snippets/, themes/, community-plugins.json, hotkeys.json...)
              se RECHAZA: es codigo o configuracion que Obsidian ejecuta al abrir el vault.
  instancia   raw/, wiki/, generacion/, memory_store/: contenido de la copia; jamas se toca (salvo una migracion, con respaldo).

Por omision solo MUESTRA lo que haria (prueba en seco); con `--aplicar` respalda cada archivo que va a cambiar en
memory_store/respaldos/estructura-AAAAMMDD-HHMMSS/ (`--deshacer` lo restaura), aplica los cambios y las MIGRACIONES de contenido de
src/migraciones.py (un campo que se renombra en las paginas, etc.), actualiza config/manifiesto.json (la version y la huella de cada
archivo instalado), deja una entrada en wiki/log.md y corre lint.py. Solo biblioteca estandar: corre aunque la version nueva pida
dependencias que la copia todavia no tiene (salvo las migraciones, que necesitan PyYAML y `vault`: si faltan y hay migraciones
pendientes, se detiene antes de escribir nada).

SEGURIDAD. Solo se instalan las rutas de la plantilla (src/**, correlaciones/*.md, tres archivos de config/, los .md de la raiz y
requirements.txt) y se crean las semillas que faltan; cualquier otra ruta del paquete es «desconocida» y no se instala nunca, y lo que
empieza por .claude/, .vscode/, .git/ o .github/ se rechaza siempre (pueden definir comandos que el asistente o el editor ejecutan
solos), igual que todo lo de .obsidian/ salvo sus 5 .json de configuracion (un plugin es JavaScript que Obsidian ejecuta al abrir
el vault; plugins/, snippets/, themes/ y community-plugins.json estan en RECHAZADAS aunque un dia se amplie esa lista). Si el paquete trae otra version de ESTE script, `--aplicar` ejecuta la del paquete (sus reglas y migraciones son las que
valen) y por eso EJECUTA SU CODIGO: aplica solo paquetes de la plantilla oficial. Sin `--aplicar` (la prueba en seco) nunca se ejecuta
codigo del paquete: se muestra el informe con este script y el SHA-256 del del paquete. `--sin-delegar` usa siempre el local.

Uso (desde la raiz de la copia):
    python src/actualizar_estructura.py --origen ../Cerebro_Docente            # que cambiaria (no escribe nada)
    python src/actualizar_estructura.py --origen plantilla-1.18.zip --detalle  # ademas, que cambia en cada archivo
    python src/actualizar_estructura.py --origen ../Cerebro_Docente --aplicar
    python src/actualizar_estructura.py --origen ... --aplicar --sobrescribir  # los conflictos tambien se reemplazan (con respaldo)
    python src/actualizar_estructura.py --origen ... --aplicar --conservar src/lint.py   # dar por buena tu version de ese archivo
    python src/actualizar_estructura.py --deshacer                             # restaura el respaldo de la ultima actualizacion
Primera vez en una copia hecha antes de este script (no tiene config/manifiesto.json), correrlo desde la plantilla nueva:
    python RUTA/src/actualizar_estructura.py --destino ../MiCopia              # todo lo que difiere queda «sin base»: no se pisa
    python RUTA/src/actualizar_estructura.py --destino ../MiCopia --base ../plantilla-vieja   # con la plantilla con que se hizo, solo lo que editaste es conflicto

Para quien mantiene la plantilla (cada version que se entrega):
    python src/actualizar_estructura.py --generar-manifiesto      # config/manifiesto.json: version y huella de cada archivo de la plantilla
    python src/actualizar_estructura.py --verificar-manifiesto    # falla si el manifiesto quedo viejo (la prueba de la plantilla lo exige)
    python src/actualizar_estructura.py --empaquetar plantilla-1.18.zip [--desde ../plantilla-1.17]   # con --desde, solo lo que cambio
"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

import migraciones

MANIFIESTO = "config/manifiesto.json"
FORMATO = 1
RESPALDOS = Path("memory_store") / "respaldos"
ESQUELETO_WIKI = ("wiki/index.md", "wiki/log.md", "wiki/marco-pedagogico.md")     # lo unico de wiki/ que trae una plantilla en limpio
CARPETAS_DE_INSTANCIA = ("raw", "wiki", "generacion", "memory_store", ".git")     # no se recorren: es contenido, no plantilla
RECHAZADAS = (".claude/", ".vscode/", ".git/", ".github/",   # nunca se instalan, aunque un dia estuvieran en la lista de lo que es plantilla
              ".obsidian/plugins/", ".obsidian/snippets/", ".obsidian/themes/", ".obsidian/community-plugins.json")    # codigo que Obsidian ejecuta al abrir el vault
OBSIDIAN_SEMILLAS = tuple(f".obsidian/{n}.json" for n in ("app", "appearance", "core-plugins", "graph", "workspace"))   # los unicos de .obsidian/ que trae la plantilla
TEXTO = {".md", ".py", ".ps1", ".json", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".sty", ".tex", ".gitkeep"}
SCRIPT = "src/actualizar_estructura.py"
MAX_NOMBRES = 6                        # cuantas funciones o secciones se nombran en el resumen de un archivo
MAX_TEXTO_RESUMEN = 600_000            # un archivo de texto mas grande no se compara linea a linea
FORMATO_PLAN = 2                       # el de los .plan.json de las presentaciones (presentaciones.FORMATO_PLAN; aqui sin importarlo)
LLAMADAS_POR_PRESENTACION = 9          # ~ una por parte del temario (la apertura y cada bloque): analizar_cambios.LLAMADAS_PRESENTACION


# ---------------------------------------------------------------------------
# Politicas y huellas
# ---------------------------------------------------------------------------


def _ruta_segura(ruta: str) -> bool:
    """Una ruta relativa, con /, sin `..`, sin rutas absolutas ni de unidad (`C:`) ni barras invertidas: nada que salga de la copia."""
    partes = ruta.split("/")
    return bool(ruta) and "\\" not in ruta and not ruta.startswith("/") and ":" not in partes[0] and all(p not in ("", ".", "..") for p in partes)


def _es_de_plantilla(ruta: str) -> bool:
    """Lo unico que se instala como plantilla: src/**, las vistas de correlaciones/, tres archivos de config/, los .md de la raiz y
    requirements.txt. Cualquier otra ruta es desconocida y no se instala nunca (una carpeta `.claude/` o `.vscode/` puede definir
    comandos que el asistente o el editor ejecutan solos)."""
    partes = ruta.split("/")
    if partes[0] == "src":
        return len(partes) > 1
    if partes[0] == "correlaciones":
        return len(partes) == 2 and ruta.endswith(".md")
    if ruta in ("config/SCHEMA.md", "config/nuevo-cerebro.py", "config/nuevo-cerebro.ps1"):
        return True
    return len(partes) == 1 and (ruta.endswith(".md") or ruta == "requirements.txt")


def politica(ruta: str) -> str:
    """plantilla | semilla | instancia | manifiesto | ignorar | desconocida | rechazada, segun la ruta (relativa a la raiz, con /).
    `desconocida` (no esta en la lista de lo que es plantilla) y `rechazada` (una ruta peligrosa o de `RECHAZADAS`) no se instalan nunca."""
    if not _ruta_segura(ruta) or ruta.startswith(RECHAZADAS):
        return "rechazada"
    partes = ruta.split("/")
    if "__pycache__" in partes or ruta.endswith(".pyc"):
        return "ignorar"
    if ruta == MANIFIESTO:
        return "manifiesto"
    if ruta in ESQUELETO_WIKI:
        return "semilla"
    if partes[0] in CARPETAS_DE_INSTANCIA:
        return "semilla" if partes[-1] == ".gitkeep" else "instancia"
    if partes[0] == ".obsidian":               # solo esos 5 archivos son semilla: un plugin, un snippet o un tema es codigo que Obsidian ejecuta
        return "semilla" if ruta in OBSIDIAN_SEMILLAS else "rechazada"
    if ruta.startswith("config/framework_iub/"):
        return "semilla"
    return "plantilla" if _es_de_plantilla(ruta) else "desconocida"


def huella(ruta: Path, relativa: str) -> str:
    """SHA-256 del archivo. Un texto se normaliza (saltos de linea, BOM) para que Windows, Git o Drive no lo cambien; el titulo de
    README.md ('# Cerebro Docente — Programa X', que pone nuevo-cerebro.py) tampoco cuenta."""
    datos = ruta.read_bytes()
    if Path(relativa).suffix.lower() in TEXTO:
        texto = datos.decode("utf-8", errors="replace").lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
        if relativa == "README.md":
            texto = re.sub(r"\A# Cerebro Docente[^\n]*", "# Cerebro Docente", texto)
        datos = texto.encode("utf-8")
    return hashlib.sha256(datos).hexdigest()


def archivos_de(raiz: Path) -> dict[str, Path]:
    """{ruta relativa: archivo} de lo que es plantilla o semilla en `raiz` (no recorre raw/, wiki/, generacion/ ni memory_store/)."""
    salida: dict[str, Path] = {}
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        base = Path(carpeta)
        en_raiz = base == raiz
        subcarpetas[:] = sorted(d for d in subcarpetas if d != "__pycache__" and not (en_raiz and d in CARPETAS_DE_INSTANCIA))
        for nombre in sorted(nombres):
            relativa = (base / nombre).relative_to(raiz).as_posix()
            if politica(relativa) in ("plantilla", "semilla"):
                salida[relativa] = base / nombre
    for relativa in ESQUELETO_WIKI:
        if (raiz / relativa).is_file():
            salida[relativa] = raiz / relativa
    return dict(sorted(salida.items()))


def no_instalables_de(raiz: Path) -> dict[str, str]:
    """{ruta: `desconocida` | `rechazada`} de lo que un paquete trae y NO se instala: lo que no esta en la lista de lo que es plantilla y
    lo que empieza por `.claude/`, `.vscode/`, `.git/` o `.github/` y todo lo de `.obsidian/` salvo sus 5 `.json` de configuracion (de `.git/` se
    lista la carpeta, no sus miles de archivos)."""
    salida: dict[str, str] = {}
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        base = Path(carpeta)
        en_raiz = base == raiz
        subcarpetas[:] = sorted(d for d in subcarpetas if d != "__pycache__" and not (en_raiz and d in CARPETAS_DE_INSTANCIA))
        for nombre in sorted(nombres):
            relativa = (base / nombre).relative_to(raiz).as_posix()
            if politica(relativa) in ("desconocida", "rechazada"):
                salida[relativa] = politica(relativa)
    if (raiz / ".git").exists():
        salida[".git/"] = "rechazada"
    return dict(sorted(salida.items()))


def version_de(raiz: Path) -> str | None:
    """La version de config/SCHEMA.md (`version: 1.16`), leida como texto: YAML leeria 1.10 como el numero 1.1."""
    try:
        m = re.search(r"(?m)^version:\s*([\d.]+)\s*$", (raiz / "config" / "SCHEMA.md").read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def leer_manifiesto(raiz: Path) -> dict | None:
    try:
        datos = json.loads((raiz / MANIFIESTO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return datos if isinstance(datos, dict) and isinstance(datos.get("archivos"), dict) else None


def construir_manifiesto(raiz: Path, previo: dict | None = None) -> dict:
    """El manifiesto de la plantilla en `raiz`: su version y la huella de cada archivo `plantilla` (los de `semilla` no llevan huella:
    la copia se los queda como esta)."""
    archivos = {rel: huella(ruta, rel) for rel, ruta in archivos_de(raiz).items() if politica(rel) == "plantilla"}
    version = version_de(raiz)
    if version is None:
        raise ValueError(f"{raiz}: no hay config/SCHEMA.md con `version:`; no parece la plantilla del cerebro")
    return {"formato": FORMATO, "version": version, "generado": date.today().isoformat(), "archivos": archivos,
            "actualizaciones": list((previo or {}).get("actualizaciones") or [])}


def escribir_manifiesto(raiz: Path, manifiesto: dict) -> None:
    ruta = raiz / MANIFIESTO
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def desfases_del_manifiesto(raiz: Path) -> list[str]:
    """Por que config/manifiesto.json de la plantilla en `raiz` no coincide con sus archivos (vacio: esta al dia)."""
    manifiesto = leer_manifiesto(raiz)
    if manifiesto is None:
        return [f"falta {MANIFIESTO} (o no se puede leer)"]
    actual = construir_manifiesto(raiz)
    problemas = []
    if manifiesto.get("version") != actual["version"]:
        problemas.append(f"la version del manifiesto es {manifiesto.get('version')} y la de config/SCHEMA.md {actual['version']}")
    for rel, h in actual["archivos"].items():
        if rel not in manifiesto["archivos"]:
            problemas.append(f"{rel}: no esta en el manifiesto")
        elif manifiesto["archivos"][rel] != h:
            problemas.append(f"{rel}: cambio despues de generar el manifiesto")
    problemas += [f"{rel}: esta en el manifiesto y ya no existe" for rel in manifiesto["archivos"] if rel not in actual["archivos"]]
    return problemas


# ---------------------------------------------------------------------------
# Que cambia en cada archivo (para no leer el archivo entero)
# ---------------------------------------------------------------------------


def _definiciones(fuente: str) -> dict[str, str]:
    """{nombre: codigo} de las funciones, clases y constantes del nivel superior de un modulo."""
    salida: dict[str, str] = {}
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            salida[nodo.name] = ast.get_source_segment(fuente, nodo) or ""
        elif isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            for objetivo in (nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]):
                if isinstance(objetivo, ast.Name):
                    salida[objetivo.id] = ast.get_source_segment(fuente, nodo) or ""
    return salida


def _secciones_md(texto: str) -> dict[str, str]:
    """{encabezado: texto} de las secciones `#`-`####` de un Markdown."""
    salida: dict[str, list[str]] = {"(inicio)": []}
    actual = "(inicio)"
    for linea in texto.splitlines():
        m = re.match(r"^#{1,4}\s+(.*?)\s*$", linea)
        if m:
            actual = m.group(1)
            salida.setdefault(actual, [])
        salida[actual].append(linea)
    return {k: "\n".join(v) for k, v in salida.items()}


def _nombres(lista: list[str]) -> str:
    return ", ".join(lista[:MAX_NOMBRES]) + (f" y {len(lista) - MAX_NOMBRES} más" if len(lista) > MAX_NOMBRES else "")


def resumen_de_cambios(ruta: str, viejo: str, nuevo: str) -> str:
    """Lo que cambia de `viejo` a `nuevo` en una linea: las lineas, y las funciones o secciones que se agregan, quitan o modifican."""
    if len(viejo) > MAX_TEXTO_RESUMEN or len(nuevo) > MAX_TEXTO_RESUMEN:
        return "archivo muy grande para compararlo"
    ops = difflib.SequenceMatcher(None, viejo.splitlines(), nuevo.splitlines()).get_opcodes()
    sumadas = sum(j2 - j1 for t, _i1, _i2, j1, j2 in ops if t in ("insert", "replace"))
    quitadas = sum(i2 - i1 for t, i1, i2, _j1, _j2 in ops if t in ("delete", "replace"))
    resumen = f"+{sumadas} −{quitadas} líneas"
    antes = despues = None
    try:
        if ruta.endswith(".py"):
            antes, despues = _definiciones(viejo), _definiciones(nuevo)
        elif ruta.endswith(".md"):
            antes, despues = _secciones_md(viejo), _secciones_md(nuevo)
    except SyntaxError:
        return resumen
    if antes is not None and despues is not None:
        for etiqueta, nombres in (("agrega", [n for n in despues if n not in antes]), ("quita", [n for n in antes if n not in despues]),
                                  ("modifica", [n for n in despues if n in antes and despues[n] != antes[n]])):
            if nombres:
                resumen += f"; {etiqueta}: {_nombres(nombres)}"
    return resumen


# ---------------------------------------------------------------------------
# Comparacion
# ---------------------------------------------------------------------------


@dataclass
class Entrada:
    ruta: str
    politica: str            # plantilla | semilla
    accion: str              # nuevo | actualizar | igual | propio | conflicto | sin_base | conservar | obsoleto | obsoleto_editado | desconocido | rechazado
    resumen: str = ""        # que cambia (actualizar, conflicto, sin_base)
    aplicada: bool = False   # ya quedo la version del paquete en la copia
    nuevo_al_lado: bool = False      # se dejo `archivo.nuevo`
    huella_paquete: str = ""


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="replace")


def clasificar(origen: Path, destino: Path, instalado: dict | None, parcial: bool, elimina: tuple[str, ...] = ()) -> list[Entrada]:
    """Que le pasa a cada archivo de la plantilla `origen` en la copia `destino`. `instalado`: el manifiesto de lo que la copia tiene
    instalado (su huella por archivo), o None si no hay (copia hecha antes de los manifiestos). `elimina`: los archivos que un paquete
    PARCIAL dice que la version nueva ya no tiene (uno completo lo deduce del manifiesto instalado)."""
    previos = instalado["archivos"] if instalado else None
    paquete = archivos_de(origen)
    entradas: list[Entrada] = []
    for rel, ruta_paquete in paquete.items():
        pol = politica(rel)
        ruta_destino = destino / rel
        if not ruta_destino.is_file():
            entradas.append(Entrada(rel, pol, "nuevo", huella_paquete=huella(ruta_paquete, rel) if pol == "plantilla" else ""))
            continue
        if pol == "semilla":
            entradas.append(Entrada(rel, pol, "conservar"))
            continue
        h_paquete, h_copia = huella(ruta_paquete, rel), huella(ruta_destino, rel)
        if h_paquete == h_copia:
            entradas.append(Entrada(rel, pol, "igual", huella_paquete=h_paquete))
            continue
        h_base = previos.get(rel) if previos is not None else None
        if previos is None:
            accion = "sin_base"
        elif h_base is None or (h_copia != h_base and h_paquete != h_base):
            accion = "conflicto"
        elif h_copia == h_base:
            accion = "actualizar"
        else:
            accion = "propio"
        resumen = ""
        if accion in ("actualizar", "conflicto", "sin_base") and Path(rel).suffix.lower() in TEXTO:
            resumen = resumen_de_cambios(rel, _leer(ruta_destino), _leer(ruta_paquete))
        entradas.append(Entrada(rel, pol, accion, resumen, huella_paquete=h_paquete))
    candidatos = sorted(previos) if previos is not None and not parcial else sorted(elimina)
    for rel in candidatos:
        if rel in paquete or politica(rel) != "plantilla" or not (destino / rel).is_file():
            continue
        h_base = (previos or {}).get(rel)
        editado = h_base is None or huella(destino / rel, rel) != h_base       # sin huella instalada no se sabe: se trata como editado
        entradas.append(Entrada(rel, "plantilla", "obsoleto_editado" if editado else "obsoleto"))
    for rel, motivo in no_instalables_de(origen).items():
        entradas.append(Entrada(rel, motivo, "rechazado" if motivo == "rechazada" else "desconocido"))
    return entradas


def presentaciones_por_plan(destino: Path) -> tuple[int, int]:
    """(cuantas presentaciones registradas en los temarios de la copia tienen su plan guardado, cuantas no). Sin YAML: solo busca
    la linea `presentacion_archivo:` (este script usa solo la biblioteca estandar). Cuenta con plan solo un .plan.json del formato
    actual (FORMATO_PLAN, con `partes` y `temario_hash`): los de un diseño anterior al 5 guardaban otra cosa y no se reutilizan, y uno
    que no se lee tampoco (presentaciones.py pediria todo de nuevo). Sin pydantic no se puede validar mas: un plan de otro temario o
    cuyas diapositivas no pasan la verificacion se cuenta con plan (lint L14 si lo distingue)."""
    con_plan = sin_plan = 0
    for ruta in sorted((destino / "generacion" / "temarios").glob("*.md")):
        m = re.search(r"(?m)^presentacion_archivo:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", _leer(ruta))
        if not m:
            continue
        tex = destino / m.group(1).strip()
        if _plan_legible(tex.with_name(tex.stem + ".plan.json")):
            con_plan += 1
        else:
            sin_plan += 1
    return con_plan, sin_plan


def _plan_legible(ruta: Path) -> bool:
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (isinstance(datos, dict) and datos.get("formato") == FORMATO_PLAN and isinstance(datos.get("partes"), dict)
            and "temario_hash" in datos)


def _llamadas(n: int) -> str:
    return f"{n} llamada" if n == 1 else f"{n} llamadas"


def efectos(entradas: list[Entrada], origen: Path, destino: Path, migradas: list[dict]) -> list[str]:
    """Lo que el usuario debe saber o hacer despues, y lo que NO hace falta rehacer (para no gastar de mas)."""
    tocados = {e.ruta for e in entradas if e.accion in ("nuevo", "actualizar", "conflicto", "sin_base")}
    texto: list[str] = []

    def cambia(*prefijos: str) -> list[str]:
        return sorted(r for r in tocados if any(r == p or r.startswith(p) for p in prefijos))

    if "requirements.txt" in tocados:
        texto.append("cambiaron las dependencias: `pip install -r requirements.txt`")
    diseno = "src/diseno_iub.py"
    if diseno in tocados and (origen / diseno).is_file():
        nuevo = re.search(r"(?m)^VERSION = (\d+)", _leer(origen / diseno))
        viejo = re.search(r"(?m)^VERSION = (\d+)", _leer(destino / diseno)) if (destino / diseno).is_file() else None
        if nuevo and (not viejo or viejo.group(1) != nuevo.group(1)):
            con_plan, sin_plan = presentaciones_por_plan(destino)
            texto.append(f"el diseño de las diapositivas pasó a la versión {nuevo.group(1)}: las presentaciones ya hechas se rehacen en la próxima corrida de "
                         "`python src/presentaciones.py CODIGO`; las que tienen su plan guardado en el formato actual (.plan.json) se rehacen sin LLM, "
                         f"pero las demás (hechas con un diseño anterior al 5, cuyo plan era de otro formato) cuestan ~{LLAMADAS_POR_PRESENTACION} "
                         "llamadas al modelo por temario (una por parte: la apertura y cada bloque)"
                         + (f" (en esta copia: {con_plan} con plan, sin LLM; {sin_plan} sin plan: ~{_llamadas(sin_plan * LLAMADAS_POR_PRESENTACION)})"
                            if con_plan or sin_plan else ""))
    if cambia("src/prompts/prompt-presentacion.md", "src/schema_presentacion.py"):
        texto.append("cambió cómo se piden las diapositivas al modelo: las presentaciones ya hechas siguen vigentes; `--replanificar` las rehace con el cambio "
                     f"(~{LLAMADAS_POR_PRESENTACION} llamadas por temario)")
    if cambia("src/temario.py", "src/schema_temario.py", "src/figuras.py", "src/pasajes.py", "src/prompts/prompt-temario"):
        texto.append("cambió la redacción de los temarios: los ya generados siguen vigentes y solo los nuevos usan el cambio; rehacerlos con `--forzar` cuesta "
                     "~10 llamadas por sesión, así que decídelo asignatura por asignatura")
    if cambia("src/schema_extraccion.py", "src/prompts/prompt-ingest", "src/ingest_manual.py"):
        texto.append("cambió la extracción de currículos o manuales: lo ya ingerido no se relee; la regla nueva vale desde el próximo documento")
    if cambia("src/correlate.py", "src/prompts/prompt-correlate.md", "src/schema_correlacion.py"):
        texto.append("cambió CORRELATE: las correlaciones guardadas siguen vigentes; `python src/correlate.py --all --dry-run` (sin LLM) muestra el gate actual")
    if cambia("src/lint.py"):
        texto.append("cambió LINT: corre `python src/lint.py` (lo hace este script al aplicar)")
    if cambia("CLAUDE.md", "config/SCHEMA.md", "AGENTS.md", "GEMINI.md"):
        texto.append("cambiaron las reglas para el asistente de IA (CLAUDE.md, SCHEMA.md): que las relea antes de la próxima operación")
    indice = _leer(destino / "wiki/index.md") if (destino / "wiki/index.md").is_file() else ""
    for rel in cambia("correlaciones/"):
        vista = Path(rel).stem
        if rel.endswith(".md") and vista not in indice and (destino / "wiki/index.md").is_file():
            texto.append(f"vista nueva `{rel}`: enlázala en wiki/index.md (sección «Generación y auditoría») con [[../correlaciones/{vista}]]")
    for e in entradas:
        if e.ruta.startswith("config/framework_iub/") and e.accion == "conservar" and (origen / e.ruta).is_file():
            if huella(origen / e.ruta, e.ruta) != huella(destino / e.ruta, e.ruta):
                texto.append("los logos institucionales del paquete difieren de los instalados: no se tocan (son de tu institución; para cambiarlos, "
                             "reemplaza los PNG de config/framework_iub/logos/). Desde el diseño 5 las presentaciones no los usan: la marca va como texto")
                break
    for m in migradas:
        texto.append(f"migración {m['version']}: {m['descripcion']} ({len(m['cambios'])} páginas)")
    texto.append("`python src/analizar_cambios.py` (sin LLM) dice si algo de lo generado quedó desactualizado")
    return texto


# ---------------------------------------------------------------------------
# El paquete: una carpeta o un ZIP
# ---------------------------------------------------------------------------


def _raiz_de_plantilla(carpeta: Path) -> Path:
    """La carpeta con CLAUDE.md: la propia, o la unica subcarpeta que la tiene (un ZIP de GitHub trae `repo-main/`)."""
    if (carpeta / "CLAUDE.md").is_file():
        return carpeta
    hijas = [d for d in carpeta.iterdir() if d.is_dir() and (d / "CLAUDE.md").is_file()]
    if len(hijas) == 1:
        return hijas[0]
    raise ValueError(f"{carpeta}: no parece la plantilla del cerebro (no tiene CLAUDE.md)")


def abrir_paquete(origen: Path, temporal: Path) -> Path:
    """La raiz de la plantilla que hay en `origen` (carpeta o ZIP; un ZIP se extrae en `temporal`, rechazando rutas que salgan de ahi)."""
    if origen.is_dir():
        raiz = _raiz_de_plantilla(origen)
    elif origen.is_file() and zipfile.is_zipfile(origen):
        base = temporal.resolve()
        with zipfile.ZipFile(origen) as z:
            for miembro in z.infolist():
                destino = (base / miembro.filename).resolve()
                if base != destino and base not in destino.parents:
                    raise ValueError(f"{origen.name}: el ZIP trae una ruta que sale de su carpeta ({miembro.filename}); no se abre")
            z.extractall(base)
        raiz = _raiz_de_plantilla(base)
    else:
        raise FileNotFoundError(f"{origen}: no es una carpeta ni un ZIP")
    if not (raiz / "src").is_dir() or version_de(raiz) is None:
        raise ValueError(f"{origen}: no parece la plantilla del cerebro (falta src/ o config/SCHEMA.md con `version:`)")
    return raiz


def _es_copia(destino: Path) -> bool:
    return (destino / "CLAUDE.md").is_file() and ((destino / "config" / "SCHEMA.md").is_file() or (destino / "wiki").is_dir())


# ---------------------------------------------------------------------------
# Respaldo
# ---------------------------------------------------------------------------


class Respaldo:
    """Guarda una copia de cada archivo antes de cambiarlo, en memory_store/respaldos/estructura-<fecha>/, con su lista de lo creado."""

    def __init__(self, destino: Path):
        self.destino = destino
        self.carpeta = destino / RESPALDOS / f"estructura-{datetime.now():%Y%m%d-%H%M%S}"
        self.guardados: list[str] = []
        self.creados: list[str] = []

    def guardar(self, ruta: Path) -> None:
        relativa = ruta.resolve().relative_to(self.destino.resolve()).as_posix()
        if relativa in self.guardados or not ruta.is_file():
            return
        copia = self.carpeta / relativa
        copia.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta, copia)
        self.guardados.append(relativa)

    def crear(self, ruta: Path) -> None:
        self.creados.append(ruta.resolve().relative_to(self.destino.resolve()).as_posix())

    def cerrar(self) -> Path | None:
        if not self.guardados and not self.creados:
            return None
        self.carpeta.mkdir(parents=True, exist_ok=True)
        (self.carpeta / "resumen.json").write_text(json.dumps({"guardados": self.guardados, "creados": self.creados}, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8", newline="\n")
        return self.carpeta


def deshacer(destino: Path, carpeta: Path | None = None) -> tuple[Path, int, int]:
    """Restaura el respaldo de la ultima actualizacion (o el de `carpeta`): devuelve (carpeta, restaurados, quitados)."""
    base = destino / RESPALDOS
    if carpeta is None:
        existentes = sorted(base.glob("estructura-*")) if base.is_dir() else []
        if not existentes:
            raise FileNotFoundError(f"no hay respaldos en {base.as_posix()}")
        carpeta = existentes[-1]
    resumen = json.loads((carpeta / "resumen.json").read_text(encoding="utf-8"))
    for rel in resumen["guardados"]:
        origen = carpeta / rel
        (destino / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino / rel)
    quitados = 0
    for rel in resumen["creados"]:                             # incluye las versiones nuevas que se dejaron al lado (`.nuevo`)
        if (destino / rel).is_file():
            (destino / rel).unlink()
            quitados += 1
    return carpeta, len(resumen["guardados"]), quitados


# ---------------------------------------------------------------------------
# La actualizacion
# ---------------------------------------------------------------------------


@dataclass
class Informe:
    origen: str
    destino: str
    version_actual: str | None
    version_nueva: str
    parcial: bool
    paquete: str = ""                                              # como lo llama quien lo dio: el nombre de la carpeta o del ZIP
    entradas: list[Entrada] = field(default_factory=list)
    migraciones: list[dict] = field(default_factory=list)          # [{version, descripcion, cambios}]
    efectos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    aplicado: bool = False
    respaldo: str | None = None
    lint: str | None = None


def _falta_para_migrar() -> str | None:
    """None si se pueden importar `yaml` y `vault` (lo que una migracion necesita para leer y escribir paginas); si no, cual falta."""
    for nombre in ("yaml", "vault"):
        try:
            importlib.import_module(nombre)
        except ImportError as error:
            return f"{nombre}: {error}"
    return None


def _copiar(origen: Path, destino: Path, relativa: str) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = origen.read_bytes()
    if relativa == "README.md" and destino.is_file():                # el titulo con el nombre de la copia se queda
        titulo = re.match(r"# Cerebro Docente[^\n]*", destino.read_text(encoding="utf-8", errors="replace").lstrip("﻿"))
        if titulo:
            datos = re.sub(rb"\A(?:\xef\xbb\xbf)?# Cerebro Docente[^\r\n]*", lambda _m: titulo.group(0).encode("utf-8"), datos, count=1)
    destino.write_bytes(datos)


def _anotar_log(destino: Path, titulo: str, lineas: list[str]) -> None:
    log = destino / "wiki" / "log.md"
    if not log.is_file():
        return
    with open(log, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n## [{date.today().isoformat()}] {titulo}\n")
        for linea in lineas:
            f.write(f"- {linea}\n")


def actualizar(origen: Path, destino: Path, aplicar: bool = False, sobrescribir: bool = False, eliminar_obsoletos: bool = False,
               conservar: tuple[str, ...] = (), permitir_anterior: bool = False, correr_lint: bool = True, nombre_paquete: str | None = None,
               base: Path | None = None) -> Informe:
    """Compara la plantilla `origen` (la raiz de una carpeta ya abierta) con la copia `destino` y, con `aplicar`, la actualiza.
    `nombre_paquete`: como se llama lo que dio el usuario (un ZIP se extrae en una carpeta temporal cuyo nombre no dice nada).
    `base`: la plantilla con que se hizo una copia SIN manifiesto (la version anterior, ya abierta): sus huellas hacen de lo instalado."""
    origen, destino = origen.resolve(), destino.resolve()
    if origen == destino:
        raise ValueError("el origen y el destino son la misma carpeta: indica --origen con la plantilla nueva")
    if not _es_copia(destino):
        raise ValueError(f"{destino}: no parece una copia del cerebro (no tiene CLAUDE.md y config/SCHEMA.md o wiki/)")
    instalado = leer_manifiesto(destino)
    tiene_manifiesto = instalado is not None
    if instalado is None and base is not None:
        instalado = construir_manifiesto(base.resolve())
    paquete = leer_manifiesto(origen)
    version_actual = (instalado or {}).get("version") or version_de(destino)
    version_nueva = version_de(origen)
    informe = Informe(str(origen), str(destino), version_actual, version_nueva, parcial=paquete is None or bool(paquete.get("parcial")),
                      paquete=nombre_paquete or origen.name)
    if version_actual and migraciones.version_tupla(version_nueva) < migraciones.version_tupla(version_actual) and not permitir_anterior:
        raise ValueError(f"el paquete es la versión {version_nueva} y la copia ya está en la {version_actual}: no se retrocede "
                         "(si de verdad quieres, --permitir-anterior)")
    if paquete is None:
        informe.avisos.append("el paquete no trae config/manifiesto.json: no se detectan archivos obsoletos ni se comprueba su integridad")
    elif not informe.parcial and (desfases := desfases_del_manifiesto(origen)):
        informe.avisos.append(f"el manifiesto del paquete no coincide con sus archivos ({desfases[0]}{' …' if len(desfases) > 1 else ''}): se usan las huellas reales")
    if instalado is None:
        informe.avisos.append("la copia no tiene config/manifiesto.json (se hizo antes de que existiera): no se sabe qué archivos editaste, así que "
                              "todo el que difiere queda como «sin base» y NO se pisa; con --sobrescribir se reemplaza (con respaldo), con --conservar se da por bueno el tuyo, "
                              "o con --base RUTA (la plantilla con que se hizo la copia) se comparan tus archivos contra ella y solo lo que editaste es conflicto")
    elif not tiene_manifiesto:
        informe.avisos.append(f"la copia no tiene config/manifiesto.json: se toma la plantilla {instalado.get('version')} de --base como lo que tiene instalado")
    if version_actual is None:
        informe.avisos.append("no se pudo leer la versión de la copia: no se corren migraciones")

    informe.entradas = clasificar(origen, destino, instalado, informe.parcial, tuple((paquete or {}).get("elimina") or ()))
    por_ruta = {e.ruta: e for e in informe.entradas}
    no_conservables = [c for c in conservar if c not in por_ruta or por_ruta[c].accion not in ("conflicto", "sin_base", "propio")]
    if no_conservables:
        raise ValueError(f"--conservar: {', '.join(no_conservables)} no es un archivo con conflicto, sin base o editado en la copia")
    no_instalados = [e.ruta for e in informe.entradas if e.accion in ("desconocido", "rechazado")]
    if no_instalados:
        informe.avisos.append(f"el paquete trae {len(no_instalados)} archivos que no son de la plantilla y NO se instalan (un paquete oficial no los trae): "
                              f"{_nombres(no_instalados)}")

    pendientes = migraciones.pendientes(version_actual, version_nueva)
    falta = _falta_para_migrar() if pendientes else None
    if falta and aplicar:                    # antes de escribir nada: una migracion sin PyYAML «no encontraria paginas» y se daria por hecha
        raise ValueError(f"hay migraciones pendientes y la copia no tiene las dependencias: `pip install -r requirements.txt` y repite ({falta})")
    if falta:
        informe.avisos.append(f"hay migraciones pendientes y la copia no tiene las dependencias ({falta}): no se pueden simular; "
                              "`pip install -r requirements.txt` antes de aplicar")
    for m in ([] if falta else pendientes):                                   # prueba en seco: que tocaria cada una
        ctx = migraciones.Contexto(destino, simular=True)
        m.aplicar(ctx)
        informe.migraciones.append({"version": m.version, "descripcion": m.descripcion, "cambios": ctx.cambios, "omitidas": ctx.omitidas})
        if ctx.omitidas:
            informe.avisos.append(f"migración {m.version}: {len(ctx.omitidas)} páginas no se pudieron leer y no se migrarán: {_nombres(ctx.omitidas)}")
    informe.efectos = efectos(informe.entradas, origen, destino, [m for m in informe.migraciones if m["cambios"]])
    if not aplicar:
        return informe

    respaldo = Respaldo(destino)
    hubo_cambios = False                     # algo se escribio de verdad (una segunda corrida sin novedades no deja rastro)
    for e in informe.entradas:
        ruta_paquete, ruta_copia = origen / e.ruta, destino / e.ruta
        if e.accion == "nuevo":
            _copiar(ruta_paquete, ruta_copia, e.ruta)
            respaldo.crear(ruta_copia)
            e.aplicada = hubo_cambios = True
        elif e.accion == "actualizar":
            respaldo.guardar(ruta_copia)
            _copiar(ruta_paquete, ruta_copia, e.ruta)
            e.aplicada = hubo_cambios = True
        elif e.accion in ("conflicto", "sin_base"):
            if e.ruta in conservar:
                pass
            elif sobrescribir:
                respaldo.guardar(ruta_copia)
                _copiar(ruta_paquete, ruta_copia, e.ruta)
                e.aplicada = hubo_cambios = True
            else:
                lado = ruta_copia.with_name(ruta_copia.name + ".nuevo")
                datos = ruta_paquete.read_bytes()
                existia = lado.is_file()
                if not existia or lado.read_bytes() != datos:
                    if existia:
                        respaldo.guardar(lado)
                    else:
                        respaldo.crear(lado)
                    lado.write_bytes(datos)
                    hubo_cambios = True
                e.nuevo_al_lado = True
        elif e.accion == "obsoleto" and eliminar_obsoletos:
            respaldo.guardar(ruta_copia)
            ruta_copia.unlink()
            e.aplicada = hubo_cambios = True
    for m in pendientes:
        ctx = migraciones.Contexto(destino, simular=False, respaldar=respaldo.guardar)
        m.aplicar(ctx)
        hubo_cambios = hubo_cambios or bool(ctx.cambios)

    hashes = dict((instalado or {}).get("archivos") or {})
    for e in informe.entradas:
        if e.politica != "plantilla":
            continue
        if e.accion in ("obsoleto", "obsoleto_editado"):
            if e.aplicada:
                hashes.pop(e.ruta, None)
        elif e.aplicada or e.accion == "igual" or e.ruta in conservar:
            hashes[e.ruta] = e.huella_paquete
        elif e.accion == "nuevo":
            hashes[e.ruta] = e.huella_paquete
    for c in conservar:                                                        # lo conservado ya no deja su `.nuevo` al lado
        (destino / (c + ".nuevo")).unlink(missing_ok=True)
    historial = list((instalado or {}).get("actualizaciones") or [])
    if hubo_cambios or version_actual != version_nueva:
        historial.append({"fecha": date.today().isoformat(), "desde": version_actual, "hasta": version_nueva, "paquete": informe.paquete})
    nuevo_manifiesto = {"formato": FORMATO, "version": version_nueva, "generado": date.today().isoformat(),
                        "archivos": dict(sorted(hashes.items())), "actualizaciones": historial}
    if not tiene_manifiesto or {k: v for k, v in instalado.items() if k not in ("generado", "actualizaciones")} != {k: v for k, v in nuevo_manifiesto.items() if k not in ("generado", "actualizaciones")}:
        respaldo.guardar(destino / MANIFIESTO)
        if not (destino / MANIFIESTO).is_file():
            respaldo.crear(destino / MANIFIESTO)
        escribir_manifiesto(destino, nuevo_manifiesto)
        hubo_cambios = True
    informe.aplicado = True
    carpeta = respaldo.cerrar()
    informe.respaldo = carpeta.as_posix() if carpeta else None

    if hubo_cambios:
        cuenta = {a: sum(1 for e in informe.entradas if e.accion == a) for a in ("nuevo", "actualizar", "conflicto", "sin_base", "obsoleto")}
        _anotar_log(destino, f"/actualizar-estructura {version_actual or '?'} → {version_nueva}", [
            f"paquete: {informe.paquete}; {cuenta['nuevo']} archivos nuevos, {cuenta['actualizar']} actualizados, "
            f"{cuenta['conflicto'] + cuenta['sin_base']} para revisar a mano, {sum(len(m['cambios']) for m in informe.migraciones)} páginas migradas",
            *([f"respaldo en {informe.respaldo}"] if informe.respaldo else [])])
    if correr_lint and (destino / "src" / "lint.py").is_file() and (destino / "wiki").is_dir():
        r = subprocess.run([sys.executable, "-B", "src/lint.py"], cwd=destino, capture_output=True, text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}, stdin=subprocess.DEVNULL)
        informe.lint = f"exit {r.returncode}: {(r.stdout.strip().splitlines() or [''])[-1]}"
    return informe


# ---------------------------------------------------------------------------
# Para quien mantiene la plantilla: empaquetar
# ---------------------------------------------------------------------------


def empaquetar(raiz: Path, salida: Path, desde: Path | None = None) -> tuple[int, bool]:
    """Un ZIP con la plantilla de `raiz` (archivos `plantilla` y `semilla` mas el manifiesto). Con `desde` (la version anterior: carpeta o
    ZIP) solo lleva lo que cambio o es nuevo, y el manifiesto dice `parcial` y lista lo que se quito. Devuelve (archivos, parcial)."""
    raiz = raiz.resolve()
    if problemas := desfases_del_manifiesto(raiz):
        raise ValueError(f"el manifiesto esta viejo ({problemas[0]}); regenéralo con --generar-manifiesto antes de empaquetar")
    manifiesto = leer_manifiesto(raiz)
    archivos = archivos_de(raiz)
    quitados: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        if desde is not None:
            base_raiz = abrir_paquete(desde, Path(tmp))
            base = {rel: (huella(ruta, rel) if politica(rel) == "plantilla" else "") for rel, ruta in archivos_de(base_raiz).items()}
            archivos = {rel: ruta for rel, ruta in archivos.items()
                        if rel not in base or (politica(rel) == "plantilla" and huella(ruta, rel) != base[rel])}
            quitados = sorted(rel for rel in base if rel not in archivos_de(raiz))
            manifiesto = {**manifiesto, "parcial": True, "elimina": quitados, "archivos": {r: h for r, h in manifiesto["archivos"].items() if r in archivos}}
        salida.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
            for rel, ruta in archivos.items():
                if rel != MANIFIESTO:
                    z.writestr(zipfile.ZipInfo(rel, (1980, 1, 1, 0, 0, 0)), ruta.read_bytes(), zipfile.ZIP_DEFLATED)
            z.writestr(zipfile.ZipInfo(MANIFIESTO, (1980, 1, 1, 0, 0, 0)), json.dumps(manifiesto, ensure_ascii=False, indent=1, sort_keys=True) + "\n", zipfile.ZIP_DEFLATED)
    return len(archivos), desde is not None


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------

_ETIQUETAS = {
    "nuevo": "NUEVO", "actualizar": "ACTUALIZAR", "conflicto": "CONFLICTO", "sin_base": "SIN BASE", "propio": "TUYO", "igual": "igual",
    "conservar": "conservar", "obsoleto": "OBSOLETO", "obsoleto_editado": "OBSOLETO*", "desconocido": "DESCONOCIDO", "rechazado": "RECHAZADO",
}


def imprimir(informe: Informe, detalle: bool = False) -> None:
    print(f"Plantilla {informe.version_nueva} ({informe.paquete}) → copia {informe.version_actual or 'sin versión conocida'} ({Path(informe.destino).name})"
          + ("  [paquete parcial]" if informe.parcial else ""))
    for aviso in informe.avisos:
        print(f"AVISO: {aviso}")
    grupos: dict[str, list[Entrada]] = {}
    for e in informe.entradas:
        grupos.setdefault(e.accion, []).append(e)
    orden = ["rechazado", "desconocido", "conflicto", "sin_base", "actualizar", "nuevo", "propio", "obsoleto", "obsoleto_editado", "igual", "conservar"]
    resumen = ", ".join(f"{len(grupos[a])} {_ETIQUETAS[a].lower()}" for a in orden if a in grupos)
    print(f"{len(informe.entradas)} archivos de la plantilla: {resumen}.")
    for accion in orden:
        lista = grupos.get(accion, [])
        if not lista or (accion in ("igual", "conservar") and not detalle) or (accion == "nuevo" and len(lista) > 12 and not detalle):
            if lista and accion == "nuevo":
                print(f"  NUEVO       {len(lista)} archivos (con --detalle, la lista)")
            continue
        for e in lista:
            marca = " (dejó `.nuevo` al lado)" if e.nuevo_al_lado else " (aplicado)" if e.aplicada else ""
            print(f"  {_ETIQUETAS[accion]:<11} {e.ruta}{'  — ' + e.resumen if e.resumen else ''}{marca}")
    if any(g in grupos for g in ("conflicto", "sin_base")):
        print("\nUn CONFLICTO (o SIN BASE) es un archivo que la copia tiene distinto y no se sabe si se editó a propósito: se deja el tuyo y la versión nueva "
              "queda como `archivo.nuevo` (el resumen de arriba compara el tuyo con el de la plantilla). Decide: --sobrescribir (con respaldo), "
              "--conservar RUTA (das por bueno el tuyo) o fusiónalos a mano.")
    if "obsoleto" in grupos:
        print("\nOBSOLETO: ya no está en la plantilla y no lo editaste; `--eliminar-obsoletos` lo quita (con respaldo). OBSOLETO*: lo editaste; se deja.")
    if any(g in grupos for g in ("desconocido", "rechazado")):
        print("\nRECHAZADO / DESCONOCIDO: rutas del paquete que no son de la plantilla, o de `.claude/`, `.vscode/`, `.git/`, `.github/` o `.obsidian/` "
              "(plugins, snippets, temas, hotkeys…; solo se crean sus 5 `.json` de configuración): NO se instalan nunca. "
              "Un paquete de la plantilla oficial no las trae: si no esperabas ninguna, desconfía de ese paquete.")
    for m in informe.migraciones:
        print(f"\nMigración {m['version']}: {m['descripcion']} — {len(m['cambios'])} páginas")
        for c in m["cambios"][:MAX_NOMBRES]:
            print(f"    {c}")
    if informe.efectos:
        print("\nDespués:")
        for texto in informe.efectos:
            print(f"  · {texto}")
    if informe.aplicado:
        print(f"\nAPLICADO. Respaldo: {informe.respaldo or '(nada que respaldar)'}" + ("  (`--deshacer` lo restaura)" if informe.respaldo else ""))
        if informe.lint:
            print(f"lint.py: {informe.lint}")
    else:
        print("\nPrueba en seco: no se escribió nada. Con `--aplicar` se respalda y se actualiza.")


def _consola_utf8() -> None:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")


def script_distinto_del_paquete(raiz_paquete: Path) -> str | None:
    """El SHA-256 (del archivo tal cual) del src/actualizar_estructura.py del paquete si es otra version que esta, o None si es la misma
    (o el paquete no lo trae)."""
    del_paquete = raiz_paquete / SCRIPT
    if not del_paquete.is_file() or huella(del_paquete, SCRIPT) == huella(Path(__file__), SCRIPT):
        return None
    return hashlib.sha256(del_paquete.read_bytes()).hexdigest()


def _delegar(argv: list[str], raiz_paquete: Path, nombre: str, sha256: str) -> int:
    """Ejecuta el script del paquete (sus reglas y migraciones son las que valen). SOLO con --aplicar: ejecutar codigo del paquete no
    es una prueba en seco, asi que quien solo mira un paquete nunca lo ejecuta. Imprime antes la huella de lo que va a ejecutar."""
    print(f"El paquete trae otra versión de {SCRIPT} (SHA-256 {sha256}): se ejecuta la del paquete, con lo que ejecuta su código "
          "(`--sin-delegar` usa la local). Aplica solo paquetes de la plantilla oficial.", flush=True)
    r = subprocess.run([sys.executable, "-B", str(raiz_paquete / SCRIPT), *argv, "--sin-delegar", "--origen", str(raiz_paquete), "--nombre-paquete", nombre],
                       stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return r.returncode


def main() -> int:
    _consola_utf8()
    p = argparse.ArgumentParser(description="Actualiza una copia del cerebro con una versión nueva de la plantilla, sin tocar su contenido.")
    p.add_argument("--origen", type=Path, help="la plantilla nueva: carpeta o ZIP (por omisión, la plantilla a la que pertenece este script)")
    p.add_argument("--destino", type=Path, default=Path("."), help="la copia a actualizar (por omisión, la carpeta actual)")
    p.add_argument("--base", type=Path, help="una copia sin manifiesto: la plantilla con que se hizo (carpeta o ZIP); así solo lo que editaste es conflicto")
    p.add_argument("--aplicar", action="store_true", help="escribe los cambios (sin esto solo los muestra)")
    p.add_argument("--sobrescribir", action="store_true", help="con --aplicar: reemplaza también los archivos en conflicto o sin base (con respaldo)")
    p.add_argument("--conservar", nargs="+", metavar="RUTA", default=[], help="con --aplicar: da por bueno tu archivo (no lo reemplaza ni lo vuelve a marcar)")
    p.add_argument("--eliminar-obsoletos", action="store_true", help="con --aplicar: quita los archivos que ya no están en la plantilla y no editaste")
    p.add_argument("--permitir-anterior", action="store_true", help="permite pasar a una versión anterior")
    p.add_argument("--detalle", action="store_true", help="lista todos los archivos, también los iguales y los conservados")
    p.add_argument("--json", action="store_true", help="el informe en JSON")
    p.add_argument("--sin-lint", action="store_true", help="no corre lint.py al terminar")
    p.add_argument("--sin-delegar", action="store_true", help="no ejecuta el script del paquete aunque sea otra versión")
    p.add_argument("--nombre-paquete", help=argparse.SUPPRESS)          # lo pone la delegacion: el nombre de lo que dio el usuario (un ZIP se extrae en una carpeta temporal)
    p.add_argument("--deshacer", action="store_true", help="restaura el respaldo de la última actualización")
    p.add_argument("--generar-manifiesto", action="store_true", help="(mantenedor) escribe config/manifiesto.json de la plantilla en --destino")
    p.add_argument("--verificar-manifiesto", action="store_true", help="(mantenedor) falla si config/manifiesto.json no coincide con los archivos")
    p.add_argument("--empaquetar", type=Path, metavar="ZIP", help="(mantenedor) un ZIP con la plantilla de --destino")
    p.add_argument("--desde", type=Path, help="con --empaquetar: la versión anterior (carpeta o ZIP); el ZIP lleva solo lo que cambió")
    args = p.parse_args()
    try:
        if args.generar_manifiesto:
            manifiesto = construir_manifiesto(args.destino.resolve(), leer_manifiesto(args.destino.resolve()))
            escribir_manifiesto(args.destino.resolve(), manifiesto)
            print(f"{MANIFIESTO}: versión {manifiesto['version']}, {len(manifiesto['archivos'])} archivos")
            return 0
        if args.verificar_manifiesto:
            problemas = desfases_del_manifiesto(args.destino.resolve())
            for problema in problemas:
                print(f"  {problema}")
            print("El manifiesto está al día." if not problemas else f"El manifiesto está viejo ({len(problemas)} diferencias): `--generar-manifiesto`.")
            return 1 if problemas else 0
        if args.empaquetar:
            n, parcial = empaquetar(args.destino, args.empaquetar, args.desde)
            print(f"{args.empaquetar}: {n} archivos" + (" (paquete parcial: solo lo que cambió respecto de " + args.desde.name + ")" if parcial else ""))
            return 0
        if args.deshacer:
            carpeta, restaurados, quitados = deshacer(args.destino.resolve())
            _anotar_log(args.destino.resolve(), "/actualizar-estructura deshacer", [f"restaurado {carpeta.name}: {restaurados} archivos, {quitados} quitados"])
            print(f"Restaurado {carpeta.name}: {restaurados} archivos devueltos a su estado anterior, {quitados} creados por la actualización quitados.")
            return 0
        origen = args.origen or Path(__file__).resolve().parent.parent
        nombre = args.nombre_paquete or origen.resolve().name
        with tempfile.TemporaryDirectory() as tmp:
            raiz = abrir_paquete(origen, Path(tmp) / "paquete")
            distinto = None
            if not args.sin_delegar and raiz.resolve() != Path(__file__).resolve().parent.parent:
                distinto = script_distinto_del_paquete(raiz)
            if distinto and args.aplicar:
                return _delegar(sys.argv[1:], raiz, nombre, distinto)
            raiz_base = abrir_paquete(args.base, Path(tmp) / "base") if args.base else None
            informe = actualizar(raiz, args.destino, args.aplicar, args.sobrescribir, args.eliminar_obsoletos, tuple(args.conservar),
                                 args.permitir_anterior, not args.sin_lint, nombre, raiz_base)
            if distinto:                     # sin --aplicar solo se mira: el script del paquete NO se ejecuta
                informe.avisos.insert(0, f"el paquete trae otra versión de este script (SHA-256 {distinto}); al aplicar se ejecutará la del paquete "
                                         "(sus migraciones son las que valen y ejecuta su código: aplica solo paquetes de la plantilla oficial); "
                                         "`--sin-delegar` usa la local")
    except (ValueError, FileNotFoundError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}")
        return 1
    if args.json:
        print(json.dumps(asdict(informe), ensure_ascii=False, indent=1))
    else:
        imprimir(informe, args.detalle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
