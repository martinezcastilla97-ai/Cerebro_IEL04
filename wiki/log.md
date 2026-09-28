# Log del Wiki — Cerebro Docente

Registro cronológico append-only de todas las operaciones. Nunca eliminar entradas anteriores. Las entradas nuevas se agregan al final (la más antigua primero); así lo hacen también los scripts de `src/`.

**Formato de entradas:**
```
## [YYYY-MM-DD] operación | descripción
```

## [2026-09-28] ingest-curricular | IEL04 - Circuitos Eléctricos I

Fuente: `raw/curriculos/Tecnología en Gestión de Sistemas Eléctricos/IEL04 - Circuitos Eléctricos I.md` (Diseño y Planeamiento Curricular, diligenciado el 2020-06-05 por Raúl J. Vanegas R.).

Creadas:
- Programa [[Tecnología en Gestión de Sistemas Eléctricos]] (nivel Pregrado) con RA-PROG-1.
- Asignatura [[IEL04 - Circuitos Eléctricos I]]: ESPECÍFICO, HAD 26 / HP 26 / HTI 65, 2 créditos, teórico-práctica (derivado de HP > 0). Casillas: práctica de laboratorio y recurso de laboratorio marcados.
- RA [[IEL04-RA1]] (LC, 29 h), [[IEL04-RA2]] (RC, 29 h), [[IEL04-RA3]] (RL, 29 h), [[IEL04-RA4]] (RLC, 30 h). Suma 117 h = total del documento. En cada RA: CE1 `cognitiva_conceptual` (0.9); CE2 y CE3 "Realizar mediciones…" `manipulacion_fisica` (0.8).
- Competencia [[UC2]] (alcance programa: la numeración UC2 sin UC1 indica que es del programa) con EC1–EC3.
- Recursos web [[recursos-bibliograficos-institucionales]] y [[acienciasgalilei]].
- [[marco-pedagogico]]: estaba vacío; se transcribió el Anexo de este currículo y la asignatura lo sigue (`sigue_marco`).

Faltantes (bibliografía sin página en `wiki/fuentes/`; no se crearon páginas vacías; `bibliografia` de los RA queda en `[]`):
- Básica: Floyd, *Principios de circuitos eléctricos* (Pearson-Prentice Hall); Nahvi y Edminister, *Circuitos eléctricos y electrónicos* (McGraw-Hill).
- Complementaria: Johnson, Hilburn, Johnson y Scott, *Análisis básico de circuitos eléctricos* (Prentice Hall); Hayt, *Análisis de circuitos en ingeniería* (McGraw-Hill); Martínez Ramos, *Fundamentos de teoría de circuitos* (Thomson).
- Ningún libro trae ISBN en el documento. No cita normas técnicas.

Discrepancias y decisiones para revisar:
- Horas: el documento suma 117 = HAD 26 + HP 26 + HTI 65, o sea, trata HP como aparte de HAD; la convención del vault es que HAD ya incluye HP. Se ingirió tal cual. LINT L13: 26 + 65 = 91 ≠ 2 × 48 = 96. Afecta al PLANEADOR: con HAD 26 la sesión es de 2 h (26/14 < 3); si las horas presenciales fueran 52, sería de 4 h. Pendiente de confirmar con el docente.
- `fecha_aprobacion` vacía: el acta de Comité curricular no tiene número ni fecha; solo hay fecha de diligenciamiento.
- IEL04-RA3 trae solo dos contenidos procedimentales (falta el de "Diferenciación de parámetros" que sí tienen los otros RA); se respetó el documento.
- Tipo de módulo leído como ESPECÍFICO (la "X" sigue a la etiqueta, igual que en PREGRADO y en las casillas de estrategias). La fila Área básica / Profesional no tiene marca legible.

Siguiente: correr LINT (hecho: 0 errores, 1 aviso L13). CORRELATE cuando haya un manual de banco ingerido.

## [2026-09-28] corrección | IEL04: horas presenciales confirmadas por el docente

El docente confirmó que cada semana hay una sesión de 2 h de teoría y otra de 2 h de práctica. Se cambió `had_totales` de 26 a 52 en [[IEL04 - Circuitos Eléctricos I]] (26 teóricas + 26 prácticas; en el vault `had_totales` incluye las HP). `hp_totales` sigue en 26 y `tipo_abordaje` en teórico-práctica. Efecto en PLANEADOR: 52/14 ≥ 3 → sesiones de 4 h. LINT L13 sigue avisando (52 + 65 = 117 ≠ 2 × 48 = 96): inconsistencia horas/créditos del propio documento.

