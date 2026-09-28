# Cerebro Docente

**Plantilla en limpio** de un segundo cerebro para correlacionar **currículo**, **bibliografía** y **manuales de banco de laboratorio**, y a partir de esa correlación generar planeadores y temarios de clase. Es un vault de Obsidian que mantiene un asistente de IA (el que prefieras: no depende de ningún modelo); las reglas que sigue están en [CLAUDE.md](CLAUDE.md).

> Solo estructura, reglas y código de apoyo: no contiene currículos, fuentes ni páginas de contenido. Cada copia se llena con los documentos de su propio programa.

## Cómo crear una copia

**Con el script (Windows, macOS y Linux; solo necesita Python):**

```
python config/nuevo-cerebro.py ../Programa_X --nombre "Programa X"
```

En Windows también existe `powershell -ExecutionPolicy Bypass -File config\nuevo-cerebro.ps1 -Destino "C:\Ruta\Programa_X" -Nombre "Programa X"`. Copia la plantilla (incluida la carpeta oculta `.obsidian`) sin `memory_store/` ni `__pycache__/`, deja el `wiki/log.md` de la copia vacío y avisa si la carpeta de origen trae contenido de una instancia (documentos en `raw/`, páginas en `wiki/`, salida en `generacion/`): copia siempre desde la plantilla en limpio. **A mano:** copiar la carpeta, renombrarla, no copiar `memory_store/` y empezar el `wiki/log.md` de cero.

> **Si tu vault vive en una carpeta sincronizada (Google Drive, OneDrive…):** `memory_store/` es el índice vectorial de las prácticas (LanceDB) — cambia con cada `--indexar` y no aporta nada al contenido del wiki, así que sincronizarlo solo gasta cuota y puede generar conflictos de archivo. Puedes sacarlo de la sincronización apuntándolo fuera con la variable de entorno `CEREBRO_DB_PATH` (por defecto, `memory_store/lancedb` dentro del vault). Aparte, si usas el plugin **Sync** de Obsidian (viene activado en `.obsidian/core-plugins.json`) junto con Drive/OneDrive sincronizando la misma carpeta, los dos pueden chocar por escribir el mismo archivo a la vez; decide tú cuál de los dos usar — no lo desactivamos por ti.

Después, en la copia:

1. Abrirla como vault en Obsidian e instalar el plugin **Dataview** (Ajustes → Complementos de la comunidad).
2. `pip install -r requirements.txt` (Python 3.10 o superior) y configurar el proveedor de IA (ver «Configurar el modelo de IA», abajo).
3. Si trabajas con un asistente de IA, abrirlo en esa carpeta: Claude Code carga `CLAUDE.md` por sí solo; otras herramientas leen `AGENTS.md` o `GEMINI.md`, que apuntan a él. Si la tuya no carga ninguno, pídele que lea `CLAUDE.md` antes de empezar.
4. Colocar los documentos en `raw/` y seguir el flujo de trabajo.

## Actualizar una copia

La plantilla sigue mejorando (scripts, prompts, matrices de `correlaciones/`, reglas) y cada copia se queda en la versión con que nació. Para llevarle una versión nueva **sin tocar sus documentos, su wiki ni lo generado**:

```
python src/actualizar_estructura.py --origen ../Cerebro_Docente                 # qué cambiaría (no escribe nada)
python src/actualizar_estructura.py --origen plantilla-nueva.zip --detalle       # también qué cambia en cada archivo
python src/actualizar_estructura.py --origen ../Cerebro_Docente --aplicar        # respalda, actualiza, migra, anota el log y corre lint
python src/actualizar_estructura.py --deshacer                                   # restaura el respaldo de la última actualización
```

