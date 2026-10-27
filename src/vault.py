"""Utilidades comunes de src/: lectura y escritura de paginas del vault, enlaces
[[...]], registro en wiki/log.md, carga de Asignaturas y RA desde wiki/, y el
UNICO punto de llamada a un LLM.

Todas las rutas son relativas a la raiz del vault: los scripts se ejecutan desde
alli (python src/<script>.py). Importar este modulo no exige ninguna clave ni
tener instalado `openai`: el cliente se crea la primera vez que se llama al LLM.

El proveedor de IA no esta atado a OpenAI: el SDK `openai` habla con cualquier servidor
compatible con su API (OpenAI, Azure OpenAI, OpenRouter, Ollama, LM Studio, vLLM...), y
todo se configura con variables de entorno (ver el README, "Configurar el modelo de IA"):
CEREBRO_MODELO, CEREBRO_BASE_URL, CEREBRO_API_KEY (o OPENAI_BASE_URL / OPENAI_API_KEY),
CEREBRO_SALIDA (estructurada | json | texto) y las de embeddings (CEREBRO_EMBEDDINGS_*).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from schema_extraccion import (
    Asignatura,
    ContenidoAprendizaje,
    CriterioEvaluacion,
    ResultadoAprendizajeModulo,
    TipoAbordaje,
)

WIKI = Path("wiki")
FUENTES = WIKI / "fuentes"
ASIGNATURAS = WIKI / "asignaturas"
RESULTADOS = WIKI / "resultados-aprendizaje"
COMPETENCIAS = WIKI / "competencias"
PLANEADOR = Path("generacion") / "planeador"
TEMARIOS = Path("generacion") / "temarios"
PRESENTACIONES = Path("generacion") / "presentaciones"
PROMPTS = Path(__file__).resolve().parent / "prompts"

MODELO_LLM = "gpt-4o"           # por defecto; CEREBRO_MODELO lo cambia
SALIDAS = ("estructurada", "json", "texto")
REINTENTOS_JSON = 2             # en los modos json/texto: cuantas veces se le pide al modelo corregir una respuesta invalida

_clients: dict[str, object] = {}


def consola_utf8() -> None:
    """La consola de Windows usa cp1252 por defecto: fuerza UTF-8 para que las tildes se vean bien."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


def _variable(*nombres: str) -> str | None:
    """El valor de la primera variable de entorno definida (y no vacia) de `nombres`."""
    return next((os.environ[n].strip() for n in nombres if os.environ.get(n, "").strip()), None)


def modelo_llm() -> str:
    return _variable("CEREBRO_MODELO") or MODELO_LLM


def modo_salida() -> str:
    modo = (_variable("CEREBRO_SALIDA") or "estructurada").lower()
    if modo not in SALIDAS:
        raise ValueError(f"CEREBRO_SALIDA={modo!r} no es valido: usa {', '.join(SALIDAS)}")
    return modo


def get_client(para: str = "llm"):
    """Cliente del SDK `openai` (compatible con cualquier servidor que hable su API). Perezoso a proposito: importar los
    modulos no debe exigir ninguna clave. `para="embeddings"` usa CEREBRO_EMBEDDINGS_BASE_URL / CEREBRO_EMBEDDINGS_API_KEY si
    estan definidas (p. ej. si el modelo de chat y el de embeddings son de proveedores distintos); si no, las de siempre.
    Sin clave pero con servidor propio (Ollama, LM Studio...) no hace falta clave."""
    if para not in _clients:
        from openai import OpenAI

        propios = ("CEREBRO_EMBEDDINGS_",) if para == "embeddings" else ()
        base_url = _variable(*(p + "BASE_URL" for p in propios), "CEREBRO_BASE_URL", "OPENAI_BASE_URL")
        clave = _variable(*(p + "API_KEY" for p in propios), "CEREBRO_API_KEY", "OPENAI_API_KEY")
        if clave is None:
            if base_url is None:
                raise RuntimeError(
                    "Falta la clave del proveedor de IA: define OPENAI_API_KEY (o CEREBRO_API_KEY). Con un servidor propio "
                    "(Ollama, LM Studio, vLLM...) define CEREBRO_BASE_URL y no hace falta clave.")
            clave = "sin-clave"
        _clients[para] = OpenAI(api_key=clave, base_url=base_url)
    return _clients[para]


def _extraer_json(texto: str):
    """El primer objeto JSON de la respuesta de un modelo (a veces lo rodea de texto o de ```)."""
    inicio = texto.find("{")
    if inicio < 0:
        raise ValueError("la respuesta no contiene ningun objeto JSON")
    profundidad, en_cadena, escape = 0, False, False
    for i in range(inicio, len(texto)):
        c = texto[i]
        if en_cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_cadena = False
            continue
        if c == '"':
            en_cadena = True
        elif c == "{":
            profundidad += 1
        elif c == "}":
            profundidad -= 1
            if profundidad == 0:
                return json.loads(texto[inicio:i + 1])
    raise ValueError("el JSON de la respuesta esta incompleto")