## [2026-09-28] ingest | Bibliografía de IEL04 (3 libros)
- Creadas: [[floyd-principios-circuitos-electricos]], [[boylestad-introduccion-analisis-circuitos]], [[deorsola-morcelle-circuitos-electricos-parte-1]]; conceptos [[capacitancia]], [[inductancia]], [[leyes-de-kirchhoff]], [[circuitos-rc]], [[circuitos-rl]], [[circuitos-rlc]].
- Actualizadas: `bibliografia` de [[IEL04-RA1]] (Floyd, Boylestad), [[IEL04-RA2]], [[IEL04-RA3]] y [[IEL04-RA4]] (Floyd, Boylestad, Deorsola); sección Bibliografía de [[IEL04 - Circuitos Eléctricos I]]; [[index]].
- Originales en `raw/bibliografia/` (Markdown; TEMARIO los lee completos: 2697, 4281 y 340 pasajes). Están en `.gitignore`: son obras con derechos de autor y el repositorio es público, así que no se suben a GitHub.
- Notas: solo Floyd está en la bibliografía del currículo (básica; el currículo no indica edición y se cargó la 8.ª). Boylestad y Deorsola son fuentes adicionales del docente. Deorsola no se enlaza a RA1: no trata tipos, estructura ni identificación de capacitores e inductores. Siguen faltando Nahvi/Edminister (básica), Johnson et al., Hayt y Martínez Ramos (complementaria).
- Se recibió un archivo `Circuitos_Electricos_III.md` vacío (0 bytes): no se ingirió.
- Entidades: no se crearon páginas de autores ni editoriales; no aportan al uso curricular del wiki.

## [2026-09-28] /planeador IEL04
- cronograma de 14 semanas, sesión de 4 h, 4 RA
- temas redactados por el LLM
- los temas los redactó el asistente de la sesión siguiendo `src/prompts/prompt-planeador.md` (sin proveedor `CEREBRO_*` configurado); cronograma calculado por `src/planeador.py`