`--origen` es una carpeta o un ZIP con la plantilla nueva; `--destino` es la copia (por omisión, la carpeta actual). Decide archivo por archivo: el código y las reglas (`src/`, prompts, `correlaciones/`, `CLAUDE.md`…) se actualizan si **no los editaste**; si los editaste y la plantilla también cambió es un **conflicto** (se deja el tuyo y la versión nueva queda al lado como `archivo.nuevo`; `--sobrescribir` la reemplaza y `--conservar RUTA` da por bueno el tuyo); los esqueletos (`wiki/index.md`, los 5 `.json` de configuración de `.obsidian/` y el tema de tu institución) se crean si faltan pero no se pisan (plugins, snippets y temas de `.obsidian/` no se instalan nunca); `raw/`, `wiki/`, `generacion/` y `memory_store/` no se tocan. Los cambios de esquema de las páginas llegan como migraciones (`src/migraciones.py`), con respaldo; estas sí necesitan las dependencias (si faltan y hay migraciones pendientes, `--aplicar` se detiene antes de escribir nada y pide `pip install -r requirements.txt`). El resto solo usa la biblioteca estándar, así que corre aunque la versión nueva pida dependencias que aún no instalaste; después, `pip install -r requirements.txt` si la salida lo dice. **Seguridad:** solo se instalan las rutas de la plantilla (`src/`, `correlaciones/*.md`, `config/SCHEMA.md`, `config/nuevo-cerebro.*`, los `.md` de la raíz, `requirements.txt`); cualquier otra ruta del paquete es «desconocida» y no se instala, y `.claude/`, `.vscode/`, `.git/`, `.github/` y todo lo de `.obsidian/` salvo sus 5 `.json` de configuración (un plugin es código que Obsidian ejecuta) se rechazan siempre. Y **aplicar un paquete ejecuta su código** (si trae otra versión del script, `--aplicar` ejecuta la suya): aplica solo paquetes de la plantilla oficial; la prueba en seco nunca ejecuta código del paquete. **Una copia hecha antes de esta función** no sabe qué archivos editaste: la primera vez córrelo desde la plantilla nueva (`python RUTA/src/actualizar_estructura.py --destino ../MiCopia`); todo lo que difiere queda «sin base» y no se pisa sin `--sobrescribir`, salvo que le des con `--base RUTA` la plantilla con que se hizo la copia (carpeta o ZIP): entonces solo lo que editaste es conflicto. Para quien mantiene la plantilla: `--generar-manifiesto` al terminar cada versión (`config/manifiesto.json` guarda la versión y la huella de cada archivo) y `--empaquetar ZIP [--desde VERSION_ANTERIOR]`. Detalle en `CLAUDE.md` § ACTUALIZAR-ESTRUCTURA.

## Configurar el modelo de IA

Los scripts de `src/` que necesitan un LLM (el juez de CORRELATE, la redacción de temas y temarios, las auditorías, la extracción de manuales) y los embeddings de `correlate.py --indexar` usan el SDK `openai`, que habla con **cualquier servidor compatible con la API de OpenAI** (OpenAI, Azure OpenAI, OpenRouter, Ollama, LM Studio, vLLM…). Se configuran con variables de entorno, sin tocar el código:

| Variable | Para qué | Por defecto |
|---|---|---|
| `OPENAI_API_KEY` (o `CEREBRO_API_KEY`) | clave del proveedor; con un servidor propio no hace falta | — |
| `CEREBRO_BASE_URL` (o `OPENAI_BASE_URL`) | dirección del servidor compatible | la de OpenAI |
| `CEREBRO_MODELO` | modelo de chat | `gpt-4o` |
| `CEREBRO_SALIDA` | cómo se obtiene el JSON: `estructurada` (la nativa de la API de OpenAI), `json` (modo JSON del servidor) o `texto` (el JSON se pide en el prompt, para servidores sin ninguno de los dos) | `estructurada` |
| `CEREBRO_MODELO_EMBEDDINGS` | modelo de embeddings | `text-embedding-3-small` |
| `CEREBRO_EMBEDDINGS_BASE_URL`, `CEREBRO_EMBEDDINGS_API_KEY` | solo si los embeddings vienen de otro proveedor que el chat | las de arriba |
| `CEREBRO_DB_PATH` | dónde vive el índice vectorial | `memory_store/lancedb` |

