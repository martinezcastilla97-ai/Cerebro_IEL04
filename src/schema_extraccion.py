"""Esquema Pydantic de extraccion para el Cerebro Docente Hibrido.

Dos raices de extraccion: ExtraccionCurricular (raw/curriculos/*.md, espanol)
y ExtraccionManual (raw/manuales-laboratorio/*.md, un experimento por llamada).

Este esquema solo captura senales -- no decide requiere_practica ni calcula
score_RA. Esa correlacion corre en /correlate, despues de la ingesta.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class TipoAbordaje(str, Enum):
    teorica = "teórica"
    teorico_practica = "teórico-práctica"


class CategoriaAccionCE(str, Enum):
    manipulacion_fisica = "manipulacion_fisica"
    cognitiva_experimental = "cognitiva_experimental"
    cognitiva_aplicada = "cognitiva_aplicada"
    cognitiva_conceptual = "cognitiva_conceptual"
    actitudinal = "actitudinal"


class CategoriaLibro(str, Enum):
    basica = "básica"
    complementaria = "complementaria"


class AlcanceCompetencia(str, Enum):
    modulo = "modulo"      # cada modulo del curriculo numera sus propias UC: pagina '{codigo_asignatura}-UC{n}'
    programa = "programa"  # el mismo codigo y texto de UC se repite en varios modulos: pagina compartida 'UC{n}'


class TipoRecursoWeb(str, Enum):
    base_datos_institucional = "base_datos_institucional"
    video = "video"
    pagina_web = "pagina_web"
    otro = "otro"


# ---------------------------------------------------------------------------
# ExtraccionCurricular -- raw/curriculos/*.md
# ---------------------------------------------------------------------------


class CriterioEvaluacion(BaseModel):
    codigo: str = Field(description="Código tal como aparece en el documento, ej. 'CE2'")
    texto: str
    categoria_accion: CategoriaAccionCE
    confianza: float = Field(ge=0.0, le=1.0)


class ContenidoAprendizaje(BaseModel):
    conceptual: list[str] = Field(default_factory=list)
    procedimental: list[str] = Field(default_factory=list)
    actitudinal: list[str] = Field(default_factory=list)


class ResultadoAprendizajePrograma(BaseModel):
    codigo: str = Field(pattern=r"^RA-PROG-\d+$")
    enunciado: str


class ResultadoAprendizajeModulo(BaseModel):
    codigo: str = Field(
        description="'{codigo_modulo}-RA{n}', ej. 'ABC01-RA1' -- nunca 'RA{n}' a secas"
    )
    enunciado: str
    horas: int
    criterios_evaluacion: list[CriterioEvaluacion]
    contenido: ContenidoAprendizaje
    tipo_abordaje: TipoAbordaje


class ElementoCompetencia(BaseModel):
    codigo: str
    texto: str


class UnidadCompetencia(BaseModel):
    codigo: str
    texto: str
    elementos: list[ElementoCompetencia]
    alcance: AlcanceCompetencia = Field(
        description="'modulo' si el currículo numera esta UC solo para este módulo; "
                    "'programa' si el mismo código y texto se repiten en varios módulos (ver CLAUDE.md, paso 5)"
    )


class Libro(BaseModel):
    autor: str
    titulo: str
    editorial: str | None = None
    isbn: str | None = None
    categoria: CategoriaLibro


class NormaTecnica(BaseModel):
    codigo_norma: str = Field(description="ej. 'NTC 2050', 'IEC 60364', 'RETIE'")
    titulo: str
    organismo_emisor: str | None = None


class RecursoWeb(BaseModel):
    url: str
    descripcion: str | None = None
    tipo_recurso: TipoRecursoWeb


class Programa(BaseModel):
    """Solo si el documento declara datos del PROGRAMA (no del módulo): nivel, duración
    en semestres o total de créditos. Ver CLAUDE.md § 'Páginas de programa'."""

    nombre: str
    nivel: str | None = None
    duracion_semestres: int | None = None
    total_creditos: int | None = None


class Asignatura(BaseModel):
    codigo: str
    nombre: str
    programa: str
    tipo_modulo: str | None = None
    had_totales: int
    hp_totales: int
    hti_totales: int
    creditos: int
    tipo_abordaje: TipoAbordaje
    aprendizajes_previos: str | None = None
    docente_autor: str | None = None
    fecha_aprobacion: str | None = None
    estrategia_practica_marcada: bool
    recurso_laboratorio_marcado: bool
    modulo_homologo: str | None = Field(
        default=None,
        description="Nombre del módulo cuyo currículo es, en RA y contenido analítico, "
                    "el mismo que este; None si no aplica (ver CLAUDE.md, paso 2, 'Módulo homólogo')",
    )

    @model_validator(mode="after")
    def tipo_abordaje_coincide_con_hp(self) -> "Asignatura":
        derivado = (
            TipoAbordaje.teorico_practica if self.hp_totales > 0 else TipoAbordaje.teorica
        )
        if self.tipo_abordaje != derivado:
            raise ValueError(
                f"tipo_abordaje='{self.tipo_abordaje.value}' no coincide con "
                f"hp_totales={self.hp_totales} (se esperaba '{derivado.value}')"
            )
        return self

    @model_validator(mode="after")
    def horas_y_creditos_validos(self) -> "Asignatura":
        for nombre, valor in (("had_totales", self.had_totales), ("hp_totales", self.hp_totales),
                              ("hti_totales", self.hti_totales), ("creditos", self.creditos)):
            if valor < 0:
                raise ValueError(f"{nombre}={valor} no puede ser negativo")
        # had_totales YA incluye las horas practicas del modulo (ver CLAUDE.md, "Capa de
        # generacion"): hp_totales > had_totales solo puede venir de un error de extraccion
        # (p. ej. columnas confundidas al reconstruir una tabla de creditos rota del PDF).
        if self.hp_totales > self.had_totales:
            raise ValueError(
                f"hp_totales={self.hp_totales} no puede ser mayor que had_totales={self.had_totales}: "
                "had_totales ya incluye las horas prácticas del módulo -- revisa si la tabla de "
                "créditos se leyó mal (columnas confundidas al reconstruir una tabla rota del PDF)"
            )
        return self


class ExtraccionCurricular(BaseModel):
    asignatura: Asignatura
    programa: Programa | None = Field(
        default=None, description="Solo si el documento declara nivel, duración en semestres o total de "
                                   "créditos del PROGRAMA; None si no los trae o si ya se cargaron antes"
    )
    resultados_programa: list[ResultadoAprendizajePrograma]
    resultados_modulo: list[ResultadoAprendizajeModulo]
    unidades_competencia: list[UnidadCompetencia]
    bibliografia: list[Libro]
    normas_tecnicas: list[NormaTecnica]
    recursos_web: list[RecursoWeb]
    texto_marco_pedagogico: str | None = Field(
        default=None,
        description="El Anexo 'Estrategias de Enseñanza Sugeridas' / 'Didácticas para el Aprendizaje', "
                    "transcrito tal cual; None si el documento no trae uno",
    )
    sigue_marco_pedagogico_institucional: bool | None = Field(
        default=None,
        description="No se decide en esta extracción aislada -- esta llamada no recibe wiki/marco-pedagogico.md "
                    "para compararlo. Lo decide quien ejecuta INGEST-CURRICULAR (ver CLAUDE.md, paso 7).",
    )


# ---------------------------------------------------------------------------
# ExtraccionManual -- raw/manuales-laboratorio/*.md, un experimento por llamada
# ---------------------------------------------------------------------------


class EquipoUsado(BaseModel):
    nombre: str
    especificacion: str | None = None
    cantidad: int = 1
    codigo_remark: str | None = Field(default=None, description="ej. 'DG-07', 'DG-YB01'")


class Practica(BaseModel):
    codigo: str = Field(description="ej. 'Exp13'")
    nombre_original: str
    capitulo: str | None = None
    pagina_inicio: int | None = None
    proposito: list[str]
    principio_resumen: str = Field(
        description="Resumen de 2-3 frases, nunca copia literal extensa del manual"
    )
    equipos: list[EquipoUsado] = Field(default_factory=list)
    terminos_clave: list[str] = Field(
        min_length=4,
        description="Puente de correlación ES/EN: términos y símbolos técnicos, nunca genéricos",
    )


class ExtraccionManual(BaseModel):
    banco_nombre: str
    fabricante: str | None = None
    idioma_original: str
    capitulo: str
    practicas: list[Practica] = Field(min_length=1, max_length=1)