## [2026-09-28] /temario IEL04 semana 1
- RA: IEL04-RA1
- tema: Condensadores: estructura, comportamiento interno, identificación y tipos
- 4278 palabras, 7 ecuaciones, 6 tablas, 3 figuras; 35 pasajes de 2 fuente(s) cargada(s)
- el plan, las unidades y el cierre los redactó el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` y los pasajes que eligió `src/pasajes.py` (sin proveedor `CEREBRO_*` configurado); `src/temario.py` validó cada respuesta, armó la página y dibujó las figuras. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales.

## [2026-09-28] /temario IEL04 semana 2
- RA: IEL04-RA1
- tema: Bobinas o inductores: estructura, comportamiento interno, identificación y tipos
- 4252 palabras, 6 ecuaciones, 6 tablas, 3 figuras; 35 pasajes de 2 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales.

## [2026-09-28] /temario IEL04 semana 3
- RA: IEL04-RA1
- tema: Condensadores y bobinas en serie, en paralelo y mixto: cálculo y medición en circuitos L, C y LC
- 3763 palabras, 8 ecuaciones, 4 tablas, 3 figuras; 35 pasajes de 2 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; los valores de los componentes son los del kit de las semanas 1 y 2.

## [2026-09-28] /temario IEL04 semana 4
- RA: IEL04-RA2
- tema: Circuito RC en serie: análisis y Ley de Voltajes de Kirchhoff
- 3958 palabras, 6 ecuaciones, 4 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; el condensador es el C2 del kit de la semana 1.

## [2026-09-28] /temario IEL04 semana 6
- RA: IEL04-RA2
- tema: Circuito RC en paralelo: análisis y Ley de Corrientes de Kirchhoff
- 3795 palabras, 5 ecuaciones, 3 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; los componentes son los del caso de la semana 4.

## [2026-09-28] /temario IEL04 semana 7
- RA: IEL04-RA2
- tema: Cálculo y medición de parámetros en circuitos RC serie y paralelo: unidades, simbología y nomenclatura
- 3739 palabras, 5 ecuaciones, 5 tablas, 2 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; R2 y C son los componentes de las semanas 4 y 6.

## [2026-09-28] /temario IEL04 semana 8
- RA: IEL04-RA3
- tema: Circuitos RL en serie y en paralelo: análisis con las leyes de voltajes y corrientes de Kirchhoff
- 3827 palabras, 7 ecuaciones, 4 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; la bobina es L3 del kit de la semana 2.

## [2026-09-28] /temario IEL04 semana 9
- RA: IEL04-RA3
- tema: Cálculo y medición de parámetros en circuitos RL serie y paralelo según el tipo de conexionado
- 3712 palabras, 6 ecuaciones, 4 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; la bobina de 3.3 mH sin marcado es un componente hipotético del caso.

## [2026-09-28] /temario IEL04 semana 11
- RA: IEL04-RA4
- tema: Circuito RLC en serie: análisis y Ley de Voltajes de Kirchhoff
- 3775 palabras, 5 ecuaciones, 4 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; L3 y C2 son los componentes del kit de las semanas 1 y 2.

## [2026-09-28] /temario IEL04 semana 12
- RA: IEL04-RA4
- tema: Circuito RLC en paralelo: análisis y Ley de Corrientes de Kirchhoff
- 3753 palabras, 6 ecuaciones, 5 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; L3 y C2 son los componentes del kit de las semanas 1 y 2.

## [2026-09-28] /temario IEL04 semana 13
- RA: IEL04-RA4
- tema: Cálculo y medición de parámetros en circuitos RLC serie y paralelo: unidades, simbología y nomenclatura
- 3672 palabras, 4 ecuaciones, 4 tablas, 3 figuras; 35 pasajes de 3 fuente(s) cargada(s)
- redactado por el asistente de la sesión con los prompts de `src/prompts/prompt-temario-*.md` (sin proveedor `CEREBRO_*`); `src/temario.py` validó, armó y dibujó. Las lecturas del caso de estudio son valores de ejemplo, no mediciones reales; L3 y C2 son los componentes del kit de las semanas 1 y 2. Con esta sesión quedan generados los 11 temarios de las semanas de clase de IEL04.

## [2026-09-28] /presentaciones IEL04
- 11 presentaciones escritas en generacion/presentaciones/IEL04/ (semanas 1, 2, 3, 4, 6, 7, 8, 9, 11, 12 y 13), de 30 a 35 diapositivas cada una; estado `generada`, sin avisos
- docente: Ing. Sergio Martinez Castilla · programa: Tecnología en Gestión de Sistemas Eléctricos · contacto: smartinezc@unibarranquilla.edu.co
- 99 partes (apertura y 8 bloques por temario) escritas por el asistente de la sesión a partir de los datos estructurados de cada temario (sin proveedor `CEREBRO_*`) y verificadas con `presentaciones.validar_parte` (lista de permitidos); `src/presentaciones.py` armó el marco y la verificación estática
- compiladas con `presentaciones.compilar` (pdfLaTeX de TeX Live, -no-shell-escape, openin_any=p/openout_any=p): 11 PDF sin errores
- corrección de la plantilla: `latex_seguro.COMANDOS_CUERPO` no admitía `\texttwosuperior` y otros símbolos que el propio `Conversor` escribe (², ³, ª, º, ¼, ¾, ‰, ¬), así que un título del índice con «CV²/2» impedía escribir el .tex; se agregaron con su prueba en `test_presentaciones.py`. En la portada, el contacto va en `\tiny` para que un correo largo no se salga del panel (`diseno_iub.portada`)

## [2026-09-28] /correlate-bibliografia IEL04
- IEL04-semana01: revisar (juez)
- IEL04-semana02: revisar (juez)
- IEL04-semana03: cubierta (juez)
- IEL04-semana04: revisar (juez)
- IEL04-semana06: cubierta (juez)
- IEL04-semana07: revisar (juez)
- IEL04-semana08: cubierta (juez)
- IEL04-semana09: revisar (juez)
- IEL04-semana11: cubierta (juez)
- IEL04-semana12: revisar (juez)
- IEL04-semana13: revisar (juez)
- vía: ningún temario tiene el marcador `[FUENTE NO CARGADA EN raw/]`, así que los 11 pasaron al juez de respaldo; hizo de juez el asistente de la sesión (sin proveedor `CEREBRO_*`), con `prompt-correlate-bibliografia.md` y solo con los resúmenes de las fuentes, como pide el protocolo
- resultado: 4 `cubierta` (semanas 3, 6, 8 y 11) y 7 `revisar` (semanas 1, 2, 4, 7, 9, 12 y 13); ningún `vacio_detectado`
- nota fuera del juicio (búsqueda en el texto completo de `raw/bibliografia/`): el código de colores de resistores (Floyd), las letras de tolerancia de condensadores (Boylestad), las puntas ×10 (Floyd), Rp = RW(Q² + 1) (Floyd), la corrección del factor de potencia (Boylestad) y los filtros pasabanda y rechazabanda (Floyd, Boylestad) sí están en los libros cargados: esos `revisar` se deben a que el resumen de la página de la fuente no los menciona (el de Floyd se corta en §17–3). El marcado de inductores (semana 2) no aparece en ninguna fuente cargada

## [2026-09-28] ingest (actualización) | Resúmenes de Floyd y Boylestad
- Actualizadas: [[floyd-principios-circuitos-electricos]], [[boylestad-introduccion-analisis-circuitos]]
- Notas: se reescribieron `## Resumen` y `## Puntos clave` para que quepan enteros en los ~1800 caracteres que leen TEMARIO y el juez de CORRELATE-BIBLIOGRAFIA (el de Floyd se cortaba en §17–3). Se agregaron, con su sección verificada en el texto completo de `raw/bibliografia/`: Floyd §2–5 (código de colores), §7–4 (efecto de carga), §11–10 (puntas ×1 y ×10), §12–2 y apéndice C (rotulado de capacitores), §16–7 (corrección del factor de potencia), §17–6 (Rp(eq) = RW(Q² + 1)), §17–8 y cap. 18 (ancho de banda, filtros pasabanda y rechazabanda); Boylestad §10.6 (rotulado y letras de tolerancia J y K), §12.5 (valores estándar y tolerancias de inductores), §19.8 (corrección del factor de potencia), §20.8 (resonancia en paralelo con la resistencia de la bobina), §23.7 y §23.8 (filtros pasa-banda y rechaza-banda)

