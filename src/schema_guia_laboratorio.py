r"""Esquema de GUIA-LABORATORIO: lo que el LLM devuelve para la guia de laboratorio de una semana de clase (una sola llamada, con
reintentos). Sigue las secciones de la plantilla institucional (config/framework_iub/guia-laboratorio/guia-laboratorio.tex):

    1. Objetivos (general y especificos, cada uno con los Criterios de Evaluacion del RA que desarrolla)
    2. Materiales y Equipos          3. Procedimiento (etapas, cada una con su diagrama de flujo y sus pasos, con la duracion, la
                                        comprobacion y la medida de seguridad de cada uno y, si ayuda, un recurso: el circuito
                                        que se monta, la ecuacion que se aplica o la grafica que se espera obtener)
    4. Cuestiones a Resolver         5. Analisis de Resultados (instrucciones y las tablas de registro de datos)
    6. Conclusiones                  7. Recomendaciones de Seguridad        8. Bibliografia (las referencias, como datos)

El texto es Markdown en linea (negrita, cursiva, `$...$`, citas `[n]`): el codigo lo convierte a LaTeX con latex_seguro.Conversor
(guia_laboratorio.py); la tabla de datos de la guia, la numeracion, el .bib y el formato los pone el codigo, nunca el modelo.

Los limites se validan aqui con un mensaje claro que vuelve al modelo (no con `Field(max_length=...)`: algunas APIs rechazan esas
restricciones en el esquema). Lo que depende del RA, de la practica o de las fuentes lo valida guia_laboratorio.py.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, model_validator

from figuras import DiagramaSpec, GraficaSpec

TIPOS_REFERENCIA = ("book", "manual", "report", "online", "article", "misc")


def _entre(nombre: str, valores: list, minimo: int, maximo: int) -> None:
    if not minimo <= len(valores) <= maximo:
        raise ValueError(f"`{nombre}`: se esperan de {minimo} a {maximo} y hay {len(valores)}")


def _texto(nombre: str, valor: str, minimo: int, maximo: int) -> str:
    valor = " ".join(str(valor).split())
    if not minimo <= len(valor) <= maximo:
        raise ValueError(f"`{nombre}` («{valor[:60]}…») mide {len(valor)} caracteres: se esperan de {minimo} a {maximo}")
    return valor


class Objetivo(BaseModel):
    enunciado: str               # empieza por un verbo en infinitivo
    criterios: list[str] = []    # codigos de los Criterios de Evaluacion del RA que desarrolla (CE1, CE2...)

    @model_validator(mode="after")
    def coherente(self):
        self.enunciado = _texto("objetivo", self.enunciado, 15, 300)
        return self


class Material(BaseModel):
    nombre: str
    especificacion: str = ""     # rango, referencia, tolerancia... (solo si se conoce: no se inventa)
    cantidad: int = 1

    @model_validator(mode="after")
    def coherente(self):
        self.nombre = _texto("material", self.nombre, 2, 120)
        self.especificacion = " ".join(self.especificacion.split())[:200]
        if not 1 <= self.cantidad <= 100:
            raise ValueError(f"la cantidad de «{self.nombre}» es {self.cantidad}: se espera de 1 a 100")
        return self


class TipoRecurso(str, Enum):
    circuito = "circuito"                # el esquema del circuito electrico o electronico que se monta (circuitikz)
    ecuacion = "ecuacion"                # la ecuacion que se aplica en el paso, con lo que significa cada simbolo
    grafica = "grafica"                  # la grafica que se espera obtener (los puntos los calcula el codigo, como en el temario)


class Recurso(BaseModel):
    """Lo que acompana a un paso para que el estudiante entienda como proceder: todo en LaTeX (circuitikz, amsmath, pgfplots), nunca
    una imagen. El codigo lo valida (guia_laboratorio.validar_guia) y lo escribe; el modelo solo da el contenido."""
    tipo: TipoRecurso
    leyenda: str                         # la leyenda de la figura o la frase que presenta la ecuacion
    circuito: str = ""                   # circuito: el cuerpo de un entorno circuitikz (\draw (0,0) to[R=$R_1$] (2,0) ...;)
    ecuacion: str = ""                   # ecuacion: la formula LaTeX (amsmath), sin $ ni entorno
    donde: str = ""                      # ecuacion: que es cada simbolo, con sus unidades
    grafica: GraficaSpec | None = None   # grafica: la especificacion (funciones con sus parametros o datos de las fuentes)

    @model_validator(mode="after")
    def coherente(self):
        self.leyenda = _texto("leyenda del recurso", self.leyenda, 5, 160)
        self.circuito = self.circuito.strip()
        self.ecuacion = self.ecuacion.strip().strip("$").strip()
        self.donde = " ".join(self.donde.split())[:500]
        if self.tipo == TipoRecurso.circuito and not 10 <= len(self.circuito) <= 2500:
            raise ValueError(f"el circuito «{self.leyenda[:50]}» necesita `circuito`: el cuerpo de un entorno circuitikz (de 10 a 2500 caracteres)")
        if self.tipo == TipoRecurso.ecuacion and not 1 <= len(self.ecuacion) <= 400:
            raise ValueError(f"la ecuación «{self.leyenda[:50]}» necesita `ecuacion`: la fórmula LaTeX (hasta 400 caracteres)")
        if self.tipo == TipoRecurso.grafica and self.grafica is None:
            raise ValueError(f"la gráfica «{self.leyenda[:50]}» necesita `grafica`: su especificación")
        return self


class Paso(BaseModel):
    texto: str
    duracion_min: int | None = None      # tiempo aproximado del paso, en minutos
    seguridad: str = ""                  # la medida de seguridad de este paso, si la tiene
    verificacion: str = ""               # lo que el estudiante debe observar para saber que el paso salio bien (y que hacer si no)
    recurso: Recurso | None = None       # si ayuda: el circuito que se monta, la ecuacion que se aplica o la grafica esperada

    @model_validator(mode="after")
    def coherente(self):
        self.texto = _texto("paso", self.texto, 10, 700)
        self.seguridad = " ".join(self.seguridad.split())[:300]
        self.verificacion = " ".join(self.verificacion.split())[:300]
        if self.duracion_min is not None and not 1 <= self.duracion_min <= 240:
            raise ValueError(f"el paso «{self.texto[:50]}» dura {self.duracion_min} min: se espera de 1 a 240")
        return self


class Etapa(BaseModel):
    titulo: str                          # «Preparación y montaje», «Medición», «Desmontaje»...
    pasos: list[Paso]
    diagrama: DiagramaSpec | None = None  # el diagrama de flujo de la etapa (sus pasos y las comprobaciones como decisiones)

    @model_validator(mode="after")
    def coherente(self):
        self.titulo = _texto("etapa", self.titulo, 3, 90)
        _entre(f"pasos de «{self.titulo}»", self.pasos, 1, 12)
        return self


class TablaRegistro(BaseModel):
    leyenda: str
    columnas: list[str]                  # con la unidad en el encabezado: «Tensión (V)»
    filas: int                           # cuantas filas vacias lleva para registrar los datos

    @model_validator(mode="after")
    def coherente(self):
        self.leyenda = _texto("leyenda de la tabla", self.leyenda, 5, 160)
        _entre(f"columnas de «{self.leyenda}»", self.columnas, 2, 7)
        self.columnas = [_texto("columna", c, 1, 40) for c in self.columnas]
        if not 2 <= self.filas <= 15:
            raise ValueError(f"la tabla «{self.leyenda}» tiene {self.filas} filas: se esperan de 2 a 15")
        return self


class Referencia(BaseModel):
    tipo: str                            # book | manual | report | online | article | misc
    autores: list[str] = []              # «Apellido, Nombre»; vacio si la fuente no lo dice
    titulo: str
    editorial: str = ""                  # editorial, fabricante u organizacion
    anio: str = ""
    edicion: str = ""
    url: str = ""

    @model_validator(mode="after")
    def coherente(self):
        if self.tipo not in TIPOS_REFERENCIA:
            raise ValueError(f"tipo de referencia «{self.tipo}»: se espera uno de {', '.join(TIPOS_REFERENCIA)}")
        self.titulo = _texto("título de la referencia", self.titulo, 2, 250)
        return self


class GuiaLaboratorio(BaseModel):
    titulo: str                          # el de la practica, como el de un capitulo
    introduccion: str                    # un parrafo que ubica la practica respecto de la sesion y del RA
    objetivo_general: str
    objetivos_especificos: list[Objetivo]
    materiales: list[Material]
    procedimiento_introduccion: str      # antes de los pasos: organizacion del trabajo, normas del banco
    etapas: list[Etapa]
    cuestiones: list[str]
    analisis: list[str]                  # parrafos: como analizar y presentar los resultados
    tablas_registro: list[TablaRegistro]
    conclusiones: str                    # lo que se pide al estudiante concluir
    preguntas_conclusion: list[str]
    seguridad: list[str]
    referencias_cargadas: list[Referencia]   # una por fuente cargada, en el mismo orden (las que se citan con [n])
    referencias_externas: list[Referencia] = []   # las que no estan cargadas (cada una marcada en el texto con el marcador)
    base_bibliografica: list[int] = []   # sin practica de un manual: los numeros [n] de las fuentes cargadas en que se basa la practica

    @model_validator(mode="after")
    def coherente(self):
        self.titulo = _texto("titulo", self.titulo, 10, 200)
        self.introduccion = _texto("introduccion", self.introduccion, 80, 2500)
        self.objetivo_general = _texto("objetivo_general", self.objetivo_general, 20, 400)
        self.procedimiento_introduccion = _texto("procedimiento_introduccion", self.procedimiento_introduccion, 40, 1500)
        self.conclusiones = _texto("conclusiones", self.conclusiones, 40, 1500)
        _entre("objetivos_especificos", self.objetivos_especificos, 2, 6)
        _entre("materiales", self.materiales, 2, 30)
        _entre("etapas", self.etapas, 2, 6)
        _entre("cuestiones", self.cuestiones, 3, 10)
        _entre("analisis", self.analisis, 1, 6)
        _entre("tablas_registro", self.tablas_registro, 1, 4)
        _entre("preguntas_conclusion", self.preguntas_conclusion, 2, 6)
        _entre("seguridad", self.seguridad, 3, 12)
        self.cuestiones = [_texto("cuestión", c, 15, 600) for c in self.cuestiones]
        self.analisis = [_texto("párrafo de análisis", a, 40, 1500) for a in self.analisis]
        self.preguntas_conclusion = [_texto("pregunta de conclusión", p, 10, 400) for p in self.preguntas_conclusion]
        self.seguridad = [_texto("recomendación de seguridad", s, 10, 400) for s in self.seguridad]
        return self

    def pasos(self) -> list[Paso]:
        return [p for e in self.etapas for p in e.pasos]
