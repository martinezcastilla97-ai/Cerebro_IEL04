# Cerebro Docente — Schema del Wiki

Eres el mantenedor de este wiki personal. Tu rol es leer fuentes, extraer conocimiento, y mantener un conjunto estructurado de archivos Markdown interconectados. Nunca modificas los archivos en `raw/`. Todo lo que escribes va en `wiki/`.

Este archivo vale para **cualquier asistente de IA**: el nombre es histórico y nada de lo que dice depende de un modelo o de una herramienta en concreto (`AGENTS.md` y `GEMINI.md` apuntan aquí). Los scripts de `src/` tampoco: usan cualquier proveedor compatible con la API de OpenAI, o ninguno (ver `README.md`, «Configurar el modelo de IA»).

---

## Estructura de directorios

```
Cerebro Docente/
├── CLAUDE.md               ← este archivo (schema y reglas, para cualquier asistente de IA)
├── AGENTS.md               ← resumen de las reglas para asistentes de IA; apunta a este archivo
├── GEMINI.md               ← apunta a este archivo y a AGENTS.md
├── config/                 ← SCHEMA.md: ontología y gobernanza de referencia (si difiere de este archivo, prevalece este); nuevo-cerebro.py (y .ps1 en Windows) crea copias limpias; manifiesto.json: la versión y la huella de cada archivo de la plantilla (con él `actualizar_estructura.py` sabe qué editaste en tu copia)
│   └── framework_iub/      ← los logos institucionales IUB (logos/; su ORIGEN.md dice de dónde salieron); las presentaciones ya no los usan (la marca va como texto)
├── .obsidian/              ← configuración de Obsidian del vault
├── raw/                    ← fuentes originales (SOLO LECTURA)
│   ├── assets/             ← imágenes descargadas localmente
│   ├── curriculos/         ← documentos "Diseño y Planeamiento Curricular" (uno por módulo, agrupados por programa)
│   ├── manuales-laboratorio/ ← manuales de los bancos de laboratorio (una carpeta por banco)
│   ├── bibliografia/       ← libros, guías y datasheets
│   ├── normas-tecnicas/    ← NTC, IEC, ISA, RETIE, PEMEX…
│   └── ...                 ← artículos, PDFs, notas y otras fuentes sueltas
├── wiki/                   ← wiki generado y mantenido por el LLM
│   ├── index.md            ← catálogo de todo el wiki
│   ├── log.md              ← registro cronológico de operaciones
│   ├── fuentes/            ← una página por fuente ingerida (libros, normas, manuales de banco)
│   ├── entidades/          ← personas, proyectos, lugares, organizaciones
│   ├── conceptos/          ← ideas, temas, marcos teóricos
│   ├── consultas/          ← respuestas a preguntas archivadas como páginas
│   ├── programas/          ← capa curricular: un programa académico por página
│   ├── asignaturas/        ← capa curricular: un módulo por página
│   ├── resultados-aprendizaje/ ← capa curricular: un RA por página
│   ├── competencias/       ← capa curricular: Unidades de Competencia
│   ├── recursos-web/       ← capa curricular: webgrafía y bases de datos institucionales
│   └── marco-pedagogico.md ← nodo único: estrategias de enseñanza compartidas entre módulos
├── correlaciones/          ← vistas Dataview de auditoría (las alimentan los protocolos CORRELATE-*)
├── generacion/             ← salida generada a partir de wiki/ (no es wiki, pero se audita igual)
│   ├── planeador/          ← {codigo}-planeador.md, programa de estudios de 14 semanas
│   ├── temarios/           ← {codigo}-semanaNN.md, una sesión por semana de clase; figuras/ guarda los PNG (gráficas y diagramas) que dibuja el código
│   └── presentaciones/     ← {codigo}/{codigo}-semanaNN.tex: la presentación Beamer (LaTeX, pdfLaTeX) de cada temario, con el diseño institucional IUB, y su plan (.plan.json); una carpeta autocontenida por asignatura
├── requirements.txt        ← dependencias de src/ (pip install -r requirements.txt)
└── src/                    ← protocolos hechos script (correlate, planeador, temario, presentaciones, auditorías, lint, ingest_manual, analizar_cambios, actualizar_estructura), esquemas Pydantic, prompts y tests
```

---

## Convenciones de páginas

### Frontmatter obligatorio
Cada página wiki lleva YAML frontmatter. La plantilla de abajo es la del **wiki base** (fuentes, entidades, conceptos, consultas); cada tipo de la capa curricular y de generación tiene su propio bloque con su propio `tipo:`, en su sección correspondiente más abajo. Lista completa de los 14 valores de `tipo` en `config/SCHEMA.md` § "Convenciones de frontmatter obligatorias".

```yaml
---
tipo: fuente | entidad | concepto | consulta
etiquetas: [lista, de, etiquetas]
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
fuentes_count: N          # solo para entidades y conceptos
---
```

### Nombres de archivo
- Minúsculas con guiones: `nombre-del-archivo.md`
- Sin espacios ni caracteres especiales
- Descriptivos y únicos

### Enlaces internos
- Usar siempre `[[nombre-del-archivo]]` para links internos (formato Obsidian)
- En el texto usar `[[nombre-del-archivo|texto visible]]` si el nombre no es legible
- Al final de cada página incluir sección `## Ver también` con links relacionados

### Páginas de fuentes (`wiki/fuentes/`)
```markdown
---
tipo: fuente
etiquetas: []
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
origen: [archivo | url | manual]
---

# Título de la fuente

**Origen:** `raw/...` o URL
**Tipo:** artículo | libro | video | podcast | nota | dato
**Fecha fuente:** YYYY-MM-DD (si aplica)

## Resumen
3-5 párrafos con los puntos clave.

## Puntos clave
- Punto 1
- Punto 2

## Citas relevantes
> "Cita textual importante" (p. X)

## Conexiones
- Actualiza [[entidad-o-concepto]] porque...
- Contradice / refuerza [[otro-articulo]]

## Ver también
[[concepto-relacionado]] | [[entidad-mencionada]]
```

**El original de una fuente y TEMARIO:** la línea `**Origen:** \`raw/...\`` de la página no es solo un rastro: TEMARIO lee de ahí el texto completo de la fuente (definiciones, ecuaciones, tablas de datos, ejemplos) para redactar cada sesión con ella y no de memoria. Solo se lee un original de texto (`.md` o `.txt`, o una carpeta de ellos) **que esté dentro de `raw/`**: la ruta se resuelve con sus `..` y sus enlaces simbólicos, y una que salga de `raw/` (`../x.txt`, `raw/../../x.txt`, una ruta absoluta, un enlace que apunte fuera, también dentro de una carpeta) no se lee —ese texto viaja al proveedor de IA— y TEMARIO lo avisa («fuera de raw/: no se lee»), igual que avisa de un PDF. Un PDF no se lee, y de esa fuente solo se usa la página del wiki — conviene convertirlo a Markdown antes de ingerirlo.

**Fuentes de tipo `equipo-laboratorio` (manuales de banco):** son una fuente más — una sola página en `wiki/fuentes/` con `equipo-laboratorio` en `etiquetas`. Sus experimentos **no** se fragmentan en páginas propias: van en el frontmatter, bajo `practicas`, una entrada por experimento con el esquema `Practica` de `src/schema_extraccion.py` a partir del manual en `raw/manuales-laboratorio/`. Se extraen con `python src/ingest_manual.py raw/manuales-laboratorio/.../manual.md --fuente NOMBRE` (un experimento por llamada, con `src/prompts/prompt-ingest-manual.md`; el código sale del encabezado — `Exp{N}`, o compuesto como `Exp3-1`/`Exp3.2` si el manual numera sub-prácticas así; `--solo-dividir` lista los experimentos sin usar el LLM y avisa si dos secciones producirían el mismo código; `--solo Exp3 Exp5` procesa únicamente esos —los que cambiaron en el manual, ver ANALIZAR-CAMBIOS—; si la página ya existe, fusiona por código sin tocar el resto). Si dos secciones de la misma corrida producen el mismo código (p. ej. un "Experiment 1" en cada capítulo), la ingesta se detiene antes de llamar al LLM — hay que distinguirlas con `--patron` o procesarlas por separado con `--prefijo`. CORRELATE toma de ahí sus candidatos. Tras cargar o modificar un manual, correr desde la raíz del vault `python src/correlate.py --indexar`.

```yaml
practicas:
  - codigo: Exp13                # 'Exp{N}' o compuesto ('Exp3-1'); se repite entre manuales, por eso una práctica se identifica por (fuente, código)
    nombre_original:
    capitulo:
    pagina_inicio:
    proposito: []
    principio_resumen:           # 2-3 frases, nunca copia literal extensa
    equipos: []
    terminos_clave: []           # 4 a 8, específicos: es el puente español/inglés
```

### Páginas de entidades (`wiki/entidades/`)
Personas, proyectos, lugares, organizaciones, herramientas.

```markdown
---
tipo: entidad
etiquetas: [persona | proyecto | lugar | org | herramienta]
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
fuentes_count: N
---

# Nombre de la Entidad

**Tipo:** persona | proyecto | lugar | organización | herramienta
**Descripción breve:** Una línea.

## Descripción
Texto comprensivo y actualizado con cada nueva fuente.

## Lo que sabemos
Hechos clave, organizados por subtema si hay varios.

## Contradicciones o incertidumbres
Puntos donde las fuentes no coinciden o hay dudas.

## Aparece en
- [[fuente-1]] — contexto breve
- [[fuente-2]] — contexto breve

## Ver también
[[concepto-relacionado]] | [[otra-entidad]]
```

### Páginas de programa (`wiki/programas/`)
Programa académico que agrupa asignaturas. Se crea una sola vez y todas sus asignaturas lo referencian. Nombre de archivo: el nombre oficial del programa (ej. `Nombre Oficial del Programa.md`).