En los modos `json` y `texto` el esquema va en el prompt y la respuesta se valida con Pydantic (con hasta 2 reintentos que le muestran el error al modelo), así que sirven para modelos sin salida estructurada nativa. Si cambias el modelo de embeddings, reindexa con `python src/correlate.py --indexar`: el índice recuerda con cuál se hizo y da un error claro si no coincide. Un servidor local, por ejemplo con Ollama (`export` en bash, `$env:` en PowerShell):

```
CEREBRO_BASE_URL=http://localhost:11434/v1  CEREBRO_MODELO=llama3.1  CEREBRO_SALIDA=json  CEREBRO_MODELO_EMBEDDINGS=nomic-embed-text
```

Sin ninguna API también se puede trabajar: `planeador.py --sin-llm` y `correlate.py --dry-run` no llaman a ningún LLM, y cada operación se puede hacer siguiendo a mano los pasos de `CLAUDE.md` (o con el asistente que uses, que es quien las ejecuta).

## Regla central

`tipo_abordaje` de cada asignatura (teórica / teórico-práctica) se **deriva** de `hp_totales` (horas prácticas del encabezado curricular) — nunca se declara a mano. Un RA de una asignatura teórica nunca busca práctica: queda `correlacion_estado: sin_candidato`; `aplicacion_potencial` es un campo aparte, opcional, que llena el docente a mano si quiere documentar una aplicación fuera de la cobertura evaluable — CORRELATE nunca lo escribe. Detalle en `CLAUDE.md` § "Capa curricular".

## Convenciones de la institución

La plantilla asume tres convenciones de la institución para la que se construyó, no reglas universales:

- **`had_totales` ya incluye las horas prácticas (`hp_totales`)**, no son columnas independientes que se deban sumar. De ahí depende `derivar_horas_sesion` en `src/schema_planeador.py` (la duración de la sesión sale solo de `had_totales`) y el validador de `Asignatura` en `src/schema_extraccion.py` (rechaza `hp_totales > had_totales`).
- **1 crédito = 48 horas** (`had_totales + hti_totales`), en `HORAS_POR_CREDITO` de `src/lint.py` (regla L13, aviso).
- **Las presentaciones llevan fija la marca IUB:** la paleta del Manual de Identidad IUB 2025 en `COLORES` de `src/diseno_iub.py`, la marca como texto (`MARCA`, «IUB», e `INSTITUCION` en ese mismo archivo: las presentaciones no usan imágenes), la tipografía (`avant`) y las cajas y estilos TikZ en su preámbulo, y `PROGRAMA_POR_DEFECTO` en `src/presentaciones.py`. Los logos de `config/framework_iub/logos/` se conservan, pero las presentaciones ya no los usan.

Si replicas esta plantilla para una institución que las defina distinto, revisa esos tres puntos: `HORAS_POR_CREDITO` en `src/lint.py`; `derivar_horas_sesion` junto con el validador de `Asignatura` si ahí las HP no forman parte de las HAD; y, para otra marca, cambia lo que lista la tercera viñeta. Detalle en `CLAUDE.md` § "Capa de generación", § "Presentaciones" y § LINT.

## Estructura