def _pedir_json(sistema: str | None, usuario: str, formato: type[BaseModel], con_response_format: bool):
    """Salida estructurada SIN depender del soporte del servidor: el esquema va en el prompt, la respuesta se valida aqui con
    Pydantic y, si no cumple, se le muestra el error al modelo y se le pide corregirla."""
    esquema = json.dumps(formato.model_json_schema(), ensure_ascii=False)
    instruccion = ("Responde UNICAMENTE con un objeto JSON valido que cumpla este esquema JSON, sin texto antes ni despues "
                   f"y sin bloques de codigo:\n{esquema}")
    mensajes = [{"role": "system", "content": f"{sistema}\n\n{instruccion}" if sistema else instruccion},
                {"role": "user", "content": usuario}]
    extra = {"response_format": {"type": "json_object"}} if con_response_format else {}
    ultimo_error = ""
    for _ in range(1 + REINTENTOS_JSON):
        respuesta = get_client().chat.completions.create(model=modelo_llm(), messages=mensajes, **extra)
        contenido = respuesta.choices[0].message.content or ""
        try:
            return formato.model_validate(_extraer_json(contenido))
        except ValueError as error:                    # JSON invalido o que no cumple el esquema (ValidationError es un ValueError)
            ultimo_error = str(error)
            mensajes += [{"role": "assistant", "content": contenido},
                         {"role": "user", "content": f"Tu respuesta no es valida: {ultimo_error[:600]}\n"
                                                      "Responde de nuevo SOLO con el objeto JSON corregido."}]
    raise ValueError(f"El modelo no devolvio un JSON valido para {formato.__name__} tras {1 + REINTENTOS_JSON} intentos: {ultimo_error[:300]}")


def pedir_estructurado(sistema: str | None, usuario: str, formato: type[BaseModel]):
    """Unico punto de llamada a un LLM con salida estructurada (los tests lo sustituyen). CEREBRO_SALIDA elige como se
    obtiene: `estructurada` (por defecto: la salida estructurada nativa de la API de OpenAI), `json` (modo JSON del servidor +
    validacion propia) o `texto` (para servidores sin ninguno de los dos: se pide el JSON en el prompt)."""
    modo = modo_salida()
    if modo != "estructurada":
        return _pedir_json(sistema, usuario, formato, con_response_format=(modo == "json"))
    mensajes = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": usuario}]
    completion = get_client().chat.completions.parse(model=modelo_llm(), messages=mensajes, response_format=formato)
    return completion.choices[0].message.parsed


def cargar_prompt(nombre: str) -> tuple[str, str]:
    """(sistema, plantilla_usuario) de un archivo de src/prompts/. El archivo tiene una
    seccion '## System' y una '## User (plantilla)' con la plantilla dentro de un bloque ```."""
    texto = (PROMPTS / nombre).read_text(encoding="utf-8")
    sistema = texto.split("## System", 1)[1].split("## User", 1)[0].strip()
    plantilla = texto.split("## User (plantilla)", 1)[1].split("```")[1].strip("\n")
    return sistema, plantilla


# ---------------------------------------------------------------------------
# Paginas, enlaces y log
# ---------------------------------------------------------------------------


def leer_pagina(ruta: Path) -> tuple[dict, str]:
    """(frontmatter, cuerpo) de una pagina Markdown; frontmatter {} si no tiene."""
    import yaml

    texto = ruta.read_text(encoding="utf-8")
    if texto.startswith("﻿"):
        texto = texto[1:]           # BOM: algunos editores lo agregan; si no se quita, "---" nunca se detecta
    if not texto.startswith("---"):
        return {}, texto
    _, crudo, cuerpo = texto.split("---", 2)
    return yaml.safe_load(crudo) or {}, cuerpo


def escribir_pagina(ruta: Path, frontmatter: dict, cuerpo: str) -> None:
    """Escribe una pagina con frontmatter YAML (UTF-8, saltos de linea LF)."""
    import yaml

    ruta.parent.mkdir(parents=True, exist_ok=True)
    crudo = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False, width=10_000)
    ruta.write_text(f"---\n{crudo}---{cuerpo}", encoding="utf-8", newline="\n")


_ENLACE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")


def _aplanar(valor):
    for v in valor:
        if isinstance(v, (list, tuple)):
            yield from _aplanar(v)
        else:
            yield v


def enlaces(valor) -> list[str]:
    """Destinos de los [[...]] de un valor de frontmatter (texto o lista). Ignora alias y #ancla."""
    if valor is None:
        return []
    if isinstance(valor, str):
        return [m.strip() for m in _ENLACE.findall(valor)]
    if isinstance(valor, (list, tuple)):
        destinos: list[str] = []
        for v in valor:
            if isinstance(v, (list, tuple)):  # [[X]] sin comillas: YAML lo lee como lista anidada
                destinos += [str(x).strip() for x in _aplanar(v)]
            else:
                destinos += enlaces(v)
        return destinos
    return []