```markdown
---
tipo: programa
nombre:
nivel:                      # solo si el documento curricular lo indica
duracion_semestres:         # ídem
total_creditos:             # ídem
asignaturas: []
resultados_programa:
  - codigo: RA-PROG-1
    enunciado:
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

`resultados_programa` guarda el "Resultado de Aprendizaje del Programa": un único enunciado compartido por todos los módulos, con código `RA-PROG-{n}`. **Nunca** se mezcla con los RA de módulo (`{codigo}-RA{n}`), que viven en `wiki/resultados-aprendizaje/`.

Cuerpo: `## Asignaturas del Programa`, separando los módulos compartidos con otros programas de los específicos de este.

### Páginas de asignatura (`wiki/asignaturas/`)
Un módulo curricular completo (ver capa curricular más abajo).

```markdown
---
tipo: asignatura
etiquetas: []
codigo: (ej. ABC01)
nombre:
programa: ["[[programa]]"]           # uno o varios: los módulos compartidos pertenecen a más de un programa
tipo_modulo: (ESPECÍFICO | TRANSVERSAL | INVESTIGACIÓN)
had_totales:
hp_totales:
hti_totales:
creditos:
tipo_abordaje: (teórica | teórico-práctica — SE DERIVA de hp_totales, ver más abajo)
aprendizajes_previos:
docente_autor:
fecha_aprobacion:
estrategia_practica_marcada: (bool — casilla "Práctica de laboratorio" en Estrategias Pedagógicas)
recurso_laboratorio_marcado: (bool — casillas "Equipo de laboratorio"/"Laboratorio" en Recursos Didácticos)
resultados_aprendizaje: []
competencias: []                     # [[{codigo}-UC{n}]] o [[UC{n}]], según el caso (ver "Páginas de competencia")
modulo_homologo: null                # solo si el currículo de este módulo es el de otro: "[[otra-asignatura]]"; sus RA se reutilizan, no se duplican
recursos_web: []
sigue_marco: "[[marco-pedagogico]]"   # solo si el Anexo del currículo coincide con el marco institucional
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

### Páginas de resultado de aprendizaje (`wiki/resultados-aprendizaje/`)
La unidad temática evaluable del currículo — lo que en un wiki genérico sería un "concepto", pero aquí atado a Criterios de Evaluación y horas específicas de una asignatura. Código canónico `{codigo_asignatura}-RA{n}` (ej. `ABC01-RA1`) — **nunca** confundir con el RA único del programa (`RA-PROG-{n}`).

```markdown
---
tipo: resultado_aprendizaje
codigo:
enunciado:
pertenece_a: "[[asignatura]]"
tipo_abordaje:
horas:
criterios_evaluacion:
  - codigo: CE1
    texto:
    categoria_accion: (manipulacion_fisica | cognitiva_experimental | cognitiva_aplicada | cognitiva_conceptual | actitudinal)
    confianza: 0.0-1.0
contenido_conceptual: []
contenido_procedimental: []
contenido_actitudinal: []
bibliografia: ["[[fuente-existente]]"]   # reutiliza wiki/fuentes/, no duplica
requiere_practica: null                  # solo si tipo_abordaje = teórico-práctica
practica_experimentos: []                # ej. ["Exp13"] — qué experimento(s) de la fuente satisfacen el RA
aplicacion_potencial: null                # opcional, solo en RA teóricos; lo llena el docente A MANO cuando quiera — CORRELATE nunca lo escribe ni lo necesita para nada
correlacion_estado: (aceptado | pendiente_revision | sin_candidato)
correlacion_score_ra:
correlacion_semantica:
correlacion_confianza:
correlacion_justificacion:               # por qué el juez propuso esa práctica (una frase): lo primero que lee el docente al revisar
correlacion_alternativas: []
correlacion_fecha: YYYY-MM-DD            # lo escribe CORRELATE
correlacion_revisado_por_docente: false
correlacion_nota_docente: null
correlacion_fecha_revision: null         # lo pone el docente al revisar
# Los escribe CORRELATE-PLANEADOR (auditoría del texto que el planeador redactó para este RA):
planeador_estado: (cubierto | revisar | desviado)
planeador_confianza:
planeador_semanas: []
planeador_semanas_con_problema: []
planeador_justificacion:
planeador_fecha:
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

### Páginas de competencia (`wiki/competencias/`)
Unidad de Competencia (UC) con sus Elementos de Competencia (EC). Hay dos casos, según cómo las numere el currículo:

- **UC propia de un módulo** (cada módulo del currículo lista las suyas): una página por módulo, `{codigo_asignatura}-UC{n}.md`, con `asignatura`.
- **UC de programa** (el mismo código y texto se repite en varios módulos): una sola página, `UC{n}.md`, con `programas` y `asignaturas`; se crea una vez y los módulos la referencian.

```markdown
---
tipo: competencia
codigo: (ej. ABC01-UC1, o UC2 si es de programa)
texto:
elementos:
  - codigo: EC1
    texto:
asignatura: "[[asignatura]]"    # solo UC propia de un módulo
programas: []                   # solo UC de programa
asignaturas: []                 # solo UC de programa: los módulos que la desarrollan
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

### Páginas de recurso web (`wiki/recursos-web/`)
Webgrafía y bases de datos institucionales que citan los currículos. Nunca se mezclan con los libros ni con las normas de `wiki/fuentes/`. Una página por recurso, compartida entre asignaturas (se crea una sola vez); nombre de archivo en minúsculas con guiones.

```markdown
---
tipo: recurso_web
url:
tipo_recurso: (base_datos_institucional | video | pagina_web | otro)
descripcion:
asignaturas: []
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

### Marco pedagógico institucional (`wiki/marco-pedagogico.md`)
Nodo único — una sola página, no una carpeta —: las estrategias de enseñanza sugeridas que el Anexo de cada currículo repite palabra por palabra. Se transcribe una vez; las asignaturas lo enlazan con `sigue_marco` y nunca se copia el texto en cada una.

```markdown
---
tipo: marco_pedagogico
referenciado_por: []
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

Cuerpo: el texto del Anexo "Estrategias de Enseñanza Sugeridas" / "Didácticas para el Aprendizaje".

### Páginas de planeador (`generacion/planeador/`)
Programa de estudios de una asignatura, generado por PLANEADOR. Vive fuera de `wiki/`, pero sigue la misma disciplina auditable.

```markdown
---
tipo: planeador
asignatura: "[[asignatura]]"
horas_sesion: 2 | 4          # derivado, ver "Capa de generación"
semanas_examen: [5, 10, 14]
semanas:                     # una entrada por semana; TEMARIO y CORRELATE-PLANEADOR leen de aquí
  - semana: 1
    tipo: clase | examen
    ra: codigo-RAn           # solo en semanas de clase
    tema:                    # lo redacta el LLM; queda vacío si se generó con --sin-llm
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

Cuerpo: el cronograma en forma de tabla (Semana · Tipo · RA · Tema), generado a partir de `semanas`.

### Páginas de temario (`generacion/temarios/`)
Una sesión completa por semana de clase, `{codigo}-semanaNN.md`, con la estructura de una guía de sesión universitaria: cabecera, metadatos, resultados de aprendizaje, índice temporizado, desarrollo teórico, caso de estudio, secciones aplicadas opcionales, síntesis y bibliografía. Nunca se genera una para una semana de examen.

```yaml
---
tipo: temario
asignatura: "[[asignatura]]"
resultado_aprendizaje: "[[codigo-RAn]]"
semana: N
total_semanas: 14
corte_evaluativo: 1 | 2 | 3            # derivado de `semana` contra semanas_examen (ver "Capa de generación")
horas_sesion: 2 | 4
horas_trabajo_independiente: N          # derivado de hti_totales / 14, ver "Capa de generación"
estadisticas:                           # las escribe TEMARIO: cuánta profundidad tiene la sesión
  palabras: N                           # de prosa (párrafos, listas, notas y pies)
  ecuaciones: N
  tablas: N
  figuras: N                            # gráficas y diagramas
  pasajes: N                            # pasajes de las fuentes cargadas con que se redactó
bibliografia_estado: (cubierta | revisar | vacio_detectado)   # lo escribe CORRELATE-BIBLIOGRAFIA
bibliografia_via: (marcador | juez | sin_bibliografia)
bibliografia_justificacion:
bibliografia_faltantes: []   # las líneas del temario marcadas con [FUENTE NO CARGADA EN raw/]
bibliografia_fecha:
# Los escribe PRESENTACIONES; un temario sin `presentacion_estado` no tiene presentación todavía:
presentacion_estado: (generada | revisar)   # `revisar` = hay avisos (una parte que el modelo no logró escribir con LaTeX admitido y quedó provisional, un dato con un carácter sin equivalente LaTeX, o algo que la verificación estática detectó)
presentacion_archivo:                       # ej. generacion/presentaciones/ABC01/ABC01-semana03.tex
presentacion_avisos: []
presentacion_temario_hash:                  # huella del cuerpo del temario al generar: si cambia, la presentación quedó desactualizada (y las partes de su plan que cambiaron: pedirlas cuesta una llamada por parte)
presentacion_fecha: YYYY-MM-DD
presentacion_diseno:                        # versión del diseño de las diapositivas (src/diseno_iub.py): si cambia, la presentación se rehace desde su plan, sin LLM (sin plan guardado en el formato actual —un diseño anterior al 5—, con ~9 llamadas)
presentacion_diapositivas:                  # cuántas diapositivas tiene (con portada, agenda, aperturas, referencias y cierre)
presentacion_docente:                       # con quién y con qué programa se hizo: si cambia alguno de los tres, la presentación se rehace (sin LLM)
presentacion_programa:
presentacion_contacto:
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---
```

Cuerpo, en este orden — lo que es determinista lo redacta el código a partir de datos ya cargados (nunca el LLM); el resto lo redacta el LLM, en tres pasos (ver TEMARIO):