```
raw/                                fuentes inmutables (solo lectura)
├── curriculos/                     documentos curriculares, agrupados por programa
├── manuales-laboratorio/           manuales de los bancos, una carpeta por banco
├── bibliografia/                   libros, guías y datasheets
├── normas-tecnicas/                NTC, IEC, ISA, RETIE…
└── assets/                         imágenes

wiki/                               conocimiento estructurado
├── index.md · log.md · marco-pedagogico.md
├── fuentes/                        libros, normas y manuales de banco (una página por fuente)
├── entidades/ · conceptos/ · consultas/
├── programas/ · asignaturas/ · resultados-aprendizaje/ · competencias/ · recursos-web/

correlaciones/                      vistas Dataview de auditoría (matriz-ra-practica, matriz-ra-planeador, matriz-temario-bibliografia, matriz-ra-bibliografia, matriz-temario-presentacion, matriz-temario-profundidad)
generacion/{planeador,temarios}/    salida generada a partir de wiki/ (los temarios llevan sus figuras PNG en temarios/figuras/)
generacion/presentaciones/          una presentación Beamer (.tex, pdfLaTeX) por temario, con el diseño institucional IUB: una carpeta autocontenida por asignatura (el .tex y su plan: sin imágenes, todo en TikZ)
src/                                protocolos hechos script (con analizar_cambios.py y actualizar_estructura.py), esquemas Pydantic, prompts y tests
config/                             SCHEMA.md (ontología y gobernanza de referencia), nuevo-cerebro.py (y .ps1 en Windows: crean copias limpias), manifiesto.json (versión y huella de cada archivo de la plantilla, para actualizar copias) y framework_iub/ (los logos institucionales IUB, que las presentaciones ya no usan)
.obsidian/                          configuración de Obsidian del vault
CLAUDE.md                           reglas y protocolos, para cualquier asistente de IA (el nombre es histórico)
AGENTS.md · GEMINI.md               punteros a CLAUDE.md para los asistentes que buscan esos nombres
requirements.txt                    dependencias de src/
```

Los manuales de banco **no** tienen carpeta propia en `wiki/`: son páginas de `wiki/fuentes/` con la etiqueta `equipo-laboratorio` y sus experimentos en el frontmatter (`practicas:`).

## Flujo de trabajo

Los comandos se ejecutan desde la raíz del vault.

| # | Qué | Cómo |
|---|---|---|
| 1 | Cargar los documentos | copiarlos a `raw/curriculos/`, `raw/manuales-laboratorio/`, `raw/bibliografia/`, `raw/normas-tecnicas/` |
| 2 | Currículos → programas, asignaturas, RA y competencias; libros y normas → `wiki/fuentes/` | **INGEST-CURRICULAR** e **INGEST**: los ejecuta el LLM siguiendo `CLAUDE.md` |
| 3 | Manuales de banco → `practicas:` de su página de `wiki/fuentes/` | `python src/ingest_manual.py raw/manuales-laboratorio/BANCO/manual.md --fuente NOMBRE` (con `--solo-dividir` lista los experimentos sin LLM) |
| 4 | Revisar la salud del vault | `python src/lint.py` |
| 5 | Indexar las prácticas | `python src/correlate.py --indexar` |
| 6 | **CORRELATE**: proponer la práctica de cada RA | `python src/correlate.py --all` (`--asignatura CODIGO`; con `--dry-run` solo calcula el gate, sin LLM) |
| 7 | Revisión del docente | `correlaciones/matriz-ra-practica.md`; al resolver un caso a mano, marcar `correlacion_revisado_por_docente: true` o la siguiente corrida lo sobrescribe |
| 8 | **PLANEADOR**: programa de 14 semanas | `python src/planeador.py CODIGO` (`--sin-llm` solo el cronograma) |
| 9 | **TEMARIO**: una sesión por semana de clase, en tres pasos (plan → cada unidad, con los pasajes de las fuentes cargadas → cierre), con ecuaciones, tablas, gráficas y diagramas; unas 10 llamadas al modelo por sesión | `python src/temario.py CODIGO --todas` |
| 10 | Auditar el texto generado | `python src/correlate_planeador.py CODIGO` · `python src/correlate_bibliografia.py CODIGO` |
| 11 | **PRESENTACIONES**: una presentación Beamer por temario (una llamada al modelo por parte del temario —la apertura y cada bloque: ~9—; rehacerla mientras el temario no cambie no cuesta llamadas, y si cambia un bloque solo se vuelve a pedir ese) | `python src/presentaciones.py CODIGO` (`--semana N`, `--all`, `--forzar`, `--replanificar`, `--docente`, `--programa`, `--contacto`, `--sin-preguntar`, `--compilar`): **en una terminal pregunta el nombre del docente y el programa** (propone lo último usado o lo que dice el wiki; Enter lo acepta); ejecutado por un asistente de IA no pregunta, y este los pide en el chat y los pasa con `--docente` y `--programa`. Qué temario ya tiene la suya: `correlaciones/matriz-temario-presentacion.md` |
| 12 | **ANALIZAR-CAMBIOS**: cuando llega un currículo nuevo o una versión nueva, un manual o bibliografía nueva, **antes** de releer o regenerar nada (sin LLM y sin escribir en `wiki/`) | `python src/analizar_cambios.py` (`--detalle`, `--asignatura CODIGO`, `--json`): qué secciones de un currículo cambiaron y a qué página del wiki tocan (se leen solo esas), qué experimentos de un manual cambiaron (`ingest_manual.py --solo`), a qué RA les sirve una fuente nueva, y qué RA volver a correlacionar (`correlate.py --ra`) o qué semanas rehacer, con el costo en llamadas frente a regenerar todo. Al terminar: `--confirmar` fija la línea base |
| 13 | **ACTUALIZAR-ESTRUCTURA**: llevar una versión nueva de la plantilla a una copia | `python src/actualizar_estructura.py --origen RUTA` (ver «Actualizar una copia») |