## [2026-09-28] /correlate-bibliografia IEL04
- IEL04-semana01: cubierta (juez)
- IEL04-semana02: revisar (juez)
- IEL04-semana03: cubierta (juez)
- IEL04-semana04: cubierta (juez)
- IEL04-semana06: cubierta (juez)
- IEL04-semana07: revisar (juez)
- IEL04-semana08: cubierta (juez)
- IEL04-semana09: cubierta (juez)
- IEL04-semana11: cubierta (juez)
- IEL04-semana12: cubierta (juez)
- IEL04-semana13: cubierta (juez)
- segunda corrida, tras ampliar los resúmenes de Floyd y Boylestad: 9 `cubierta` y 2 `revisar`; juez: el asistente de la sesión (sin proveedor `CEREBRO_*`), solo con los resúmenes
- semana 2 (`revisar`, hueco real): ninguna fuente cargada trae la lectura del marcado de inductores (código de colores, código de tres dígitos, «R» decimal); además, el temario cita [1] (Floyd) para el código de colores de inductores y Floyd solo lo menciona de pasada: conviene revisar esa cita o cargar una hoja de datos de fabricante
- semana 7 (`revisar`): la salida de 50 Ω del generador, el ancho de banda del multímetro y las tierras comunes no están en ninguna fuente cargada; las puntas ×10 y el efecto de carga sí (Floyd §11–10 y §7–4)


## [2026-09-28] /correlate-planeador IEL04
- IEL04-RA1: cubierto — Las semanas 1 a 3 cubren los ocho contenidos conceptuales (estructura, comportamiento interno, identificación, tipos y asociaciones de condensadores y bobinas) y los tres criterios: identificación en las semanas 1 y 2 y medición en circuitos L, C y LC en la semana 3.
- IEL04-RA2: revisar — Los temas cubren el análisis y las leyes de Kirchhoff del RC en serie y en paralelo y la medición (semana 7), pero ninguno nombra el criterio «Identificar los tipos de resistores y capacitores», que debería aparecer, por ejemplo, en la semana 4.
- IEL04-RA3: revisar — Los temas cubren el análisis y las leyes de Kirchhoff del RL en serie y en paralelo y la medición (semana 9), pero ninguno nombra el criterio «Identificar los tipos de resistores e inductores», que debería aparecer, por ejemplo, en la semana 8.
- IEL04-RA4: revisar — Los temas cubren el análisis y las leyes de Kirchhoff del RLC en serie y en paralelo y la medición (semana 13), pero ninguno nombra el criterio «Identificar los tipos de resistores, inductores y capacitores», que debería aparecer, por ejemplo, en la semana 11.
- juez: el asistente de la sesión (sin proveedor `CEREBRO_*`), solo con el RA y los temas del planeador, como pide el protocolo
- el `revisar` de RA2, RA3 y RA4 está solo en el texto del planeador: los temarios de las semanas 4, 8 y 11 sí desarrollan la identificación de tipos en su bloque 2 (4.2.1). Para cerrarlo basta con nombrar la identificación en el tema de esas semanas del planeador (editándolo a mano, sin `--forzar`, que regeneraría todos los temas)