```
# {título descriptivo de la sesión}                                              (LLM)
> **Módulos:** ABC01 — Nombre · XYZ02 — Otro            (determinista: la asignatura y los módulos que le declaran `modulo_homologo`)
> **Duración:** 120 minutos (sesión teórica | teórico-práctica)       (determinista)
> **Nivel:** …                                          (determinista, solo si la página del programa trae `nivel`: no se inventa)
> **Plataforma de referencia:** …                       (LLM, solo si el tema tiene una plataforma, herramienta o norma marco)
> **Semana:** N de 14 (corte evaluativo k) · **Resultado de aprendizaje del módulo:** [[ABC01-RA1]] · **Trabajo independiente:** N h/semana   (determinista)
## 1. Metadatos de la Sesión
### 1.1 Continuidad curricular       un párrafo (LLM) y la lista de la sesión anterior, la presente y la siguiente (determinista, del planeador)
### 1.2 Prerrequisitos               lista (LLM)
## 2. Resultados de Aprendizaje      el RA, sus Criterios de Evaluación y las Unidades de Competencia (determinista, directo de `wiki/`, nunca redactado
                                     de nuevo) y la tabla `# | Resultado de aprendizaje | Nivel (Taxonomía de Bloom)` de la sesión (LLM: de 3 a 5, cada uno
                                     con el verbo en negrita y los Criterios de Evaluación que desarrolla; entre todos cubren todos los del RA)
## 3. Índice Temporizado (N minutos)  tabla Bloque | Contenido | Duración: un bloque por unidad, en múltiplos de 5 min que suman la sesión (determinista)
## 4. Desarrollo Teórico
### 4.1 Introducción Conceptual (Bloque 1)
### 4.2 Conceptos Clave
#### 4.2.1 {concepto} (Bloque 2) … de 3 a 6 conceptos, cada uno una unidad desarrollada a fondo
## 5. Caso de Estudio Aplicado: {título} (Bloque k)   con subtítulos `### 5.1 …`; datos numéricos y cálculos paso a paso. Si la asignatura es
                                     teórico-práctica y el RA tiene práctica asignada, abre con `**Práctica de referencia:** [[fuente]] — ExpN` y se apoya en ella
## 6. {título del análisis} (Bloque k)         opcional: dimensionamiento, comparación o selección con justificación cuantitativa
## 7. {título de la implementación} (Bloque k) opcional: código o procedimiento de referencia, reproducible y comentado
## N. Síntesis (Bloque k)  +  ### Componente Actitudinal
## N+1. Bibliografía (Formato IEEE)   las fuentes cargadas, numeradas [1], [2]… (el número con que se citan en el texto), y las no cargadas, con el marcador
```

Cada unidad se compone de bloques con nombre, que el código escribe siempre igual: **párrafos** (con `$...$` en línea y citas `[n]`); **listas**; **ecuaciones** en `$$...$$`, seguidas de un párrafo «donde…» que define cada símbolo con sus unidades; **tablas** (`**Tabla N.** leyenda` y la tabla Markdown); **notas** (`> **Nota pedagógica:** …`); **código** (`**Listado N.** leyenda` y un bloque con su lenguaje); y **figuras**: una imagen `![Figura N. leyenda](figuras/{codigo}-semanaNN-figK.png)` y su pie `*Figura N. leyenda*` (los PNG están en `generacion/temarios/figuras/`, y Obsidian los muestra tal cual). Un tema conceptual puede no llevar ecuaciones ni gráficas, y una sesión de un tema no técnico puede no llevar ni análisis ni implementación.

### Presentaciones (`generacion/presentaciones/`)
La presentación de cada temario, en LaTeX Beamer con el diseño institucional IUB, al estilo de las presentaciones de ejemplo del docente. No son páginas Markdown (no llevan frontmatter): son archivos `.tex` que se compilan con **pdfLaTeX** (dos pasadas). Su estado vive en los campos `presentacion_*` del propio temario (ver arriba), que es lo que lee la vista `correlaciones/matriz-temario-presentacion.md`.

```
generacion/presentaciones/{codigo}/
├── {codigo}-semanaNN.tex        ← lo que siempre se entrega: el código LaTeX completo (preámbulo con el diseño incluido)
├── {codigo}-semanaNN.plan.json  ← las diapositivas que escribió el modelo, por parte y con la huella de cada una: rehacer el .tex no vuelve a llamar al modelo
└── {codigo}-semanaNN.pdf        ← solo si se corrió con --compilar y hay pdflatex instalado
```

La carpeta de cada asignatura es autocontenida y **sin imágenes** (la marca «IUB» va como texto y todas las figuras son TikZ): se puede comprimir tal cual y subir a Overleaf (compilador pdfLaTeX), o compilar en local. No depende de ningún tema `.sty`: el preámbulo va en cada `.tex`.

**Cómo se hace (diseño 5: el modelo escribe el LaTeX de cada diapositiva; el código, el marco).** El temario se divide, sin LLM, en **partes**: la **apertura** (secciones 1 y 2: metadatos y resultados de aprendizaje) y cada **bloque** de su índice temporizado (los encabezados `(Bloque k)`, con el título y los minutos de su fila del índice). Por cada parte hay **una llamada** al modelo (~9 por temario), con `src/prompts/prompt-presentacion.md`, que reúne la instrucción del docente («experto en LaTeX y en presentaciones académicas de alto nivel… integra de forma proactiva figuras, bloques de texto y diagramas de flujo… sin saturar… viñetas concisas… destaca los conceptos clave»), su skill `experto-en-latex` (código limpio y compilable; `amsmath`, `siunitx`, `booktabs`/`tabularx`, TikZ o circuitikz para esquemas técnicos) y fragmentos de las presentaciones de ejemplo. El modelo devuelve sus diapositivas (`src/schema_presentacion.py`: de 1 a 6, cada una con `titulo` y `cuerpo` en LaTeX): cajas de color en columnas (`caja`, `cajaplana`, `cardB/O/G/N`), diagramas de flujo y esquemas en TikZ (estilos `bloque`, `box`, `bB/bO/bG/bN`, `flecha`, `nodo`, `term`, `cable`, `dec`, `tag`), gráficas pgfplots con los datos o las ecuaciones del temario, circuitos en circuitikz, tablas con encabezado oscuro (`\rowcolor{iubnavy}`, `\hd{}`) y código en un `codebox`. Las **figuras del temario** (PNG) no se usan: el texto que recibe el modelo las describe y, si aportan, las redibuja en TikZ o pgfplots. Lo que no cumple vuelve al modelo con el motivo, hasta 2 veces: un comando fuera de la lista de permitidos (ver abajo), un título largo, un cuerpo con `\begin{frame}`, y —solo mientras quedan reintentos— una parte de varias diapositivas sin ningún recurso visual. Si tras los reintentos una parte sigue sin cumplir, queda una **diapositiva provisional** con el aviso (estado `revisar`), la presentación se escribe igual y la próxima corrida pide solo esa parte.

El **marco** lo escribe el código (`src/diseno_iub.py`, sin LLM), siempre igual, con el preámbulo de las presentaciones de ejemplo y el **Manual de Identidad Visual IUB 2025**: fondo blanco (#FFFFFF) y texto #121023; franja superior #121023 con el título de la diapositiva en amarillo #FFDF2D y «IUB» a la derecha; pie #121023 con el módulo, el docente, la semana y el número de diapositiva; cajas, diagramas y gráficas en la paleta complementaria —azul #00ADE7, naranja #E39037, verde #3B9C6D— con texto blanco; tipografía `avant` (URW Gothic) con `\renewcommand{\familydefault}{\sfdefault}` (el manual usa Nexa y Avenir Next, que pdfLaTeX no tiene), como pidió el docente. Además pone, con datos del temario, del planeador y del wiki: la **portada** (panel #121023 con «IUB», la institución, el programa, el docente y el contacto; el código, la semana y el corte, el nombre de la asignatura, el título de la sesión —el `#` del temario—, la plataforma de referencia y la duración), la **ruta de la sesión** (los bloques del índice temporizado con una barra proporcional a sus minutos), un **separador** por bloque («BLOQUE 0k», su título y su duración), las **referencias** (la bibliografía del temario, paginada) y el **cierre** («¡Gracias!», la próxima sesión del planeador, docente y contacto). Los datos que vienen del wiki y del temario (títulos, docente, programa, referencias) se escapan con `latex_seguro.Conversor`.