Las presentaciones salen en `generacion/presentaciones/CODIGO/` (el `.tex` y su plan `.plan.json`; sin imágenes): para verlas en PDF, comprime esa carpeta y súbela a Overleaf (compilador **pdfLaTeX**), o compila en local con MiKTeX/TeX Live (`pdflatex archivo.tex`, dos pasadas; `--compilar` lo hace si `pdflatex` está instalado). Generar el `.tex` no requiere LaTeX. **Cómo se hacen (diseño 5, al estilo de las presentaciones de ejemplo del docente):** el temario se divide en partes —la apertura (metadatos y resultados de aprendizaje) y cada bloque de su índice temporizado— y, por cada una, el modelo escribe sus diapositivas en LaTeX con las directrices de un experto en LaTeX y en presentaciones académicas (el prompt reúne la instrucción del docente y su skill `experto-en-latex`): cajas de color en columnas, diagramas de flujo y esquemas en TikZ, gráficas pgfplots con los datos o las ecuaciones del temario, circuitos en circuitikz, tablas con encabezado oscuro y código en un panel oscuro. Las figuras del temario (PNG) no se usan: si aportan, el modelo las redibuja en TikZ o pgfplots. El código (`src/diseno_iub.py`, sin LLM) pone el preámbulo —paleta del Manual de Identidad IUB 2025, `avant` sans serif, franja #121023 con el título en amarillo #FFDF2D y «IUB», pie con el módulo, el docente y la semana, las cajas tcolorbox y los estilos TikZ— y la portada, la ruta de la sesión con los minutos de cada bloque, un separador «BLOQUE 0k» por bloque, las referencias y el cierre. **Seguridad:** el LaTeX del modelo se compila, así que pasa por una **lista de comandos permitidos** (`src/latex_seguro.py`: texto, matemáticas, tablas, TikZ, pgfplots, circuitikz y las cajas del diseño; nada de `\input`, `\write18`, `\def`, `\csname`, `\includegraphics`, `\addplot table`, `saveto=`… ni `^^`); lo que no la cumple vuelve al modelo con el motivo, y si no la cumple tras los reintentos esa parte queda con una diapositiva provisional. Un plan guardado se vuelve a verificar antes de reutilizarlo, un `.tex` en el que la verificación estática del documento completo encuentre algo que podría ejecutarse no se escribe ni se compila, y `pdflatex` corre siempre con `-no-shell-escape` y con `openin_any=p` y `openout_any=p` (TeX Live no le deja leer ni escribir fuera de la carpeta de la presentación). Las **opciones** de TikZ, pgfplots, circuitikz y las cajas también van con lista de permitidos (colores, grosores, los estilos del diseño, posiciones, tamaños, fuentes, formas, ejes y leyendas, componentes de circuitos), y los manejadores de claves (`/.code`, `/.style`…) y `\tikzset` no se admiten. **Compila en Overleaf** (aísla cada proyecto): es lo recomendado; `--compilar` en local lleva esas restricciones, pero MiKTeX puede no respetar esas dos variables de TeX Live. **Rehacer sin LLM exige el plan guardado de cada parte:** el de las presentaciones de un diseño anterior al 5 era de otro formato, así que pasarlas al diseño 5 cuesta ~9 llamadas por temario (`lint.py`, en L14, y `actualizar_estructura.py` lo avisan).

