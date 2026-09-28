---
tipo: index
fecha_actualizacion: 2026-09-28
total_fuentes: 3
total_entidades: 0
total_conceptos: 6
total_consultas: 0
total_programas: 1
total_asignaturas: 1
total_resultados_aprendizaje: 4
total_recursos_web: 2
modulos: [IEL04]
---

# Índice del Wiki — Cerebro Docente

Catálogo completo de todas las páginas. El LLM lee este archivo primero al responder cualquier consulta.

---

## Fuentes

| Página | Resumen | Fecha |
|--------|---------|-------|
| [[floyd-principios-circuitos-electricos]] | Floyd, 8.ª ed. (2007). Bibliografía básica de IEL04: capacitores, inductores, circuitos RC, RL y RLC en serie y paralelo. | 2026-09-28 |
| [[boylestad-introduccion-analisis-circuitos]] | Boylestad, 10.ª ed. (2004). Fuente adicional: análisis de cd y ca, transitorios, resonancia, simulación. | 2026-09-28 |
| [[deorsola-morcelle-circuitos-electricos-parte-1]] | Deorsola y Morcelle del Valle, UNLP (2017). Fuente adicional: elementos pasivos, Kirchhoff, fasores, régimen transitorio RL/GC/RLC. | 2026-09-28 |

---

## Equipos de Laboratorio

Bancos de entrenamiento físico y sus manuales. A diferencia de las demás fuentes (libros/handbooks), son manuales de equipo real — permiten verificar experimentalmente la teoría documentada en el resto del wiki, y son las fuentes que CORRELATE busca para `requiere_practica`.

| Página | Resumen | Fecha |
|--------|---------|-------|

---

## Programas

| Página | Nivel | Asignaturas |
|--------|-------|-------------|
| [[Tecnología en Gestión de Sistemas Eléctricos]] | Pregrado | 1 |

---

## Asignaturas

| Asignatura | Programa | Abordaje | HAD / HP / HTI | Créditos | RA | Competencias |
|---|---|---|---|---|---|---|
| [[IEL04 - Circuitos Eléctricos I]] | [[Tecnología en Gestión de Sistemas Eléctricos]] | teórico-práctica | 52 / 26 / 65 | 2 | [[IEL04-RA1]] · [[IEL04-RA2]] · [[IEL04-RA3]] · [[IEL04-RA4]] | [[UC2]] |

### Resultados de aprendizaje

| RA | Enunciado | Horas |
|---|---|---|
| [[IEL04-RA1]] | Calcular un circuito capacitivo, inductivo y LC, sea en serie o paralelo. | 29 |
| [[IEL04-RA2]] | Calcular un circuito resistivo, capacitivo y RC, sea en serie o paralelo. | 29 |
| [[IEL04-RA3]] | Calcular un circuito resistivo, inductivo y RL, sea en serie o paralelo. | 29 |
| [[IEL04-RA4]] | Calcular un circuito resistivo, inductivo, capacitivo y RLC, sea en serie o paralelo. | 30 |

### Competencias

| Página | Alcance | Asignaturas |
|---|---|---|
| [[UC2]] | programa | [[IEL04 - Circuitos Eléctricos I]] |

Ver `CLAUDE.md` § "Capa curricular" para la regla de bifurcación teórica/teórico-práctica, y [[../correlaciones/matriz-ra-practica]] para la vista de correlación (también vacía hasta que haya contenido).

---

## Recursos Web

Webgrafía y bases de datos institucionales que citan los currículos. Nunca se mezclan con las fuentes bibliográficas.

| Página | Tipo | Asignaturas |
|--------|------|-------------|
| [[recursos-bibliograficos-institucionales]] | base_datos_institucional | [[IEL04 - Circuitos Eléctricos I]] |
| [[acienciasgalilei]] | pagina_web | [[IEL04 - Circuitos Eléctricos I]] |

---

## Marco pedagógico institucional

Nodo único compartido por todas las asignaturas: [[marco-pedagogico]] (transcrito desde el Anexo de IEL04; lo sigue [[IEL04 - Circuitos Eléctricos I]]).

---

## Generación y auditoría

Capa de generación (`generacion/planeador/`, `generacion/temarios/`, `generacion/presentaciones/`). **IEL04:** planeador `generacion/planeador/IEL04-planeador.md` (14 semanas, sesiones de 4 h); 11 temarios `generacion/temarios/IEL04-semana{01,02,03,04,06,07,08,09,11,12,13}.md` (las semanas 5, 10 y 14 son de examen); 11 presentaciones Beamer en `generacion/presentaciones/IEL04/` (`.tex`, `.plan.json` y `.pdf` compilado con pdfLaTeX). Vistas de auditoría en `correlaciones/`: [[../correlaciones/matriz-ra-practica]] · [[../correlaciones/matriz-ra-planeador]] · [[../correlaciones/matriz-temario-bibliografia]] · [[../correlaciones/matriz-ra-bibliografia]] (reservada, sin protocolo todavía) · [[../correlaciones/matriz-temario-presentacion]] · [[../correlaciones/matriz-temario-profundidad]] (palabras, ecuaciones, tablas, figuras y pasajes de fuentes de cada temario). Ver `CLAUDE.md` § "Capa de generación".

---

## Entidades

| Página | Tipo | Fuentes |
|--------|------|---------|

---

## Conceptos

| Página | Descripción breve | Fuentes |
|--------|-------------------|---------|
| [[capacitancia]] | Almacenamiento de carga; τ = RC; serie y paralelo | 3 |
| [[inductancia]] | Oposición a cambios de corriente; τ = L/R; serie y paralelo | 3 |
| [[leyes-de-kirchhoff]] | LVK y LCK, también con fasores | 3 |
| [[circuitos-rc]] | Impedancia, análisis serie/paralelo y transitorio RC | 3 |
| [[circuitos-rl]] | Impedancia, análisis serie/paralelo y transitorio RL | 3 |
| [[circuitos-rlc]] | Análisis serie/paralelo y resonancia | 3 |
| [[impedancia-y-admitancia]] | Z = R ± jX, Y = G + jB; serie con Z, paralelo con Y | 3 |
| [[reactancia]] | X_C = 1/(2πfC), X_L = 2πfL; dependencia de la frecuencia | 3 |
| [[fasores]] | Representación compleja de magnitudes sinusoidales; diagrama fasorial | 3 |
| [[resonancia]] | X_L = X_C, f_r, factor de calidad Q, ancho de banda, tanque real y filtros | 2 |
| [[factor-de-potencia]] | P, Q, S, triángulo de potencia y corrección con capacitores | 2 |
| [[constante-de-tiempo]] | τ = RC y τ = L/R; 63.2 % y 5τ; medición con onda cuadrada | 3 |

---

## Consultas

| Página | Pregunta | Fecha |
|--------|----------|-------|