**El LaTeX del modelo se compila, así que pasa por una lista de PERMITIDOS (`latex_seguro.verificar_cuerpo`) antes de llegar al `.tex`:** solo se admiten comandos de texto y formato, los matemáticos conocidos (`_COMANDOS_MATEMATICOS`, con `siunitx`), tablas, TikZ, pgfplots, circuitikz, columnas, listas y las cajas del diseño (`COMANDOS_CUERPO`, `ENTORNOS_CUERPO`). Cualquier otro comando —`\input`, `\write18`, `\def`, `\let`, `\newcommand`, `\csname`, `\catcode`, `\includegraphics`, `\usepackage`, `\verb`, `\url`, `\href`…—, la notación `^^`, las variables de un `\foreach` o de `\pgfmathsetmacro` con nombre de primitivo (`\foreach \input in…`), las claves que leen o escriben archivos o llaman al sistema (`\addplot table`, `file`, `gnuplot`, `shell`, `graphics`; `saveto`, `record`, `listing file`, `external`, `escapeinside`, `mathescape`…) y un `%` o un `#` sin escapar devuelven la diapositiva al modelo. **Las opciones también van con lista de permitidos** (`opciones_no_admitidas`, `CLAVES_PERMITIDAS`): TikZ, pgfplots, circuitikz, tcolorbox y adjustbox actúan a través de sus claves (`execute at begin node`, `every axis/.append code`, `external/system call`…), así que toda opción `[...]` dentro de un `tikzpicture` o `circuitikz` (con sus `axis` y `scope`), de un `\tikz` en línea, de un `\foreach`, de las cajas del diseño y de un `adjustbox` tiene que estar en la lista: colores (y las claves que reciben un color, como `fill=` o los estilos del diseño `bloque=`, solo admiten un color), grosores, los estilos del diseño, flechas, posiciones, anclas, tamaños, fuentes, formas, las claves de ejes y leyendas de pgfplots que usan los ejemplos y los componentes y etiquetas de circuitikz; las que llevan otra lista de claves por valor (`legend style`, `decoration`…) se revisan igual. Los **manejadores de pgfkeys** (`/.code`, `/.style`, `/.append style`, `/.store in`, `/.initial`, `/.expanded`, `/.cd`…) no se admiten en ningún lugar del cuerpo, y `\tikzset` y `\pgfplotsset` no están en la lista: el modelo usa los estilos del diseño y escribe las opciones en cada nodo. Las claves prohibidas de antes (`saveto`, `listing file`, `\addplot table`…) quedan como segunda capa. Se usa una lista de permitidos y no de prohibidos porque esta última siempre deja fuera algún comando que lee archivos; un comando con «input», «file», «read», «write», «open», «shell» o `@`, o que empiece por `\pdf`, `\lst` o `\verb`, no se admite aunque alguien lo agregue a la lista (si un comando legítimo se rechaza, se agrega a la lista con su prueba en `src/test_presentaciones.py`). La verificación también **normaliza** sin cambiar el sentido: quita los comentarios, escribe como `\ensuremath{…}` los símbolos Unicode que pdfLaTeX no compila y reescribe cada `codebox` en su forma canónica —el código transliterado a ASCII (con pdfLaTeX, `listings` no admite Unicode), `\end{frame}` y `\end{codebox}` neutralizados (`\end {frame}`: el primero cerraría la diapositiva `[fragile]` y lo que siguiera se ejecutaría como TeX) y solo las opciones `language=` y `firstnumber=`—; la diapositiva con código se marca `[fragile]` sola. Un **plan guardado** (`.plan.json`) se vuelve a verificar al leerlo: una parte que no pasa (alguien editó el archivo) se pide otra vez. Antes de escribir el `.tex` se hace una segunda verificación **estática** del documento completo (`verificar_latex`: la misma lista de permitidos —comandos, entornos y opciones— en todo el documento, fuera del preámbulo que escribe el código, más `\bloque` y `frame`; ningún `\end{frame}` dentro del código; `[fragile]`; entornos y llaves balanceados; caracteres soportados); cualquier aviso deja la presentación en `presentacion_estado: revisar`, y si lo que encuentra podría ejecutarse al compilar (`latex_seguro.graves`) **el `.tex` no se escribe** —se borran el anterior y el plan que lo produjo— y `--compilar` no lo compila (`compilar()` vuelve a verificar el archivo antes de llamar a pdflatex, siempre con `-no-shell-escape` y con `openin_any=p` y `openout_any=p` en el entorno: el modo «paranoico» de TeX Live, que no deja leer ni escribir fuera de la carpeta de la presentación). **Lo recomendado es compilar en Overleaf**, que compila cada proyecto aislado; `--compilar` en local lleva esas restricciones, pero son variables de TeX Live: MiKTeX tiene su propia configuración y puede no respetarlas, así que en Windows con MiKTeX cuente solo con `-no-shell-escape` y la verificación estática.

**Qué no está comprobado:** el diseño 5 **no se ha compilado en el equipo donde se escribió** (no tiene LaTeX). Usa solo paquetes estándar de TeX Live y Overleaf (`avant`, `babel`, `amsmath`, `mathtools`, `siunitx`, `adjustbox`, `booktabs`, `tabularx`, `multirow`, `tikz`, `pgfplots`, `circuitikz`, `tcolorbox`, `listings`), con el mismo preámbulo de las presentaciones de ejemplo; las pruebas comprueban la estructura y la seguridad, no el resultado visual. La lista de permitidos impide que el LaTeX del modelo lea o escriba archivos, pero no que un dibujo se salga de la diapositiva o que una construcción válida no compile: la primera compilación real (Overleaf o `--compilar`) es la que lo confirma, y una parte que falla se vuelve a pedir quitándola del `.plan.json` o con `--replanificar`.

### Páginas de conceptos (`wiki/conceptos/`)
Ideas, marcos teóricos, patrones, temas recurrentes.

```markdown
---
tipo: concepto
etiquetas: []
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
fuentes_count: N
---

# Nombre del Concepto

**Definición:** Una línea precisa.

## Explicación
Desarrollo comprensivo del concepto.

## Cómo aparece en mis fuentes
Cómo este concepto se manifiesta en el material que he leído.

## Tensiones o matices
Ambigüedades, contradicciones, variantes del concepto.

## Ver también
[[concepto-relacionado]] | [[entidad-que-lo-usa]]
```

---

## Capa curricular — teórica vs. teórico-práctica

Estructura lista para cuando se cargue un currículo real (ningún archivo de `wiki/programas/`, `wiki/asignaturas/`, `wiki/resultados-aprendizaje/`, `wiki/competencias/` o `wiki/recursos-web/` existe todavía — están vacías a propósito; `wiki/marco-pedagogico.md` existe como esqueleto sin texto). No reemplaza fuentes/entidades/conceptos — los reutiliza: una `Asignatura` cita libros y normas ya existentes en `wiki/fuentes/` en vez de duplicarlos, y un Resultado de Aprendizaje puede requerir una práctica que ya vive dentro de una fuente tipo "equipo de laboratorio", señalando el experimento exacto en `practica_experimentos`.

**Regla estructural — no inferir por palabras clave:**

```
Asignatura.tipo_abordaje SE DERIVA de Asignatura.hp_totales (Horas Prácticas del
encabezado curricular):
    hp_totales == 0   -> teórica
    hp_totales > 0    -> teórico-práctica
```

**Puntaje tolerante por Resultado de Aprendizaje** (reemplaza un simple verbo exacto porque el vocabulario de los Criterios de Evaluación varía entre docentes):

```
score_RA = 0.5·señal_estructural + 0.2·señal_checklist + 0.3·señal_semantica

señal_estructural = 1 si hp_totales > 0, si no 0
señal_checklist   = 1 si estrategia_practica_marcada o recurso_laboratorio_marcado
señal_semantica   = máxima confianza entre los CE clasificados como
                     manipulacion_fisica o cognitiva_experimental

Si Asignatura.tipo_abordaje = teórica: NUNCA se busca práctica, sea cual sea score_RA
(la fórmula de arriba solo pre-filtra teórico-prácticas) -> correlacion_estado: sin_candidato
siempre. aplicacion_potencial es un campo opcional que el docente llena A MANO si quiere
documentar una aplicación fuera de la cobertura evaluable; CORRELATE nunca lo escribe.

Si Asignatura.tipo_abordaje = teórico-práctica:
score_RA < 0.40  -> no se busca práctica -> correlacion_estado: sin_candidato
score_RA >= 0.40 -> buscar en wiki/fuentes/ (tipo equipo-laboratorio) el/los
                    experimento(s) más afines; confianza_final = score_RA × similitud
                    >= 0.70          -> correlacion_estado: aceptado
                    0.35 <= x < 0.70 -> correlacion_estado: pendiente_revision
                    < 0.35           -> correlacion_estado: sin_candidato
```

Taxonomía de clasificación de Criterios de Evaluación:

| Categoría | Verbos indicativos | ¿Aporta señal de banco? |
|---|---|---|
| `manipulacion_fisica` | medir, calibrar, operar, montar, conectar, ensayar | peso alto |
| `cognitiva_experimental` | determinar/verificar + "experimentalmente"/"en el banco" | peso medio |
| `cognitiva_aplicada` | calcular, resolver, aplicar, determinar (sin calificador) | ninguno por sí solo |
| `cognitiva_conceptual` | identificar, reconocer, explicar, definir | ninguno |
| `actitudinal` | comparte, respeta, es puntual | se excluye |

**Advertencia de extracción — "Procedimental" no equivale a "práctico":** todo RA trae `contenido_procedimental`, pero describe una habilidad (puede ser cálculo en papel). La `señal_semantica` sale de clasificar cada Criterio de Evaluación, nunca del bloque procedimental completo — evita falsos positivos por texto genérico.

`correlacion_revisado_por_docente` / `correlacion_nota_docente` nunca los escribe CORRELATE solo — solo existen cuando el usuario confirma o descarta a mano un caso de `pendiente_revision`, y distinguen "sin revisar" de "revisado y descartado". Con `correlacion_revisado_por_docente: true`, CORRELATE no vuelve a escribir en ese RA — solo deja en `wiki/log.md` su propuesta automática, por si conviene revisarla (p. ej. porque se cargó un manual nuevo). Por eso, para resolver un caso a mano hay que marcar ese campo: cambiar solo `correlacion_estado` no protege la decisión de la próxima corrida.

Colisión de códigos: el "Resultado de Aprendizaje del Programa" (uno por programa, `RA-PROG-{n}`) y los `RA1..RAn` de cada módulo (`{codigo}-RA{n}`) no son el mismo objeto aunque compartan numeración en el documento fuente. El primero vive en `resultados_programa` de la página del programa; los segundos, en `wiki/resultados-aprendizaje/`.

**Módulos homólogos:** cuando dos asignaturas comparten Resultados de Aprendizaje vía `modulo_homologo` (el RA es una sola página, enlazada desde ambas), CORRELATE usa las horas y las casillas de checklist (`estrategia_practica_marcada`, `recurso_laboratorio_marcado`) de la asignatura que el RA declara en `pertenece_a` — nunca las del módulo homólogo. Si ambos módulos generan planeador y se audita el mismo RA compartido desde los dos, la corrida de CORRELATE-PLANEADOR más reciente sobrescribe los campos `planeador_*`: son del RA, no de un planeador en particular. No cambiar este comportamiento sin consultarlo primero — no es un descuido, es que el RA es una sola entidad con un solo juego de campos de auditoría.

---

## Capa de generación — de RA a clase

Igual que en CORRELATE, se separa lo determinista de lo generativo: el cronograma lo calcula código, no el LLM; el LLM solo redacta el texto de cada semana. La **generación** (PLANEADOR, TEMARIO, PRESENTACIONES) solo lee `wiki/` (y, PRESENTACIONES, los temarios ya generados) y escribe en `generacion/` — nunca en `raw/` ni en `wiki/`. Su **auditoría** es distinta y sí escribe de vuelta en `wiki/`: CORRELATE-PLANEADOR escribe los campos `planeador_*` en el RA de `wiki/resultados-aprendizaje/`; CORRELATE-BIBLIOGRAFIA escribe los campos `bibliografia_*` en el propio temario, que vive en `generacion/`, no en `wiki/`.

**Cronograma de 14 semanas (determinista, sin LLM):**