## Qué está probado

Catorce suites en `src/` (`python src/test_*.py`) que **no llaman a ningún LLM**: sustituyen las respuestas del LLM y de los embeddings por valores fijos y comprueban todo lo demás — esquemas, cronograma, escritura de páginas, protecciones, comandos reales. `test_ia.py` prueba con un cliente simulado que el proveedor de IA se configura por variables de entorno y funciona con o sin salida estructurada nativa. `test_compatibilidad.py` valida la estructura: la plantilla está limpia de datos de una instancia, el código es válido en Python 3.10+ y no depende de un sistema operativo, solo `vault.py` habla con el proveedor, las instrucciones para asistentes no dependen de un modelo, la documentación coincide con el código, y una copia que perdió las carpetas vacías (ZIP, git, Drive) arranca sana. `test_flujo_completo.py` encadena lint → correlate → planeador → temario → auditorías → presentaciones → lint sobre un vault de muestra inventado. `test_temario.py` prueba la redacción del temario: las figuras (dibujadas con matplotlib de verdad: expresiones peligrosas rechazadas, diagramas sin nodos superpuestos), la búsqueda en las fuentes (BM25, ES/EN), los esquemas y el flujo con validación y reintentos. `test_presentaciones.py` prueba PRESENTACIONES sin LLM y sin compilar: la lista de comandos permitidos del LaTeX que escribe el modelo (`latex_seguro.py`: lo que admite de los ejemplos y ~40 construcciones hostiles que rechaza, más 1500 cuerpos al azar con fichas hostiles), el diseño IUB de los ejemplos (preámbulo, portada, ruta, separadores, referencias, cierre, sin imágenes), la división del temario en partes, y el flujo (una llamada por parte, el plan por partes que evita llamadas —y que se revalida si alguien lo manipula—, reintentos, la diapositiva provisional, que un `.tex` inseguro no se escribe ni se compila, lint L14 y el comando real). `test_analizar_cambios.py` prueba ANALIZAR-CAMBIOS sobre un vault de muestra inventado: las secciones de un currículo y a qué página tocan, la línea base, currículos, manuales (con `ingest_manual.py --solo`), libros y PDF, los desfases entre el wiki y lo generado (cronograma, duración, alineación, correlación), `correlate.py --ra`, y que el análisis no escriba nada en `wiki/`, `generacion/` ni `raw/`. `test_actualizar_estructura.py` prueba ACTUALIZAR-ESTRUCTURA sobre plantillas sintéticas (política de cada archivo, conflictos, `.nuevo`, respaldo, `--deshacer`, migraciones, ZIP completos y parciales, el script del paquete, que la prueba en seco no ejecute código del paquete, que solo se instalen las rutas de la plantilla y que una migración sin PyYAML no se dé por hecha) y sobre la plantilla real: que su `config/manifiesto.json` esté al día y que una copia de `nuevo-cerebro.py` no difiera de ella. `test_indexar.py` usa LanceDB real y se omite si no está instalado; `test_replica.py` prueba `config/nuevo-cerebro.py` en cualquier sistema (y `nuevo-cerebro.ps1` solo en Windows).

## Qué falta por probar (tu primera corrida real)

