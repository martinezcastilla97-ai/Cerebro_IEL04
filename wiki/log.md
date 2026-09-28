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