```
horas_sesion = 4 si had_totales / 14 >= 3, si no 2
semanas_examen = {5, 10, 14}          # aplicación práctica, Student Outcomes ABET
11 semanas restantes -> repartidas entre los RA, proporcional a `horas`,
                        por método de mayor resto (la suma da exacto)
```

`had_totales` ya incluye las horas prácticas del módulo (no son una columna independiente que se deba sumar — eso las contaría dos veces), así que la duración de la sesión semanal sale solo de `had_totales`. `hp_totales` sigue siendo, por separado, la señal que deriva `tipo_abordaje` y alimenta `score_RA` (ver "Capa curricular"); simplemente no entra en esta cuenta. Por eso mismo `hp_totales` nunca puede ser mayor que `had_totales`: el esquema (`schema_extraccion.Asignatura`) lo rechaza, igual que rechaza cualquier hora o crédito negativo. Una asignatura sin RA cargados se rechaza con error — no se genera un plan vacío. Los RA se ven en el orden de `resultados_aprendizaje` de la asignatura; si algún RA recibiera 0 semanas (más RA que semanas de clase), también se rechaza: hay que decidirlo a mano.

**Dentro de cada sesión (TEMARIO), también determinista:**

```
corte_evaluativo(semana)   -> 1, 2 o 3, según en qué tramo cae respecto a semanas_examen (5, 10, 14)
horas_trabajo_independiente = hti_totales / 14, redondeado (hti_totales es del semestre)
minutos de cada bloque     -> múltiplos de 5 (CUANTO_MINUTOS), al menos uno por bloque, que suman exactamente
                              horas_sesion × 60; se reparten por mayor resto según el peso relativo que el LLM le da
                              a cada bloque (minutos_por_bloque en schema_planeador.py)
```

El LLM nunca reparte minutos ni calcula el corte evaluativo: solo da el peso relativo de cada bloque de contenido.

Implementación en `src/`: `schema_planeador.py` (el cronograma y estas mismas funciones), `planeador.py`, `temario.py` con `schema_temario.py` (lo que el LLM devuelve en cada paso), `pasajes.py` (búsqueda en las fuentes) y `figuras.py` (gráficas y diagramas), `presentaciones.py` con `schema_presentacion.py` (las diapositivas en LaTeX que devuelve el LLM por cada parte del temario), `diseno_iub.py` (el preámbulo y las diapositivas fijas con el diseño institucional, sin LLM) y `latex_seguro.py` (la lista de permitidos del LaTeX del modelo, el escapado de los datos, las fórmulas y la verificación estática; TEMARIO también la usa), `correlate_planeador.py` y `correlate_bibliografia.py`; los prompts de estos pasos están en `src/prompts/`.

---

## Operaciones

Casi todas las operaciones tienen un script en `src/` que se ejecuta desde la raíz del vault (`python src/<script>.py`); el LLM que mantiene el wiki puede usarlo o seguir los pasos a mano. Las dependencias están en `requirements.txt` y `python src/test_*.py` comprueba la instalación sin llamar a ningún LLM.

### INGEST-CURRICULAR — Incorporar un currículo

Variante de INGEST para un documento "Diseño y Planeamiento Curricular" ya cargado en `raw/`. Lo convierte en páginas de `wiki/asignaturas/`, `wiki/resultados-aprendizaje/` y `wiki/competencias/`, y lo enlaza con su programa, sus recursos web y el marco pedagógico. Solo extrae señales: nunca decide `requiere_practica` ni calcula `score_RA` — eso es CORRELATE, que corre después, cuando el currículo y al menos un manual de banco ya están ingeridos. Esquema de extracción y prompt de referencia: `src/schema_extraccion.py` y `src/prompts/prompt-ingest-curricular.md`.

Antes de empezar:
- **Si el documento ya estaba ingerido** (una versión nueva de un currículo), no lo releas entero: corre `python src/analizar_cambios.py --detalle` (sin LLM; ver ANALIZAR-CAMBIOS). Dice qué secciones cambiaron, a qué página del wiki corresponde cada una y trae solo su texto: actualiza únicamente esas páginas. Un currículo nuevo sí se lee completo.
- El documento está en español y la conversión PDF→Markdown suele romper las tablas (celdas partidas en varias filas, separadores `|` desalineados). Reconstruir el contenido semántico; no reproducir la fragmentación.
- La única fuente de verdad es el documento: no completar con conocimiento externo sobre la asignatura ni con contenido de otros módulos.
- Nombres de archivo — excepción a la regla de minúsculas, para que coincidan con los códigos del currículo: programa `{nombre oficial}.md`, asignatura `{codigo} - {nombre}.md`, RA `{codigo}-RA{n}.md`, competencia `{codigo_asignatura}-UC{n}.md` o `UC{n}.md` (ver paso 5). Los enlaces `[[...]]` usan ese mismo nombre.

1. Leer el currículo en `raw/curriculos/` (agrupados por programa).
2. **Asignatura:** crear `wiki/asignaturas/{codigo} - {nombre}.md`, con `**Origen:** \`raw/...\`` en el cuerpo para que todo pueda auditarse hasta el documento. `tipo_modulo` y `aprendizajes_previos` se toman del documento; `programa` enlaza la página del programa (paso 7); `docente_autor` y `fecha_aprobacion`, de "Proceso de Aprobación". `had_totales`, `hp_totales`, `hti_totales` y `creditos` salen de "Información de Créditos Académicos" (enteros, nunca negativos). `had_totales` YA incluye las horas prácticas del módulo, así que `hp_totales` nunca puede superarlo — el esquema lo rechaza (si el documento parece decirlo, sospecha primero de una tabla mal reconstruida antes de reportarlo). `tipo_abordaje` se DERIVA de `hp_totales`: si el documento declara otra categoría, no ingerir en silencio — avisar al usuario. **Módulo compartido:** si la asignatura ya existe (el mismo módulo aparece en el currículo de otro programa), no crear otra página ni duplicar sus RA y competencias: agregar el programa a `programa` y a la lista `asignaturas` del programa; si el documento difiere de lo ya ingerido (horas, RA), avisar en vez de sobrescribir. **Módulo homólogo:** si el currículo de un módulo es, en contenido analítico y RA, el de otro módulo, no duplicar los RA: poner `modulo_homologo`, reutilizar los RA del otro en `resultados_aprendizaje` y pedir confirmación al usuario.
3. **Señales de checklist:** `estrategia_practica_marcada` sale de la fila "Práctica de laboratorio" en "Estrategias Pedagógicas y Didácticas"; `recurso_laboratorio_marcado`, de "Equipo de laboratorio" o "Laboratorio" en "Recursos Didácticos" / "Recursos Locativos".
4. **Resultados de aprendizaje:** una página `wiki/resultados-aprendizaje/{codigo}-RA{n}.md` por cada bloque de la tabla RA / Criterios de Evaluación / Conceptual-Procedimental-Actitudinal / Horas — nunca con el código `RA{n}` a secas. Cada RA hereda el `tipo_abordaje` de su asignatura y se enlaza en `resultados_aprendizaje` de esta. Cada Criterio de Evaluación se clasifica con `categoria_accion` (taxonomía de la capa curricular) y una `confianza` honesta: si el verbo es ambiguo, confianza baja — no forzar `manipulacion_fisica`. El enunciado del RA va en `enunciado`. Los contenidos conceptual, procedimental y actitudinal van a `contenido_conceptual`, `contenido_procedimental` y `contenido_actitudinal`.
5. **Competencias:** cada Unidad de Competencia (UC) con sus Elementos (EC) va en una página de `wiki/competencias/`, enlazada en `competencias` de la asignatura. Si cada módulo lista sus propias UC, una página por módulo: `{codigo_asignatura}-UC{n}.md`, con `asignatura`. Si el mismo código y texto de UC se repite en varios módulos (UC de programa), una sola página `UC{n}.md`, con `programas` y `asignaturas`: si ya existe, no crear otra — solo agregar la asignatura a su lista `asignaturas`.
6. **Bibliografía y normas:** no mezclarlas. Un libro tiene autor, editorial e ISBN; una norma sigue un patrón normativo (`NTC ####`, `IEC #####`, `RETIE`, `IEEE Std ###`, `ISO ####`). Para cada una, buscar una página existente en `wiki/fuentes/` y enlazarla (reutilizar, no duplicar) en el cuerpo de la asignatura: `## Bibliografía` (básica / complementaria) o `## Normas técnicas`. Si no existe todavía, listarla como faltante en el log — no crear páginas de fuente vacías. En `bibliografia` de un RA solo van las fuentes cuyo contenido justifique su contenido conceptual; si no se puede justificar, dejar `[]` — nunca fabricar una cobertura.
7. **Programa, webgrafía y marco pedagógico:**
   - **Programa:** crear `wiki/programas/{nombre oficial del programa}.md` si no existe (una sola vez; todas las asignaturas del programa lo comparten; `nivel`, `duracion_semestres` y `total_creditos` solo si el documento los indica), enlazarlo en `programa` de la asignatura y agregar la asignatura a su lista `asignaturas`. El "Resultado de Aprendizaje del Programa" es un único enunciado compartido por todos los módulos: va en `resultados_programa` con código `RA-PROG-{n}`, nunca con un código de RA de módulo. Si la página ya tiene ese enunciado y el documento trae uno distinto, no sobrescribir — avisar al usuario.
   - **Webgrafía y Bases de Datos:** una página `wiki/recursos-web/{nombre-del-recurso}.md` por recurso, con su `tipo_recurso`. Si ya existe (mismo `url`), solo agregar la asignatura a su lista `asignaturas`. Enlazarlos en `recursos_web` de la asignatura. Nunca mezclarlos con la bibliografía.
   - **Marco pedagógico:** el Anexo "Estrategias de Enseñanza Sugeridas" / "Didácticas para el Aprendizaje" es texto institucional compartido. Compararlo contra `wiki/marco-pedagogico.md`: si esa página aún no tiene texto, transcribir el Anexo allí una sola vez; si coincide, no transcribirlo de nuevo; si difiere, no sobrescribir — avisar al usuario. Si coincide (o se acaba de transcribir), poner `sigue_marco: "[[marco-pedagogico]]"` en la asignatura y agregar la asignatura a `referenciado_por` del marco.