- Las llamadas reales a un proveedor de IA (juez, embeddings, redacción de temas y temarios, extracción de manuales): el código y sus prompts están, pero nunca se han ejecutado contra una API real, ni la de OpenAI ni la de ningún servidor compatible (Ollama, OpenRouter…); las pruebas usan un cliente simulado. Los modos `json` y `texto` de `CEREBRO_SALIDA` tampoco se han probado con un modelo real: con modelos pequeños el JSON puede salir malformado más a menudo (hay 2 reintentos, y si fallan, un error claro).
- Si la API acepta los esquemas tal como están (solo el modo `estructurada`; en `json` y `texto` las restricciones las valida Pydantic en local): algunos llevan restricciones de Pydantic (mínimos y máximos de listas, rangos, patrones). Si rechazara alguna, hay que quitarla del esquema que se envía y validarla después en código, como ya se hace con el número de conceptos del temario. Prueba barata: `python src/ingest_manual.py ... --limite 1`.
- Que las presentaciones **compilen y se vean bien con pdfLaTeX**: el diseño 5 (`src/diseno_iub.py`, el preámbulo de las presentaciones de ejemplo del docente) **no se ha compilado en el equipo donde se escribió** (no tiene LaTeX). Usa paquetes estándar de TeX Live y Overleaf (`avant`, `babel`, `amsmath`, `siunitx`, `adjustbox`, `booktabs`, `tabularx`, `tikz`, `pgfplots`, `circuitikz`, `tcolorbox`, `listings`) y las pruebas comprueban su estructura y su seguridad, no el resultado visual. Lo que más riesgo tiene es el LaTeX que escribe el modelo: la lista de permitidos impide que lea o escriba archivos, pero no que un dibujo se salga de la diapositiva o que una construcción válida no compile. La primera vez, sube una carpeta de `generacion/presentaciones/CODIGO/` a Overleaf y revisa el `.log`; si una parte falla, bórrala del `.plan.json` (o corre con `--replanificar`) para pedirla otra vez. Tampoco se ha probado con un modelo real: si respeta las reglas de LaTeX y del lienzo, y cuántas diapositivas escribe por bloque (el prompt está en `src/prompts/prompt-presentacion.md`).
- El temario de tres pasos con un modelo real: que el modelo cumpla los esquemas y los mínimos sin agotar los reintentos (los mínimos de palabras y de elementos están en `src/temario.py` y `src/schema_temario.py`: se ajustan ahí), que la búsqueda en las fuentes traiga pasajes útiles con libros reales (los originales han de estar en `raw/` como `.md` o `.txt`; un PDF solo aporta su página del wiki), cuánto cuesta una asignatura completa (~100 llamadas) y que las gráficas y diagramas que el modelo especifica salgan legibles (los diagramas de más de 8 nodos quedan pequeños en la diapositiva).
- **ANALIZAR-CAMBIOS con un currículo real:** reconoce las secciones por encabezado, negrita o por el rótulo suelto de un PDF convertido (un rótulo de ≤ 9 palabras que nombra uno de los apartados de INGEST-CURRICULAR); con currículos de otro formato puede no partir bien —queda «sin reconocer» o todo el documento como una sola sección, sin ahorro pero sin error—, y la relevancia de un libro es por palabras (no entiende sinónimos ni el salto español/inglés). Se probó con documentos inventados, y su primera corrida real no tiene línea base (los documentos con página en el wiki se suponen incorporados).
- **ACTUALIZAR-ESTRUCTURA en una copia real que ya tenga contenido:** se probó sobre plantillas sintéticas, sobre la plantilla real y sobre una copia de `nuevo-cerebro.py`, no sobre una copia vieja con un año de uso. Las copias anteriores a `config/manifiesto.json` no saben qué editaste: sin la plantilla con que se hicieron (`--base`), todo lo que difiere queda «sin base» y hay que decidir archivo por archivo (`--sobrescribir`, `--conservar`). Las constantes de la institución que el README lista en «Convenciones» (`HORAS_POR_CREDITO`, `COLORES`…) viven dentro de archivos de la plantilla: si las editaste en tu copia, esos archivos serán conflictos en cada actualización (`--conservar` los da por buenos). La única migración de contenido que hay (1.20: quitar `presentacion_framework` de los temarios) y el mecanismo se probaron sobre copias sintéticas.
- La calidad de lo que un LLM real escriba, y un currículo y un manual reales de punta a punta.
- Las vistas Dataview: no se han abierto en Obsidian.

Recomendación: la primera vez, en una copia, con un programa pequeño (2–3 módulos y 1 manual), y `--dry-run` / `--limite` / `--sin-llm` para ver qué haría antes de gastar llamadas.
