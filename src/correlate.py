"""/correlate -- cruza Resultados de Aprendizaje ya ingeridos contra Practicas
ya ingeridas y decide requiere_practica. Corre DESPUES de /ingest y solo lee
wiki/ -- nunca vuelve a tocar raw/.

Las Practicas viven en wiki/fuentes/: un manual de banco es UNA pagina (con la
etiqueta `equipo-laboratorio`) y sus experimentos van en su frontmatter, bajo
`practicas:`, una entrada por experimento con el esquema de `Practica`.
'Exp13' se repite entre manuales, asi que una Practica se identifica por el
par (fuente, codigo). El resultado se escribe en el RA como
`requiere_practica: [[fuente]]` + `practica_experimentos: [codigo]`.

Un RA con `correlacion_revisado_por_docente: true` es una decision humana: no se
reescribe (ver escribir_relacion); solo queda la propuesta automatica en el log.

Uso (desde la raiz del vault):
    python src/correlate.py --indexar                    # reconstruye el indice de practicas
    python src/correlate.py --all --dry-run              # solo el gate de cada RA (sin LLM, sin escribir)
    python src/correlate.py --all                        # correlaciona todos los RA
    python src/correlate.py --asignatura ABC01           # solo los RA de una asignatura
    python src/correlate.py --asignatura ABC01 --ra ABC01-RA2 ABC01-RA3   # solo esos RA (lo que cambio; ver analizar_cambios.py)

Pipeline por RA:
    1. GATE   -- score_ra (formula ya validada) decide si vale la pena buscar
    2. RECALL -- similitud vectorial (embeddings) sobre TODAS las Practicas
                 de wiki/fuentes/, sin importar el manual o el idioma de origen
                 (el store vectorial se reconstruye con --indexar)
    3. JUDGE  -- un juez LLM compara el RA contra cada candidato por concepto,
                 no por texto -- resuelve el salto español/inglés
    4. DECIDE -- confianza_final = score_ra * confianza_semantica
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import vault
from schema_correlacion import EstadoCorrelacion, JuicioCorrelacion, RelacionPropuesta
from schema_extraccion import Asignatura, CategoriaAccionCE, Practica, ResultadoAprendizajeModulo, TipoAbordaje


def _get_client():
    """Cliente de EMBEDDINGS. Perezoso a propósito: calcular_score_ra() no llama a ningún LLM y no
    debería exigir ninguna clave solo para poder importarse (ver vault.get_client)."""
    return vault.get_client("embeddings")


WIKI = vault.WIKI
FUENTES = vault.FUENTES
# CEREBRO_DB_PATH: para que el indice vectorial (que cambia con cada --indexar y no
# aporta nada a la wiki en si) no quede dentro de una carpeta sincronizada por Google
# Drive; por defecto, el de siempre. Ver README "Cómo crear una copia".
DB_PATH = Path(os.environ.get("CEREBRO_DB_PATH", "memory_store/lancedb"))
ETIQUETA_BANCO = "equipo-laboratorio"     # etiqueta de wiki/fuentes/ que marca un manual de banco
MODELO_EMBEDDINGS = "text-embedding-3-small"      # por defecto; CEREBRO_MODELO_EMBEDDINGS lo cambia
ARCHIVO_MODELO = "modelo-embeddings.txt"          # junto al indice: con que modelo se calcularon sus vectores


def modelo_embeddings() -> str:
    return os.environ.get("CEREBRO_MODELO_EMBEDDINGS", "").strip() or MODELO_EMBEDDINGS


PESO_ESTRUCTURAL = 0.5
PESO_CHECKLIST = 0.2
PESO_SEMANTICA = 0.3
UMBRAL_GATE = 0.40      # por debajo, ni se busca practica
UMBRAL_ACEPTAR = 0.70   # confianza_final -> aceptado
UMBRAL_REVISAR = 0.35   # confianza_final -> pendiente_revision; menos, se descarta

ACCIONES_QUE_CUENTAN = (CategoriaAccionCE.manipulacion_fisica, CategoriaAccionCE.cognitiva_experimental)


def calcular_score_ra(ra: ResultadoAprendizajeModulo, asignatura: Asignatura) -> float:
    """El pre-filtro, no la decisión final -- ver artifact para la tabla de bandas original."""
    señal_estructural = 1.0 if asignatura.hp_totales > 0 else 0.0
    señal_checklist = 1.0 if (asignatura.estrategia_practica_marcada or asignatura.recurso_laboratorio_marcado) else 0.0
    confianzas = [ce.confianza for ce in ra.criterios_evaluacion if ce.categoria_accion in ACCIONES_QUE_CUENTAN]
    señal_semantica = max(confianzas, default=0.0)
    return (
        PESO_ESTRUCTURAL * señal_estructural
        + PESO_CHECKLIST * señal_checklist
        + PESO_SEMANTICA * señal_semantica
    )


def ref_practica(fuente: str, codigo: str) -> str:
    """Identificador unico de una Practica: 'Exp13' se repite entre manuales."""
    return f"{fuente}#{codigo}"


def _enlace_practica(ref: str) -> str:
    """'fuente#Exp15' -> '[[fuente]] — Exp15' (enlace Obsidian a la fuente + experimento)."""
    fuente, codigo = ref.split("#", 1)
    return f"[[{fuente}]] — {codigo}"


def _fuentes_banco() -> list[tuple[str, dict]]:
    """(nombre, frontmatter) de cada pagina de wiki/fuentes/ etiquetada
    `equipo-laboratorio`. El nombre es el del archivo sin .md, el mismo de [[...]]."""
    banco = []
    for ruta in sorted(FUENTES.glob("*.md")):
        frontmatter, _ = vault.leer_pagina(ruta)
        etiquetas = frontmatter.get("etiquetas") or []
        if isinstance(etiquetas, str):
            etiquetas = [etiquetas]
        if ETIQUETA_BANCO in etiquetas:
            banco.append((ruta.stem, frontmatter))
    return banco


def listar_practicas() -> list[tuple[str, Practica]]:
    """Todas las Practicas de wiki/fuentes/, como pares (fuente, Practica)."""
    practicas: list[tuple[str, Practica]] = []
    vistos: set[tuple[str, str]] = set()
    for fuente, frontmatter in _fuentes_banco():
        for entrada in frontmatter.get("practicas") or []:
            practica = Practica.model_validate(entrada)
            if (fuente, practica.codigo) in vistos:
                raise ValueError(f"wiki/fuentes/{fuente}.md repite la practica {practica.codigo}")
            vistos.add((fuente, practica.codigo))
            practicas.append((fuente, practica))
    return practicas


def cargar_practica(fuente: str, codigo: str) -> Practica:
    """Lee UNA Practica del frontmatter de wiki/fuentes/{fuente}.md."""
    frontmatter, _ = vault.leer_pagina(FUENTES / f"{fuente}.md")
    for entrada in frontmatter.get("practicas") or []:
        if entrada.get("codigo") == codigo:
            return Practica.model_validate(entrada)
    raise KeyError(f"{codigo} no esta en 'practicas' de wiki/fuentes/{fuente}.md")


def texto_practica(practica: Practica) -> str:
    """Lo que se embebe de cada Practica. Los terminos_clave son el puente ES/EN."""
    return " ".join([practica.nombre_original, *practica.terminos_clave, practica.principio_resumen])


def indexar_practicas() -> int:
    """Reconstruye el store vectorial desde wiki/fuentes/ (tabla 'practicas':
    fuente, codigo, vector) y devuelve cuantas Practicas indexo. Correr despues
    de cada /ingest de un manual de banco."""
    import lancedb  # perezoso: solo el store vectorial lo necesita

    for fuente, frontmatter in _fuentes_banco():
        if not frontmatter.get("practicas"):
            print(f"AVISO: wiki/fuentes/{fuente}.md esta etiquetada '{ETIQUETA_BANCO}' "
                  "pero no tiene 'practicas' en el frontmatter -- no aporta candidatos.")

    practicas = listar_practicas()
    if not practicas:
        return 0
    respuesta = _get_client().embeddings.create(
        model=modelo_embeddings(), input=[texto_practica(p) for _, p in practicas]
    )
    filas = [
        {"fuente": fuente, "codigo": practica.codigo, "vector": item.embedding}
        for (fuente, practica), item in zip(practicas, respuesta.data)
    ]
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    lancedb.connect(str(DB_PATH)).create_table("practicas", data=filas, mode="overwrite")
    (DB_PATH.parent / ARCHIVO_MODELO).write_text(modelo_embeddings() + "\n", encoding="utf-8")
    return len(filas)


def recall_practicas_candidatas(ra: ResultadoAprendizajeModulo, k: int = 3) -> list[tuple[str, str]]:
    """Los k pares (fuente, codigo) mas cercanos al RA en el store vectorial. Sin ninguna Practica en wiki/fuentes/ (ningun
    manual de banco ingerido) no hay candidatos: el RA cierra sin_candidato, sin indice ni embeddings (--indexar no crea
    un indice vacio)."""
    if not listar_practicas():
        return []
    if not DB_PATH.exists():
        raise FileNotFoundError(f"No hay indice de practicas en {DB_PATH}: corre `python src/correlate.py --indexar`.")
    archivo = DB_PATH.parent / ARCHIVO_MODELO
    con_que = archivo.read_text(encoding="utf-8").strip() if archivo.exists() else None
    if con_que and con_que != modelo_embeddings():         # vectores de otro modelo: ni siquiera tienen el mismo largo
        raise RuntimeError(f"El indice de practicas se construyo con el modelo de embeddings {con_que!r} y ahora se usa "
                           f"{modelo_embeddings()!r}: sus vectores no son comparables. Corre `python src/correlate.py --indexar`.")
    import lancedb  # perezoso: solo esta función necesita el store vectorial

    db = lancedb.connect(str(DB_PATH))
    tabla = db.open_table("practicas")
    texto_ra = ra.enunciado + " " + " ".join(ra.contenido.conceptual)
    vector_ra = _get_client().embeddings.create(model=modelo_embeddings(), input=texto_ra).data[0].embedding
    return [(fila["fuente"], fila["codigo"]) for fila in tabla.search(vector_ra).limit(k).to_list()]


def juzgar_correlacion(ra: ResultadoAprendizajeModulo, practica: Practica, fuente: str) -> JuicioCorrelacion:
    sistema, plantilla = vault.cargar_prompt("prompt-correlate.md")
    usuario = plantilla.format(
        codigo_ra=ra.codigo,
        enunciado=ra.enunciado,
        conceptual=", ".join(ra.contenido.conceptual) or "(sin contenido conceptual)",
        criterios=", ".join(ce.texto for ce in ra.criterios_evaluacion) or "(sin criterios)",
        codigo_practica=practica.codigo,
        fuente=fuente,
        nombre_practica=practica.nombre_original,
        terminos_clave=", ".join(practica.terminos_clave),
        principio_resumen=practica.principio_resumen,
    )
    juicio = vault.pedir_estructurado(sistema, usuario, JuicioCorrelacion)
    # No se confia en que el LLM repita bien los codigos: se fijan aqui.
    return juicio.model_copy(update={"ra_codigo": ra.codigo, "practica_codigo": practica.codigo})


def correlacionar_ra(ra: ResultadoAprendizajeModulo, asignatura: Asignatura) -> RelacionPropuesta:
    score = calcular_score_ra(ra, asignatura)
    # Regla central de CLAUDE.md: una asignatura teorica JAMAS busca practica, sea cual
    # sea el score (score_RA es solo el pre-filtro de las teorico-practicas). El caso
    # teorico queda sin_candidato; `aplicacion_potencial` es opcional y lo llena el
    # docente a mano -- CORRELATE nunca lo escribe.
    if asignatura.tipo_abordaje == TipoAbordaje.teorica or score < UMBRAL_GATE:
        return RelacionPropuesta(ra_codigo=ra.codigo, practica_codigo=None, score_ra=score, estado=EstadoCorrelacion.sin_candidato)

    candidatos = recall_practicas_candidatas(ra)
    if not candidatos:
        return RelacionPropuesta(ra_codigo=ra.codigo, practica_codigo=None, score_ra=score, estado=EstadoCorrelacion.sin_candidato)

    juicios = [
        (fuente, juzgar_correlacion(ra, cargar_practica(fuente, codigo), fuente))
        for fuente, codigo in candidatos
    ]
    # 'confianza_semantica' mide CUANTO la practica satisface el RA, no la seguridad del
    # veredicto (ver prompt-correlate.md): un candidato con coincide=False y confianza
    # alta no debe poder ganar, asi que solo compiten los que el juez dice que SI coinciden.
    coincidentes = [(f, j) for f, j in juicios if j.coincide]
    if not coincidentes:
        return RelacionPropuesta(
            ra_codigo=ra.codigo, practica_codigo=None, score_ra=score, estado=EstadoCorrelacion.sin_candidato,
            candidatos_alternativos=[ref_practica(f, j.practica_codigo) for f, j in juicios],
        )

    fuente_mejor, mejor = max(coincidentes, key=lambda par: par[1].confianza_semantica)
    confianza_final = score * mejor.confianza_semantica

    if confianza_final >= UMBRAL_ACEPTAR:
        estado = EstadoCorrelacion.aceptado
    elif confianza_final >= UMBRAL_REVISAR:
        estado = EstadoCorrelacion.pendiente_revision
    else:
        estado = EstadoCorrelacion.sin_candidato
    hay_candidato = estado != EstadoCorrelacion.sin_candidato

    return RelacionPropuesta(
        ra_codigo=ra.codigo,
        practica_codigo=mejor.practica_codigo if hay_candidato else None,
        fuente=fuente_mejor if hay_candidato else None,
        score_ra=score,
        confianza_semantica=mejor.confianza_semantica,
        confianza_final=confianza_final,
        candidatos_alternativos=[ref_practica(f, j.practica_codigo) for f, j in juicios if j is not mejor],
        justificacion=mejor.justificacion if hay_candidato else None,
        estado=estado,
    )


def _describir_propuesta(relacion: RelacionPropuesta) -> str:
    if not relacion.practica_codigo:
        return f"{relacion.estado.value}, sin práctica"
    return (f"{relacion.estado.value}, {relacion.practica_codigo} en {relacion.fuente} "
            f"(confianza {relacion.confianza_final:.2f})")


def escribir_relacion(relacion: RelacionPropuesta) -> bool:
    """Actualiza el frontmatter del RA y devuelve True. matriz-ra-practica.md NO
    se toca aquí -- es una vista Dataview que lee ese frontmatter en vivo desde
    Obsidian.

    Un RA con `correlacion_revisado_por_docente: true` guarda una decisión
    humana: NO se reescribe (ni su estado, ni su práctica, ni su formato) y la
    función devuelve False. Solo queda en wiki/log.md la propuesta automática,
    por si conviene revisarla -- p. ej. porque se cargó un manual nuevo.

    Si no hay candidato, se borra el rastro de una corrida anterior (requiere_practica,
    practica_experimentos, semantica, confianza, justificacion): el RA no debe seguir
    apuntando a una práctica que ya no se propone."""
    if relacion.practica_codigo and not relacion.fuente:
        raise ValueError(f"{relacion.ra_codigo}: una practica ({relacion.practica_codigo}) exige su fuente en wiki/fuentes/")

    ruta = vault.RESULTADOS / f"{relacion.ra_codigo}.md"
    frontmatter, cuerpo = vault.leer_pagina(ruta)

    if frontmatter.get("correlacion_revisado_por_docente"):
        vault.anotar_log(f"/correlate {relacion.ra_codigo} (omitido)", [
            f"decisión del docente respetada: correlacion_estado = {frontmatter.get('correlacion_estado')}",
            f"propuesta automática (no aplicada): {_describir_propuesta(relacion)}",
        ])
        return False

    frontmatter["correlacion_estado"] = relacion.estado.value
    frontmatter["correlacion_score_ra"] = round(relacion.score_ra, 4)
    frontmatter["correlacion_fecha"] = vault.hoy()
    if relacion.practica_codigo:
        frontmatter["requiere_practica"] = f"[[{relacion.fuente}]]"
        frontmatter["practica_experimentos"] = [relacion.practica_codigo]
        frontmatter["correlacion_semantica"] = round(relacion.confianza_semantica, 4)
        frontmatter["correlacion_confianza"] = round(relacion.confianza_final, 4)
        frontmatter["correlacion_justificacion"] = relacion.justificacion
    else:
        frontmatter["requiere_practica"] = None
        frontmatter["practica_experimentos"] = []
        frontmatter["correlacion_semantica"] = None
        frontmatter["correlacion_confianza"] = None
        frontmatter["correlacion_justificacion"] = None
    frontmatter["correlacion_alternativas"] = [_enlace_practica(c) for c in relacion.candidatos_alternativos]

    vault.escribir_pagina(ruta, frontmatter, cuerpo)

    lineas = [f"estado: {relacion.estado.value}"]
    if relacion.practica_codigo:
        lineas.append(f"práctica: {relacion.practica_codigo} en {relacion.fuente} (confianza {relacion.confianza_final:.2f})")
    if relacion.justificacion:
        lineas.append(f"justificación: {relacion.justificacion}")
    vault.anotar_log(f"/correlate {relacion.ra_codigo}", lineas)
    return True


def correlacionar_vault(codigo_asignatura: str | None = None, dry_run: bool = False, codigos_ra: list[str] | None = None) -> dict:
    """Recorre los RA de wiki/resultados-aprendizaje/ (todos, los de una asignatura, o solo los `codigos_ra`),
    los correlaciona y escribe el resultado. Un RA con datos incompletos se informa y se
    sigue con el resto. Con dry_run solo se calcula el gate: sin LLM y sin escribir.
    `codigos_ra` sirve para no repetir el trabajo (y las llamadas al LLM) de los RA que no cambiaron: ANALIZAR-CAMBIOS
    dice cuales son; un codigo que no existe se informa como error, no se ignora en silencio.

    Devuelve un resumen: {total, aceptado, pendiente_revision, sin_candidato,
    omitidos_por_docente, gate_abierto, gate_cerrado, errores}."""
    resumen = {"total": 0, "aceptado": 0, "pendiente_revision": 0, "sin_candidato": 0,
               "omitidos_por_docente": 0, "gate_abierto": 0, "gate_cerrado": 0, "errores": []}
    asignaturas: dict[str, Asignatura | Exception] = {}
    pedidos = {c.strip() for c in codigos_ra or [] if c.strip()}
    vistos: set[str] = set()

    for ruta in vault.listar_ras():
        try:
            frontmatter, _ = vault.leer_pagina(ruta)
            if pedidos:
                if str(frontmatter.get("codigo")) not in pedidos:
                    continue
                vistos.add(str(frontmatter.get("codigo")))
            nombre_asignatura = vault.enlace(frontmatter.get("pertenece_a"))
            if not nombre_asignatura:
                raise ValueError("falta `pertenece_a`")

            if codigo_asignatura:
                # Se lee el `codigo` crudo de la pagina de la asignatura, SIN validarla
                # todavia: una asignatura rota (o inexistente) de OTRO codigo no debe
                # ensuciar el informe de este filtro (antes se validaba -- y podia fallar
                # o dar FileNotFoundError -- antes de filtrar). Sin filtro (--all) el
                # error de una asignatura inexistente si debe seguir apareciendo: eso
                # pasa mas abajo, fuera de este bloque.
                try:
                    fm_asignatura_cruda, _ = vault.leer_pagina(vault.ASIGNATURAS / f"{nombre_asignatura}.md")
                except FileNotFoundError:
                    continue
                if str(fm_asignatura_cruda.get("codigo")) != codigo_asignatura:
                    continue

            if nombre_asignatura not in asignaturas:
                try:
                    asignaturas[nombre_asignatura] = vault.cargar_asignatura(nombre_asignatura)[0]
                except Exception as error:
                    asignaturas[nombre_asignatura] = error
            asignatura = asignaturas[nombre_asignatura]
            if isinstance(asignatura, Exception):
                raise asignatura
            ra = vault.ra_desde_frontmatter(frontmatter)

            resumen["total"] += 1
            if dry_run:
                score = calcular_score_ra(ra, asignatura)
                abierto = asignatura.tipo_abordaje != TipoAbordaje.teorica and score >= UMBRAL_GATE
                resumen["gate_abierto" if abierto else "gate_cerrado"] += 1
                print(f"  {ra.codigo:16s} score_ra={score:.3f}  gate {'ABIERTO' if abierto else 'cerrado'}")
                continue

            relacion = correlacionar_ra(ra, asignatura)
            if escribir_relacion(relacion):
                resumen[relacion.estado.value] += 1
                print(f"  {ra.codigo:16s} -> {_describir_propuesta(relacion)}")
            else:
                resumen["omitidos_por_docente"] += 1
                print(f"  {ra.codigo:16s} -> omitido (decisión del docente); propuesta: {_describir_propuesta(relacion)}")
        except Exception as error:
            resumen["errores"].append(f"{ruta.name}: {error}")
    for codigo in sorted(pedidos - vistos):
        resumen["errores"].append(f"{codigo}: no hay ningún RA con ese código en {vault.RESULTADOS.as_posix()}/")
    return resumen


def _imprimir_resumen(resumen: dict, dry_run: bool) -> None:
    print()
    if dry_run:
        print(f"{resumen['total']} RA: gate abierto {resumen['gate_abierto']}, cerrado {resumen['gate_cerrado']} (dry-run: no se escribió nada)")
    else:
        print(f"{resumen['total']} RA: aceptado {resumen['aceptado']}, pendiente_revision {resumen['pendiente_revision']}, "
              f"sin_candidato {resumen['sin_candidato']}, omitidos por decisión del docente {resumen['omitidos_por_docente']}")
    for error in resumen["errores"]:
        print(f"ERROR: {error}")


if __name__ == "__main__":
    vault.consola_utf8()
    parser = argparse.ArgumentParser(description="Correlaciona Resultados de Aprendizaje con las prácticas de wiki/fuentes/.")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--indexar", action="store_true", help="reconstruye el store vectorial desde wiki/fuentes/")
    grupo.add_argument("--all", action="store_true", help="correlaciona todos los RA de wiki/resultados-aprendizaje/")
    grupo.add_argument("--asignatura", metavar="CODIGO", help="correlaciona solo los RA de esa asignatura")
    parser.add_argument("--dry-run", action="store_true", help="solo calcula el gate de cada RA: sin LLM y sin escribir nada")
    parser.add_argument("--ra", nargs="+", metavar="CODIGO",
                        help="con --all o --asignatura: correlaciona solo esos RA (los que ANALIZAR-CAMBIOS dice que cambiaron), sin gastar llamadas en el resto")
    args = parser.parse_args()
    if args.ra and args.indexar:
        parser.error("--ra no se combina con --indexar")

    if args.indexar:
        print(f"{indexar_practicas()} practicas indexadas desde {FUENTES}/")
    else:
        resumen = correlacionar_vault(None if args.all else args.asignatura, dry_run=args.dry_run, codigos_ra=args.ra)
        _imprimir_resumen(resumen, args.dry_run)
        sys.exit(1 if resumen["errores"] else 0)