8. Actualizar `wiki/index.md` y agregar entrada al `wiki/log.md` (con los faltantes del paso 6 y las discrepancias del paso 7). Después, sugerir correr LINT y, cuando haya un manual de banco ingerido, CORRELATE.

### CORRELATE — Vincular un Resultado de Aprendizaje con fuentes y prácticas

1. Leer la `Asignatura` y calcular/confirmar `tipo_abordaje` desde `hp_totales`.
2. Si la asignatura es teórica: nunca buscar práctica — el RA cierra con `correlacion_estado: sin_candidato`, siempre. (`aplicacion_potencial` es un campo aparte, opcional, que llena el docente a mano si quiere; CORRELATE no lo toca.) Si es teórico-práctica: para cada RA calcular `score_RA`. Si < 0.40, cerrar con `sin_candidato` sin buscar.
3. Si >= 0.40: buscar en `wiki/fuentes/` (bibliografía para `bibliografia`, equipos de laboratorio para `requiere_practica`) los candidatos más afines por concepto, no por texto literal — el currículo suele estar en español y algunos manuales en inglés. Los candidatos de práctica son las entradas de `practicas` en el frontmatter de las fuentes `equipo-laboratorio`; una práctica se identifica por (fuente, código), porque `Exp13` se repite entre manuales.
4. De los candidatos, solo compiten por ser la mejor práctica los que el juez marca `coincide: true` — su `confianza_semantica` mide cuánto satisface el RA, no la seguridad del veredicto, así que un candidato que el juez dice que NO coincide nunca debe ganar por tener una confianza alta. Si ninguno coincide, `sin_candidato`. Decidir `correlacion_estado` según `confianza_final` del mejor candidato que sí coincide (ver tabla arriba). Registrar `correlacion_alternativas` con los candidatos no elegidos. Si hay candidato, `requiere_practica` enlaza la fuente (`[[fuente]]`) y `practica_experimentos` lista el experimento. Si el RA tiene `correlacion_revisado_por_docente: true`, no se reescribe: solo se anota en el log la propuesta automática.
5. Si el mejor candidato es dudoso, dejar `pendiente_revision` y preguntar al usuario en vez de forzar una correlación — nunca inventar una coincidencia.
6. Actualizar `wiki/log.md`. `correlaciones/matriz-ra-practica.md` no se toca: es una vista Dataview que lee el frontmatter de los RA en vivo desde Obsidian.

**Script:** `python src/correlate.py --indexar` (reconstruye el índice de prácticas) y después `--all` o `--asignatura CODIGO`; con `--ra CODIGO [CODIGO …]` solo esos RA (los que ANALIZAR-CAMBIOS dice que cambiaron: no se gasta en el resto). Con `--dry-run` solo calcula el gate de cada RA, sin LLM y sin escribir. Un RA con datos incompletos se informa y no detiene el resto; una asignatura rota de otro código nunca ensucia el informe de `--asignatura`. `correlacion_justificacion` guarda la razón del juez (prompt: `src/prompts/prompt-correlate.md`); si un RA ya no tiene candidato, se borra su práctica anterior.

### PLANEADOR — Programa de estudios de una asignatura

1. Leer la `Asignatura` y sus páginas de `wiki/resultados-aprendizaje/`. Si no hay ningún RA cargado, detenerse y avisar — no generar un plan vacío.
2. Calcular el cronograma de 14 semanas con la regla determinista de "Capa de generación" (sin LLM).
3. Redactar el programa de estudios en `generacion/planeador/{codigo}-planeador.md`: el LLM escribe un tema por semana de clase, RA por RA.
4. Actualizar `wiki/log.md`.

**Script:** `python src/planeador.py CODIGO`. Con `--sin-llm` escribe solo el cronograma. Un planeador que ya existe no se sobrescribe (para no perder ediciones a mano) salvo con `--forzar`.

### TEMARIO — Una sesión por semana de clase

Una sesión profunda no cabe en una sola llamada (saldría corta y superficial): se redacta en tres pasos, y de cada respuesta del modelo el código valida lo que puede.

1. Leer `generacion/planeador/{codigo}-planeador.md`, el RA que le toca a la semana, sus fuentes cargadas (las de `bibliografia` del RA y el manual de la práctica de referencia, si la hay) y las competencias de la asignatura. Nunca se genera temario para una semana de examen.
2. Calcular lo determinista (sin LLM): la cabecera, la alineación con el RA (enunciado, criterios de evaluación y competencias), el corte evaluativo, las horas de trabajo independiente, la lista de sesiones vecinas, los minutos de cada bloque del índice (ver "Capa de generación"), la numeración y la bibliografía.
3. **Paso 1 — el plan (LLM):** título, plataforma de referencia, continuidad curricular, prerrequisitos, resultados de la sesión (con su nivel de Bloom; cubren todos los Criterios de Evaluación del RA y ninguno ajeno) y las unidades: una introducción, de 3 a 6 conceptos, un caso de estudio, opcionalmente un análisis y una implementación, y la síntesis. Cada unidad trae su peso, de 4 a 10 términos de búsqueda **en español e inglés** (los libros suelen estar en inglés y el currículo en español) y los elementos que debe llevar (ecuación, tabla, gráfica, diagrama, código). Mínimos de la sesión: 2 unidades con tabla, 2 figuras y, si el tema usa ecuaciones, 3 unidades con ecuación.
4. **Paso 2 — cada unidad (LLM):** con los pasajes de las fuentes cargadas que mejor responden a sus términos de búsqueda (`src/pasajes.py`: BM25 en memoria, sin embeddings, sobre el texto completo de `raw/` —si el original es `.md` o `.txt`— y las páginas de `wiki/fuentes/`), un mínimo de palabras de prosa (220 la introducción, 320 cada concepto, 380 el caso, 220 el análisis, 180 la implementación; ×1,4 con una sesión de 4 h) y los elementos planeados. Cita las fuentes cargadas con `[n]`, y si se apoya en algo que no está cargado (el nombre del marcador es histórico: significa «sin página en `wiki/fuentes/`») lo marca en línea con `[FUENTE NO CARGADA EN raw/]` y da su referencia IEEE aparte — así detectar huecos bibliográficos es un `grep`, no otra llamada al LLM.
5. **Paso 3 — el cierre (LLM):** la síntesis y la reflexión actitudinal.
6. El LLM no escribe Markdown suelto sino bloques (`src/schema_temario.py`): las tablas, la numeración y la bibliografía las arma el código, y las gráficas y los diagramas los **dibuja el código** (`src/figuras.py`, matplotlib, paleta IUB) a partir de una especificación —funciones con sus parámetros, datos de una tabla, o nodos y flechas—: nunca hay puntos inventados, y las expresiones (de hasta 300 caracteres; una más larga o anidada hasta desbordar el analizador se devuelve al modelo como cualquier otro error) se evalúan con un evaluador propio, no con `eval`. Lo que no cumple (una tabla descuadrada, una expresión que no se entiende, menos palabras que el mínimo, una cita `[n]` a una fuente que no existe, la práctica de referencia ignorada, un criterio sin cubrir) se devuelve al modelo con el motivo, hasta 2 veces; un comando LaTeX que la presentación no admite se pide corregir, pero en el último intento no detiene la sesión.
7. Si la asignatura es teórico-práctica y el RA ya tiene una práctica asignada (`requiere_practica`), el caso de estudio se apoya en ella (nombra su código y sus mismas mediciones).
8. Guardar en `generacion/temarios/{codigo}-semanaNN.md` (las figuras, en `generacion/temarios/figuras/`), con su `estadisticas` en el frontmatter, y actualizar `wiki/log.md`. `correlaciones/matriz-temario-profundidad.md` (vista Dataview) muestra cuántas palabras, ecuaciones, tablas, figuras y pasajes de las fuentes tiene cada temario, y cuáles se redactaron sin apoyo en la bibliografía.

**Script:** `python src/temario.py CODIGO --semana N` o `--todas` (omite las semanas que ya tienen temario; `--forzar` las sobrescribe y reemplaza sus figuras). Exige el planeador de la asignatura y `matplotlib` (`pip install -r requirements.txt`; sin él falla antes de gastar una llamada). Una sesión cuesta de 8 a 12 llamadas al modelo, más los reintentos: `--todas` de una asignatura son ~100.

### PRESENTACIONES — Una presentación Beamer por temario

Corre sobre los temarios ya generados de una asignatura (todas las semanas de clase que tengan temario, o solo `--semana N`). **Cuesta una llamada al modelo por parte del temario** —la apertura y cada bloque de su índice temporizado: ~9 por temario, más los reintentos—; las diapositivas de cada parte se guardan en el plan, junto al `.tex`, con la huella de su texto. Mientras una parte no cambie **no se vuelve a pedir**: rehacer la presentación (otro docente, otro programa, otro contacto, una versión nueva del diseño, `--forzar`) no llama al modelo, y editar un bloque del temario solo vuelve a pedir ese bloque. Las presentaciones hechas antes del diseño 5 guardaban otro plan (el formato anterior no se reutiliza), así que rehacerlas **cuesta ~9 llamadas por temario** (LINT L14 y ACTUALIZAR-ESTRUCTURA lo distinguen y lo dicen).

**Antes de ejecutarlo, pregunta al usuario el nombre del docente y el programa académico** que van en la portada, el pie y el cierre de las presentaciones (nunca los inventes). El script los pregunta él mismo cuando lo ejecuta una persona en una terminal (propone lo último usado o lo que dice el wiki; Enter lo acepta); si lo ejecutas tú, o cualquier herramienta que capture la salida, no pregunta nada: pásalos con `--docente` y `--programa`. Sin ellos usa lo último usado o lo del wiki y lo dice en pantalla.

