#!/usr/bin/env python3
"""Crea una copia limpia de esta plantilla de cerebro docente (Windows, macOS y Linux; solo biblioteca estandar).

Copia toda la plantilla (incluida la carpeta oculta .obsidian y las carpetas vacias) a una carpeta nueva, sin lo que es
propio de una instancia en uso (memory_store, __pycache__, .git), deja el wiki/log.md de la copia vacio (solo la cabecera
y el formato de entradas) y, con --nombre, pone el nombre de la copia en el titulo del README. Avisa si la carpeta de
origen trae contenido de una instancia (documentos en raw/, paginas en wiki/, salida en generacion/): la copia lo
arrastraria, y una plantilla en limpio no lo tiene. La copia lleva config/manifiesto.json (la version y la huella de cada
archivo de la plantilla): con el sabe src/actualizar_estructura.py, mas adelante, que archivos editaste tu.

Uso:
    python config/nuevo-cerebro.py DESTINO [--nombre "Programa X"]

Equivale a config/nuevo-cerebro.ps1 (solo Windows).
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

EXCLUIR = ("memory_store", "__pycache__", ".git", "*.pyc")
ESQUELETO_WIKI = {"index.md", "log.md", "marco-pedagogico.md"}     # las unicas paginas que trae una plantilla en limpio
ENTRADA_DE_LOG = re.compile(r"(?m)^## \[\d{4}-\d{2}-\d{2}\]")      # solo cuenta un encabezado con fecha real: la cabecera trae "## [YYYY-MM-DD]"


def contenido_de_instancia(raiz: Path) -> list[str]:
    """Archivos que una plantilla en limpio NO trae: documentos en raw/, paginas de wiki/ (salvo el esqueleto) y salida
    en generacion/. (Los .gitkeep no cuentan: solo mantienen carpetas vacias.)"""
    encontrados: list[Path] = []
    for carpeta in ("raw", "generacion"):
        if (raiz / carpeta).is_dir():
            encontrados += [p for p in (raiz / carpeta).rglob("*") if p.is_file() and not p.name.startswith(".git")]
    if (raiz / "wiki").is_dir():
        encontrados += [p for p in (raiz / "wiki").rglob("*.md") if p.relative_to(raiz / "wiki").as_posix() not in ESQUELETO_WIKI]
    return sorted(p.relative_to(raiz).as_posix() for p in encontrados)


def vaciar_log(ruta: Path) -> None:
    """Deja solo la cabecera y el formato de entradas (todo lo anterior a la primera entrada con fecha)."""
    if not ruta.exists():
        return
    log = ruta.read_text(encoding="utf-8")
    entrada = ENTRADA_DE_LOG.search(log)
    if entrada:
        log = log[: entrada.start()].rstrip() + "\n"
    ruta.write_text(log, encoding="utf-8", newline="\n")


def vaciar_recientes(ruta: Path) -> None:
    """Obsidian recuerda los ultimos archivos abiertos en .obsidian/workspace.json: son de quien uso la plantilla, no de la copia."""
    if not ruta.exists():
        return
    texto = ruta.read_text(encoding="utf-8")
    ruta.write_text(re.sub(r'"lastOpenFiles":\s*\[[^\]]*\]', '"lastOpenFiles": []', texto), encoding="utf-8", newline="\n")


def crear_copia(origen: Path, destino: Path, nombre: str | None = None) -> list[str]:
    """Copia la plantilla de `origen` a `destino` (que no debe existir) y devuelve los avisos."""
    destino = destino.resolve()
    if destino.exists():
        raise FileExistsError(f"El destino ya existe: {destino}. Elige una carpeta nueva.")
    if destino == origen or origen in destino.parents:
        raise ValueError(f"El destino no puede estar dentro de la plantilla ({origen}): elige una carpeta fuera de ella.")
    avisos = []
    extras = contenido_de_instancia(origen)
    if extras:
        avisos.append(f"la carpeta de origen trae {len(extras)} archivos de contenido de una instancia (raw/, wiki/, generacion/), "
                      f"por ejemplo {extras[0]}: la copia los arrastrara. Una plantilla en limpio no los tiene.")
    shutil.copytree(origen, destino, ignore=shutil.ignore_patterns(*EXCLUIR))
    vaciar_log(destino / "wiki" / "log.md")
    vaciar_recientes(destino / ".obsidian" / "workspace.json")
    if nombre:
        readme = destino / "README.md"
        texto = readme.read_text(encoding="utf-8")
        readme.write_text(re.sub(r"^# Cerebro Docente", f"# Cerebro Docente — {nombre}", texto, count=1), encoding="utf-8", newline="\n")
    return avisos


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea una copia limpia de la plantilla de cerebro docente.")
    parser.add_argument("destino", type=Path, help="carpeta nueva (no debe existir)")
    parser.add_argument("--nombre", help="nombre de la copia, para el titulo del README")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        avisos = crear_copia(Path(__file__).resolve().parent.parent, args.destino, args.nombre)
    except (FileExistsError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1
    for aviso in avisos:
        print(f"AVISO: {aviso}")
    print(f"Copia creada en: {args.destino.resolve()}")
    print("Siguientes pasos:")
    print("  1. Abrir la carpeta como vault en Obsidian e instalar el plugin Dataview.")
    print("  2. pip install -r requirements.txt   y configurar el proveedor de IA (README, 'Configurar el modelo de IA').")
    print("  3. Si trabajas con un asistente de IA, abrirlo en esa carpeta: sus reglas estan en CLAUDE.md (AGENTS.md y GEMINI.md apuntan a el).")
    print("  4. Colocar los documentos en raw/ y seguir el flujo de trabajo del README.")
    print("  5. Mas adelante, para llevarle a esta copia una version nueva de la plantilla sin tocar su contenido:")
    print("     python src/actualizar_estructura.py --origen RUTA_DE_LA_PLANTILLA_NUEVA   (README, 'Actualizar una copia')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
