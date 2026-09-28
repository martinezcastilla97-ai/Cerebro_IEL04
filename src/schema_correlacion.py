"""Esquema de /correlate.

/correlate no lee raw/ ni re-extrae nada: opera solo sobre lo que ya salio
de ExtraccionCurricular y ExtraccionManual y ya vive en wiki/. Su trabajo es
cruzar RA contra Practica y decidir requiere_practica.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EstadoCorrelacion(str, Enum):
    aceptado = "aceptado"
    pendiente_revision = "pendiente_revision"
    sin_candidato = "sin_candidato"


class JuicioCorrelacion(BaseModel):
    """Salida del juez LLM (etapa 2) para UN par RA-Practica candidato."""

    ra_codigo: str
    practica_codigo: str
    coincide: bool
    justificacion: str = Field(description="Una frase, para auditoría en wiki/log.md")
    confianza_semantica: float = Field(ge=0.0, le=1.0)


class RelacionPropuesta(BaseModel):
    """Registro final: lo que /correlate escribe en el frontmatter del RA
    y en correlaciones/matriz-ra-practica.md."""

    ra_codigo: str
    practica_codigo: str | None
    fuente: str | None = Field(
        default=None,
        description="Página de wiki/fuentes/ (sin .md) que contiene la práctica; con practica_codigo identifica el experimento",
    )
    score_ra: float = Field(
        ge=0.0, le=1.0, description="Pre-filtro — ver artifact, 'De verbo exacto a puntaje tolerante'"
    )
    confianza_semantica: float | None = Field(default=None, ge=0.0, le=1.0)
    confianza_final: float | None = Field(
        default=None, ge=0.0, le=1.0, description="score_ra × confianza_semantica"
    )
    candidatos_alternativos: list[str] = Field(
        default_factory=list, description="Referencias '{fuente}#{codigo}' (una práctica se repite entre manuales)"
    )
    justificacion: str | None = Field(
        default=None, description="Por qué el juez propuso esa práctica (una frase); se guarda para que el docente la vea al revisar"
    )
    estado: EstadoCorrelacion
    revisado_por_docente: bool = Field(
        default=False, description="True si un humano confirmó o rechazó esto a mano, no /correlate solo"
    )
    nota_docente: str | None = Field(
        default=None, description="Por qué el docente aceptó un caso límite o descartó el mejor candidato automático"
    )