1. Leer cada temario de `generacion/temarios/` (y el planeador, para la «próxima sesión») y dividirlo en partes (sin LLM): la apertura y un bloque por cada encabezado `(Bloque k)`, con el título y los minutos del índice temporizado.
2. **Diapositivas (LLM):** por cada parte nueva o que cambió (o todas, con `--replanificar`), pedir al modelo sus diapositivas en LaTeX con `src/prompts/prompt-presentacion.md` y verificarlas con la lista de permitidos (ver «Presentaciones», arriba); guardarlas en `{codigo}-semanaNN.plan.json`. Una parte guardada se reutiliza solo si vuelve a pasar la verificación; si no, se pide otra vez. Si el modelo no cumple tras los reintentos, esa parte queda provisional.
3. **Diseño (sin LLM):** escribir `generacion/presentaciones/{codigo}/{codigo}-semanaNN.tex` con `src/diseno_iub.py` (preámbulo, portada, ruta de la sesión, separadores de bloque, las diapositivas del modelo, referencias y cierre) y verificar el documento completo. Si la verificación encuentra algo que podría ejecutarse al compilar, no se escribe el `.tex` (ver «Presentaciones»).
4. Escribir en el frontmatter del temario los campos `presentacion_*` (estado, archivo, avisos, huella del cuerpo del temario, fecha, versión del diseño, número de diapositivas, docente, programa y contacto) y anotar `wiki/log.md`. `correlaciones/matriz-temario-presentacion.md` (vista Dataview) muestra qué temario tiene su presentación, cuáles hay que revisar y cuáles faltan.
5. Las que ya están al día (mismo temario, docente, programa, contacto y versión del diseño, con todas sus partes en el plan) se omiten. Si `presentacion_estado` queda en `revisar`, abrir el `.tex` (o compilarlo) y mirar `presentacion_avisos` antes de usarla.

**Script:** `python src/presentaciones.py CODIGO` (o `--all` para todas las asignaturas con planeador; `--semana N [N…]` solo esas; `--forzar` rehace el `.tex` aunque esté al día —desde el plan guardado, sin LLM; las partes que falten en el plan, una llamada cada una—; `--replanificar` vuelve a pedir todas las partes aunque el temario no haya cambiado; `--docente "Nombre"`, `--programa "Programa"` y `--contacto correo` para la portada, el pie y el cierre —si no se indican, el docente y el programa se preguntan (o, sin terminal, se usan los de la última vez o los del wiki: el `docente_autor` y los programas de la asignatura) y el cierre va sin contacto—; `--sin-preguntar` no pregunta nunca; `--compilar` además genera el PDF si hay `pdflatex`).

### CORRELATE-PLANEADOR — Auditar el texto del planeador

Audita si el texto de la semana N realmente cumple el RA que le tocaba. El cronograma no se reabre, solo el texto. Misma forma que CORRELATE: juez LLM + Dataview, nunca edición a mano de los datos.

1. Para cada semana, comparar el texto generado contra el RA asignado.
2. Escribir el resultado en los campos `planeador_*` del RA.
3. `correlaciones/matriz-ra-planeador.md` se actualiza sola (vista Dataview).

**Script:** `python src/correlate_planeador.py CODIGO` o `--all`. Estados: `cubierto` / `revisar` / `desviado`; `planeador_semanas_con_problema` señala qué semanas. Un planeador sin temas (generado con `--sin-llm`) no se audita.

### CORRELATE-BIBLIOGRAFIA — ¿El temario necesita una fuente que no está en `raw/`?

Escribe en los campos `bibliografia_*` del propio temario; `correlaciones/matriz-temario-bibliografia.md` los refleja. Corre en dos vías, por costo:

1. Escanear el marcador `[FUENTE NO CARGADA EN raw/]` en el temario (gratis; el marcador dice "raw/" mas su significado real es "sin página en `wiki/fuentes/`" — ver TEMARIO, paso 5).
2. Solo si no lo encuentra, llamar a un juez LLM de respaldo que compara la profundidad de lo escrito contra la `bibliografia` del RA (el contexto que recibe es el resumen de cada fuente — `## Resumen` + `## Puntos clave` de su página, hasta ~1800 caracteres).

Estados: `cubierta` / `revisar` / `vacio_detectado`. Mismo principio de siempre: nunca fabricar una cobertura falsa — ante la duda, dejar `revisar` y preguntar al usuario.

**Script:** `python src/correlate_bibliografia.py CODIGO` o `--all`. Si el RA no tiene fuentes cargadas enlazadas en `bibliografia`, queda `revisar` (`bibliografia_via: sin_bibliografia`) sin gastar una llamada al LLM.

### INGEST — Incorporar una fuente nueva

1. Leer el archivo en `raw/` (o el contenido proporcionado)
2. Conversar con el usuario sobre puntos clave si es útil
3. Crear `wiki/fuentes/nombre-fuente.md`
4. Identificar entidades y conceptos mencionados:
   - Si ya tienen página: actualizar con nueva información, incrementar `fuentes_count`
   - Si no tienen página: crear nueva en `wiki/entidades/` o `wiki/conceptos/`
5. Actualizar `wiki/index.md` con la nueva fuente y páginas creadas/modificadas
6. Agregar entrada al `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] ingest | Título de la fuente
   - Creadas: lista de páginas nuevas
   - Actualizadas: lista de páginas modificadas
   - Notas: observaciones relevantes
   ```

### QUERY — Responder una pregunta

1. Leer `wiki/index.md` para identificar páginas relevantes
2. Leer las páginas identificadas
3. Sintetizar respuesta con citas `[[fuente]]`
4. Preguntar al usuario si quiere archivar la respuesta como página en `wiki/consultas/`
5. Si sí: crear `wiki/consultas/nombre-consulta.md` y actualizar index y log

### LINT — Revisión de salud del wiki

Buscar y reportar:
- Páginas sin enlaces entrantes (huérfanas)
- Contradicciones entre páginas
- Entidades/conceptos mencionados pero sin página propia
- Referencias a fuentes que aún no están en `wiki/fuentes/`
- Páginas con `fuentes_count: 1` que podrían necesitar más investigación
- Capa curricular: `tipo_abordaje` declarado que no coincide con `hp_totales` (rechazar)
- Capa curricular: cualquier `requiere_practica` en un RA de una asignatura teórica (prohibido; solo se permite `aplicacion_potencial`)
- Capa curricular: RA de una asignatura teórico-práctica con `score_RA` < 0.40 — advertir "RA sin evidencia semántica de práctica pese a HP>0". Con los pesos actuales no puede ocurrir (la señal estructural sola ya da 0.5): la regla protege ante un cambio de pesos.
- Sugerir nuevas fuentes o preguntas de investigación

**Script:** `python src/lint.py` hace las comprobaciones mecánicas (L01 frontmatter y `tipo` por carpeta · L02 asignatura válida (incluye `tipo_abordaje` acorde con `hp_totales`, `hp_totales <= had_totales` y ninguna hora o crédito negativo) · L03 `requiere_practica` en teóricas · L04 RA válidos y con código canónico · L05 RA huérfanos · L06 enlaces rotos · L07 códigos duplicados · L08 manuales de banco y sus prácticas · L09 el aviso de `score_RA` · L10 temarios en semanas de examen o sin planeador · L11 asignaturas que su programa no lista · L12 nombre de archivo de un RA que no coincide con su `codigo` — aviso, porque `correlate.py`, `temario.py` y `correlate_planeador.py` localizan el RA por `{codigo}.md`; el efecto real ya aparece como L05/L06 · L13 `had_totales` + `hti_totales` no cuadra con `creditos × 48` — aviso; `had_totales` ya incluye las horas prácticas, no se suman aparte · L14 presentaciones — aviso: un temario cuya presentación `.tex` ya no existe, quedó desactualizada (el temario cambió después de generarla) o se hizo con otra versión del diseño, o un `.tex` que ningún temario registra; el aviso dice cuánto cuesta rehacerla: sin LLM si el `.plan.json` tiene, verificadas, todas las partes del temario con la misma huella, y si no, una llamada al modelo por cada parte que falta o cambió (un plan de un diseño anterior al 5, corrupto o de otra versión del temario no vale) · L15 figuras del temario — aviso: un temario que incluye una figura (`figuras/x.png`) que ya no existe en `generacion/temarios/figuras/`, o una figura que ningún temario incluye). Sale con código 1 si hay errores; los avisos no fallan. Las comprobaciones de contenido (contradicciones, conceptos sin página, huérfanas del wiki base) las hace el LLM.

### ANALIZAR-CAMBIOS — Qué actualizar (y qué no) cuando llega algo nuevo

Cuando llega un currículo nuevo o una versión nueva de uno, un manual de banco o bibliografía nueva, **corre esto antes de releer o regenerar nada**. No usa ningún LLM y no escribe en `wiki/` ni en `generacion/`: dice qué hay que rehacer y qué sigue vigente, para no gastar llamadas (tokens) en releer un currículo entero ni en regenerar temarios que no cambiaron (una sesión son ~10 llamadas). Trabaja en dos planos:

1. **`raw/` contra la línea base** (`memory_store/estado-cambios.json`: cómo estaba `raw/` la última vez que se corrió con `--confirmar`; es de la instancia y no viaja en las copias). Un documento es nuevo, modificado o eliminado (la huella no cambia por saltos de línea de Windows ni por espacios al final).
   - **Currículo modificado:** qué **secciones** cambiaron (por encabezado, en negrita o por el rótulo suelto de un PDF convertido) y a qué página del wiki corresponde cada una —«Información de Créditos Académicos» → campos de la asignatura; «Resultados de Aprendizaje» → páginas de RA; competencias, estrategias, recursos, bibliografía, webgrafía, aprobación, aprendizajes previos, anexo—, con lo que cada cambio arrastra aguas abajo y cuántos tokens hay que leer de los que tiene el documento. `--detalle` trae el texto de esas secciones: INGEST-CURRICULAR lee solo eso y actualiza solo esas páginas. Una sección que no reconoce se marca «sin reconocer»: se lee y se decide.
   - **Manual de banco:** qué **experimentos** cambiaron (nuevos, modificados, eliminados) → `python src/ingest_manual.py RUTA --fuente NOMBRE --solo Exp3 Exp5`; y qué RA volver a correlacionar: los de gate abierto sin práctica aceptada y los que apuntan a un experimento que cambió (no toca los de la decisión del docente, ni filtra por palabras: el RA está en español y el manual suele estar en inglés).
   - **Libro o norma nueva o modificada:** a qué RA les serviría —cuántos de los conceptos de su `contenido_conceptual` aparecen en el texto, por palabras y sin embeddings—, si ya la citan, y qué temarios de esos RA podrían ganar (opcional, marcando los que se escribieron sin apoyo en las fuentes); si una referencia `[FUENTE NO CARGADA EN raw/]` de un temario se parece a la fuente, lo dice. Sugiere a cuáles mirar: **no decide la bibliografía de un RA** (nunca se fabrica una cobertura).
   - Un PDF u otro binario no se lee: se avisa que hay que convertirlo a Markdown.