def enlace(valor) -> str | None:
    destinos = enlaces(valor)
    return destinos[0] if destinos else None


def destino_pagina(destino: str) -> str:
    """'../correlaciones/matriz' -> 'matriz' (Obsidian resuelve por nombre de pagina)."""
    return destino.replace("\\", "/").rsplit("/", 1)[-1]


def hoy() -> str:
    return date.today().isoformat()


def anotar_log(titulo: str, lineas: list[str]) -> None:
    """Agrega una entrada AL FINAL de wiki/log.md (registro cronologico: la mas antigua primero)."""
    with open(WIKI / "log.md", "a", encoding="utf-8", newline="\n") as log:
        log.write(f"\n## [{hoy()}] {titulo}\n")
        for linea in lineas:
            log.write(f"- {linea}\n")


# ---------------------------------------------------------------------------
# De paginas de wiki/ a objetos del esquema
# ---------------------------------------------------------------------------


def _texto_programa(valor) -> str:
    destinos = enlaces(valor)
    if destinos:
        return ", ".join(destinos)
    if isinstance(valor, (list, tuple)):
        return ", ".join(str(v) for v in valor)
    return str(valor or "")


def asignatura_desde_frontmatter(fm: dict) -> Asignatura:
    fecha = fm.get("fecha_aprobacion")
    return Asignatura(
        codigo=str(fm.get("codigo")),
        nombre=fm.get("nombre"),
        programa=_texto_programa(fm.get("programa")),
        tipo_modulo=fm.get("tipo_modulo"),
        had_totales=fm.get("had_totales"),
        hp_totales=fm.get("hp_totales"),
        hti_totales=fm.get("hti_totales"),
        creditos=fm.get("creditos"),
        tipo_abordaje=TipoAbordaje(fm.get("tipo_abordaje")),
        aprendizajes_previos=fm.get("aprendizajes_previos"),
        docente_autor=fm.get("docente_autor"),
        fecha_aprobacion=None if fecha is None else str(fecha),
        estrategia_practica_marcada=bool(fm.get("estrategia_practica_marcada")),
        recurso_laboratorio_marcado=bool(fm.get("recurso_laboratorio_marcado")),
    )


def ra_desde_frontmatter(fm: dict) -> ResultadoAprendizajeModulo:
    return ResultadoAprendizajeModulo(
        codigo=str(fm.get("codigo")),
        enunciado=fm.get("enunciado"),
        horas=fm.get("horas"),
        tipo_abordaje=TipoAbordaje(fm.get("tipo_abordaje")),
        criterios_evaluacion=[CriterioEvaluacion(**ce) for ce in fm.get("criterios_evaluacion") or []],
        contenido=ContenidoAprendizaje(
            conceptual=fm.get("contenido_conceptual") or [],
            procedimental=fm.get("contenido_procedimental") or [],
            actitudinal=fm.get("contenido_actitudinal") or [],
        ),
    )


def cargar_asignatura(nombre_pagina: str) -> tuple[Asignatura, dict]:
    """(Asignatura, frontmatter) de wiki/asignaturas/{nombre_pagina}.md."""
    ruta = ASIGNATURAS / f"{nombre_pagina}.md"
    fm, _ = leer_pagina(ruta)
    try:
        return asignatura_desde_frontmatter(fm), fm
    except Exception as error:
        raise ValueError(f"{ruta.name}: {error}") from error


def cargar_ra(ruta: Path) -> tuple[ResultadoAprendizajeModulo, dict, str]:
    """(RA, frontmatter, nombre de la pagina de su asignatura) de una pagina de resultados-aprendizaje/."""
    fm, _ = leer_pagina(ruta)
    nombre_asignatura = enlace(fm.get("pertenece_a"))
    if not nombre_asignatura:
        raise ValueError(f"{ruta.name}: falta `pertenece_a`")
    try:
        return ra_desde_frontmatter(fm), fm, nombre_asignatura
    except Exception as error:
        raise ValueError(f"{ruta.name}: {error}") from error


def listar_ras() -> list[Path]:
    return sorted(RESULTADOS.glob("*.md"))


def localizar_asignatura(codigo: str) -> tuple[str, Asignatura, dict]:
    """(nombre de pagina, Asignatura, frontmatter) de la asignatura con ese `codigo`."""
    for ruta in sorted(ASIGNATURAS.glob("*.md")):
        fm, _ = leer_pagina(ruta)
        if str(fm.get("codigo")) == codigo:
            asignatura, fm = cargar_asignatura(ruta.stem)
            return ruta.stem, asignatura, fm
    raise FileNotFoundError(f"No hay ninguna asignatura con codigo {codigo} en {ASIGNATURAS}/")


def cargar_ras_de(fm_asignatura: dict) -> list[ResultadoAprendizajeModulo]:
    """Los RA que lista `resultados_aprendizaje` de una asignatura, en ese orden."""
    return [cargar_ra(RESULTADOS / f"{nombre}.md")[0] for nombre in enlaces(fm_asignatura.get("resultados_aprendizaje"))]
