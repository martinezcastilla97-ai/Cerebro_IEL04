"""Prueba de la creacion de copias limpias de la plantilla: config/nuevo-cerebro.py (Windows, macOS y Linux) y
config/nuevo-cerebro.ps1 (solo Windows; en otros sistemas se omite).

Copia la plantilla a una carpeta temporal, le agrega lo que una instancia en uso tendria y la copia NO debe llevarse
(memory_store/, __pycache__/, una entrada en wiki/log.md, archivos recientes de Obsidian), ejecuta el script real, y
comprueba que la copia arranca sana (pasa lint.py y una suite de pruebas propia).

Uso (desde src/):  python test_replica.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PLANTILLA = Path(__file__).resolve().parent.parent
ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}


def archivos(raiz: Path) -> set[str]:
    return {p.relative_to(raiz).as_posix() for p in raiz.rglob("*") if p.is_file()}


def con_python(origen: Path, destino: Path, nombre: str | None) -> subprocess.CompletedProcess:
    extra = ["--nombre", nombre] if nombre else []
    return subprocess.run([sys.executable, "-B", str(origen / "config" / "nuevo-cerebro.py"), str(destino), *extra],
                          capture_output=True, text=True, encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)


def con_powershell(origen: Path, destino: Path, nombre: str | None) -> subprocess.CompletedProcess:
    extra = ["-Nombre", nombre] if nombre else []
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(origen / "config" / "nuevo-cerebro.ps1"),
                           "-Destino", str(destino), *extra], capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)


def probar(script: str, crear) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        origen, destino = Path(tmp) / "origen", Path(tmp) / "destino"
        shutil.copytree(PLANTILLA, origen, ignore=shutil.ignore_patterns("memory_store", "__pycache__"))
        (origen / "memory_store" / "lancedb").mkdir(parents=True)
        (origen / "memory_store" / "lancedb" / "dato.bin").write_bytes(b"x")
        (origen / "src" / "__pycache__").mkdir()
        (origen / "src" / "__pycache__" / "a.pyc").write_bytes(b"x")
        with open(origen / "wiki" / "log.md", "a", encoding="utf-8", newline="\n") as log:
            log.write("\n## [2026-01-01] entrada de una instancia en uso\n- algo\n")
        espacio = origen / ".obsidian" / "workspace.json"
        espacio.write_text(re.sub(r'"lastOpenFiles":\s*\[[^\]]*\]', '"lastOpenFiles": ["wiki/paginas/de-otra-instancia.md", "raw/x.pdf"]',
                                  espacio.read_text(encoding="utf-8")), encoding="utf-8")

        r = crear(origen, destino, "Programa de prueba")
        assert r.returncode == 0 and "Copia creada" in r.stdout, (r.returncode, r.stdout, r.stderr)
        print(f"1. {script}: termina bien y avisa de los siguientes pasos -- OK")

        assert not (destino / "memory_store").exists() and not (destino / "src" / "__pycache__").exists()
        assert archivos(destino) == {a for a in archivos(origen) if not a.startswith("memory_store/") and "__pycache__" not in a}
        assert (destino / ".obsidian" / "core-plugins.json").exists() and (destino / "raw" / "curriculos").is_dir()
        print(f"2. {script}: la copia trae toda la plantilla (incluida .obsidian y las carpetas vacias) pero no memory_store ni __pycache__ -- OK")

        log = (destino / "wiki" / "log.md").read_text(encoding="utf-8")
        cabecera = re.split(r"(?m)^## \[\d{4}-\d{2}-\d{2}\]", (PLANTILLA / "wiki" / "log.md").read_text(encoding="utf-8"), maxsplit=1)[0].rstrip() + "\n"
        assert log == cabecera and log.count("```") % 2 == 0, log                                   # cabecera completa, sin bloques de codigo sin cerrar
        assert "entrada de una instancia en uso" in (origen / "wiki" / "log.md").read_text(encoding="utf-8")   # el origen no se toca
        print(f"3. {script}: el log de la copia queda vacio (cabecera y formato completos); el de la plantilla de origen no se modifica -- OK")

        primera = (destino / "README.md").read_text(encoding="utf-8").splitlines()[0]
        assert primera == "# Cerebro Docente — Programa de prueba", primera
        print(f"4. {script}: el titulo del README lleva el nombre de la copia -- OK")

        recientes = json.loads((destino / ".obsidian" / "workspace.json").read_text(encoding="utf-8"))["lastOpenFiles"]
        assert recientes == [] and "de-otra-instancia" in espacio.read_text(encoding="utf-8")          # la copia sale sin archivos recientes; el origen no se toca
        print(f"5. {script}: Obsidian no arrastra los archivos recientes de quien uso la plantilla (y workspace.json sigue siendo JSON valido) -- OK")

        r = crear(origen, destino, None)
        assert r.returncode != 0 and "ya existe" in (r.stdout + r.stderr), (r.stdout, r.stderr)
        print(f"6. {script}: no pisa una carpeta que ya existe: error claro -- OK")

        for args in (("src/lint.py",), ("src/test_lint.py",)):
            r = subprocess.run([sys.executable, "-B", *args], cwd=destino, capture_output=True, text=True, encoding="utf-8", env=ENTORNO, stdin=subprocess.DEVNULL)
            assert r.returncode == 0, (args, r.stdout[-800:], r.stderr[-800:])
        print(f"7. {script}: la copia arranca sana: pasa lint.py y su propia suite test_lint.py -- OK")


def probar_avisos() -> None:
    """Solo el script de Python (el de PowerShell no lo hace): avisa del contenido de instancia y de un destino dentro de la plantilla."""
    with tempfile.TemporaryDirectory() as tmp:
        origen = Path(tmp) / "origen"
        shutil.copytree(PLANTILLA, origen, ignore=shutil.ignore_patterns("memory_store", "__pycache__"))
        (origen / "raw" / "curriculos" / "modulo.md").write_text("contenido de una instancia\n", encoding="utf-8")
        (origen / "raw" / "curriculos" / ".gitkeep").write_text("", encoding="utf-8")            # un .gitkeep no cuenta como contenido
        r = con_python(origen, Path(tmp) / "copia", None)
        assert r.returncode == 0 and "AVISO" in r.stdout and "1 archivos" in r.stdout and "raw/curriculos/modulo.md" in r.stdout, (r.stdout, r.stderr)
        limpia = con_python(PLANTILLA, Path(tmp) / "copia-limpia", None)
        assert limpia.returncode == 0 and "AVISO" not in limpia.stdout, limpia.stdout             # la plantilla real, en limpio: sin avisos
        dentro = con_python(origen, origen / "copia-dentro", None)
        assert dentro.returncode == 1 and "dentro de la plantilla" in dentro.stdout, (dentro.stdout, dentro.stderr)
        assert not (origen / "copia-dentro").exists()
    print("8. nuevo-cerebro.py avisa si la carpeta de origen trae contenido de una instancia (sin contar .gitkeep), no avisa con la plantilla en limpio, y se niega a copiar dentro de si misma -- OK")


def main() -> None:
    probar("nuevo-cerebro.py", con_python)
    probar_avisos()
    if os.name == "nt":
        probar("nuevo-cerebro.ps1", con_powershell)
    else:
        print("SKIP -- nuevo-cerebro.ps1 es un script de PowerShell para Windows (nuevo-cerebro.py ya se probo)")
    print("TODO OK -- las copias limpias de la plantilla se crean bien y arrancan sanas.")


if __name__ == "__main__":
    main()