2. **`wiki/` contra `generacion/`** (sin línea base: recalcula lo determinista, así que sirve también tras editar el wiki a mano): el cronograma de 14 semanas y la duración de la sesión contra el planeador; y, en cada temario, el RA de su semana, su duración, las horas de trabajo independiente y la alineación con el RA (sección 2) contra lo que hoy dice el wiki; y la correlación de cada RA (gate, score, manual más nuevo, práctica que ya no existe, gate cerrado). Separa lo que **obliga** a rehacer una sesión (cambia el RA de la semana o la duración) de lo **leve** (solo la cabecera o la alineación: el resto sigue vigente) y de lo **opcional** (una fuente nueva).

Flujo: `python src/analizar_cambios.py` (`--asignatura CODIGO`, `--detalle`, `--json`) → actualizar las páginas del wiki que indica la sección 1 → volver a correrlo: ahora la sección 2 muestra lo que quedó desfasado en la generación → ejecutar los comandos de su **plan mínimo** (`correlate.py --asignatura X --ra …`, `planeador.py X --forzar`, `temario.py X --semana N --forzar`, `presentaciones.py` —~9 llamadas por temario rehecho: una por cada parte que cambió—, con el costo en llamadas frente a regenerar todo) → `python src/analizar_cambios.py --confirmar` (todo `raw/`, o solo `--confirmar RUTA`) para fijar la línea base. La primera corrida no tiene línea base: los documentos con página en el wiki (por su línea `**Origen:**`) se suponen incorporados. Es una guía, no un juez: lo que propone se revisa con el docente antes de ejecutarlo (`pisa las ediciones a mano` del planeador, por ejemplo).

### ACTUALIZAR-ESTRUCTURA — Llevar una versión nueva de la plantilla a una copia

La plantilla evoluciona (scripts, prompts, matrices de `correlaciones/`, reglas, esquema) y cada copia hecha con `nuevo-cerebro.py` se queda en la versión con que nació. **`python src/actualizar_estructura.py --origen RUTA`** (una carpeta o un ZIP con la plantilla nueva; `--destino` es la copia, por omisión la carpeta actual) lleva los cambios sin tocar el contenido. Decide archivo por archivo con tres políticas, según la ruta:

- **plantilla** (`src/`, prompts, `correlaciones/*.md`, `CLAUDE.md`, `README.md`, `config/SCHEMA.md`, `requirements.txt`, `AGENTS.md`…): se actualizan. Si el archivo **no se editó** en la copia (su huella es la de `config/manifiesto.json`, lo instalado) se reemplaza; si se editó y la plantilla también cambió es un **conflicto**: se deja el tuyo y la versión nueva queda al lado como `archivo.nuevo` para fusionar. Un archivo editado que la plantilla no cambió se deja («tuyo»); lo que la plantilla ya no trae es **obsoleto** (se avisa; `--eliminar-obsoletos` lo quita).
- **semilla** (`wiki/index.md`, `log.md`, `marco-pedagogico.md`, **solo los 5 `.json` de configuración de `.obsidian/` que trae la plantilla** —`app`, `appearance`, `core-plugins`, `graph` y `workspace`—, los logos de `config/framework_iub/`): se crean si faltan y **nunca se pisan** (los logos son los de tu institución). Cualquier otra ruta bajo `.obsidian/` (`plugins/`, `snippets/`, `themes/`, `community-plugins.json`, `hotkeys.json`…) se **rechaza**: un plugin es JavaScript que Obsidian ejecuta al abrir el vault (y el README pide instalar Dataview, que quita el modo restringido).
- **instancia** (`raw/`, `wiki/`, `generacion/`, `memory_store/`): jamás se toca, salvo una **migración** con respaldo.

Por omisión solo **muestra** lo que haría (prueba en seco, con el resumen de qué cambia en cada archivo: funciones o secciones que se agregan, quitan o modifican, y qué hay que hacer después —instalar dependencias, que las presentaciones se rehacen desde su plan (sin LLM) si el diseño cambió, salvo las de un diseño anterior al 5, cuyo plan era de otro formato y cuestan ~9 llamadas por temario (las cuenta en la copia), enlazar una vista nueva en el índice—, sin gastar de más: lo ya generado sigue vigente). Con `--aplicar` respalda cada archivo que va a cambiar en `memory_store/respaldos/estructura-AAAAMMDD-HHMMSS/`, aplica los cambios y las **migraciones** de contenido de `src/migraciones.py` (un campo que se renombra en las páginas, uno nuevo con su valor por defecto…: idempotentes, con respaldo y sin escribir en seco), actualiza `config/manifiesto.json` (la versión y la huella de lo instalado), anota `wiki/log.md` y corre `lint.py`. `--deshacer` restaura el último respaldo. `--sobrescribir` reemplaza también los conflictos (con respaldo) y `--conservar RUTA` da por bueno tu archivo (deja de marcarse como conflicto hasta que la plantilla lo cambie otra vez). Solo usa la biblioteca estándar: corre aunque la versión nueva pida dependencias que la copia aún no tiene —**salvo las migraciones, que sí las necesitan** (PyYAML y `vault`/pydantic, para leer y escribir páginas): si hay migraciones pendientes y faltan, `--aplicar` se detiene antes de escribir nada («`pip install -r requirements.txt` y repite») y la prueba en seco lo avisa; una página que una migración no puede leer (YAML roto, cabecera sin cerrar) no se migra pero se **informa**, nunca se salta en silencio.

**Seguridad: qué se instala y qué se ejecuta.** Solo se instalan como plantilla estas rutas: `src/**` (con `src/prompts/`), `correlaciones/*.md`, `config/SCHEMA.md`, `config/nuevo-cerebro.py`, `config/nuevo-cerebro.ps1`, los `.md` de la raíz y `requirements.txt` (más `config/manifiesto.json`, que el script escribe) y se crean las semillas que faltan. **Cualquier otra ruta del paquete es «desconocida» y no se instala nunca**, y lo que empieza por `.claude/`, `.vscode/`, `.git/` o `.github/`, todo lo de `.obsidian/` que no sea uno de sus 5 `.json` de configuración (`plugins/`, `snippets/`, `themes/` y `community-plugins.json` están además en la lista de rechazadas, aunque un día se amplíe la de semillas) y cualquier ruta que salga de la copia (`..`, absolutas, `C:`) se **rechaza siempre**: pueden definir comandos que el asistente, el editor u Obsidian ejecutan solos. El informe las lista con un aviso; un paquete de la plantilla oficial no trae ninguna, así que si no esperabas alguna, desconfía. Además, **aplicar un paquete ejecuta su código**: si trae otra versión de `src/actualizar_estructura.py`, `--aplicar` ejecuta la del paquete (sus reglas y migraciones son las que valen) e imprime antes su SHA-256; por eso **solo se aplican paquetes de la plantilla oficial**. La prueba en seco (sin `--aplicar`) nunca ejecuta código del paquete: muestra el informe con el script local y avisa, con esa misma huella, que al aplicar se ejecutaría el del paquete; `--sin-delegar` usa siempre el local. Una copia hecha antes de los manifiestos no sabe qué archivos editó: todo lo que difiere queda «sin base» y no se pisa sin `--sobrescribir`, salvo que se indique con `--base RUTA` la plantilla con que se hizo la copia (carpeta o ZIP): entonces solo lo que editaste es conflicto. La primera vez se corre el script desde la plantilla nueva (`python RUTA/src/actualizar_estructura.py --destino ../MiCopia [--base ../plantilla-vieja]`).

Para quien mantiene la plantilla: `--generar-manifiesto` (al terminar cada versión: `config/manifiesto.json`), `--verificar-manifiesto` (falla si quedó viejo; `test_actualizar_estructura.py` lo exige) y `--empaquetar ZIP [--desde VERSION_ANTERIOR]` (un ZIP con la plantilla, o solo con lo que cambió respecto de la versión anterior). Un cambio de esquema en las páginas (un campo que se renombra) se entrega con su migración en `src/migraciones.py` —las copias que salten varias versiones corren todas las que les falten, en orden— y con la versión nueva en `config/SCHEMA.md`.

---

## Reglas generales

- **Nunca modificar archivos en `raw/`**
- Siempre actualizar `wiki/index.md` y `wiki/log.md` en cada operación
- Mantener los enlaces internos `[[...]]` consistentes — si renombras una página, busca y actualiza todas las referencias
- Cuando una fuente contradice información existente: no silenciar la contradicción, documentarla explícitamente en la sección correspondiente
- Ser conciso en resúmenes; ser comprensivo en páginas de entidades y conceptos
- El usuario lee el wiki en Obsidian — usar todas las funciones: `[[links]]`, `#etiquetas`, frontmatter para Dataview

---

## Sesión nueva — checklist de inicio

Al comenzar una nueva sesión de trabajo:
1. Leer `wiki/log.md` (últimas 10 entradas) para recordar contexto reciente
2. Leer `wiki/index.md` para tener el mapa del wiki
3. Preguntar al usuario qué quiere hacer: INGEST / INGEST-CURRICULAR / QUERY / LINT / CORRELATE / PLANEADOR / TEMARIO / PRESENTACIONES / CORRELATE-PLANEADOR / CORRELATE-BIBLIOGRAFIA / ANALIZAR-CAMBIOS / ACTUALIZAR-ESTRUCTURA / otro. Si llegó un documento nuevo o una versión nueva, empezar por ANALIZAR-CAMBIOS.
